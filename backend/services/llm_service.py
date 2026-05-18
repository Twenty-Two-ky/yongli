import json
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, LLM_MODEL

client = Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are an API testing expert. Given a natural language instruction and environment info, output a JSON task definition.

Output schema — exactly one of three modes:

1. sequential (single API test):
{"mode": "sequential", "steps": [{"step": 1, "method": "GET|POST|PUT|DELETE", "path": "/api/v1/...", "headers": {}, "body": {} or null, "query": {} or null, "assert": {"status_code": 200}}]}

2. parameterized (abnormal input test):
{"mode": "parameterized", "template": {"method": "...", "path": "...", "headers": {}, "body": {} or null, "query": {} or null}, "payloads": [{"label": "description", "value": "the value to substitute for ${PAYLOAD}"}], "assert": {"status_code_in": [200, 400, 422]}}

3. load (concurrency stress test):
{"mode": "load", "template": {"method": "...", "path": "...", "headers": {}, "body": {} or null, "query": {} or null}, "load_config": {"rate_per_second": 100, "duration_seconds": 60, "max_concurrent": 200}}

Rules:
- Infer the mode from the user's intent. "测试/验证/校验" + single endpoint → sequential. "异常输入/空值/特殊字符/boundary/fuzz" → parameterized. "并发/压测/QPS/高并发/每秒" → load.
- Use the environment's auth_config to fill credentials in login steps.
- Use the environment's base_url to construct full paths or keep paths relative starting with /api/v1/.
- For parameterized mode, generate 3-5 diverse payloads (empty, very long, special chars, unicode, SQL-like).
- Output ONLY valid JSON, no markdown, no explanation."""


# ── Fallback: pre-defined parsed_actions for the 3 demo scenarios ──
# Keyed by simple keyword matching. Used when LLM call fails (network, timeout, API error).
FALLBACK_PARSED_ACTIONS = {
    "login_admin_123456": {
        "task_type": "single",
        "parsed_actions": {
            "mode": "sequential",
            "steps": [{
                "step": 1, "method": "POST", "path": "/api/v1/login",
                "headers": {"Content-Type": "application/json"},
                "body": {"username": "admin", "password": "123456"},
                "query": None,
                "assert": {"status_code": 200}
            }]
        }
    },
    "search_abnormal_input": {
        "task_type": "abnormal",
        "parsed_actions": {
            "mode": "parameterized",
            "template": {
                "method": "GET", "path": "/api/v1/products",
                "headers": {}, "body": None, "query": {"keyword": "${PAYLOAD}"}
            },
            "payloads": [
                {"label": "empty", "value": ""},
                {"label": "long_string", "value": "A" * 5000},
                {"label": "special_chars", "value": "<script>alert(1)</script>"},
                {"label": "sql_injection", "value": "' OR '1'='1"},
                {"label": "unicode", "value": "测试🔥"}
            ],
            "assert": {"status_code_in": [200, 400, 422]}
        }
    },
    "load_test_search": {
        "task_type": "stress",
        "parsed_actions": {
            "mode": "load",
            "template": {
                "method": "GET", "path": "/api/v1/products",
                "headers": {}, "body": None, "query": {"keyword": "test"}
            },
            "load_config": {"rate_per_second": 100, "duration_seconds": 60, "max_concurrent": 200}
        }
    }
}

def _match_fallback(nl_text: str) -> dict | None:
    """Simple keyword matching for fallback when LLM is unavailable."""
    lower = nl_text.lower()
    if ("登录" in nl_text or "login" in lower) and "admin" in lower and "123456" in nl_text:
        return FALLBACK_PARSED_ACTIONS["login_admin_123456"]
    if ("异常" in nl_text or "空值" in nl_text or "特殊字符" in nl_text) and ("keyword" in lower or "搜索" in nl_text or "search" in lower):
        return FALLBACK_PARSED_ACTIONS["search_abnormal_input"]
    if ("并发" in nl_text or "压测" in nl_text or "qps" in lower) and ("每秒" in nl_text or "持续" in nl_text or "分钟" in nl_text):
        return FALLBACK_PARSED_ACTIONS["load_test_search"]
    return None


def parse_nl_task(natural_language: str, environment: dict) -> dict:
    """Parse natural language into a task definition. LLM-first with keyword fallback."""
    env_context = f"""Environment: {environment['name']}
Base URL: {environment['base_url']}
Auth config: {json.dumps(environment.get('auth_config', {}))}
Default headers: {json.dumps(environment.get('default_headers', {}))}"""

    try:
        message = client.messages.create(
            model=LLM_MODEL,
            max_tokens=2048,
            temperature=0,
            timeout=15,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Environment info:\n{env_context}\n\nInstruction: {natural_language}"}],
        )
        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        parsed = json.loads(response_text)
        mode = parsed["mode"]
        task_type_map = {"sequential": "single", "parameterized": "abnormal", "load": "stress"}
        task_type = task_type_map.get(mode, "single")
        return {
            "task_type": task_type,
            "parsed_actions": parsed,
            "source": "llm",
            "inferred_env_reason": f"AI matched environment '{environment['name']}' based on instruction context",
        }
    except Exception as llm_error:
        fallback = _match_fallback(natural_language)
        if fallback:
            return {
                **fallback,
                "source": "fallback",
                "llm_error": str(llm_error),
                "inferred_env_reason": f"LLM unavailable — used cached fallback for environment '{environment['name']}'",
            }
        raise


FAILURE_ANALYSIS_PROMPT = """You are an API failure analyst. Given a task context and a list of failed test results, categorize each failure and provide a root cause summary.

Categories: "401_auth_failure", "500_server_error", "400_client_error", "404_not_found", "assertion_failure", "network_timeout", "other"

Output JSON:
{"summary": "one-sentence root cause analysis", "failure_categories": [{"category": "401_auth_failure", "count": N, "sample_errors": ["error message 1", "error message 2"]}]}

Rules:
- Group similar errors together even if the error messages differ slightly.
- If multiple 500 errors share the same pattern, flag it as a probable server-side code bug.
- If 401 errors appear with valid credentials, flag it as an auth config issue.
- Output ONLY valid JSON."""


def analyze_failures(task_context: dict, failed_results: list[dict]) -> dict:
    """Analyze failed results and return categorized analysis."""
    if not failed_results:
        return {"summary": "All tests passed.", "failure_categories": []}

    failures_text = "\n".join([
        f"- [{r.get('method', 'GET')} {r.get('url', '')}] status={r.get('status_code', 'N/A')} error={r.get('error_message', 'N/A')}"
        for r in failed_results
    ])

    message = client.messages.create(
        model=LLM_MODEL,
        max_tokens=1024,
        system=FAILURE_ANALYSIS_PROMPT,
        messages=[{"role": "user", "content": f"Task: {task_context.get('natural_language', '')}\nTask type: {task_context.get('task_type', '')}\n\nFailed results ({len(failed_results)} failures):\n{failures_text}"}],
    )

    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    return json.loads(response_text)
