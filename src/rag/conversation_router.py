from src.database.query_ai_conversation_database import (
    add_ai_conversation_exchange,
    get_ai_conversation
)

from src.rag.adaptation_tool_service import (
    generate_adaptation_conversation_answer
)

from src.rag.context_coaching_service import (
    generate_context_coaching_answer
)

from src.rag.conversation_service import (
    ConversationNotFoundError,
    generate_conversation_research_answer
)

from src.rag.meal_tool_service import (
    DEFAULT_MEAL_FRACTION,
    generate_meal_conversation_answer
)

from src.rag.nutrition_action_classifier import (
    ACTION_MEAL_GENERATION,
    classify_nutrition_action
)

from src.rag.question_classifier import (
    ROUTE_ADAPTATION,
    ROUTE_NUTRITION,
    ROUTE_RESEARCH,
    ROUTE_SAFETY,
    ROUTE_UNKNOWN,
    ROUTE_WORKOUT,
    classify_question,
    normalize_question
)

from src.rag.safety_response import (
    build_safety_response
)

from src.rag.workout_action_classifier import (
    classify_workout_action
)

from src.rag.workout_tool_service import (
    generate_workout_conversation_answer
)


UNKNOWN_MESSAGE = (
    "I could not confidently understand that message. Please rephrase it with "
    "a little more detail so I can route it safely."
)


def persist_deterministic_response(
    user_id,
    conversation_id,
    question,
    answer,
    retrieval_status
):
    conversation = get_ai_conversation(
        user_id,
        conversation_id
    )

    if conversation is None:
        raise ConversationNotFoundError("Conversation was not found")

    exchange = add_ai_conversation_exchange(
        user_id=user_id,
        conversation_id=conversation_id,
        user_content=question,
        assistant_content=answer,
        citations=[],
        retrieval_status=retrieval_status,
        citation_repair_used=False
    )

    if exchange is None:
        raise ConversationNotFoundError("Conversation was not found")

    return exchange


def route_conversation_message(
    user_id,
    conversation_id,
    question,
    provider,
    top_k=5,
    min_relevance_score=0.05,
    strong_relevance_score=0.20,
    max_context_chars=6000,
    max_personal_context_chars=5000,
    history_limit=5,
    history_message_limit=8,
    max_history_chars=4000,
    meal_fraction=DEFAULT_MEAL_FRACTION,
    exercise_count=None,
    topic=None,
    subtopic=None,
    min_year=None,
    max_year=None,
    study_design=None
):
    normalized_question = normalize_question(
        question
    )

    classification = classify_question(
        normalized_question
    )

    route = classification[
        "route"
    ]

    if route == ROUTE_SAFETY:
        answer = build_safety_response(
            classification
        )

        exchange = persist_deterministic_response(
            user_id=user_id,
            conversation_id=conversation_id,
            question=normalized_question,
            answer=answer,
            retrieval_status=f"safety:{classification['safety_level']}"
        )

        return {
            "status": "safety_response",
            "conversation_id": conversation_id,
            "route": route,
            "routing": classification,
            "question": normalized_question,
            "answer": answer,
            "citations": [],
            "citation_repair_used": False,
            "user_message": exchange[
                "user_message"
            ],
            "assistant_message": exchange[
                "assistant_message"
            ]
        }

    if route == ROUTE_UNKNOWN:
        exchange = persist_deterministic_response(
            user_id=user_id,
            conversation_id=conversation_id,
            question=normalized_question,
            answer=UNKNOWN_MESSAGE,
            retrieval_status="unknown"
        )

        return {
            "status": "insufficient_evidence",
            "conversation_id": conversation_id,
            "route": route,
            "routing": classification,
            "question": normalized_question,
            "answer": UNKNOWN_MESSAGE,
            "citations": [],
            "citation_repair_used": False,
            "user_message": exchange[
                "user_message"
            ],
            "assistant_message": exchange[
                "assistant_message"
            ]
        }

    if route == ROUTE_RESEARCH:
        result = generate_conversation_research_answer(
            user_id=user_id,
            conversation_id=conversation_id,
            question=normalized_question,
            provider=provider,
            top_k=top_k,
            min_relevance_score=min_relevance_score,
            strong_relevance_score=strong_relevance_score,
            max_context_chars=max_context_chars,
            max_personal_context_chars=max_personal_context_chars,
            history_limit=history_limit,
            history_message_limit=history_message_limit,
            max_history_chars=max_history_chars,
            topic=topic,
            subtopic=subtopic,
            min_year=min_year,
            max_year=max_year,
            study_design=study_design
        )

        result[
            "route"
        ] = route

        result[
            "routing"
        ] = classification

        return result

    if route == ROUTE_WORKOUT:
        workout_action = classify_workout_action(
            normalized_question
        )

        result = generate_workout_conversation_answer(
            user_id=user_id,
            conversation_id=conversation_id,
            question=normalized_question,
            workout_action=workout_action[
                "action"
            ],
            provider=provider,
            exercise_count=exercise_count
        )

        result[
            "routing"
        ] = classification

        result[
            "workout_routing"
        ] = workout_action

        return result

    if route == ROUTE_ADAPTATION:
        result = generate_adaptation_conversation_answer(
            user_id=user_id,
            conversation_id=conversation_id,
            question=normalized_question,
            provider=provider
        )

        result[
            "routing"
        ] = classification

        return result

    if route == ROUTE_NUTRITION:
        nutrition_action = classify_nutrition_action(
            normalized_question
        )

        if nutrition_action[
            "action"
        ] == ACTION_MEAL_GENERATION:
            result = generate_meal_conversation_answer(
                user_id=user_id,
                conversation_id=conversation_id,
                question=normalized_question,
                provider=provider,
                meal_fraction=meal_fraction
            )

            result[
                "routing"
            ] = classification

            result[
                "nutrition_action"
            ] = nutrition_action

            return result

        result = generate_context_coaching_answer(
            user_id=user_id,
            conversation_id=conversation_id,
            question=normalized_question,
            route=route,
            provider=provider,
            history_limit=history_limit,
            history_message_limit=history_message_limit,
            max_history_chars=max_history_chars,
            max_personal_context_chars=max_personal_context_chars
        )

        result[
            "routing"
        ] = classification

        result[
            "nutrition_action"
        ] = nutrition_action

        return result

    result = generate_context_coaching_answer(
        user_id=user_id,
        conversation_id=conversation_id,
        question=normalized_question,
        route=route,
        provider=provider,
        history_limit=history_limit,
        history_message_limit=history_message_limit,
        max_history_chars=max_history_chars,
        max_personal_context_chars=max_personal_context_chars
    )

    result[
        "routing"
    ] = classification

    return result