from src.database.query_ai_conversation_database import (
    add_ai_conversation_exchange,
    get_ai_conversation,
    get_ai_conversation_messages
)

from src.rag.answer_generator import (
    validate_generated_answer,
    validate_provider
)

from src.rag.citation_validator import (
    extract_citation_ids
)

from src.rag.context_coaching_prompt_builder import (
    build_context_coaching_prompts
)

from src.rag.conversation_service import (
    ConversationNotFoundError
)

from src.rag.user_context import (
    DEFAULT_HISTORY_LIMIT,
    build_user_context,
    get_user_context_summary
)

from src.rag.verified_route_data import (
    DEFAULT_MAX_VERIFIED_DATA_CHARS,
    build_verified_route_data,
    get_verified_route_data_summary
)


def validate_non_research_answer(answer):
    citation_ids = extract_citation_ids(
        answer
    )

    if citation_ids:
        raise ValueError(f"Non-research answer invented research citations: {citation_ids}")

    return answer


def generate_context_coaching_answer(
    user_id,
    conversation_id,
    question,
    route,
    provider,
    history_limit=DEFAULT_HISTORY_LIMIT,
    history_message_limit=8,
    max_history_chars=4000,
    max_personal_context_chars=5000,
    max_verified_data_chars=DEFAULT_MAX_VERIFIED_DATA_CHARS,
    verified_route_data_builder=None
):
    validate_provider(
        provider
    )

    if verified_route_data_builder is None:
        verified_route_data_builder = build_verified_route_data

    if not callable(
        verified_route_data_builder
    ):
        raise ValueError("verified_route_data_builder must be callable")

    conversation = get_ai_conversation(
        user_id,
        conversation_id
    )

    if conversation is None:
        raise ConversationNotFoundError(
            "Conversation was not found"
        )

    messages = get_ai_conversation_messages(
        user_id,
        conversation_id,
        limit=history_message_limit
    )

    if messages is None:
        raise ConversationNotFoundError(
            "Conversation was not found"
        )

    user_context = build_user_context(
        user_id,
        history_limit=history_limit
    )

    verified_route_data = verified_route_data_builder(
        user_id,
        route
    )

    prompts = build_context_coaching_prompts(
        question=question,
        route=route,
        user_context=user_context,
        conversation_messages=messages,
        verified_route_data=verified_route_data,
        max_history_chars=max_history_chars,
        max_personal_context_chars=max_personal_context_chars,
        max_verified_data_chars=max_verified_data_chars
    )

    answer = provider.generate(
        prompts[
            "system_prompt"
        ],
        prompts[
            "user_prompt"
        ]
    )

    answer = validate_generated_answer(
        answer
    )

    answer = validate_non_research_answer(
        answer
    )

    exchange = add_ai_conversation_exchange(
        user_id=user_id,
        conversation_id=conversation_id,
        user_content=question,
        assistant_content=answer,
        citations=[],
        retrieval_status=f"route:{route}",
        citation_repair_used=False
    )

    if exchange is None:
        raise ConversationNotFoundError(
            "Conversation was not found"
        )

    return {
        "status": "generated",
        "conversation_id": conversation_id,
        "route": route,
        "question": question.strip(),
        "answer": answer,
        "citations": [],
        "citation_validation": {
            "valid": True,
            "cited_paper_ids": [],
            "allowed_paper_ids": [],
            "invalid_paper_ids": [],
            "uncited_evidence_ids": [],
            "missing_required_citation": False
        },
        "citation_repair_used": False,
        "user_context_summary": get_user_context_summary(
            user_context
        ),
        "verified_route_data_summary": get_verified_route_data_summary(
            verified_route_data
        ),
        "history_message_count": len(
            messages
        ),
        "user_message": exchange[
            "user_message"
        ],
        "assistant_message": exchange[
            "assistant_message"
        ]
    }