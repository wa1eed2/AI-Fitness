from src.database.query_ai_conversation_database import (
    create_ai_conversation,
    get_ai_conversation_messages
)

from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.rag.conversation_service import (
    ConversationNotFoundError
)

from src.rag.fake_llm_provider import (
    FakeLLMProvider
)

from src.rag.meal_tool_service import (
    MealSafetyValidationError,
    build_verified_meal_package,
    generate_meal_conversation_answer
)

from src.rag.nutrition_action_classifier import (
    ACTION_MEAL_GENERATION,
    ACTION_NUTRITION_CONTEXT,
    classify_nutrition_action
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
                "servings": 1.0
            },
            {
                "food_id": "F002",
                "name": "Rice",
                "servings": 1.2
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


def test_meal_request_is_detected():
    result = classify_nutrition_action(
        "Build me a meal around my macros"
    )

    if result["action"] != ACTION_MEAL_GENERATION:
        raise ValueError("FAIL: Explicit meal request was not detected")

    print("PASS: Nutrition action classifier detects meal-generation request")


def test_macro_question_is_not_meal_generation():
    result = classify_nutrition_action(
        "What are my macros?"
    )

    if result["action"] != ACTION_NUTRITION_CONTEXT:
        raise ValueError("FAIL: Macro explanation was incorrectly classified as meal generation")

    print("PASS: Nutrition explanation remains separate from meal generation")


def test_meal_targets_come_from_daily_target():
    package = build_verified_meal_package(
        user_id=1,
        meal_fraction=0.25,
        nutrition_target_getter=fake_target_getter,
        safe_foods_getter=fake_safe_foods_getter,
        meal_builder=fake_meal_builder
    )

    target = package["meal_target"]

    if target["calorie_target"] != 600:
        raise ValueError("FAIL: Meal calorie target was calculated incorrectly")

    if target["protein_g"] != 40:
        raise ValueError("FAIL: Meal protein target was calculated incorrectly")

    if target["carbs_g"] != 70:
        raise ValueError("FAIL: Meal carbohydrate target was calculated incorrectly")

    if target["fat_g"] != 17.5:
        raise ValueError("FAIL: Meal fat target was calculated incorrectly")

    print("PASS: Meal fraction deterministically derives meal macro targets")


def test_safe_meal_is_preserved():
    package = build_verified_meal_package(
        user_id=1,
        meal_fraction=0.25,
        nutrition_target_getter=fake_target_getter,
        safe_foods_getter=fake_safe_foods_getter,
        meal_builder=fake_meal_builder
    )

    if package["status"] != "meal_ready":
        raise ValueError("FAIL: Safe deterministic meal was not accepted")

    if package["meal"]["foods"][0]["food_id"] != "F001":
        raise ValueError("FAIL: Deterministic meal foods were not preserved")

    print("PASS: Safe deterministic meal is preserved for application output")


def test_unsafe_food_is_blocked():
    def unsafe_builder(user_id, meal_fraction):
        meal = fake_meal_builder(
            user_id,
            meal_fraction
        )

        meal["foods"] = [
            {
                "food_id": "F999",
                "name": "Unsafe Food",
                "servings": 1
            }
        ]

        return meal

    try:
        build_verified_meal_package(
            user_id=1,
            nutrition_target_getter=fake_target_getter,
            safe_foods_getter=fake_safe_foods_getter,
            meal_builder=unsafe_builder
        )

    except MealSafetyValidationError:
        print("PASS: Meal safety validation rejects food outside safe-food set")
        return

    raise ValueError("FAIL: Unsafe deterministic meal food was accepted")


def test_missing_target_skips_meal_builder():
    builder_calls = []

    def missing_target(user_id):
        return None

    def builder(user_id, meal_fraction):
        builder_calls.append(
            True
        )

        return fake_meal_builder(
            user_id,
            meal_fraction
        )

    package = build_verified_meal_package(
        user_id=1,
        nutrition_target_getter=missing_target,
        safe_foods_getter=fake_safe_foods_getter,
        meal_builder=builder
    )

    if package["status"] != "nutrition_target_missing":
        raise ValueError("FAIL: Missing nutrition target returned incorrect status")

    if builder_calls:
        raise ValueError("FAIL: Meal builder ran without nutrition target")

    print("PASS: Missing nutrition target blocks meal generation before meal builder")


def test_no_safe_foods_blocks_meal_generation():
    builder_calls = []

    def no_safe_foods(user_id):
        return []

    def builder(user_id, meal_fraction):
        builder_calls.append(
            True
        )

        return fake_meal_builder(
            user_id,
            meal_fraction
        )

    package = build_verified_meal_package(
        user_id=1,
        nutrition_target_getter=fake_target_getter,
        safe_foods_getter=no_safe_foods,
        meal_builder=builder
    )

    if package["status"] != "meal_unavailable":
        raise ValueError("FAIL: Empty safe-food set returned incorrect status")

    if builder_calls:
        raise ValueError("FAIL: Meal builder ran despite empty safe-food set")

    print("PASS: Empty safe-food set fails safely before meal generation")


def test_model_receives_totals_but_not_food_names():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            "The generated meal is close to its calorie and protein targets."
        )

        result = generate_meal_conversation_answer(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="Build me a meal",
            provider=provider,
            nutrition_target_getter=fake_target_getter,
            safe_foods_getter=fake_safe_foods_getter,
            meal_builder=fake_meal_builder
        )

        prompt = provider.calls[0]["user_prompt"]

        if '"total_protein_g": 42.0' not in prompt:
            raise ValueError("FAIL: Meal explanation prompt omitted deterministic macro totals")

        if "Chicken Breast" in prompt or "Rice" in prompt:
            raise ValueError("FAIL: Food names were exposed to meal explanation model")

        if result["meal"]["foods"][0]["name"] != "Chicken Breast":
            raise ValueError("FAIL: Structured deterministic meal was not returned to application")

        print("PASS: Groq receives aggregate meal data while structured foods remain deterministic")

    finally:
        delete_user(
            user_id
        )


def test_missing_target_does_not_call_provider():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            "This must not be generated."
        )

        result = generate_meal_conversation_answer(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="Build me a meal",
            provider=provider,
            nutrition_target_getter=lambda user_id: None,
            safe_foods_getter=fake_safe_foods_getter,
            meal_builder=fake_meal_builder
        )

        if result["status"] != "nutrition_target_missing":
            raise ValueError("FAIL: Missing target returned incorrect response status")

        if provider.calls:
            raise ValueError("FAIL: Provider was called despite missing nutrition target")

        messages = get_ai_conversation_messages(
            user_id,
            conversation["conversation_id"],
            limit=20
        )

        if len(messages) != 2:
            raise ValueError("FAIL: Deterministic target-missing response was not persisted")

        print("PASS: Missing nutrition target returns deterministic response without model call")

    finally:
        delete_user(
            user_id
        )


def test_successful_meal_is_persisted():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            "The generated meal reaches its calorie and protein targets."
        )

        result = generate_meal_conversation_answer(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="Build me a meal",
            provider=provider,
            nutrition_target_getter=fake_target_getter,
            safe_foods_getter=fake_safe_foods_getter,
            meal_builder=fake_meal_builder
        )

        messages = get_ai_conversation_messages(
            user_id,
            conversation["conversation_id"],
            limit=20
        )

        if result["status"] != "meal_generated":
            raise ValueError("FAIL: Successful meal returned incorrect status")

        if len(messages) != 2:
            raise ValueError("FAIL: Successful meal exchange was not persisted")

        if messages[-1]["retrieval_status"] != "nutrition:meal_generated":
            raise ValueError("FAIL: Stored meal explanation lost deterministic route status")

        print("PASS: Successful deterministic meal exchange is persisted")

    finally:
        delete_user(
            user_id
        )


def test_meal_model_cannot_invent_research_citation():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            "This meal is scientifically optimal [P999]."
        )

        try:
            generate_meal_conversation_answer(
                user_id=user_id,
                conversation_id=conversation["conversation_id"],
                question="Build me a meal",
                provider=provider,
                nutrition_target_getter=fake_target_getter,
                safe_foods_getter=fake_safe_foods_getter,
                meal_builder=fake_meal_builder
            )

        except ValueError as error:
            if "invented research citations" not in str(error):
                raise ValueError(f"FAIL: Incorrect fabricated-citation error: {error}")

            print("PASS: Meal explanation cannot fabricate research citations")
            return

        raise ValueError("FAIL: Meal explanation accepted fabricated research citation")

    finally:
        delete_user(
            user_id
        )


def test_cross_user_meal_request_is_blocked_before_tools():
    owner_id = create_user()
    other_id = create_user()

    target_calls = []

    try:
        conversation = create_ai_conversation(
            owner_id
        )

        def tracked_target_getter(user_id):
            target_calls.append(
                user_id
            )

            return fake_target_getter(
                user_id
            )

        try:
            generate_meal_conversation_answer(
                user_id=other_id,
                conversation_id=conversation["conversation_id"],
                question="Build me a meal",
                provider=FakeLLMProvider("Unused"),
                nutrition_target_getter=tracked_target_getter,
                safe_foods_getter=fake_safe_foods_getter,
                meal_builder=fake_meal_builder
            )

        except ConversationNotFoundError:
            if target_calls:
                raise ValueError("FAIL: Nutrition tools ran before conversation ownership validation")

            print("PASS: Meal generation validates conversation ownership before nutrition tools")
            return

        raise ValueError("FAIL: Cross-user meal request was allowed")

    finally:
        delete_user(
            owner_id
        )

        delete_user(
            other_id
        )


if __name__ == "__main__":
    test_meal_request_is_detected()
    test_macro_question_is_not_meal_generation()
    test_meal_targets_come_from_daily_target()
    test_safe_meal_is_preserved()
    test_unsafe_food_is_blocked()
    test_missing_target_skips_meal_builder()
    test_no_safe_foods_blocks_meal_generation()
    test_model_receives_totals_but_not_food_names()
    test_missing_target_does_not_call_provider()
    test_successful_meal_is_persisted()
    test_meal_model_cannot_invent_research_citation()
    test_cross_user_meal_request_is_blocked_before_tools()