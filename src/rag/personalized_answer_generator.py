from src.rag.answer_generator import (
    INSUFFICIENT_EVIDENCE_MESSAGE,
    validate_provider
)

from src.rag.citation_validator import (
    validate_answer_citations
)

from src.rag.personalized_prompt_builder import (
    DEFAULT_MAX_PERSONAL_CONTEXT_CHARS,
    build_personalized_generation_prompts
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


def generate_personalized_research_answer(
    user_id,
    question,
    provider,
    top_k=5,
    min_relevance_score=DEFAULT_MIN_RELEVANCE_SCORE,
    strong_relevance_score=DEFAULT_STRONG_RELEVANCE_SCORE,
    max_context_chars=6000,
    max_personal_context_chars=DEFAULT_MAX_PERSONAL_CONTEXT_CHARS,
    history_limit=DEFAULT_HISTORY_LIMIT,
    topic=None,
    subtopic=None,
    min_year=None,
    max_year=None,
    study_design=None
):
    validate_provider(
        provider
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
        return {
            "status": "insufficient_evidence",
            "answer": INSUFFICIENT_EVIDENCE_MESSAGE,
            "question": prepared["question"],
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
            "user_context_summary": context_summary
        }

    prompts = build_personalized_generation_prompts(
        prepared,
        user_context,
        max_personal_context_chars=max_personal_context_chars
    )

    answer = provider.generate(
        prompts["system_prompt"],
        prompts["user_prompt"]
    )

    if not isinstance(answer, str):
        raise ValueError("LLM provider must return a string")

    answer = answer.strip()

    if not answer:
        raise ValueError("LLM provider returned an empty answer")

    citation_validation = validate_answer_citations(
        answer,
        prepared["citations"],
        require_citation=True
    )

    if not citation_validation[
        "valid"
    ]:
        invalid_ids = citation_validation[
            "invalid_paper_ids"
        ]

        if invalid_ids:
            raise ValueError(f"Generated answer contains unsupported citations: {invalid_ids}")

        if citation_validation[
            "missing_required_citation"
        ]:
            raise ValueError("Generated personalized research answer did not cite retrieved evidence")

        raise ValueError("Generated personalized answer failed citation validation")

    return {
        "status": "generated",
        "answer": answer,
        "question": prepared["question"],
        "retrieval": prepared["retrieval"],
        "citations": prepared["citations"],
        "citation_validation": citation_validation,
        "user_context_summary": context_summary
    }