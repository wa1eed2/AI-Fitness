from src.database.query_ai_conversation_database import (
    create_ai_conversation
)

from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.rag.context_coaching_prompt_builder import (
    build_context_coaching_prompts
)

from src.rag.context_coaching_service import (
    generate_context_coaching_answer
)

from src.rag.fake_llm_provider import (
    FakeLLMProvider
)

from src.rag.question_classifier import (
    ROUTE_COACHING,
    ROUTE_NUTRITION,
    ROUTE_PERSONAL_DATA
)


def fake_user_context(user_id=1):
    return {
        "user_id": user_id,
        "profile": None,
        "equipment_access": [],
        "exercise_preferences": [],
        "limitations": [],
        "nutrition_target": None,
        "food_allergies": [],
        "recent_workouts": [],
        "recent_progress": [],
        "recent_body_measurements": [],
        "recent_activities": []
    }


def fake_nutrition_route_data(user_id, route):
    return {
        "route": route,
        "source": "deterministic_nutrition_system",
        "data": {
            "nutrition_target": {
                "calorie_target": 2350,
                "protein_g": 175,
                "carbs_g": 260,
                "fat_g": 70
            },
            "food_allergies": [
                {
                    "allergen": "Shellfish"
                }
            ]
        }
    }


def fake_personal_route_data(user_id, route):
    return {
        "route": route,
        "source": "deterministic_analytics_system",
        "data": {
            "dashboard_analytics": {
                "completed_workouts": 9
            },
            "training_analytics": {
                "training_sessions": 3
            },
            "trend_analytics": {
                "trend_marker": "stable"
            },
            "progression_analytics": {
                "improving_exercises": 2
            }
        }
    }


def test_nutrition_prompt_contains_verified_targets():
    prompts = build_context_coaching_prompts(
        question="What are my macros?",
        route=ROUTE_NUTRITION,
        user_context=fake_user_context(),
        conversation_messages=[],
        verified_route_data=fake_nutrition_route_data(
            1,
            ROUTE_NUTRITION
        )
    )

    prompt = prompts["user_prompt"]

    if '"protein_g": 175' not in prompt:
        raise ValueError("FAIL: Nutrition prompt omitted deterministic protein target")

    if '"calorie_target": 2350' not in prompt:
        raise ValueError("FAIL: Nutrition prompt omitted deterministic calorie target")

    print("PASS: Nutrition prompt receives exact verified targets")


def test_nutrition_prompt_contains_allergy_constraints():
    prompts = build_context_coaching_prompts(
        question="What are my macros?",
        route=ROUTE_NUTRITION,
        user_context=fake_user_context(),
        conversation_messages=[],
        verified_route_data=fake_nutrition_route_data(
            1,
            ROUTE_NUTRITION
        )
    )

    if "Shellfish" not in prompts["user_prompt"]:
        raise ValueError("FAIL: Nutrition prompt omitted verified allergy data")

    if "Food allergies are hard safety constraints" not in prompts["system_prompt"]:
        raise ValueError("FAIL: Nutrition system prompt omitted hard allergy rule")

    print("PASS: Nutrition prompt combines verified data with hard allergy rules")


def test_verified_data_is_not_called_research_evidence():
    prompts = build_context_coaching_prompts(
        question="What are my macros?",
        route=ROUTE_NUTRITION,
        user_context=fake_user_context(),
        conversation_messages=[],
        verified_route_data=fake_nutrition_route_data(
            1,
            ROUTE_NUTRITION
        )
    )

    required = [
        "Verified application data is not scientific research evidence",
        "These values are not scientific research evidence"
    ]

    combined = (
        prompts["system_prompt"]
        + "\n"
        + prompts["user_prompt"]
    )

    for phrase in required:
        if phrase not in combined:
            raise ValueError(f"FAIL: Verified-data grounding rule missing: {phrase}")

    print("PASS: Deterministic tool output remains separate from research evidence")


def test_nutrition_model_cannot_recalculate_targets():
    prompts = build_context_coaching_prompts(
        question="Change my macros",
        route=ROUTE_NUTRITION,
        user_context=fake_user_context(),
        conversation_messages=[],
        verified_route_data=fake_nutrition_route_data(
            1,
            ROUTE_NUTRITION
        )
    )

    if "Do not calculate replacement calorie or macro targets yourself" not in prompts["system_prompt"]:
        raise ValueError("FAIL: Nutrition model was not prohibited from recalculating targets")

    print("PASS: LLM cannot replace deterministic nutrition calculations")


def test_personal_data_prompt_contains_analytics():
    prompts = build_context_coaching_prompts(
        question="How has my training been lately?",
        route=ROUTE_PERSONAL_DATA,
        user_context=fake_user_context(),
        conversation_messages=[],
        verified_route_data=fake_personal_route_data(
            1,
            ROUTE_PERSONAL_DATA
        )
    )

    prompt = prompts["user_prompt"]

    required = [
        "dashboard_analytics",
        "training_analytics",
        "trend_analytics",
        "progression_analytics",
        '"completed_workouts": 9'
    ]

    for phrase in required:
        if phrase not in prompt:
            raise ValueError(f"FAIL: Personal-data prompt omitted verified analytics value: {phrase}")

    print("PASS: Personal-data prompt receives deterministic analytics output")


def test_service_passes_verified_data_to_provider():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            "Your stored target contains 175 grams of protein."
        )

        result = generate_context_coaching_answer(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="What are my macros?",
            route=ROUTE_NUTRITION,
            provider=provider,
            verified_route_data_builder=fake_nutrition_route_data
        )

        prompt = provider.calls[0]["user_prompt"]

        if '"protein_g": 175' not in prompt:
            raise ValueError("FAIL: Context service did not pass verified nutrition data to provider")

        if result["verified_route_data_summary"]["source"] != "deterministic_nutrition_system":
            raise ValueError("FAIL: Context service returned incorrect verified-data summary")

        print("PASS: Context service supplies deterministic route data before generation")

    finally:
        delete_user(
            user_id
        )


def test_service_does_not_echo_detailed_verified_data():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            "Your stored nutrition information is available."
        )

        result = generate_context_coaching_answer(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="What are my macros?",
            route=ROUTE_NUTRITION,
            provider=provider,
            verified_route_data_builder=fake_nutrition_route_data
        )

        summary = result["verified_route_data_summary"]

        if "175" in str(summary) or "2350" in str(summary) or "Shellfish" in str(summary):
            raise ValueError("FAIL: API-facing verified-data summary leaked detailed route data")

        print("PASS: Context response exposes only a structural verified-data summary")

    finally:
        delete_user(
            user_id
        )


def test_coaching_route_still_works_without_tool_payload():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            "Focus on completing one planned action today."
        )

        result = generate_context_coaching_answer(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="Help me stay consistent",
            route=ROUTE_COACHING,
            provider=provider
        )

        if result["route"] != ROUTE_COACHING:
            raise ValueError("FAIL: Coaching route stopped working after tool-data integration")

        if result["verified_route_data_summary"]["available_sections"]:
            raise ValueError("FAIL: Coaching route unexpectedly exposed route-specific tool sections")

        print("PASS: Coaching route remains lightweight without unnecessary analytics calls")

    finally:
        delete_user(
            user_id
        )


if __name__ == "__main__":
    test_nutrition_prompt_contains_verified_targets()
    test_nutrition_prompt_contains_allergy_constraints()
    test_verified_data_is_not_called_research_evidence()
    test_nutrition_model_cannot_recalculate_targets()
    test_personal_data_prompt_contains_analytics()
    test_service_passes_verified_data_to_provider()
    test_service_does_not_echo_detailed_verified_data()
    test_coaching_route_still_works_without_tool_payload()