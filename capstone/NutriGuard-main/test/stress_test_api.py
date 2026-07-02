import argparse
import concurrent.futures
import json
import statistics
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests


DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 20


@dataclass
class RequestResult:
    name: str
    method: str
    path: str
    status_code: int | None
    elapsed_ms: float
    ok: bool
    error: str = ""


class ApiClient:
    def __init__(self, base_url: str, timeout_seconds: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.results: list[RequestResult] = []

    def request(
        self,
        name: str,
        method: str,
        path: str,
        *,
        expected_statuses: set[int] | None = None,
        **kwargs: Any,
    ) -> Any:
        expected = expected_statuses or {200}
        started = time.perf_counter()
        status_code = None
        error = ""
        payload: Any = {}

        try:
            response = self.session.request(
                method,
                f"{self.base_url}{path}",
                timeout=self.timeout_seconds,
                **kwargs,
            )
            status_code = response.status_code
            if response.text:
                try:
                    payload = response.json()
                except json.JSONDecodeError:
                    payload = {"raw": response.text[:300]}
            ok = status_code in expected
            if not ok:
                error = json.dumps(payload)[:300]
        except requests.RequestException as exc:
            ok = False
            error = str(exc)

        elapsed_ms = (time.perf_counter() - started) * 1000
        self.results.append(
            RequestResult(
                name=name,
                method=method,
                path=path,
                status_code=status_code,
                elapsed_ms=elapsed_ms,
                ok=ok,
                error=error,
            )
        )

        if not ok:
            raise RuntimeError(f"{name} failed: {status_code} {error}")
        return payload


def build_profile_payload() -> dict[str, Any]:
    return {
        "goals": ["reduce_deficiency", "maintenance"],
        "diet_type": "vegetarian",
        "health_conditions_text": "Iron deficiency and low vitamin D",
        "deficiencies_text": "Low ferritin, vitamin D",
        "supplements_text": "Iron tablet in the morning and vitamin D weekly",
        "health_report_text": "Ferritin low. Vitamin D insufficient. HbA1c normal.",
    }


def build_meal_payload(user_id: int, meal_index: int) -> dict[str, Any]:
    meal_types = ["breakfast", "lunch", "snack", "dinner"]
    foods = ["poha with peanuts", "dal rice with salad", "curd and fruit", "paneer roti"]
    drinks = ["tea", "water", "coffee", "buttermilk"]
    return {
        "user_id": user_id,
        "foods_text": foods[meal_index % len(foods)],
        "drinks_text": drinks[meal_index % len(drinks)],
        "supplements_text": "iron tablet" if meal_index % 2 == 0 else "",
        "notes_text": "stress test meal entry",
        "meal_type": meal_types[meal_index % len(meal_types)],
        "meal_time": datetime.now(timezone.utc).isoformat(),
    }


def run_user_workflow(
    worker_id: int,
    base_url: str,
    meals_per_user: int,
    timeout_seconds: int,
    run_id: str,
) -> list[RequestResult]:
    client = ApiClient(base_url, timeout_seconds)
    email = f"stress-{run_id}-{worker_id}@example.com"
    password = "strongpass123"

    client.request("health", "GET", "/health")

    user = client.request(
        "signup",
        "POST",
        "/users/signup",
        json={"name": f"Stress User {worker_id}", "email": email, "password": password},
        expected_statuses={200, 409},
    )

    if "id" not in user:
        user = client.request(
            "login",
            "POST",
            "/users/login",
            json={"email": email, "password": password},
        )
    else:
        client.request(
            "login",
            "POST",
            "/users/login",
            json={"email": email, "password": password},
        )

    user_id = user["id"]

    client.request(
        "save_profile",
        "POST",
        f"/users/{user_id}/profile",
        json=build_profile_payload(),
    )
    client.request("get_profile", "GET", f"/users/{user_id}/profile")

    client.request(
        "upload_health_report",
        "POST",
        f"/users/{user_id}/profile/report",
        files={"file": ("stress-report.txt", "Ferritin: low\nVitamin D: insufficient\n", "text/plain")},
    )

    meal_ids: list[int] = []
    for meal_index in range(meals_per_user):
        meal = client.request(
            "create_meal",
            "POST",
            "/meals",
            json=build_meal_payload(user_id, meal_index),
        )
        meal_id = meal["meal_log_id"]
        meal_ids.append(meal_id)
        client.request("get_meal", "GET", f"/meals/{meal_id}")
        client.request("get_meal_report", "GET", f"/meals/{meal_id}/report")

    client.request("list_user_meals", "GET", f"/users/{user_id}/meals")
    client.request("daily_report", "GET", f"/users/{user_id}/daily-report")
    client.request("daily_report_details", "GET", f"/users/{user_id}/daily-report/details")

    return client.results


def summarize(results: list[RequestResult], started: float) -> None:
    total_elapsed = time.perf_counter() - started
    success_count = sum(1 for result in results if result.ok)
    failure_count = len(results) - success_count

    print("\nStress test summary")
    print("===================")
    print(f"Total requests: {len(results)}")
    print(f"Successful:      {success_count}")
    print(f"Failed:          {failure_count}")
    print(f"Wall time:       {total_elapsed:.2f}s")

    by_name: dict[str, list[RequestResult]] = {}
    for result in results:
        by_name.setdefault(result.name, []).append(result)

    print("\nEndpoint latency")
    print("----------------")
    for name in sorted(by_name):
        timings = [result.elapsed_ms for result in by_name[name]]
        p95 = statistics.quantiles(timings, n=20)[18] if len(timings) >= 20 else max(timings)
        failures = sum(1 for result in by_name[name] if not result.ok)
        print(
            f"{name:22} count={len(timings):4} "
            f"avg={statistics.mean(timings):8.1f}ms "
            f"p95={p95:8.1f}ms "
            f"max={max(timings):8.1f}ms "
            f"failures={failures}"
        )

    failures = [result for result in results if not result.ok]
    if failures:
        print("\nFailures")
        print("--------")
        for result in failures[:20]:
            print(
                f"{result.name} {result.method} {result.path} "
                f"status={result.status_code} elapsed={result.elapsed_ms:.1f}ms error={result.error}"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stress test NutriGuard backend APIs with requests.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Backend API base URL.")
    parser.add_argument("--users", type=int, default=5, help="Concurrent virtual users.")
    parser.add_argument("--meals-per-user", type=int, default=3, help="Meals each virtual user logs.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="Request timeout in seconds.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_id = uuid.uuid4().hex[:8]
    started = time.perf_counter()
    all_results: list[RequestResult] = []

    print(f"Running stress test against {args.base_url}")
    print(f"Virtual users: {args.users}, meals per user: {args.meals_per_user}, run id: {run_id}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.users) as executor:
        futures = [
            executor.submit(
                run_user_workflow,
                worker_id,
                args.base_url,
                args.meals_per_user,
                args.timeout,
                run_id,
            )
            for worker_id in range(args.users)
        ]

        for future in concurrent.futures.as_completed(futures):
            try:
                all_results.extend(future.result())
            except Exception as exc:
                print(f"Worker failed: {exc}")

    summarize(all_results, started)
    return 1 if any(not result.ok for result in all_results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
