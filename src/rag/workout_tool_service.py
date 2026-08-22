from src.database.query_ai_conversation_database import (
    add_ai_conversation_exchange,
    get_ai_conversation
)

from src.database.query_user_database import (
    get_user_profile
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

from src.rag.tool_fallbacks import (
    build_workout_provider_fallback
)

from src.rag.workout_action_classifier import (
    ACTION_SINGLE_WORKOUT,
    ACTION_WEEKLY_WORKOUT
)

from src.rag.workout_prompt_builder import (
    build_workout_explanation_prompts
)


WORKOUT_PROFILE_REQUIRED_MESSAGE = (
    "I cannot generate a workout yet because your fitness profile is incomplete. "
    "Your fitness level, goal, session duration, training frequency, and preferred "
    "environment are needed before the deterministic workout system can build a plan."
)


WORKOUT_UNAVAILABLE_MESSAGE = (
    "I could not build a workout from the exercises currently compatible with your "
    "profile, equipment, preferences, limitations, and environment."
)


class WorkoutSafetyValidationError(RuntimeError):
    pass


def validate_exercise_count(exercise_count):
    if exercise_count is None:
        return

    if not isinstance(exercise_count, int) or isinstance(exercise_count, bool):
        raise ValueError("exercise_count must be an integer or None")

    if exercise_count < 1 or exercise_count > 20:
        raise ValueError("exercise_count must be between 1 and 20")


def get_default_candidate_exercises(user_id):
    from src.recommendations.workout_recommendations import (
        get_candidate_exercises_for_user
    )

    return get_candidate_exercises_for_user(
        user_id
    )


def build_default_single_workout(user_id, exercise_count=None):
    from src.recommendations.workout_recommendations import (
        build_workout_plan_for_user
    )

    return build_workout_plan_for_user(
        user_id,
        exercise_count=exercise_count
    )


def build_default_weekly_workout(user_id, exercise_count=None):
    from src.recommendations.workout_recommendations import (
        build_weekly_workout_plan_for_user
    )

    return build_weekly_workout_plan_for_user(
        user_id,
        exercise_count=exercise_count
    )


def get_exercise_id(exercise):
    if not isinstance(exercise, dict) and not hasattr(exercise, "keys"):
        raise WorkoutSafetyValidationError("Workout exercise record is invalid")

    exercise_id = exercise["exercise_id"]

    if not isinstance(exercise_id, str) or not exercise_id.strip():
        raise WorkoutSafetyValidationError("Workout exercise is missing a valid exercise_id")

    return exercise_id.strip()


def collect_plan_exercise_ids(plan):
    exercise_ids = []

    def visit(value):
        if isinstance(value, dict):
            if "exercise_id" in value:
                exercise_id = value["exercise_id"]

                if not isinstance(exercise_id, str) or not exercise_id.strip():
                    raise WorkoutSafetyValidationError("Generated workout contains invalid exercise_id")

                exercise_ids.append(
                    exercise_id.strip()
                )

            for child in value.values():
                visit(child)

        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child)

    visit(plan)

    return exercise_ids


def validate_workout_plan_safety(workout_plan, candidate_exercises):
    if not isinstance(workout_plan, dict):
        raise ValueError("Deterministic workout builder must return a dictionary")

    if not isinstance(candidate_exercises, list):
        raise ValueError("Candidate exercises must be a list")

    candidate_ids = {
        get_exercise_id(
            exercise
        )
        for exercise in candidate_exercises
    }

    selected_ids = collect_plan_exercise_ids(
        workout_plan
    )

    if not selected_ids:
        raise WorkoutSafetyValidationError("Generated workout does not contain any exercise IDs")

    unsafe_ids = sorted(
        {
            exercise_id
            for exercise_id in selected_ids
            if exercise_id not in candidate_ids
        }
    )

    if unsafe_ids:
        raise WorkoutSafetyValidationError(
            f"Generated workout contains exercises outside the user's safe candidate set: {unsafe_ids}"
        )

    return selected_ids


def build_verified_workout_package(
    user_id,
    workout_action,
    exercise_count=None,
    profile_getter=None,
    candidate_getter=None,
    single_workout_builder=None,
    weekly_workout_builder=None
):
    validate_exercise_count(
        exercise_count
    )

    if workout_action not in {
        ACTION_SINGLE_WORKOUT,
        ACTION_WEEKLY_WORKOUT
    }:
        raise ValueError("Unsupported workout action")

    if profile_getter is None:
        profile_getter = get_user_profile

    if candidate_getter is None:
        candidate_getter = get_default_candidate_exercises

    if single_workout_builder is None:
        single_workout_builder = build_default_single_workout

    if weekly_workout_builder is None:
        weekly_workout_builder = build_default_weekly_workout

    if not callable(profile_getter):
        raise ValueError("profile_getter must be callable")

    if not callable(candidate_getter):
        raise ValueError("candidate_getter must be callable")

    if not callable(single_workout_builder):
        raise ValueError("single_workout_builder must be callable")

    if not callable(weekly_workout_builder):
        raise ValueError("weekly_workout_builder must be callable")

    profile = profile_getter(
        user_id
    )

    if profile is None:
        return {
            "status": "profile_required",
            "workout_action": workout_action,
            "requested_exercise_count": exercise_count,
            "candidate_exercise_count": 0,
            "selected_exercise_count": 0,
            "workout_plan": None
        }

    candidate_exercises = candidate_getter(
        user_id
    )

    if not candidate_exercises:
        return {
            "status": "workout_unavailable",
            "workout_action": workout_action,
            "requested_exercise_count": exercise_count,
            "candidate_exercise_count": 0,
            "selected_exercise_count": 0,
            "workout_plan": None
        }

    if workout_action == ACTION_WEEKLY_WORKOUT:
        workout_plan = weekly_workout_builder(
            user_id,
            exercise_count
        )
    else:
        workout_plan = single_workout_builder(
            user_id,
            exercise_count
        )

    selected_ids = validate_workout_plan_safety(
        workout_plan,
        candidate_exercises
    )

    return {
        "status": "workout_ready",
        "workout_action": workout_action,
        "requested_exercise_count": exercise_count,
        "candidate_exercise_count": len(candidate_exercises),
        "selected_exercise_count": len(selected_ids),
        "workout_plan": workout_plan
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


def persist_workout_exchange(
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
        retrieval_status=f"workout:{status}",
        citation_repair_used=False
    )

    if exchange is None:
        raise ConversationNotFoundError("Conversation was not found")

    return exchange


def build_workout_result(
    status,
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
        "route": "workout",
        "question": question.strip(),
        "answer": answer,
        "workout_action": package["workout_action"],
        "candidate_exercise_count": package["candidate_exercise_count"],
        "selected_exercise_count": package["selected_exercise_count"],
        "workout_plan": package["workout_plan"],
        "citations": [],
        "citation_validation": empty_citation_validation(),
        "citation_repair_used": False,
        "explanation_source": explanation_source,
        "provider_available": provider_available,
        "user_message": exchange["user_message"],
        "assistant_message": exchange["assistant_message"]
    }


def generate_workout_conversation_answer(
    user_id,
    conversation_id,
    question,
    workout_action,
    provider,
    exercise_count=None,
    profile_getter=None,
    candidate_getter=None,
    single_workout_builder=None,
    weekly_workout_builder=None
):
    conversation = get_ai_conversation(
        user_id,
        conversation_id
    )

    if conversation is None:
        raise ConversationNotFoundError("Conversation was not found")

    package = build_verified_workout_package(
        user_id=user_id,
        workout_action=workout_action,
        exercise_count=exercise_count,
        profile_getter=profile_getter,
        candidate_getter=candidate_getter,
        single_workout_builder=single_workout_builder,
        weekly_workout_builder=weekly_workout_builder
    )

    if package["status"] == "profile_required":
        exchange = persist_workout_exchange(
            user_id=user_id,
            conversation_id=conversation_id,
            question=question,
            answer=WORKOUT_PROFILE_REQUIRED_MESSAGE,
            status="profile_required"
        )

        return build_workout_result(
            status="profile_required",
            conversation_id=conversation_id,
            question=question,
            answer=WORKOUT_PROFILE_REQUIRED_MESSAGE,
            package=package,
            explanation_source="deterministic",
            provider_available=None,
            exchange=exchange
        )

    if package["status"] == "workout_unavailable":
        exchange = persist_workout_exchange(
            user_id=user_id,
            conversation_id=conversation_id,
            question=question,
            answer=WORKOUT_UNAVAILABLE_MESSAGE,
            status="workout_unavailable"
        )

        return build_workout_result(
            status="workout_unavailable",
            conversation_id=conversation_id,
            question=question,
            answer=WORKOUT_UNAVAILABLE_MESSAGE,
            package=package,
            explanation_source="deterministic",
            provider_available=None,
            exchange=exchange
        )

    validate_provider(
        provider
    )

    prompts = build_workout_explanation_prompts(
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
        answer = build_workout_provider_fallback(
            package
        )

        exchange = persist_workout_exchange(
            user_id=user_id,
            conversation_id=conversation_id,
            question=question,
            answer=answer,
            status="workout_generated_provider_fallback"
        )

        return build_workout_result(
            status="workout_generated",
            conversation_id=conversation_id,
            question=question,
            answer=answer,
            package=package,
            explanation_source="deterministic_fallback",
            provider_available=False,
            exchange=exchange
        )

    exchange = persist_workout_exchange(
        user_id=user_id,
        conversation_id=conversation_id,
        question=question,
        answer=answer,
        status="workout_generated"
    )

    return build_workout_result(
        status="workout_generated",
        conversation_id=conversation_id,
        question=question,
        answer=answer,
        package=package,
        explanation_source="llm",
        provider_available=True,
        exchange=exchange
    )