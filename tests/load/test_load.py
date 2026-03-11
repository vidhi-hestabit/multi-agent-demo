"""
Basic load test - sends concurrent queries to the orchestrator.
Requires all services running.
Run with: pytest tests/load/test_load.py -v -s
"""

import asyncio
import time
import httpx
import pytest

ORCHESTRATOR_URL = "http://localhost:8004"
CONCURRENCY = 5
TOTAL_REQUESTS = 10

QUERIES = [
    "What is the weather in London?",
    "Latest AI news",
    "Weather in Tokyo",
    "News about climate change",
    "Weather forecast for Paris",
]


async def single_request(client: httpx.AsyncClient, query: str, idx: int) -> dict:
    start = time.perf_counter()
    try:
        r = await client.post(
            f"{ORCHESTRATOR_URL}/query",
            json={"query": query, "stream": False},
            timeout=60,
        )
        elapsed = (time.perf_counter() - start) * 1000
        return {"idx": idx, "query": query, "status": r.status_code, "elapsed_ms": elapsed, "ok": r.status_code == 200}
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return {"idx": idx, "query": query, "status": 0, "elapsed_ms": elapsed, "ok": False, "error": str(e)}


@pytest.mark.asyncio
async def test_concurrent_load():
    try:
        async with httpx.AsyncClient(timeout=5) as check:
            r = await check.get(f"{ORCHESTRATOR_URL}/health")
            r.raise_for_status()
    except Exception:
        pytest.skip("Orchestrator not running")

    async with httpx.AsyncClient() as client:
        tasks = [
            single_request(client, QUERIES[i % len(QUERIES)], i)
            for i in range(TOTAL_REQUESTS)
        ]

        start_all = time.perf_counter()
        results = await asyncio.gather(*tasks)
        total_elapsed = (time.perf_counter() - start_all) * 1000

    successes = [r for r in results if r["ok"]]
    failures = [r for r in results if not r["ok"]]
    avg_ms = sum(r["elapsed_ms"] for r in results) / len(results)
    p95_ms = sorted(r["elapsed_ms"] for r in results)[int(len(results) * 0.95)]

    print(f"\nLoad Test Results ({TOTAL_REQUESTS} requests, {CONCURRENCY} concurrency)")
    print(f"  Success: {len(successes)}/{TOTAL_REQUESTS}")
    print(f"  Failures: {len(failures)}")
    print(f"  Avg latency: {avg_ms:.0f}ms")
    print(f"  P95 latency: {p95_ms:.0f}ms")
    print(f"  Total time: {total_elapsed:.0f}ms")
    print(f"  Throughput: {TOTAL_REQUESTS / (total_elapsed / 1000):.2f} req/s")

    for f in failures:
        print(f"  FAILED [{f['idx']}]: {f.get('error', f['status'])}")

    # Assert at least 80% success rate
    assert len(successes) >= TOTAL_REQUESTS * 0.8, f"Too many failures: {len(failures)}"
