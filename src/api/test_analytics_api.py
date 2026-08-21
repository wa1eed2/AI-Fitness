from src.api.test_helpers import (
    auth_headers,
    create_test_client,
    register_account,
    safe_delete_user
)


def test_fitness_analytics_overview():
    client = create_test_client()
    account = register_account(client, "analytics-fitness")

    try:
        response = client.get(
            f"/api/v1/users/{account['user_id']}/analytics",
            headers=auth_headers(account)
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Fitness analytics returned HTTP {response.status_code}: {response.text}")

        if not isinstance(response.json(), dict):
            raise ValueError("FAIL: Fitness analytics did not return a JSON object")

        print("PASS: API returns fitness analytics overview")

    finally:
        safe_delete_user(account["user_id"])


def test_training_analytics_overview():
    client = create_test_client()
    account = register_account(client, "analytics-training")

    try:
        response = client.get(
            f"/api/v1/users/{account['user_id']}/analytics/training",
            headers=auth_headers(account)
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Training analytics returned HTTP {response.status_code}: {response.text}")

        if not isinstance(response.json(), dict):
            raise ValueError("FAIL: Training analytics did not return a JSON object")

        print("PASS: API returns training analytics overview")

    finally:
        safe_delete_user(account["user_id"])


def test_trend_analytics_overview():
    client = create_test_client()
    account = register_account(client, "analytics-trends")

    try:
        response = client.get(
            f"/api/v1/users/{account['user_id']}/analytics/trends",
            headers=auth_headers(account)
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Trend analytics returned HTTP {response.status_code}: {response.text}")

        if not isinstance(response.json(), dict):
            raise ValueError("FAIL: Trend analytics did not return a JSON object")

        print("PASS: API returns trend analytics overview")

    finally:
        safe_delete_user(account["user_id"])


def test_trend_analytics_reference_date():
    client = create_test_client()
    account = register_account(client, "analytics-trend-date")

    try:
        response = client.get(
            f"/api/v1/users/{account['user_id']}/analytics/trends",
            headers=auth_headers(account),
            params={
                "reference_date": "2030-06-15"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Trend reference date returned HTTP {response.status_code}: {response.text}")

        if not isinstance(response.json(), dict):
            raise ValueError("FAIL: Trend reference-date analytics did not return a JSON object")

        print("PASS: API accepts trend analytics reference date")

    finally:
        safe_delete_user(account["user_id"])


def test_invalid_trend_reference_date_rejected():
    client = create_test_client()
    account = register_account(client, "analytics-invalid-date")

    try:
        response = client.get(
            f"/api/v1/users/{account['user_id']}/analytics/trends",
            headers=auth_headers(account),
            params={
                "reference_date": "not-a-date"
            }
        )

        if response.status_code != 400:
            raise ValueError(f"FAIL: Invalid trend reference date returned HTTP {response.status_code} instead of 400")

        print("PASS: API rejects invalid trend analytics reference date")

    finally:
        safe_delete_user(account["user_id"])


def test_dashboard_analytics():
    client = create_test_client()
    account = register_account(client, "analytics-dashboard")

    try:
        response = client.get(
            f"/api/v1/users/{account['user_id']}/analytics/dashboard",
            headers=auth_headers(account)
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Dashboard analytics returned HTTP {response.status_code}: {response.text}")

        if not isinstance(response.json(), dict):
            raise ValueError("FAIL: Dashboard analytics did not return a JSON object")

        print("PASS: API returns dashboard analytics")

    finally:
        safe_delete_user(account["user_id"])


def test_dashboard_reference_date():
    client = create_test_client()
    account = register_account(client, "analytics-dashboard-date")

    try:
        response = client.get(
            f"/api/v1/users/{account['user_id']}/analytics/dashboard",
            headers=auth_headers(account),
            params={
                "reference_date": "2030-06-15"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Dashboard reference date returned HTTP {response.status_code}: {response.text}")

        if not isinstance(response.json(), dict):
            raise ValueError("FAIL: Dashboard reference-date analytics did not return a JSON object")

        print("PASS: API accepts dashboard analytics reference date")

    finally:
        safe_delete_user(account["user_id"])


def test_progression_analytics_overview():
    client = create_test_client()
    account = register_account(client, "analytics-progression")

    try:
        response = client.get(
            f"/api/v1/users/{account['user_id']}/analytics/progression",
            headers=auth_headers(account)
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Progression analytics returned HTTP {response.status_code}: {response.text}")

        if not isinstance(response.json(), dict):
            raise ValueError("FAIL: Progression analytics did not return a JSON object")

        print("PASS: API returns progression analytics overview")

    finally:
        safe_delete_user(account["user_id"])


def test_exercise_progression_overview():
    client = create_test_client()
    account = register_account(client, "analytics-exercise-progression")

    try:
        response = client.get(
            f"/api/v1/users/{account['user_id']}/analytics/progression/exercises",
            headers=auth_headers(account)
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Exercise progression overview returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if not isinstance(data, (dict, list)):
            raise ValueError("FAIL: Exercise progression overview returned unexpected JSON type")

        print("PASS: API returns exercise progression overview")

    finally:
        safe_delete_user(account["user_id"])


def test_training_data_quality_analytics():
    client = create_test_client()
    account = register_account(client, "analytics-data-quality")

    try:
        response = client.get(
            f"/api/v1/users/{account['user_id']}/analytics/data-quality",
            headers=auth_headers(account)
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Data-quality analytics returned HTTP {response.status_code}: {response.text}")

        if not isinstance(response.json(), dict):
            raise ValueError("FAIL: Data-quality analytics did not return a JSON object")

        print("PASS: API returns training data-quality analytics")

    finally:
        safe_delete_user(account["user_id"])


def test_analytics_routes_appear_in_openapi():
    client = create_test_client()

    response = client.get(
        "/openapi.json"
    )

    if response.status_code != 200:
        raise ValueError("FAIL: OpenAPI schema was unavailable")

    paths = response.json()[
        "paths"
    ]

    expected_paths = {
        "/api/v1/users/{user_id}/analytics",
        "/api/v1/users/{user_id}/analytics/training",
        "/api/v1/users/{user_id}/analytics/trends",
        "/api/v1/users/{user_id}/analytics/dashboard",
        "/api/v1/users/{user_id}/analytics/progression",
        "/api/v1/users/{user_id}/analytics/progression/exercises",
        "/api/v1/users/{user_id}/analytics/progression/exercises/{exercise_id}",
        "/api/v1/users/{user_id}/analytics/data-quality"
    }

    if not expected_paths.issubset(set(paths.keys())):
        raise ValueError("FAIL: OpenAPI schema is missing analytics routes")

    security = paths[
        "/api/v1/users/{user_id}/analytics"
    ][
        "get"
    ].get(
        "security"
    )

    if not security:
        raise ValueError("FAIL: Analytics routes are not documented as authenticated")

    print("PASS: OpenAPI documentation includes authenticated analytics routes")


if __name__ == "__main__":
    test_fitness_analytics_overview()
    test_training_analytics_overview()

    test_trend_analytics_overview()
    test_trend_analytics_reference_date()
    test_invalid_trend_reference_date_rejected()

    test_dashboard_analytics()
    test_dashboard_reference_date()

    test_progression_analytics_overview()
    test_exercise_progression_overview()
    test_training_data_quality_analytics()

    test_analytics_routes_appear_in_openapi()