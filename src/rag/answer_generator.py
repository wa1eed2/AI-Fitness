from src.rag.citation_repair import repair_answer_citations

from src.rag.citation_validator import validate_answer_citations

from src.rag.prompt_builder import build_generation_prompts

from src.rag.rag_service import (
    DEFAULT_MIN_RELEVANCE_SCORE,
    DEFAULT_STRONG_RELEVANCE_SCORE,
    prepare_research_rag
)


INSUFFICIENT_EVIDENCE_MESSAGE = (
    "I do not have sufficiently relevant research evidence in the current "
    "research database to answer this question reliably."
)


def validate_provider(provider):
    if provider is None:
        raise ValueError("LLM provider is required")

    generate = getattr(
        provider,
        "generate",
        None
    )

    if generate is None or not callable(generate):
        raise ValueError("LLM provider must provide a callable generate method")


def validate_generated_answer(answer):
    if not isinstance(answer, str):
        raise ValueError("LLM provider must return a string")

    answer = answer.strip()

    if not answer:
        raise ValueError("LLM provider returned an empty answer")

    return answer


def validate_or_repair_citations(
    answer,
    prepared,
    provider,
    system_prompt
):
    validation = validate_answer_citations(
        answer,
        prepared["citations"],
        require_citation=True
    )

    if validation["valid"]:
        return answer, validation, False

    repaired_answer = repair_answer_citations(
        provider=provider,
        answer=answer,
        prepared_rag=prepared,
        system_prompt=system_prompt
    )

    repaired_validation = validate_answer_citations(
        repaired_answer,
        prepared["citations"],
        require_citation=True
    )

    if not repaired_validation["valid"]:
        invalid_ids = repaired_validation[
            "invalid_paper_ids"
        ]

        if invalid_ids:
            raise ValueError(f"Generated answer contains unsupported citations after repair: {invalid_ids}")

        if repaired_validation[
            "missing_required_citation"
        ]:
            raise ValueError("Generated research answer did not cite retrieved evidence after repair")

        raise ValueError("Generated answer failed citation validation after repair")

    return (
        repaired_answer,
        repaired_validation,
        True
    )


def generate_research_answer(
    question,
    provider,
    top_k=5,
    min_relevance_score=DEFAULT_MIN_RELEVANCE_SCORE,
    strong_relevance_score=DEFAULT_STRONG_RELEVANCE_SCORE,
    max_context_chars=6000,
    topic=None,
    subtopic=None,
    min_year=None,
    max_year=None,
    study_design=None
):
    validate_provider(
        provider
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

    if not prepared[
        "retrieval"
    ][
        "generation_allowed"
    ]:
        return {
            "status": "insufficient_evidence",
            "answer": INSUFFICIENT_EVIDENCE_MESSAGE,
            "question": prepared[
                "question"
            ],
            "retrieval": prepared[
                "retrieval"
            ],
            "citations": [],
            "citation_validation": {
                "valid": True,
                "cited_paper_ids": [],
                "allowed_paper_ids": [],
                "invalid_paper_ids": [],
                "uncited_evidence_ids": [],
                "missing_required_citation": False
            },
            "citation_repair_used": False
        }

    prompts = build_generation_prompts(
        prepared
    )

    answer = provider.generate(
        prompts["system_prompt"],
        prompts["user_prompt"]
    )

    answer = validate_generated_answer(
        answer
    )

    answer, citation_validation, repair_used = validate_or_repair_citations(
        answer=answer,
        prepared=prepared,
        provider=provider,
        system_prompt=prompts["system_prompt"]
    )

    return {
        "status": "generated",
        "answer": answer,
        "question": prepared[
            "question"
        ],
        "retrieval": prepared[
            "retrieval"
        ],
        "citations": prepared[
            "citations"
        ],
        "citation_validation": citation_validation,
        "citation_repair_used": repair_used
    }