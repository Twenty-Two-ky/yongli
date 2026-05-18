import time
import httpx

async def execute_step(client: httpx.AsyncClient, base_url: str, step: dict, step_index: int = 0) -> dict:
    """Execute a single HTTP step and return result dict."""
    method = step.get("method", "GET").upper()
    path = step.get("path", "/")
    url = f"{base_url.rstrip('/')}{path}"
    headers = step.get("headers", {}) or {}
    body = step.get("body")
    query = step.get("query")
    assertions = step.get("assert", {})
    result = {"step_index": step_index, "method": method, "url": url, "request_body": str(body)[:500] if body else None, "request_headers": headers, "is_success": True, "status_code": None, "response_body": None, "latency_ms": None, "error_message": None}
    try:
        start = time.time()
        kwargs = {"headers": headers}
        if body:
            kwargs["json"] = body
        if query:
            kwargs["params"] = query
        resp = await client.request(method, url, **kwargs)
        result["latency_ms"] = round((time.time() - start) * 1000, 2)
        result["status_code"] = resp.status_code
        result["response_body"] = resp.text[:500]
        # Assertions
        if "status_code" in assertions:
            result["is_success"] = resp.status_code == assertions["status_code"]
        elif "status_code_in" in assertions:
            result["is_success"] = resp.status_code in assertions["status_code_in"]
    except Exception as e:
        result["is_success"] = False
        result["error_message"] = f"{type(e).__name__}: {str(e)}"
        result["latency_ms"] = round((time.time() - start) * 1000, 2) if 'start' in dir() else 0
    return result
