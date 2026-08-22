from src.database.query_ai_conversation_database import (
    create_ai_conversation,
    get_ai_conversation_messages
)

from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.rag.llm_provider import (
    LLMProviderUnavailableError
)

from src.rag.meal_tool_service import (
    generate_meal_conversation_answer
)

from src.rag.tool_fallbacks import (
    build_meal_provider_fallback,
    build_workout_provider_fallback
)

from src.rag.workout_action_classifier import (
    ACTION_SINGLE_WORKOUT
)

from src.rag.workout_tool_service import (
    generate_workout_conversation_answer
)


class UnavailableProvider:
    def __init__(self):
        self.calls = []

    def generate(self, system_prompt, user_prompt):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt
            }
        )

        raise LLMProviderUnavailableError(
            "Provider temporarily unavailable"
        )


def fake_target_getter(user_id):
    return {
        "calorie_target": 2400,
        "protein_g": 160,
        "carbs_g": 280,
        "fat_g": 70
    }


def fake_safe_foods_getter(user_id):
    return [
        {
            "food_id": "F001",
            "name": "Chicken Breast"
        },
        {
            "food_id": "F002",
            "name": "Rice"
        }
    ]


def fake_meal_builder(user_id, meal_fraction):
    return {
        "foods": [
            {
                "food_id": "F001",
                "name": "Chicken Breast",
                "servings": 1
            },
            {
                "food_id": "F002",
                "name": "Rice",
                "servings": 1
            }
        ],
        "total_calories": 590.0,
        "total_protein_g": 42.0,
        "total_carbs_g": 68.0,
        "total_fat_g": 16.0,
        "protein_target_met": True,
        "calorie_target_met": True,
        "carb_target_met": False,
        "fat_target_met": False
    }


def fake_profile_getter(user_id):
    return {
        "user_id": user_id,
        "fitness_level": "Beginner",
        "primary_goal": "General Fitness",
        "session_duration_minutes": 45,
        "training_days_per_week": 3,
        "preferred_environment": "Home"
    }


def fake_candidate_getter(user_id):
    return [
        {
            "exercise_id": "E001",
            "name": "Push-Up"
        },
        {
            "exercise_id": "E005",
            "name": "Bodyweight Reverse Lunge"
        }
    ]


def fake_workout_builder(user_id, exercise_count=None):
    return {
        "status": "ready",
        "estimated_duration_minutes": 35,
        "exercises": [
            {
                "exercise_id": "E001",
                "name": "Push-Up",
                "sets": 3,
                "reps": "8-12"
            },
            {
                "exercise_id": "E005",
                "name": "Bodyweight Reverse Lunge",
                "sets": 3,
                "reps": "8-12"
            }
        ]
    }


def fake_weekly_builder(user_id, exercise_count=None):
    return {
        "days": [
            {
                "exercises": [
                    {
                        "exercise_id": "E001",
                        "name": "Push-Up"
                    }
                ]
            }
        ]
    }


def ready_meal_package():
    return {
        "status": "meal_ready",
        "meal_fraction": 0.25,
        "daily_target": fake_target_getter(1),
        "meal_target": {
            "calorie_target": 600,
            "protein_g": 40,
            "carbs_g": 70,
            "fat_g": 17.5
        },
        "meal": fake_meal_builder(
            1,
            0.25
        )
    }


def ready_workout_package():
    return {
        "status": "workout_ready",
        "workout_action": ACTION_SINGLE_WORKOUT,
        "requested_exercise_count": 2,
        "candidate_exercise_count": 5,
        "selected_exercise_count": 2,
        "workout_plan": fake_workout_builder(
            1,
            2
        )
    }


def test_meal_fallback_uses_deterministic_values():
    answer = build_meal_provider_fallback(
        ready_meal_package()
    )

    if "600 calories" not in answer:
        raise ValueError("FAIL: Meal fallback omitted deterministic calorie target")

    if "40 g of protein" not in answer:
        raise ValueError("FAIL: Meal fallback omitted deterministic protein target")

    if "[P" in answer:
        raise ValueError("FAIL: Meal fallback invented research citation")

    print("PASS: Meal provider fallback uses deterministic values without research claims")


def test_workout_fallback_uses_deterministic_counts():
    answer = build_workout_provider_fallback(
        ready_workout_package()
    )

    if "2 selected exercise entries" not in answer:
        raise ValueError("FAIL: Workout fallback omitted selected exercise count")

    if "5 compatible candidate exercises" not in answer:
        raise ValueError("FAIL: Workout fallback omitted candidate count")

    if "[P" in answer:
        raise ValueError("FAIL: Workout fallback invented research citation")

    print("PASS: Workout provider fallback uses deterministic plan metadata")


def test_meal_survives_provider_outage():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = UnavailableProvider()

        result = generate_meal_conversation_answer(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="Build me a meal",
            provider=provider,
            nutrition_target_getter=fake_target_getter,
            safe_foods_getter=fake_safe_foods_getter,
            meal_builder=fake_meal_builder
        )

        if result["status"] != "meal_generated":
            raise ValueError("FAIL: Provider outage destroyed deterministic meal result")

        if result["explanation_source"] != "deterministic_fallback":
            raise ValueError("FAIL: Meal outage did not use deterministic fallback explanation")

        if result["provider_available"] is not False:
            raise ValueError("FAIL: Meal result did not report unavailable provider")

        if result["meal"]["foods"][0]["food_id"] != "F001":
            raise ValueError("FAIL: Provider outage lost deterministic meal")

        if len(provider.calls) != 1:
            raise ValueError("FAIL: Meal provider outage did not occur after exactly one request")

        print("PASS: Deterministic meal survives AI-provider outage")

    finally:
        delete_user(
            user_id
        )


def test_workout_survives_provider_outage():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = UnavailableProvider()

        result = generate_workout_conversation_answer(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="Build me a workout",
            workout_action=ACTION_SINGLE_WORKOUT,
            provider=provider,
            profile_getter=fake_profile_getter,
            candidate_getter=fake_candidate_getter,
            single_workout_builder=fake_workout_builder,
            weekly_workout_builder=fake_weekly_builder
        )

        if result["status"] != "workout_generated":
            raise ValueError("FAIL: Provider outage destroyed deterministic workout result")

        if result["explanation_source"] != "deterministic_fallback":
            raise ValueError("FAIL: Workout outage did not use deterministic fallback explanation")

        if result["provider_available"] is not False:
            raise ValueError("FAIL: Workout result did not report unavailable provider")

        if result["workout_plan"]["exercises"][0]["exercise_id"] != "E001":
            raise ValueError("FAIL: Provider outage lost deterministic workout plan")

        if len(provider.calls) != 1:
            raise ValueError("FAIL: Workout provider outage did not occur after exactly one request")

        print("PASS: Deterministic workout survives AI-provider outage")

    finally:
        delete_user(
            user_id
        )


def test_meal_fallback_is_persisted():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        generate_meal_conversation_answer(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="Build me a meal",
            provider=UnavailableProvider(),
            nutrition_target_getter=fake_target_getter,
            safe_foods_getter=fake_safe_foods_getter,
            meal_builder=fake_meal_builder
        )

        messages = get_ai_conversation_messages(
            user_id,
            conversation["conversation_id"],
            limit=20
        )

        if messages[-1]["retrieval_status"] != "nutrition:meal_generated_provider_fallback":
            raise ValueError("FAIL: Meal provider fallback status was not persisted")

        print("PASS: Meal provider fallback is persisted in conversation history")

    finally:
        delete_user(
            user_id
        )


def test_workout_fallback_is_persisted():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        generate_workout_conversation_answer(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="Build me a workout",
            workout_action=ACTION_SINGLE_WORKOUT,
            provider=UnavailableProvider(),
            profile_getter=fake_profile_getter,
            candidate_getter=fake_candidate_getter,
            single_workout_builder=fake_workout_builder,
            weekly_workout_builder=fake_weekly_builder
        )

        messages = get_ai_conversation_messages(
            user_id,
            conversation["conversation_id"],
            limit=20
        )

        if messages[-1]["retrieval_status"] != "workout:workout_generated_provider_fallback":
            raise ValueError("FAIL: Workout provider fallback status was not persisted")

        print("PASS: Workout provider fallback is persisted in conversation history")

    finally:
        delete_user(
            user_id
        )


if __name__ == "__main__":
    test_meal_fallback_uses_deterministic_values()
    test_workout_fallback_uses_deterministic_counts()
    test_meal_survives_provider_outage()
    test_workout_survives_provider_outage()
    test_meal_fallback_is_persisted()
    test_workout_fallback_is_persisted()