import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


def percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0
    sorted_values = sorted(values)
    index = round((len(sorted_values) - 1) * percent)
    return round(sorted_values[index], 2)


def request_once(base_url: str, endpoint: str, token: str | None, timeout: int) -> dict:
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    request = urllib.request.Request(url, method="GET")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    started_at = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(250)
            return {
                "ok": 200 <= response.status < 400,
                "status": response.status,
                "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                "body_sample": body.decode("utf-8", errors="replace"),
            }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "status": exc.code,
            "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "error": exc.read(250).decode("utf-8", errors="replace"),
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": None,
            "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "error": str(exc),
        }


def run_load_test(args: argparse.Namespace) -> dict:
    started_at = time.perf_counter()
    results = []

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [
            executor.submit(request_once, args.base_url, args.endpoint, args.token, args.timeout)
            for _ in range(args.requests)
        ]
        for future in as_completed(futures):
            results.append(future.result())

    durations = [item["duration_ms"] for item in results]
    status_counts = {}
    for item in results:
        key = str(item["status"])
        status_counts[key] = status_counts.get(key, 0) + 1

    return {
        "base_url": args.base_url,
        "endpoint": args.endpoint,
        "requests": len(results),
        "concurrency": args.concurrency,
        "success": sum(1 for item in results if item["ok"]),
        "failed": sum(1 for item in results if not item["ok"]),
        "wall_time_seconds": round(time.perf_counter() - started_at, 2),
        "average_ms": round(statistics.mean(durations), 2) if durations else 0,
        "p95_ms": percentile(durations, 0.95),
        "max_ms": round(max(durations), 2) if durations else 0,
        "status_counts": status_counts,
        "sample_error": next((item.get("error") for item in results if item.get("error")), None),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only load test for NutriGuard backend latency.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend API base URL.")
    parser.add_argument("--endpoint", default="/health", help="GET endpoint to call.")
    parser.add_argument("--requests", type=int, default=50, help="Total requests to send.")
    parser.add_argument("--concurrency", type=int, default=5, help="Parallel workers.")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds.")
    parser.add_argument("--token", default=None, help="Optional bearer token for authenticated GET endpoints.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_load_test(args)
    print(json.dumps(summary, indent=2))
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
