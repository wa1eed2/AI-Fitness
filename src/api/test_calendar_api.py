from src.api.test_helpers import (
    auth_headers,
    create_test_client,
    register_account,
    safe_delete_user
)

from src.database.query_workout_log_database import (
    finish_workout_session,
    start_workout_from_plan
)


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


def schedule_test_workout(
    client,
    account,
    scheduled_for="2030-01-10T10:00:00"
):
    response = client.post(
        f"/api/v1/users/{account['user_id']}/calendar/workouts",
        headers=auth_headers(account),
        json={
            "scheduled_for": scheduled_for,
            "workout_plan": workout_plan(),
            "notes": "Test workout"
        }
    )

    if response.status_code != 201:
        raise ValueError(f"FAIL: Scheduled workout could not be created: {response.status_code} {response.text}")

    return response.json()


def extract_header(
    data
):
    if "scheduled_workout" in data:
        return data[
            "scheduled_workout"
        ]

    return data


def test_schedule_workout():
    client = create_test_client()
    account = register_account(client, "calendar-schedule")

    try:
        data = schedule_test_workout(
            client,
            account
        )

        header = extract_header(
            data
        )

        if header["user_id"] != account["user_id"]:
            raise ValueError("FAIL: Scheduled workout returned incorrect user")

        if header["status"] != "Planned":
            raise ValueError("FAIL: New scheduled workout was not Planned")

        print("PASS: API schedules workout")

    finally:
        safe_delete_user(account["user_id"])


def test_get_scheduled_workout():
    client = create_test_client()
    account = register_account(client, "calendar-get")

    try:
        created = schedule_test_workout(
            client,
            account
        )

        scheduled_workout_id = extract_header(
            created
        )[
            "scheduled_workout_id"
        ]

        response = client.get(
            f"/api/v1/users/{account['user_id']}/calendar/workouts/{scheduled_workout_id}",
            headers=auth_headers(account)
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Scheduled workout detail returned HTTP {response.status_code}: {response.text}")

        print("PASS: API retrieves scheduled workout")

    finally:
        safe_delete_user(account["user_id"])


def test_calendar_date_filter():
    client = create_test_client()
    account = register_account(client, "calendar-filter")

    try:
        schedule_test_workout(
            client,
            account,
            "2030-01-10T10:00:00"
        )

        schedule_test_workout(
            client,
            account,
            "2030-02-10T10:00:00"
        )

        response = client.get(
            f"/api/v1/users/{account['user_id']}/calendar/workouts",
            headers=auth_headers(account),
            params={
                "start_date": "2030-01-01",
                "end_date": "2030-01-31"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Calendar date filter returned HTTP {response.status_code}: {response.text}")

        if len(response.json()) != 1:
            raise ValueError("FAIL: Calendar date filter returned incorrect count")

        print("PASS: API filters calendar by date range")

    finally:
        safe_delete_user(account["user_id"])


def test_reschedule_workout():
    client = create_test_client()
    account = register_account(client, "calendar-reschedule")

    try:
        created = schedule_test_workout(
            client,
            account
        )

        scheduled_workout_id = extract_header(
            created
        )[
            "scheduled_workout_id"
        ]

        response = client.patch(
            f"/api/v1/users/{account['user_id']}/calendar/workouts/{scheduled_workout_id}/reschedule",
            headers=auth_headers(account),
            json={
                "scheduled_for": "2030-01-12T15:00:00"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Calendar reschedule returned HTTP {response.status_code}: {response.text}")

        header = extract_header(
            response.json()
        )

        if not header["scheduled_for"].startswith("2030-01-12"):
            raise ValueError("FAIL: Scheduled workout was not rescheduled")

        print("PASS: API reschedules workout")

    finally:
        safe_delete_user(account["user_id"])


def test_update_scheduled_workout_status():
    client = create_test_client()
    account = register_account(client, "calendar-status")

    try:
        created = schedule_test_workout(
            client,
            account
        )

        scheduled_workout_id = extract_header(
            created
        )[
            "scheduled_workout_id"
        ]

        response = client.patch(
            f"/api/v1/users/{account['user_id']}/calendar/workouts/{scheduled_workout_id}/status",
            headers=auth_headers(account),
            json={
                "status": "Skipped"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Calendar status PATCH returned HTTP {response.status_code}: {response.text}")

        header = extract_header(
            response.json()
        )

        if header["status"] != "Skipped":
            raise ValueError("FAIL: Calendar status was not updated")

        print("PASS: API updates scheduled workout status")

    finally:
        safe_delete_user(account["user_id"])


def test_complete_scheduled_workout_with_session():
    client = create_test_client()
    account = register_account(client, "calendar-complete")

    try:
        created = schedule_test_workout(
            client,
            account
        )

        scheduled_workout_id = extract_header(
            created
        )[
            "scheduled_workout_id"
        ]

        workout_session_id = start_workout_from_plan(
            account["user_id"],
            workout_plan()
        )

        finish_workout_session(
            workout_session_id,
            actual_duration_minutes=40
        )

        response = client.post(
            f"/api/v1/users/{account['user_id']}/calendar/workouts/{scheduled_workout_id}/complete",
            headers=auth_headers(account),
            json={
                "workout_session_id": workout_session_id
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Calendar completion returned HTTP {response.status_code}: {response.text}")

        header = extract_header(
            response.json()
        )

        if header["status"] != "Completed":
            raise ValueError("FAIL: Scheduled workout was not marked Completed")

        print("PASS: API links completed workout session to calendar")

    finally:
        safe_delete_user(account["user_id"])


def test_calendar_ownership_protected():
    client = create_test_client()

    first = register_account(
        client,
        "calendar-owner"
    )

    second = register_account(
        client,
        "calendar-other"
    )

    try:
        created = schedule_test_workout(
            client,
            first
        )

        scheduled_workout_id = extract_header(
            created
        )[
            "scheduled_workout_id"
        ]

        response = client.get(
            f"/api/v1/users/{second['user_id']}/calendar/workouts/{scheduled_workout_id}",
            headers=auth_headers(second)
        )

        if response.status_code != 404:
            raise ValueError(f"FAIL: Another user's scheduled workout ID returned HTTP {response.status_code} instead of 404")

        print("PASS: API protects calendar ownership")

    finally:
        safe_delete_user(first["user_id"])
        safe_delete_user(second["user_id"])


def test_calendar_mutation_ownership_protected():
    client = create_test_client()

    first = register_account(
        client,
        "calendar-mutation-owner"
    )

    second = register_account(
        client,
        "calendar-mutation-other"
    )

    try:
        created = schedule_test_workout(
            client,
            first
        )

        scheduled_workout_id = extract_header(
            created
        )[
            "scheduled_workout_id"
        ]

        response = client.patch(
            f"/api/v1/users/{second['user_id']}/calendar/workouts/{scheduled_workout_id}/status",
            headers=auth_headers(second),
            json={
                "status": "Skipped"
            }
        )

        if response.status_code != 404:
            raise ValueError(f"FAIL: Another user's calendar mutation returned HTTP {response.status_code} instead of 404")

        print("PASS: API protects calendar mutations")

    finally:
        safe_delete_user(first["user_id"])
        safe_delete_user(second["user_id"])


def test_delete_scheduled_workout():
    client = create_test_client()
    account = register_account(client, "calendar-delete")
    headers = auth_headers(account)

    try:
        created = schedule_test_workout(
            client,
            account
        )

        scheduled_workout_id = extract_header(
            created
        )[
            "scheduled_workout_id"
        ]

        response = client.delete(
            f"/api/v1/users/{account['user_id']}/calendar/workouts/{scheduled_workout_id}",
            headers=headers
        )

        if response.status_code != 204:
            raise ValueError(f"FAIL: Scheduled workout DELETE returned HTTP {response.status_code}")

        missing = client.get(
            f"/api/v1/users/{account['user_id']}/calendar/workouts/{scheduled_workout_id}",
            headers=headers
        )

        if missing.status_code != 404:
            raise ValueError("FAIL: Deleted scheduled workout remained available")

        print("PASS: API deletes scheduled workout")

    finally:
        safe_delete_user(account["user_id"])


def test_calendar_routes_appear_in_openapi():
    client = create_test_client()

    paths = client.get(
        "/openapi.json"
    ).json()[
        "paths"
    ]

    expected = {
        "/api/v1/users/{user_id}/calendar/workouts",
        "/api/v1/users/{user_id}/calendar/workouts/{scheduled_workout_id}",
        "/api/v1/users/{user_id}/calendar/workouts/{scheduled_workout_id}/reschedule",
        "/api/v1/users/{user_id}/calendar/workouts/{scheduled_workout_id}/status",
        "/api/v1/users/{user_id}/calendar/workouts/{scheduled_workout_id}/complete"
    }

    if not expected.issubset(set(paths.keys())):
        raise ValueError("FAIL: OpenAPI schema is missing calendar routes")

    security = paths[
        "/api/v1/users/{user_id}/calendar/workouts"
    ][
        "get"
    ].get(
        "security"
    )

    if not security:
        raise ValueError("FAIL: Calendar routes are not documented as authenticated")

    print("PASS: OpenAPI documentation includes authenticated calendar routes")


if __name__ == "__main__":
    test_schedule_workout()
    test_get_scheduled_workout()
    test_calendar_date_filter()
    test_reschedule_workout()
    test_update_scheduled_workout_status()
    test_complete_scheduled_workout_with_session()
    test_calendar_ownership_protected()
    test_calendar_mutation_ownership_protected()
    test_delete_scheduled_workout()
    test_calendar_routes_appear_in_openapi()