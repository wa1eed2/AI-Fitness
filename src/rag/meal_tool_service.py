from src.database.query_ai_conversation_database import (
    add_ai_conversation_exchange,
    get_ai_conversation
)

from src.rag.answer_generator import (
    validate_generated_answer,
    validate_provider
)

from src.rag.context_coaching_service import (
    validate_non_research_answer
)

from src.rag.conversation_service import (
    ConversationNotFoundError
)

from src.rag.llm_provider import (
    LLMProviderUnavailableError
)

from src.rag.meal_prompt_builder import (
    build_meal_explanation_prompts
)

from src.rag.tool_fallbacks import (
    build_meal_provider_fallback
)

from src.rag.verified_route_data import (
    to_json_safe
)


DEFAULT_MEAL_FRACTION = 0.25


NUTRITION_TARGET_MISSING_MESSAGE = (
    "I cannot generate a meal yet because you do not currently have a stored "
    "nutrition target. A nutrition target needs to be generated first."
)


MEAL_UNAVAILABLE_MESSAGE = (
    "I could not build a meal from the currently available foods while preserving "
    "your deterministic nutrition and allergy constraints."
)


class MealSafetyValidationError(RuntimeError):
    pass


def validate_meal_fraction(meal_fraction):
    if isinstance(meal_fraction, bool) or not isinstance(meal_fraction, (int, float)):
        raise ValueError("meal_fraction must be a number")

    if not 0 < meal_fraction <= 1:
        raise ValueError("meal_fraction must be greater than 0 and at most 1")


def get_default_nutrition_target(user_id):
    from src.database.query_user_database import (
        get_user_nutrition_target
    )

    return get_user_nutrition_target(
        user_id
    )


def get_default_safe_foods(user_id):
    from src.database.query_user_database import (
        get_safe_foods_for_user
    )

    return get_safe_foods_for_user(
        user_id
    )


def build_default_meal(user_id, meal_fraction):
    from src.nutrition.meal_recommendations import (
        build_meal_from_user_target
    )

    return build_meal_from_user_target(
        user_id,
        meal_fraction=meal_fraction
    )


def normalize_nutrition_target(target):
    if not isinstance(target, dict) and not hasattr(target, "keys"):
        raise ValueError("Nutrition target must be dictionary-like")

    required = [
        "calorie_target",
        "protein_g",
        "carbs_g",
        "fat_g"
    ]

    normalized = {}

    for key in required:
        value = target[key]

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Nutrition target field {key} must be numeric")

        normalized[key] = value

    if normalized["calorie_target"] <= 0:
        raise ValueError("Nutrition calorie target must be greater than 0")

    if normalized["protein_g"] <= 0:
        raise ValueError("Nutrition protein target must be greater than 0")

    if normalized["carbs_g"] < 0:
        raise ValueError("Nutrition carbohydrate target cannot be negative")

    if normalized["fat_g"] < 0:
        raise ValueError("Nutrition fat target cannot be negative")

    return normalized


def build_meal_target(daily_target, meal_fraction):
    return {
        "calorie_target": round(
            daily_target["calorie_target"] * meal_fraction,
            2
        ),
        "protein_g": round(
            daily_target["protein_g"] * meal_fraction,
            2
        ),
        "carbs_g": round(
            daily_target["carbs_g"] * meal_fraction,
            2
        ),
        "fat_g": round(
            daily_target["fat_g"] * meal_fraction,
            2
        )
    }


def validate_meal_result(meal):
    if not isinstance(meal, dict):
        raise ValueError("Deterministic meal builder must return a dictionary")

    required = {
        "foods",
        "total_calories",
        "total_protein_g",
        "total_carbs_g",
        "total_fat_g",
        "protein_target_met",
        "calorie_target_met",
        "carb_target_met",
        "fat_target_met"
    }

    missing = required.difference(
        meal.keys()
    )

    if missing:
        raise ValueError(f"Deterministic meal result is missing fields: {sorted(missing)}")

    if not isinstance(meal["foods"], list):
        raise ValueError("Deterministic meal foods must be a list")

    return meal


def get_food_id(food):
    if not isinstance(food, dict) and not hasattr(food, "keys"):
        raise MealSafetyValidationError("Meal food record is invalid")

    food_id = food["food_id"]

    if not isinstance(food_id, str) or not food_id.strip():
        raise MealSafetyValidationError("Meal food is missing a valid food_id")

    return food_id.strip()


def validate_meal_food_safety(meal, safe_foods):
    if not isinstance(safe_foods, list):
        raise ValueError("Safe foods must be a list")

    safe_food_ids = {
        get_food_id(
            food
        )
        for food in safe_foods
    }

    for food in meal["foods"]:
        food_id = get_food_id(
            food
        )

        if food_id not in safe_food_ids:
            raise MealSafetyValidationError(
                f"Deterministic meal contains food outside the user's safe-food set: {food_id}"
            )


def build_verified_meal_package(
    user_id,
    meal_fraction=DEFAULT_MEAL_FRACTION,
    nutrition_target_getter=None,
    safe_foods_getter=None,
    meal_builder=None
):
    validate_meal_fraction(
        meal_fraction
    )

    if nutrition_target_getter is None:
        nutrition_target_getter = get_default_nutrition_target

    if safe_foods_getter is None:
        safe_foods_getter = get_default_safe_foods

    if meal_builder is None:
        meal_builder = build_default_meal

    if not callable(nutrition_target_getter):
        raise ValueError("nutrition_target_getter must be callable")

    if not callable(safe_foods_getter):
        raise ValueError("safe_foods_getter must be callable")

    if not callable(meal_builder):
        raise ValueError("meal_builder must be callable")

    target = nutrition_target_getter(
        user_id
    )

    if target is None:
        return {
            "status": "nutrition_target_missing",
            "meal_fraction": meal_fraction,
            "daily_target": None,
            "meal_target": None,
            "meal": None
        }

    daily_target = normalize_nutrition_target(
        target
    )

    meal_target = build_meal_target(
        daily_target,
        meal_fraction
    )

    safe_foods = safe_foods_getter(
        user_id
    )

    if not safe_foods:
        return {
            "status": "meal_unavailable",
            "meal_fraction": meal_fraction,
            "daily_target": daily_target,
            "meal_target": meal_target,
            "meal": None
        }

    meal = meal_builder(
        user_id,
        meal_fraction
    )

    meal = validate_meal_result(
        meal
    )

    validate_meal_food_safety(
        meal,
        safe_foods
    )

    if not meal["foods"]:
        return {
            "status": "meal_unavailable",
            "meal_fraction": meal_fraction,
            "daily_target": daily_target,
            "meal_target": meal_target,
            "meal": to_json_safe(meal)
        }

    return {
        "status": "meal_ready",
        "meal_fraction": meal_fraction,
        "daily_target": daily_target,
        "meal_target": meal_target,
        "meal": to_json_safe(meal)
    }


def empty_citation_validation():
    return {
        "valid": True,
        "cited_paper_ids": [],
        "allowed_paper_ids": [],
        "invalid_paper_ids": [],
        "uncited_evidence_ids": [],
        "missing_required_citation": False
    }


def persist_meal_exchange(
    user_id,
    conversation_id,
    question,
    answer,
    status
):
    exchange = add_ai_conversation_exchange(
        user_id=user_id,
        conversation_id=conversation_id,
        user_content=question,
        assistant_content=answer,
        citations=[],
        retrieval_status=f"nutrition:{status}",
        citation_repair_used=False
    )

    if exchange is None:
        raise ConversationNotFoundError("Conversation was not found")

    return exchange


def build_meal_result(
    status,
    user_id,
    conversation_id,
    question,
    answer,
    package,
    explanation_source,
    provider_available,
    exchange
):
    return {
        "status": status,
        "conversation_id": conversation_id,
        "route": "nutrition",
        "question": question.strip(),
        "answer": answer,
        "meal_fraction": package["meal_fraction"],
        "daily_target": package["daily_target"],
        "meal_target": package["meal_target"],
        "meal": package["meal"],
        "citations": [],
        "citation_validation": empty_citation_validation(),
        "citation_repair_used": False,
        "explanation_source": explanation_source,
        "provider_available": provider_available,
        "user_message": exchange["user_message"],
        "assistant_message": exchange["assistant_message"]
    }


def generate_meal_conversation_answer(
    user_id,
    conversation_id,
    question,
    provider,
    meal_fraction=DEFAULT_MEAL_FRACTION,
    nutrition_target_getter=None,
    safe_foods_getter=None,
    meal_builder=None
):
    conversation = get_ai_conversation(
        user_id,
        conversation_id
    )

    if conversation is None:
        raise ConversationNotFoundError("Conversation was not found")

    package = build_verified_meal_package(
        user_id=user_id,
        meal_fraction=meal_fraction,
        nutrition_target_getter=nutrition_target_getter,
        safe_foods_getter=safe_foods_getter,
        meal_builder=meal_builder
    )

    if package["status"] == "nutrition_target_missing":
        exchange = persist_meal_exchange(
            user_id=user_id,
            conversation_id=conversation_id,
            question=question,
            answer=NUTRITION_TARGET_MISSING_MESSAGE,
            status="target_missing"
        )

        return build_meal_result(
            status="nutrition_target_missing",
            user_id=user_id,
            conversation_id=conversation_id,
            question=question,
            answer=NUTRITION_TARGET_MISSING_MESSAGE,
            package=package,
            explanation_source="deterministic",
            provider_available=None,
            exchange=exchange
        )

    if package["status"] == "meal_unavailable":
        exchange = persist_meal_exchange(
            user_id=user_id,
            conversation_id=conversation_id,
            question=question,
            answer=MEAL_UNAVAILABLE_MESSAGE,
            status="meal_unavailable"
        )

        return build_meal_result(
            status="meal_unavailable",
            user_id=user_id,
            conversation_id=conversation_id,
            question=question,
            answer=MEAL_UNAVAILABLE_MESSAGE,
            package=package,
            explanation_source="deterministic",
            provider_available=None,
            exchange=exchange
        )

    validate_provider(
        provider
    )

    prompts = build_meal_explanation_prompts(
        question,
        package
    )

    try:
        answer = provider.generate(
            prompts["system_prompt"],
            prompts["user_prompt"]
        )

        answer = validate_generated_answer(
            answer
        )

        answer = validate_non_research_answer(
            answer
        )

    except LLMProviderUnavailableError:
        answer = build_meal_provider_fallback(
            package
        )

        exchange = persist_meal_exchange(
            user_id=user_id,
            conversation_id=conversation_id,
            question=question,
            answer=answer,
            status="meal_generated_provider_fallback"
        )

        return build_meal_result(
            status="meal_generated",
            user_id=user_id,
            conversation_id=conversation_id,
            question=question,
            answer=answer,
            package=package,
            explanation_source="deterministic_fallback",
            provider_available=False,
            exchange=exchange
        )

    exchange = persist_meal_exchange(
        user_id=user_id,
        conversation_id=conversation_id,
        question=question,
        answer=answer,
        status="meal_generated"
    )

    return build_meal_result(
        status="meal_generated",
        user_id=user_id,
        conversation_id=conversation_id,
        question=question,
        answer=answer,
        package=package,
        explanation_source="llm",
        provider_available=True,
        exchange=exchange
    )