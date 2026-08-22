from src.api.test_helpers import (
    auth_headers,
    create_test_client,
    register_account,
    safe_delete_user
)

from src.database.query_user_database import (
    create_user_profile
)

from src.rag.fake_llm_provider import (
    FakeLLMProvider
)


def create_conversation(client, account):
    response = client.post(
        "/api/v1/ai/conversations",
        headers=auth_headers(account),
        json={
            "title": "Workout routing test"
        }
    )

    if response.status_code != 201:
        raise ValueError(f"FAIL: Could not create AI conversation: {response.text}")

    return response.json()


def create_workout_profile(user_id):
    return create_user_profile(
        user_id,
        {
            "age": 30,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Beginner",
            "primary_goal": "General Fitness",
            "training_days_per_week": 3,
            "session_duration_minutes": 45,
            "preferred_environment": "Home"
        }
    )


def test_workout_request_requires_profile_before_model():
    provider = FakeLLMProvider(
        "This must not be called."
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "workout-no-profile"
    )

    try:
        conversation = create_conversation(
            client,
            account
        )

        response = client.post(
            f"/api/v1/ai/conversations/{conversation['conversation_id']}/messages",
            headers=auth_headers(account),
            json={
                "question": "Build me a workout"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Missing-profile workout request returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["route"] != "workout":
            raise ValueError("FAIL: Workout request did not use workout route")

        if data["status"] != "profile_required":
            raise ValueError("FAIL: Missing-profile workout returned incorrect status")

        if provider.calls:
            raise ValueError("FAIL: Model was called before workout profile requirements were satisfied")

        print("PASS: Workout API requires deterministic profile data before generation")

    finally:
        safe_delete_user(account["user_id"])


def test_profiled_user_can_generate_workout():
    provider = FakeLLMProvider(
        "Your workout was generated from your profile and compatible exercise set."
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "workout-profiled"
    )

    try:
        create_workout_profile(
            account["user_id"]
        )

        conversation = create_conversation(
            client,
            account
        )

        response = client.post(
            f"/api/v1/ai/conversations/{conversation['conversation_id']}/messages",
            headers=auth_headers(account),
            json={
                "question": "Build me a workout",
                "exercise_count": 3
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Profiled workout request returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["route"] != "workout":
            raise ValueError("FAIL: Profiled workout request used incorrect route")

        if data["status"] != "workout_generated":
            raise ValueError(f"FAIL: Profiled workout returned unexpected status: {data['status']}")

        if not data["workout_plan"]:
            raise ValueError("FAIL: Workout API did not return structured deterministic plan")

        if len(provider.calls) != 1:
            raise ValueError("FAIL: Workout explanation model was not called exactly once")

        print("PASS: Profiled user receives deterministic structured workout through AI API")

    finally:
        safe_delete_user(account["user_id"])


def test_weekly_workout_request_uses_weekly_planner():
    provider = FakeLLMProvider(
        "Your weekly training plan was generated from your stored schedule and profile."
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "workout-weekly"
    )

    try:
        create_workout_profile(
            account["user_id"]
        )

        conversation = create_conversation(
            client,
            account
        )

        response = client.post(
            f"/api/v1/ai/conversations/{conversation['conversation_id']}/messages",
            headers=auth_headers(account),
            json={
                "question": "Build me a weekly workout plan",
                "exercise_count": 3
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Weekly workout request returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["workout_routing"]["action"] != "weekly_workout":
            raise ValueError("FAIL: Weekly workout request did not select weekly planner")

        if data["status"] != "workout_generated":
            raise ValueError("FAIL: Weekly workout request did not generate deterministic plan")

        print("PASS: AI API routes weekly workout requests to weekly deterministic planner")

    finally:
        safe_delete_user(account["user_id"])


def test_api_rejects_invalid_exercise_count():
    client = create_test_client(
        llm_provider=FakeLLMProvider("Unused")
    )

    account = register_account(
        client,
        "workout-invalid-count"
    )

    try:
        conversation = create_conversation(
            client,
            account
        )

        response = client.post(
            f"/api/v1/ai/conversations/{conversation['conversation_id']}/messages",
            headers=auth_headers(account),
            json={
                "question": "Build me a workout",
                "exercise_count": 0
            }
        )

        if response.status_code != 422:
            raise ValueError(f"FAIL: Invalid exercise count returned HTTP {response.status_code}")

        print("PASS: AI API validates requested workout exercise count")

    finally:
        safe_delete_user(account["user_id"])


if __name__ == "__main__":
    test_workout_request_requires_profile_before_model()
    test_profiled_user_can_generate_workout()
    test_weekly_workout_request_uses_weekly_planner()
    test_api_rejects_invalid_exercise_count()