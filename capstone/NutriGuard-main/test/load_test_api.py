import argparse
import json
import ssl
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


def ssl_context(insecure_skip_tls_verify: bool):
    if insecure_skip_tls_verify:
        return ssl._create_unverified_context()
    return None


def request_once(
    base_url: str,
    endpoint: str,
    token: str | None,
    timeout: int,
    insecure_skip_tls_verify: bool,
) -> dict:
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    request = urllib.request.Request(url, method="GET")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    started_at = time.perf_counter()
    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
            context=ssl_context(insecure_skip_tls_verify),
        ) as response:
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


def _read_error_body(exc: urllib.error.HTTPError) -> str:
    try:
        return exc.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def login_for_user(
    base_url: str,
    email: str,
    password: str,
    timeout: int,
    insecure_skip_tls_verify: bool,
) -> dict:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/users/login",
        method="POST",
        data=json.dumps({"email": email, "password": password}).encode("utf-8"),
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
            context=ssl_context(insecure_skip_tls_verify),
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = _read_error_body(exc)
        raise RuntimeError(f"Login failed with HTTP {exc.code}: {body}") from exc

    token = payload.get("access_token")
    if not token:
        raise RuntimeError("Login response did not include access_token")
    return payload


def run_load_test(args: argparse.Namespace) -> dict:
    started_at = time.perf_counter()
    results = []
    endpoint = args.endpoint
    token = args.token
    login_user = None
    if args.profile:
        if not token:
            if not args.email or not args.password:
                raise SystemExit("--token or both --email and --password are required with --profile")
            login_user = login_for_user(
                args.base_url,
                args.email,
                args.password,
                args.timeout,
                args.insecure_skip_tls_verify,
            )
            token = login_user["access_token"]
        profile_user_id = args.profile_user_id or (login_user or {}).get("id")
        if not profile_user_id:
            raise SystemExit("--profile-user-id is required with --profile when using --token")
        if login_user and args.profile_user_id and args.profile_user_id != login_user.get("id") and not login_user.get("is_admin"):
            raise SystemExit(
                f"Logged-in user id is {login_user.get('id')}, but --profile-user-id is {args.profile_user_id}. "
                "Use the logged-in user's id or login as an admin."
            )
        endpoint = f"/users/{profile_user_id}/profile"

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [
            executor.submit(
                request_once,
                args.base_url,
                endpoint,
                token,
                args.timeout,
                args.insecure_skip_tls_verify,
            )
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
        "source": "load_test_api",
        "base_url": args.base_url,
        "endpoint": endpoint,
        "scenario": "profile" if args.profile else "custom_get",
        "auth": "token" if token else "none",
        "login_user_id": (login_user or {}).get("id"),
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


def publish_summary(
    summary: dict,
    backend_url: str,
    internal_api_key: str,
    timeout: int,
    insecure_skip_tls_verify: bool,
) -> dict:
    request = urllib.request.Request(
        f"{backend_url.rstrip('/')}/internal/load-test-results",
        method="POST",
        data=json.dumps(summary).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-internal-api-key": internal_api_key,
        },
    )
    with urllib.request.urlopen(
        request,
        timeout=timeout,
        context=ssl_context(insecure_skip_tls_verify),
    ) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only load test for NutriGuard backend latency.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend API base URL.")
    parser.add_argument("--endpoint", default="/health", help="GET endpoint to call.")
    parser.add_argument("--profile", action="store_true", help="Load test GET /users/{user_id}/profile.")
    parser.add_argument("--profile-user-id", type=int, default=None, help="User ID for --profile. Optional when using --email and --password.")
    parser.add_argument("--requests", type=int, default=50, help="Total requests to send.")
    parser.add_argument("--concurrency", type=int, default=5, help="Parallel workers.")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds.")
    parser.add_argument("--token", default=None, help="Optional bearer token for authenticated GET endpoints.")
    parser.add_argument("--email", default=None, help="Login email. Used to fetch JWT when --token is not provided.")
    parser.add_argument("--password", default=None, help="Login password. Used to fetch JWT when --token is not provided.")
    parser.add_argument("--publish", action="store_true", help="Publish summary to backend admin dashboard.")
    parser.add_argument("--publish-url", default=None, help="Backend API URL used for publishing. Defaults to --base-url.")
    parser.add_argument("--internal-api-key", default=None, help="Internal API key for publishing.")
    parser.add_argument(
        "--insecure-skip-tls-verify",
        action="store_true",
        help="Skip TLS certificate verification for local/proxy/self-signed certificate testing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_load_test(args)
    print(json.dumps(summary, indent=2))
    if args.publish:
        if not args.internal_api_key:
            raise SystemExit("--internal-api-key is required with --publish")
        publish_url = args.publish_url or args.base_url
        publish_result = publish_summary(
            summary,
            publish_url,
            args.internal_api_key,
            args.timeout,
            args.insecure_skip_tls_verify,
        )
        print(json.dumps({"publish": publish_result}, indent=2))
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
