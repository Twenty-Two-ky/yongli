import asyncio
import time
import httpx
from http_runner import execute_step

class LoadTestRunner:
    """Execute load test with rate limiting and concurrency control."""
    def __init__(self, client: httpx.AsyncClient, base_url: str, template: dict, load_config: dict):
        self.client = client
        self.base_url = base_url
        self.template = template
        self.rate_per_second = load_config.get("rate_per_second", 100)
        self.duration_seconds = load_config.get("duration_seconds", 60)
        self.max_concurrent = load_config.get("max_concurrent", 200)
        self.results = []
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        self._start_time = None

    async def run(self):
        self._start_time = time.time()
        deadline = self._start_time + self.duration_seconds
        tasks = []
        request_count = 0
        while time.time() < deadline:
            batch_start = time.time()
            batch_tasks = []
            for _ in range(self.rate_per_second):
                request_count += 1
                batch_tasks.append(asyncio.create_task(self._send_one()))
            tasks.extend(batch_tasks)
            elapsed = time.time() - batch_start
            sleep_time = 1.0 - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        # Wait for all in-flight requests to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        return self.results

    async def _send_one(self):
        async with self._semaphore:
            result = await execute_step(self.client, self.base_url, self.template)
            self.results.append(result)

def compute_aggregated_stats(results: list[dict]) -> dict:
    """Compute aggregated statistics from result list."""
    if not results:
        return {}
    total = len(results)
    success = sum(1 for r in results if r["is_success"])
    fail = total - success
    latencies = sorted([r["latency_ms"] for r in results if r["latency_ms"] is not None])
    if not latencies:
        return {"success_count": success, "fail_count": fail, "total_count": total}
    def percentile(data, p):
        k = (len(data) - 1) * p / 100
        f = int(k)
        c = k - f
        return data[f] if f + 1 >= len(data) else data[f] + c * (data[f + 1] - data[f])
    return {
        "success_count": success, "fail_count": fail, "total_count": total,
        "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
        "p50_latency_ms": round(percentile(latencies, 50), 2),
        "p95_latency_ms": round(percentile(latencies, 95), 2),
        "p99_latency_ms": round(percentile(latencies, 99), 2),
        "min_latency_ms": round(latencies[0], 2),
        "max_latency_ms": round(latencies[-1], 2),
        "error_rate": round(fail / total, 4) if total > 0 else 0,
    }
