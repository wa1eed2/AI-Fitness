from src.api.test_helpers import (
    auth_headers,
    create_test_client,
    register_account,
    safe_delete_user
)

from src.database.query_user_database import (
    get_user_profile
)


def valid_profile_payload():
    return {
        "age": 25,
        "sex": "Male",
        "height_cm": 180,
        "weight_kg": 80,
        "fitness_level": "Intermediate",
        "primary_goal": "Strength",
        "training_days_per_week": 4,
        "session_duration_minutes": 60,
        "preferred_environment": "Gym"
    }


def test_api_creates_user_profile():
    client = create_test_client()
    account = register_account(client, "profile-create")

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/profile",
            headers=auth_headers(account),
            json=valid_profile_payload()
        )

        if response.status_code != 201:
            raise ValueError(f"FAIL: Profile creation returned HTTP {response.status_code}: {response.text}")

        if response.json()["user_id"] != account["user_id"]:
            raise ValueError("FAIL: Profile API returned incorrect user")

        print("PASS: API creates user profile")

    finally:
        safe_delete_user(account["user_id"])


def test_api_retrieves_user_profile():
    client = create_test_client()
    account = register_account(client, "profile-get")

    try:
        create_response = client.post(
            f"/api/v1/users/{account['user_id']}/profile",
            headers=auth_headers(account),
            json=valid_profile_payload()
        )

        if create_response.status_code != 201:
            raise ValueError(f"FAIL: Profile setup returned HTTP {create_response.status_code}: {create_response.text}")

        response = client.get(
            f"/api/v1/users/{account['user_id']}/profile",
            headers=auth_headers(account)
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Profile GET returned HTTP {response.status_code}: {response.text}")

        if response.json()["primary_goal"] != "Strength":
            raise ValueError("FAIL: Profile GET returned incorrect data")

        print("PASS: API retrieves user profile")

    finally:
        safe_delete_user(account["user_id"])


def test_missing_user_profile_returns_404():
    client = create_test_client()
    account = register_account(client, "profile-missing")

    try:
        response = client.get(
            f"/api/v1/users/{account['user_id']}/profile",
            headers=auth_headers(account)
        )

        if response.status_code != 404:
            raise ValueError(f"FAIL: Missing profile returned HTTP {response.status_code} instead of 404")

        print("PASS: Missing user profile returns HTTP 404")

    finally:
        safe_delete_user(account["user_id"])


def test_duplicate_profile_returns_409():
    client = create_test_client()
    account = register_account(client, "profile-duplicate")

    try:
        first = client.post(
            f"/api/v1/users/{account['user_id']}/profile",
            headers=auth_headers(account),
            json=valid_profile_payload()
        )

        if first.status_code != 201:
            raise ValueError(f"FAIL: Initial profile creation failed: {first.status_code} {first.text}")

        second = client.post(
            f"/api/v1/users/{account['user_id']}/profile",
            headers=auth_headers(account),
            json=valid_profile_payload()
        )

        if second.status_code != 409:
            raise ValueError(f"FAIL: Duplicate profile returned HTTP {second.status_code} instead of 409")

        print("PASS: Duplicate profile creation returns HTTP 409")

    finally:
        safe_delete_user(account["user_id"])


def test_partial_profile_update():
    client = create_test_client()
    account = register_account(client, "profile-update")

    try:
        create_response = client.post(
            f"/api/v1/users/{account['user_id']}/profile",
            headers=auth_headers(account),
            json=valid_profile_payload()
        )

        if create_response.status_code != 201:
            raise ValueError(f"FAIL: Profile setup returned HTTP {create_response.status_code}: {create_response.text}")

        response = client.patch(
            f"/api/v1/users/{account['user_id']}/profile",
            headers=auth_headers(account),
            json={
                "weight_kg": 77.5,
                "training_days_per_week": 5
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Profile PATCH returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["weight_kg"] != 77.5:
            raise ValueError("FAIL: Profile PATCH did not update weight")

        if data["training_days_per_week"] != 5:
            raise ValueError("FAIL: Profile PATCH did not update training days")

        if data["primary_goal"] != "Strength":
            raise ValueError("FAIL: Profile PATCH changed an unspecified field")

        print("PASS: API partially updates user profile")

    finally:
        safe_delete_user(account["user_id"])


def test_empty_profile_update_returns_400():
    client = create_test_client()
    account = register_account(client, "profile-empty-update")

    try:
        create_response = client.post(
            f"/api/v1/users/{account['user_id']}/profile",
            headers=auth_headers(account),
            json=valid_profile_payload()
        )

        if create_response.status_code != 201:
            raise ValueError(f"FAIL: Profile setup returned HTTP {create_response.status_code}: {create_response.text}")

        response = client.patch(
            f"/api/v1/users/{account['user_id']}/profile",
            headers=auth_headers(account),
            json={}
        )

        if response.status_code != 400:
            raise ValueError(f"FAIL: Empty profile PATCH returned HTTP {response.status_code} instead of 400")

        print("PASS: Empty profile update returns HTTP 400")

    finally:
        safe_delete_user(account["user_id"])


def test_schema_rejects_invalid_numeric_ranges():
    client = create_test_client()
    account = register_account(client, "profile-range")

    try:
        payload = valid_profile_payload()
        payload["training_days_per_week"] = 8

        response = client.post(
            f"/api/v1/users/{account['user_id']}/profile",
            headers=auth_headers(account),
            json=payload
        )

        if response.status_code != 422:
            raise ValueError(f"FAIL: Invalid numeric range returned HTTP {response.status_code} instead of 422")

        print("PASS: API schema validation rejects invalid numeric ranges")

    finally:
        safe_delete_user(account["user_id"])


def test_domain_validation_returns_400():
    client = create_test_client()
    account = register_account(client, "profile-domain")

    try:
        payload = valid_profile_payload()
        payload["fitness_level"] = "Superhuman"

        response = client.post(
            f"/api/v1/users/{account['user_id']}/profile",
            headers=auth_headers(account),
            json=payload
        )

        if response.status_code != 400:
            raise ValueError(f"FAIL: Domain validation returned HTTP {response.status_code} instead of 400")

        print("PASS: Database domain validation reaches API as HTTP 400")

    finally:
        safe_delete_user(account["user_id"])


def test_api_deletes_user_and_cascades_profile():
    client = create_test_client()
    account = register_account(client, "profile-delete")

    create_response = client.post(
        f"/api/v1/users/{account['user_id']}/profile",
        headers=auth_headers(account),
        json=valid_profile_payload()
    )

    if create_response.status_code != 201:
        safe_delete_user(account["user_id"])
        raise ValueError(f"FAIL: Profile setup returned HTTP {create_response.status_code}: {create_response.text}")

    response = client.delete(
        f"/api/v1/users/{account['user_id']}",
        headers=auth_headers(account)
    )

    if response.status_code != 204:
        safe_delete_user(account["user_id"])
        raise ValueError(f"FAIL: User DELETE returned HTTP {response.status_code}: {response.text}")

    if get_user_profile(account["user_id"]) is not None:
        raise ValueError("FAIL: Profile remained after user deletion")

    print("PASS: API deletes user and cascades profile data")


def test_deleted_user_token_is_unavailable():
    client = create_test_client()
    account = register_account(client, "profile-delete-token")

    response = client.delete(
        f"/api/v1/users/{account['user_id']}",
        headers=auth_headers(account)
    )

    if response.status_code != 204:
        safe_delete_user(account["user_id"])
        raise ValueError(f"FAIL: User DELETE failed: {response.status_code} {response.text}")

    me_response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(account)
    )

    if me_response.status_code != 401:
        raise ValueError("FAIL: Deleted user's bearer token remained usable")

    print("PASS: Deleted user data is unavailable through API")


def test_profile_response_schema():
    client = create_test_client()
    account = register_account(client, "profile-schema")

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/profile",
            headers=auth_headers(account),
            json=valid_profile_payload()
        )

        if response.status_code != 201:
            raise ValueError(f"FAIL: Profile schema test could not create profile: {response.status_code} {response.text}")

        expected_fields = {
            "profile_id",
            "user_id",
            "age",
            "sex",
            "height_cm",
            "weight_kg",
            "fitness_level",
            "primary_goal",
            "training_days_per_week",
            "session_duration_minutes",
            "preferred_environment"
        }

        if set(response.json().keys()) != expected_fields:
            raise ValueError("FAIL: Profile API exposes unexpected response fields")

        print("PASS: Profile API exposes expected response schema")

    finally:
        safe_delete_user(account["user_id"])


def test_openapi_contains_user_routes():
    client = create_test_client()

    response = client.get(
        "/openapi.json"
    )

    if response.status_code != 200:
        raise ValueError("FAIL: OpenAPI schema unavailable")

    paths = response.json()["paths"]

    expected = {
        "/api/v1/users/{user_id}/profile",
        "/api/v1/users/{user_id}"
    }

    if not expected.issubset(set(paths.keys())):
        raise ValueError("FAIL: OpenAPI documentation is missing user/profile routes")

    if "/api/v1/users" in paths and "post" in paths["/api/v1/users"]:
        raise ValueError("FAIL: Legacy unauthenticated POST /users still appears in OpenAPI")

    profile_security = paths[
        "/api/v1/users/{user_id}/profile"
    ][
        "get"
    ].get(
        "security"
    )

    if not profile_security:
        raise ValueError("FAIL: Profile route is not documented as authenticated")

    print("PASS: OpenAPI documentation includes authenticated user/profile routes only")


if __name__ == "__main__":
    test_api_creates_user_profile()
    test_api_retrieves_user_profile()
    test_missing_user_profile_returns_404()
    test_duplicate_profile_returns_409()
    test_partial_profile_update()
    test_empty_profile_update_returns_400()
    test_schema_rejects_invalid_numeric_ranges()
    test_domain_validation_returns_400()
    test_api_deletes_user_and_cascades_profile()
    test_deleted_user_token_is_unavailable()
    test_profile_response_schema()
    test_openapi_contains_user_routes()