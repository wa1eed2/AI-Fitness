from src.api.test_helpers import (
    auth_headers,
    create_test_client,
    register_account,
    safe_delete_user
)


def workout_plan(
    with_exercise=True
):
    exercises = []

    if with_exercise:
        exercises = [
            {
                "exercise_id": "E001",
                "sets": 2,
                "reps": "8-12",
                "rest_seconds": 90
            }
        ]

    return {
        "primary_goal": "Strength",
        "session_duration_minutes": 45,
        "exercises": exercises
    }


def start_test_workout(
    client,
    account,
    with_exercise=True
):
    response = client.post(
        f"/api/v1/users/{account['user_id']}/workouts",
        headers=auth_headers(account),
        json=workout_plan(
            with_exercise
        )
    )

    if response.status_code != 201:
        raise ValueError(f"FAIL: Test workout could not start: {response.status_code} {response.text}")

    return response.json()


def test_api_starts_workout():
    client = create_test_client()
    account = register_account(client, "workout-start")

    try:
        data = start_test_workout(
            client,
            account
        )

        if data["session"]["user_id"] != account["user_id"]:
            raise ValueError("FAIL: Workout API returned incorrect user")

        if data["session"]["status"] != "In Progress":
            raise ValueError("FAIL: New workout did not have In Progress status")

        if len(data["exercises"]) != 1:
            raise ValueError("FAIL: Workout API returned incorrect exercise count")

        if data["exercises"][0]["exercise_id"] != "E001":
            raise ValueError("FAIL: Workout API returned incorrect exercise")

        print("PASS: API starts workout from plan")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_api_gets_active_workout():
    client = create_test_client()
    account = register_account(client, "workout-active")

    try:
        started = start_test_workout(
            client,
            account
        )

        response = client.get(
            f"/api/v1/users/{account['user_id']}/workouts/active",
            headers=auth_headers(account)
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Active workout endpoint returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["session"]["workout_session_id"] != started["session"]["workout_session_id"]:
            raise ValueError("FAIL: Active workout endpoint returned incorrect session")

        print("PASS: API retrieves active workout")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_missing_active_workout_returns_404():
    client = create_test_client()
    account = register_account(client, "workout-no-active")

    try:
        response = client.get(
            f"/api/v1/users/{account['user_id']}/workouts/active",
            headers=auth_headers(account)
        )

        if response.status_code != 404:
            raise ValueError(f"FAIL: Missing active workout returned HTTP {response.status_code} instead of 404")

        print("PASS: Missing active workout returns HTTP 404")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_second_active_workout_rejected():
    client = create_test_client()
    account = register_account(client, "workout-second-active")

    try:
        start_test_workout(
            client,
            account
        )

        response = client.post(
            f"/api/v1/users/{account['user_id']}/workouts",
            headers=auth_headers(account),
            json=workout_plan()
        )

        if response.status_code != 400:
            raise ValueError(f"FAIL: Second active workout returned HTTP {response.status_code} instead of 400")

        print("PASS: API prevents multiple active workouts per user")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_api_gets_workout_details():
    client = create_test_client()
    account = register_account(client, "workout-details")

    try:
        started = start_test_workout(
            client,
            account
        )

        workout_session_id = started[
            "session"
        ][
            "workout_session_id"
        ]

        response = client.get(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}",
            headers=auth_headers(account)
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Workout details returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["session"]["workout_session_id"] != workout_session_id:
            raise ValueError("FAIL: Workout details returned incorrect session")

        if "sets" not in data["exercises"][0]:
            raise ValueError("FAIL: Workout details did not include nested set logs")

        print("PASS: API retrieves nested workout details")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_api_logs_workout_set():
    client = create_test_client()
    account = register_account(client, "workout-log-set")

    try:
        started = start_test_workout(
            client,
            account
        )

        workout_session_id = started["session"]["workout_session_id"]
        session_exercise_id = started["exercises"][0]["session_exercise_id"]

        response = client.post(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}/exercises/{session_exercise_id}/sets",
            headers=auth_headers(account),
            json={
                "set_number": 1,
                "reps_completed": 10,
                "weight_kg": 50,
                "rir_actual": 2,
                "rpe_actual": 8
            }
        )

        if response.status_code != 201:
            raise ValueError(f"FAIL: Set logging returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["set_number"] != 1:
            raise ValueError("FAIL: Set API returned incorrect set number")

        if data["reps_completed"] != 10:
            raise ValueError("FAIL: Set API returned incorrect reps")

        if data["weight_kg"] != 50:
            raise ValueError("FAIL: Set API returned incorrect weight")

        print("PASS: API logs workout set")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_api_updates_workout_set():
    client = create_test_client()
    account = register_account(client, "workout-update-set")
    headers = auth_headers(account)

    try:
        started = start_test_workout(
            client,
            account
        )

        workout_session_id = started["session"]["workout_session_id"]
        session_exercise_id = started["exercises"][0]["session_exercise_id"]

        created = client.post(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}/exercises/{session_exercise_id}/sets",
            headers=headers,
            json={
                "set_number": 1,
                "reps_completed": 10,
                "weight_kg": 50
            }
        ).json()

        set_log_id = created[
            "set_log_id"
        ]

        response = client.patch(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}/exercises/{session_exercise_id}/sets/{set_log_id}",
            headers=headers,
            json={
                "reps_completed": 12,
                "weight_kg": 55
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Workout set PATCH returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["reps_completed"] != 12:
            raise ValueError("FAIL: Set PATCH did not update reps")

        if data["weight_kg"] != 55:
            raise ValueError("FAIL: Set PATCH did not update weight")

        print("PASS: API updates workout set")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_empty_workout_set_patch_rejected():
    client = create_test_client()
    account = register_account(client, "workout-empty-set")
    headers = auth_headers(account)

    try:
        started = start_test_workout(
            client,
            account
        )

        workout_session_id = started["session"]["workout_session_id"]
        session_exercise_id = started["exercises"][0]["session_exercise_id"]

        created = client.post(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}/exercises/{session_exercise_id}/sets",
            headers=headers,
            json={
                "set_number": 1,
                "reps_completed": 10
            }
        ).json()

        response = client.patch(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}/exercises/{session_exercise_id}/sets/{created['set_log_id']}",
            headers=headers,
            json={}
        )

        if response.status_code != 400:
            raise ValueError(f"FAIL: Empty set PATCH returned HTTP {response.status_code} instead of 400")

        print("PASS: Empty workout set update returns HTTP 400")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_invalid_workout_set_values_rejected():
    client = create_test_client()
    account = register_account(client, "workout-invalid-set")

    try:
        started = start_test_workout(
            client,
            account
        )

        workout_session_id = started["session"]["workout_session_id"]
        session_exercise_id = started["exercises"][0]["session_exercise_id"]

        response = client.post(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}/exercises/{session_exercise_id}/sets",
            headers=auth_headers(account),
            json={
                "set_number": 0,
                "reps_completed": -1,
                "weight_kg": -10
            }
        )

        if response.status_code != 422:
            raise ValueError(f"FAIL: Invalid set values returned HTTP {response.status_code} instead of 422")

        print("PASS: API schema rejects invalid workout set values")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_api_deletes_workout_set():
    client = create_test_client()
    account = register_account(client, "workout-delete-set")
    headers = auth_headers(account)

    try:
        started = start_test_workout(
            client,
            account
        )

        workout_session_id = started["session"]["workout_session_id"]
        session_exercise_id = started["exercises"][0]["session_exercise_id"]

        created = client.post(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}/exercises/{session_exercise_id}/sets",
            headers=headers,
            json={
                "set_number": 1,
                "reps_completed": 10
            }
        ).json()

        response = client.delete(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}/exercises/{session_exercise_id}/sets/{created['set_log_id']}",
            headers=headers
        )

        if response.status_code != 204:
            raise ValueError(f"FAIL: Workout set DELETE returned HTTP {response.status_code}")

        details = client.get(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}",
            headers=headers
        ).json()

        if details["exercises"][0]["sets"] != []:
            raise ValueError("FAIL: Deleted workout set remained in details")

        print("PASS: API deletes workout set")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_api_marks_exercise_complete_and_incomplete():
    client = create_test_client()
    account = register_account(client, "workout-toggle")
    headers = auth_headers(account)

    try:
        started = start_test_workout(
            client,
            account
        )

        workout_session_id = started["session"]["workout_session_id"]
        session_exercise_id = started["exercises"][0]["session_exercise_id"]

        complete_response = client.post(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}/exercises/{session_exercise_id}/complete",
            headers=headers
        )

        if complete_response.status_code != 200:
            raise ValueError(f"FAIL: Exercise complete returned HTTP {complete_response.status_code}")

        if complete_response.json()["completed"] != 1:
            raise ValueError("FAIL: Exercise was not marked complete")

        incomplete_response = client.post(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}/exercises/{session_exercise_id}/incomplete",
            headers=headers
        )

        if incomplete_response.status_code != 200:
            raise ValueError(f"FAIL: Exercise incomplete returned HTTP {incomplete_response.status_code}")

        if incomplete_response.json()["completed"] != 0:
            raise ValueError("FAIL: Exercise was not marked incomplete")

        print("PASS: API toggles workout exercise completion")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_api_finishes_workout():
    client = create_test_client()
    account = register_account(client, "workout-finish")

    try:
        started = start_test_workout(
            client,
            account,
            with_exercise=False
        )

        workout_session_id = started["session"]["workout_session_id"]

        response = client.post(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}/finish",
            headers=auth_headers(account),
            json={
                "actual_duration_minutes": 42,
                "notes": "Good session"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Workout finish returned HTTP {response.status_code}: {response.text}")

        data = response.json()["session"]

        if data["status"] != "Completed":
            raise ValueError("FAIL: Finished workout did not have Completed status")

        if data["actual_duration_minutes"] != 42:
            raise ValueError("FAIL: Finished workout returned incorrect duration")

        if data["notes"] != "Good session":
            raise ValueError("FAIL: Finished workout returned incorrect notes")

        print("PASS: API finishes workout session")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_api_cancels_workout():
    client = create_test_client()
    account = register_account(client, "workout-cancel")

    try:
        started = start_test_workout(
            client,
            account,
            with_exercise=False
        )

        workout_session_id = started["session"]["workout_session_id"]

        response = client.post(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}/cancel",
            headers=auth_headers(account),
            json={
                "notes": "Schedule changed"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Workout cancellation returned HTTP {response.status_code}: {response.text}")

        data = response.json()["session"]

        if data["status"] != "Cancelled":
            raise ValueError("FAIL: Cancelled workout returned incorrect status")

        if data["notes"] != "Schedule changed":
            raise ValueError("FAIL: Cancelled workout returned incorrect notes")

        print("PASS: API cancels workout session")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_completed_workout_appears_in_history():
    client = create_test_client()
    account = register_account(client, "workout-history")
    headers = auth_headers(account)

    try:
        started = start_test_workout(
            client,
            account,
            with_exercise=False
        )

        workout_session_id = started["session"]["workout_session_id"]

        client.post(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}/finish",
            headers=headers,
            json={
                "actual_duration_minutes": 30
            }
        )

        response = client.get(
            f"/api/v1/users/{account['user_id']}/workouts",
            headers=headers,
            params={
                "status": "Completed"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Workout history returned HTTP {response.status_code}: {response.text}")

        history = response.json()

        if len(history) != 1:
            raise ValueError("FAIL: Completed history filter returned incorrect count")

        if history[0]["status"] != "Completed":
            raise ValueError("FAIL: Workout history status filter returned incorrect workout")

        print("PASS: API filters workout history by status")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_workout_history_limit():
    client = create_test_client()
    account = register_account(client, "workout-history-limit")
    headers = auth_headers(account)

    try:
        for _ in range(2):
            started = start_test_workout(
                client,
                account,
                with_exercise=False
            )

            workout_session_id = started["session"]["workout_session_id"]

            client.post(
                f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}/finish",
                headers=headers,
                json={}
            )

        response = client.get(
            f"/api/v1/users/{account['user_id']}/workouts",
            headers=headers,
            params={
                "limit": 1
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Workout history limit returned HTTP {response.status_code}")

        if len(response.json()) != 1:
            raise ValueError("FAIL: Workout history limit returned incorrect count")

        print("PASS: API limits workout history")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_missing_workout_returns_404():
    client = create_test_client()
    account = register_account(client, "workout-missing")

    try:
        response = client.get(
            f"/api/v1/users/{account['user_id']}/workouts/999999999",
            headers=auth_headers(account)
        )

        if response.status_code != 404:
            raise ValueError(f"FAIL: Missing workout returned HTTP {response.status_code} instead of 404")

        print("PASS: Missing workout session returns HTTP 404")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_workout_ownership_is_protected():
    client = create_test_client()

    first = register_account(
        client,
        "workout-owner"
    )

    second = register_account(
        client,
        "workout-other"
    )

    try:
        started = start_test_workout(
            client,
            first
        )

        workout_session_id = started[
            "session"
        ][
            "workout_session_id"
        ]

        response = client.get(
            f"/api/v1/users/{second['user_id']}/workouts/{workout_session_id}",
            headers=auth_headers(second)
        )

        if response.status_code != 404:
            raise ValueError(f"FAIL: Another user's workout ID returned HTTP {response.status_code} instead of 404")

        print("PASS: API protects workout ownership")

    finally:
        safe_delete_user(
            first["user_id"]
        )

        safe_delete_user(
            second["user_id"]
        )


def test_set_mutation_ownership_is_protected():
    client = create_test_client()

    first = register_account(
        client,
        "set-owner"
    )

    second = register_account(
        client,
        "set-other"
    )

    try:
        started = start_test_workout(
            client,
            first
        )

        workout_session_id = started["session"]["workout_session_id"]
        session_exercise_id = started["exercises"][0]["session_exercise_id"]

        created = client.post(
            f"/api/v1/users/{first['user_id']}/workouts/{workout_session_id}/exercises/{session_exercise_id}/sets",
            headers=auth_headers(first),
            json={
                "set_number": 1,
                "reps_completed": 10
            }
        ).json()

        response = client.patch(
            f"/api/v1/users/{second['user_id']}/workouts/{workout_session_id}/exercises/{session_exercise_id}/sets/{created['set_log_id']}",
            headers=auth_headers(second),
            json={
                "reps_completed": 20
            }
        )

        if response.status_code != 404:
            raise ValueError(f"FAIL: Another user's set mutation returned HTTP {response.status_code} instead of 404")

        print("PASS: API protects workout set ownership")

    finally:
        safe_delete_user(
            first["user_id"]
        )

        safe_delete_user(
            second["user_id"]
        )


def test_api_deletes_cancelled_workout():
    client = create_test_client()
    account = register_account(client, "workout-delete")
    headers = auth_headers(account)

    try:
        started = start_test_workout(
            client,
            account,
            with_exercise=False
        )

        workout_session_id = started["session"]["workout_session_id"]

        client.post(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}/cancel",
            headers=headers,
            json={}
        )

        response = client.delete(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}",
            headers=headers
        )

        if response.status_code != 204:
            raise ValueError(f"FAIL: Workout DELETE returned HTTP {response.status_code}: {response.text}")

        missing = client.get(
            f"/api/v1/users/{account['user_id']}/workouts/{workout_session_id}",
            headers=headers
        )

        if missing.status_code != 404:
            raise ValueError("FAIL: Deleted workout remained accessible")

        print("PASS: API deletes workout session")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_workout_routes_appear_in_openapi():
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
        "/api/v1/users/{user_id}/workouts",
        "/api/v1/users/{user_id}/workouts/active",
        "/api/v1/users/{user_id}/workouts/{workout_session_id}",
        "/api/v1/users/{user_id}/workouts/{workout_session_id}/finish",
        "/api/v1/users/{user_id}/workouts/{workout_session_id}/cancel",
        "/api/v1/users/{user_id}/workouts/{workout_session_id}/exercises/{session_exercise_id}/sets",
        "/api/v1/users/{user_id}/workouts/{workout_session_id}/exercises/{session_exercise_id}/sets/{set_log_id}",
        "/api/v1/users/{user_id}/workouts/{workout_session_id}/exercises/{session_exercise_id}/complete",
        "/api/v1/users/{user_id}/workouts/{workout_session_id}/exercises/{session_exercise_id}/incomplete"
    }

    if not expected_paths.issubset(
        set(
            paths.keys()
        )
    ):
        raise ValueError("FAIL: OpenAPI schema is missing workout routes")

    security = paths[
        "/api/v1/users/{user_id}/workouts"
    ][
        "get"
    ].get(
        "security"
    )

    if not security:
        raise ValueError("FAIL: Workout routes are not documented as authenticated")

    print("PASS: OpenAPI documentation includes authenticated workout routes")


if __name__ == "__main__":
    test_api_starts_workout()
    test_api_gets_active_workout()
    test_missing_active_workout_returns_404()
    test_second_active_workout_rejected()
    test_api_gets_workout_details()

    test_api_logs_workout_set()
    test_api_updates_workout_set()
    test_empty_workout_set_patch_rejected()
    test_invalid_workout_set_values_rejected()
    test_api_deletes_workout_set()

    test_api_marks_exercise_complete_and_incomplete()

    test_api_finishes_workout()
    test_api_cancels_workout()
    test_completed_workout_appears_in_history()
    test_workout_history_limit()

    test_missing_workout_returns_404()
    test_workout_ownership_is_protected()
    test_set_mutation_ownership_is_protected()
    test_api_deletes_cancelled_workout()

    test_workout_routes_appear_in_openapi()