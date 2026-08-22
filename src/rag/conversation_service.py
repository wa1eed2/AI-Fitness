from src.database.query_ai_conversation_database import (
    add_ai_conversation_exchange,
    get_ai_conversation,
    get_ai_conversation_messages
)

from src.rag.answer_generator import (
    INSUFFICIENT_EVIDENCE_MESSAGE,
    validate_generated_answer,
    validate_or_repair_citations,
    validate_provider
)

from src.rag.conversation_prompt_builder import (
    DEFAULT_MAX_HISTORY_CHARS,
    build_conversation_generation_prompts
)

from src.rag.personalized_prompt_builder import (
    DEFAULT_MAX_PERSONAL_CONTEXT_CHARS
)

from src.rag.rag_service import (
    DEFAULT_MIN_RELEVANCE_SCORE,
    DEFAULT_STRONG_RELEVANCE_SCORE,
    prepare_research_rag
)

from src.rag.user_context import (
    DEFAULT_HISTORY_LIMIT,
    build_user_context,
    get_user_context_summary
)


DEFAULT_CONVERSATION_MESSAGE_LIMIT = 8
MAX_CONVERSATION_MESSAGE_LIMIT = 20


class ConversationNotFoundError(ValueError):
    pass


def validate_conversation_message_limit(limit):
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError("history_message_limit must be an integer")

    if limit < 1 or limit > MAX_CONVERSATION_MESSAGE_LIMIT:
        raise ValueError(f"history_message_limit must be between 1 and {MAX_CONVERSATION_MESSAGE_LIMIT}")


def generate_conversation_research_answer(
    user_id,
    conversation_id,
    question,
    provider,
    top_k=5,
    min_relevance_score=DEFAULT_MIN_RELEVANCE_SCORE,
    strong_relevance_score=DEFAULT_STRONG_RELEVANCE_SCORE,
    max_context_chars=6000,
    max_personal_context_chars=DEFAULT_MAX_PERSONAL_CONTEXT_CHARS,
    history_limit=DEFAULT_HISTORY_LIMIT,
    history_message_limit=DEFAULT_CONVERSATION_MESSAGE_LIMIT,
    max_history_chars=DEFAULT_MAX_HISTORY_CHARS,
    topic=None,
    subtopic=None,
    min_year=None,
    max_year=None,
    study_design=None
):
    validate_provider(
        provider
    )

    validate_conversation_message_limit(
        history_message_limit
    )

    conversation = get_ai_conversation(
        user_id,
        conversation_id
    )

    if conversation is None:
        raise ConversationNotFoundError(
            "Conversation was not found"
        )

    conversation_messages = get_ai_conversation_messages(
        user_id,
        conversation_id,
        limit=history_message_limit
    )

    if conversation_messages is None:
        raise ConversationNotFoundError(
            "Conversation was not found"
        )

    user_context = build_user_context(
        user_id,
        history_limit=history_limit
    )

    prepared = prepare_research_rag(
        question,
        top_k=top_k,
        min_relevance_score=min_relevance_score,
        strong_relevance_score=strong_relevance_score,
        max_context_chars=max_context_chars,
        topic=topic,
        subtopic=subtopic,
        min_year=min_year,
        max_year=max_year,
        study_design=study_design
    )

    context_summary = get_user_context_summary(
        user_context
    )

    if not prepared[
        "retrieval"
    ][
        "generation_allowed"
    ]:
        exchange = add_ai_conversation_exchange(
            user_id=user_id,
            conversation_id=conversation_id,
            user_content=prepared["question"],
            assistant_content=INSUFFICIENT_EVIDENCE_MESSAGE,
            citations=[],
            retrieval_status=prepared["retrieval"]["status"],
            citation_repair_used=False
        )

        if exchange is None:
            raise ConversationNotFoundError(
                "Conversation was not found"
            )

        return {
            "status": "insufficient_evidence",
            "conversation_id": conversation_id,
            "question": prepared["question"],
            "answer": INSUFFICIENT_EVIDENCE_MESSAGE,
            "retrieval": prepared["retrieval"],
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
            "user_context_summary": context_summary,
            "history_message_count": len(
                conversation_messages
            ),
            "user_message": exchange[
                "user_message"
            ],
            "assistant_message": exchange[
                "assistant_message"
            ]
        }

    prompts = build_conversation_generation_prompts(
        prepared,
        user_context,
        conversation_messages,
        max_history_chars=max_history_chars,
        max_personal_context_chars=max_personal_context_chars
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

    answer, citation_validation, repair_used = validate_or_repair_citations(
        answer=answer,
        prepared=prepared,
        provider=provider,
        system_prompt=prompts[
            "system_prompt"
        ]
    )

    exchange = add_ai_conversation_exchange(
        user_id=user_id,
        conversation_id=conversation_id,
        user_content=prepared["question"],
        assistant_content=answer,
        citations=prepared["citations"],
        retrieval_status=prepared["retrieval"]["status"],
        citation_repair_used=repair_used
    )

    if exchange is None:
        raise ConversationNotFoundError(
            "Conversation was not found"
        )

    return {
        "status": "generated",
        "conversation_id": conversation_id,
        "question": prepared["question"],
        "answer": answer,
        "retrieval": prepared["retrieval"],
        "citations": prepared["citations"],
        "citation_validation": citation_validation,
        "citation_repair_used": repair_used,
        "user_context_summary": context_summary,
        "history_message_count": len(
            conversation_messages
        ),
        "user_message": exchange[
            "user_message"
        ],
        "assistant_message": exchange[
            "assistant_message"
        ]
    }