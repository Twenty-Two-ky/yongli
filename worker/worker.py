import asyncio
import httpx
from config import MASTER_URL, WORKER_NAME, HEARTBEAT_INTERVAL, LONG_POLL_TIMEOUT, RESULTS_BATCH_SIZE
from http_runner import execute_step
from concurrency import LoadTestRunner, compute_aggregated_stats

def _substitute_payload(template: dict, payload_value) -> dict:
    """Recursively replace ${PAYLOAD} placeholder in template. Handles any value type safely."""
    import copy
    result = copy.deepcopy(template)
    def walk(obj):
        if isinstance(obj, dict):
            return {k: walk(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [walk(v) for v in obj]
        if isinstance(obj, str):
            if obj == "${PAYLOAD}":
                return payload_value  # preserve original type
            if "${PAYLOAD}" in obj:
                return obj.replace("${PAYLOAD}", str(payload_value))
            return obj
        return obj
    return walk(result)

async def main():
    worker_id = None
    async with httpx.AsyncClient(timeout=30) as client:
        # Register
        resp = await client.post(f"{MASTER_URL}/api/workers/register", json={"name": WORKER_NAME})
        worker = resp.json()
        worker_id = worker["id"]
        print(f"[{WORKER_NAME}] Registered as id={worker_id}")

        while True:
            # Heartbeat
            try:
                await client.post(f"{MASTER_URL}/api/workers/{worker_id}/heartbeat")
            except Exception as e:
                print(f"[{WORKER_NAME}] Heartbeat failed: {e}")

            # Long-poll for task
            try:
                resp = await client.get(f"{MASTER_URL}/api/workers/{worker_id}/next-task?wait=15", timeout=LONG_POLL_TIMEOUT + 5)
            except httpx.TimeoutException:
                continue
            except Exception as e:
                print(f"[{WORKER_NAME}] Fetch task error: {e}")
                await asyncio.sleep(5)
                continue

            if resp.status_code == 204:
                continue

            task = resp.json()
            task_id = task["id"]
            env_id = task["environment_id"]
            parsed = task["parsed_actions"]
            mode = parsed.get("mode", "sequential")

            # Get environment base_url
            env_resp = await client.get(f"{MASTER_URL}/api/environments")
            envs = env_resp.json()
            env = next((e for e in envs if e["id"] == env_id), None)
            if not env:
                print(f"[{WORKER_NAME}] Environment {env_id} not found")
                continue
            base_url = env["base_url"]

            print(f"[{WORKER_NAME}] Executing task {task_id}, mode={mode}")

            try:
                if mode == "sequential":
                    results = []
                    for i, step in enumerate(parsed.get("steps", [])):
                        r = await execute_step(client, base_url, step, step_index=i + 1)
                        results.append(r)
                    agg = compute_aggregated_stats(results)
                    await _submit_batch(client, task_id, results, agg, final=True)

                elif mode == "parameterized":
                    results = []
                    template = parsed.get("template", {})
                    payloads = parsed.get("payloads", [])
                    assertions = parsed.get("assert", {})
                    for i, p in enumerate(payloads):
                        step = _substitute_payload(template, p["value"])
                        step["assert"] = assertions
                        r = await execute_step(client, base_url, step, step_index=i + 1)
                        r["step_label"] = p.get("label", "")
                        results.append(r)
                    agg = compute_aggregated_stats(results)
                    await _submit_batch(client, task_id, results, agg, final=True)

                elif mode == "load":
                    load_config = parsed.get("load_config", {})
                    template = parsed.get("template", {})
                    runner = LoadTestRunner(client, base_url, template, load_config)
                    all_results = await runner.run()
                    # Stream results in batches — pass cumulative stats so UI shows growing total
                    batch_size = RESULTS_BATCH_SIZE
                    cumulative = []
                    for i in range(0, len(all_results), batch_size):
                        batch = all_results[i:i + batch_size]
                        cumulative.extend(batch)
                        is_final = (i + batch_size) >= len(all_results)
                        agg = compute_aggregated_stats(cumulative)  # cumulative, not per-batch
                        await _submit_batch(client, task_id, batch, agg, final=is_final)

                print(f"[{WORKER_NAME}] Task {task_id} completed")
            except Exception as e:
                print(f"[{WORKER_NAME}] Task {task_id} execution error: {e}")
                try:
                    await client.post(f"{MASTER_URL}/api/tasks/{task_id}/results", json={
                        "aggregated": {"success_count": 0, "fail_count": 1, "total_count": 1, "error_rate": 1.0},
                        "results": [{"method": "ERROR", "url": "", "error_message": str(e), "is_success": False}],
                        "final": True,
                    })
                except Exception:
                    pass

async def _submit_batch(client, task_id, results, agg, final=False):
    try:
        await client.post(f"{MASTER_URL}/api/tasks/{task_id}/results", json={
            "aggregated": agg,
            "results": results,
            "final": final,
        })
    except Exception as e:
        print(f"[{WORKER_NAME}] Submit batch error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
