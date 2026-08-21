from uuid import uuid4

from fastapi.testclient import TestClient

from src.api.app import (
    create_app
)

from src.database.query_user_database import (
    delete_user
)


def create_test_client():
    return TestClient(
        create_app()
    )


def unique_email(
    prefix
):
    return f"{prefix}-{uuid4().hex}@example.com"


def register_account(
    client,
    prefix
):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email(
                prefix
            ),
            "password": "StrongPassword123"
        }
    )

    if response.status_code != 201:
        raise ValueError(f"FAIL: Test registration failed: {response.status_code} {response.text}")

    return response.json()


def auth_headers(
    account
):
    return {
        "Authorization": f"Bearer {account['access_token']}"
    }


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


def workout_plan():
    return {
        "primary_goal": "Strength",
        "session_duration_minutes": 45,
        "exercises": [
            {
                "exercise_id": "E001",
                "sets": 2,
                "reps": "8-12",
                "rest_seconds": 90
            }
        ]
    }


def test_profile_requires_authentication():
    client = create_test_client()

    account = register_account(
        client,
        "profile-auth"
    )

    try:
        response = client.get(
            f"/api/v1/users/{account['user_id']}/profile"
        )

        if response.status_code != 401:
            raise ValueError(f"FAIL: Unauthenticated profile request returned HTTP {response.status_code}")

        print("PASS: Profile API requires authentication")

    finally:
        delete_user(
            account["user_id"]
        )


def test_authenticated_user_can_create_own_profile():
    client = create_test_client()

    account = register_account(
        client,
        "own-profile"
    )

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/profile",
            headers=auth_headers(
                account
            ),
            json=valid_profile_payload()
        )

        if response.status_code != 201:
            raise ValueError(f"FAIL: Authenticated profile creation returned HTTP {response.status_code}: {response.text}")

        if response.json()["user_id"] != account["user_id"]:
            raise ValueError("FAIL: Own profile returned incorrect user")

        print("PASS: Authenticated user can create own profile")

    finally:
        delete_user(
            account["user_id"]
        )


def test_user_cannot_access_another_profile():
    client = create_test_client()

    first = register_account(
        client,
        "profile-first"
    )

    second = register_account(
        client,
        "profile-second"
    )

    try:
        response = client.get(
            f"/api/v1/users/{second['user_id']}/profile",
            headers=auth_headers(
                first
            )
        )

        if response.status_code != 403:
            raise ValueError(f"FAIL: Cross-user profile request returned HTTP {response.status_code} instead of 403")

        print("PASS: API blocks cross-user profile access")

    finally:
        delete_user(
            first["user_id"]
        )

        delete_user(
            second["user_id"]
        )


def test_user_settings_require_matching_account():
    client = create_test_client()

    first = register_account(
        client,
        "settings-first"
    )

    second = register_account(
        client,
        "settings-second"
    )

    try:
        own_response = client.get(
            f"/api/v1/users/{first['user_id']}/exercise-preferences",
            headers=auth_headers(
                first
            )
        )

        if own_response.status_code != 200:
            raise ValueError(f"FAIL: Own settings request returned HTTP {own_response.status_code}: {own_response.text}")

        other_response = client.get(
            f"/api/v1/users/{second['user_id']}/exercise-preferences",
            headers=auth_headers(
                first
            )
        )

        if other_response.status_code != 403:
            raise ValueError("FAIL: Cross-user settings request was not forbidden")

        print("PASS: User-settings API enforces authenticated ownership")

    finally:
        delete_user(
            first["user_id"]
        )

        delete_user(
            second["user_id"]
        )


def test_workout_routes_require_matching_account():
    client = create_test_client()

    first = register_account(
        client,
        "workout-first"
    )

    second = register_account(
        client,
        "workout-second"
    )

    try:
        own_response = client.post(
            f"/api/v1/users/{first['user_id']}/workouts",
            headers=auth_headers(
                first
            ),
            json=workout_plan()
        )

        if own_response.status_code != 201:
            raise ValueError(f"FAIL: Own workout creation returned HTTP {own_response.status_code}: {own_response.text}")

        other_response = client.get(
            f"/api/v1/users/{first['user_id']}/workouts/active",
            headers=auth_headers(
                second
            )
        )

        if other_response.status_code != 403:
            raise ValueError("FAIL: Cross-user workout request was not forbidden")

        print("PASS: Workout API enforces authenticated ownership")

    finally:
        delete_user(
            first["user_id"]
        )

        delete_user(
            second["user_id"]
        )


def test_progress_routes_require_matching_account():
    client = create_test_client()

    first = register_account(
        client,
        "progress-first"
    )

    second = register_account(
        client,
        "progress-second"
    )

    try:
        own_response = client.post(
            f"/api/v1/users/{first['user_id']}/progress",
            headers=auth_headers(
                first
            ),
            json={
                "weight_kg": 80
            }
        )

        if own_response.status_code != 201:
            raise ValueError(f"FAIL: Own progress creation returned HTTP {own_response.status_code}: {own_response.text}")

        other_response = client.get(
            f"/api/v1/users/{first['user_id']}/progress",
            headers=auth_headers(
                second
            )
        )

        if other_response.status_code != 403:
            raise ValueError("FAIL: Cross-user progress request was not forbidden")

        print("PASS: Progress API enforces authenticated ownership")

    finally:
        delete_user(
            first["user_id"]
        )

        delete_user(
            second["user_id"]
        )


def test_calendar_routes_require_matching_account():
    client = create_test_client()

    first = register_account(
        client,
        "calendar-first"
    )

    second = register_account(
        client,
        "calendar-second"
    )

    try:
        own_response = client.get(
            f"/api/v1/users/{first['user_id']}/calendar/workouts",
            headers=auth_headers(
                first
            )
        )

        if own_response.status_code != 200:
            raise ValueError(f"FAIL: Own calendar request returned HTTP {own_response.status_code}: {own_response.text}")

        other_response = client.get(
            f"/api/v1/users/{first['user_id']}/calendar/workouts",
            headers=auth_headers(
                second
            )
        )

        if other_response.status_code != 403:
            raise ValueError("FAIL: Cross-user calendar request was not forbidden")

        print("PASS: Calendar API enforces authenticated ownership")

    finally:
        delete_user(
            first["user_id"]
        )

        delete_user(
            second["user_id"]
        )


def test_analytics_routes_require_matching_account():
    client = create_test_client()

    first = register_account(
        client,
        "analytics-first"
    )

    second = register_account(
        client,
        "analytics-second"
    )

    try:
        own_response = client.get(
            f"/api/v1/users/{first['user_id']}/analytics",
            headers=auth_headers(
                first
            )
        )

        if own_response.status_code != 200:
            raise ValueError(f"FAIL: Own analytics request returned HTTP {own_response.status_code}: {own_response.text}")

        other_response = client.get(
            f"/api/v1/users/{first['user_id']}/analytics",
            headers=auth_headers(
                second
            )
        )

        if other_response.status_code != 403:
            raise ValueError("FAIL: Cross-user analytics request was not forbidden")

        print("PASS: Analytics API enforces authenticated ownership")

    finally:
        delete_user(
            first["user_id"]
        )

        delete_user(
            second["user_id"]
        )


def test_user_cannot_delete_another_account():
    client = create_test_client()

    first = register_account(
        client,
        "delete-first"
    )

    second = register_account(
        client,
        "delete-second"
    )

    try:
        response = client.delete(
            f"/api/v1/users/{second['user_id']}",
            headers=auth_headers(
                first
            )
        )

        if response.status_code != 403:
            raise ValueError("FAIL: Cross-user account deletion was not forbidden")

        second_me = client.get(
            "/api/v1/auth/me",
            headers=auth_headers(
                second
            )
        )

        if second_me.status_code != 200:
            raise ValueError("FAIL: Forbidden deletion damaged the other account")

        print("PASS: API blocks cross-user account deletion")

    finally:
        delete_user(
            first["user_id"]
        )

        delete_user(
            second["user_id"]
        )


def test_user_can_delete_own_account():
    client = create_test_client()

    account = register_account(
        client,
        "self-delete"
    )

    response = client.delete(
        f"/api/v1/users/{account['user_id']}",
        headers=auth_headers(
            account
        )
    )

    if response.status_code != 204:
        raise ValueError(f"FAIL: Self deletion returned HTTP {response.status_code}: {response.text}")

    me_response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(
            account
        )
    )

    if me_response.status_code != 401:
        raise ValueError("FAIL: Deleted account's access token remained valid")

    print("PASS: Authenticated user can delete own account")


def test_protected_routes_publish_bearer_security():
    client = create_test_client()

    schema = client.get(
        "/openapi.json"
    ).json()

    security_schemes = schema.get(
        "components",
        {}
    ).get(
        "securitySchemes",
        {}
    )

    if not security_schemes:
        raise ValueError("FAIL: OpenAPI contains no authentication security scheme")

    workout_operation = schema[
        "paths"
    ][
        "/api/v1/users/{user_id}/workouts"
    ][
        "get"
    ]

    if not workout_operation.get(
        "security"
    ):
        raise ValueError("FAIL: Protected workout route does not publish security requirement")

    print("PASS: OpenAPI documents bearer authentication on protected routes")


if __name__ == "__main__":
    test_profile_requires_authentication()
    test_authenticated_user_can_create_own_profile()
    test_user_cannot_access_another_profile()

    test_user_settings_require_matching_account()
    test_workout_routes_require_matching_account()
    test_progress_routes_require_matching_account()
    test_calendar_routes_require_matching_account()
    test_analytics_routes_require_matching_account()

    test_user_cannot_delete_another_account()
    test_user_can_delete_own_account()

    test_protected_routes_publish_bearer_security()