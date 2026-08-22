from src.rag.citation_builder import (
    build_citations
)

from src.rag.context_builder import (
    build_research_context
)

from src.rag.research_retriever import (
    retrieve_research
)


DEFAULT_MIN_RELEVANCE_SCORE = 0.05
DEFAULT_STRONG_RELEVANCE_SCORE = 0.20


def validate_relevance_score(
    value,
    field_name
):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be numeric")

    if value < 0 or value > 1:
        raise ValueError(f"{field_name} must be between 0 and 1")


def validate_rag_inputs(
    question,
    top_k,
    min_relevance_score,
    strong_relevance_score,
    max_context_chars
):
    if not isinstance(question, str):
        raise ValueError("Question must be a string")

    if not question.strip():
        raise ValueError("Question cannot be empty")

    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer")

    validate_relevance_score(
        min_relevance_score,
        "min_relevance_score"
    )

    validate_relevance_score(
        strong_relevance_score,
        "strong_relevance_score"
    )

    if strong_relevance_score < min_relevance_score:
        raise ValueError("strong_relevance_score cannot be lower than min_relevance_score")

    if not isinstance(max_context_chars, int) or isinstance(max_context_chars, bool) or max_context_chars < 500:
        raise ValueError("max_context_chars must be an integer of at least 500")


def filter_relevant_papers(
    papers,
    min_relevance_score=DEFAULT_MIN_RELEVANCE_SCORE
):
    if not isinstance(papers, list):
        raise ValueError("Papers must be provided as a list")

    validate_relevance_score(
        min_relevance_score,
        "min_relevance_score"
    )

    relevant = []

    for paper in papers:
        score = paper.get(
            "similarity_score"
        )

        if score is None:
            continue

        if float(score) >= min_relevance_score:
            relevant.append(
                paper
            )

    return relevant


def assess_retrieval(
    papers,
    min_relevance_score=DEFAULT_MIN_RELEVANCE_SCORE,
    strong_relevance_score=DEFAULT_STRONG_RELEVANCE_SCORE
):
    relevant = filter_relevant_papers(
        papers,
        min_relevance_score=min_relevance_score
    )

    if not relevant:
        return {
            "status": "no_relevant_evidence",
            "generation_allowed": False,
            "retrieved_count": len(
                papers
            ),
            "relevant_count": 0,
            "top_similarity_score": None,
            "reason": "No retrieved paper met the minimum relevance threshold."
        }

    top_score = float(
        relevant[
            0
        ][
            "similarity_score"
        ]
    )

    if top_score >= strong_relevance_score:
        status = "high_relevance"
        reason = "At least one retrieved paper has high textual relevance to the question."
    else:
        status = "limited_relevance"
        reason = "Relevant evidence was retrieved, but textual relevance is limited."

    return {
        "status": status,
        "generation_allowed": True,
        "retrieved_count": len(
            papers
        ),
        "relevant_count": len(
            relevant
        ),
        "top_similarity_score": top_score,
        "reason": reason
    }


def is_no_vocabulary_error(
    error
):
    return (
        isinstance(
            error,
            ValueError
        )
        and str(
            error
        )
        == "No query terms were found in the research vocabulary"
    )


def prepare_research_rag(
    question,
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
    validate_rag_inputs(
        question,
        top_k,
        min_relevance_score,
        strong_relevance_score,
        max_context_chars
    )

    normalized_question = question.strip()

    try:
        retrieved = retrieve_research(
            normalized_question,
            top_k=top_k,
            min_score=0.0,
            topic=topic,
            subtopic=subtopic,
            min_year=min_year,
            max_year=max_year,
            study_design=study_design
        )

    except ValueError as error:
        if not is_no_vocabulary_error(
            error
        ):
            raise

        retrieved = []

    assessment = assess_retrieval(
        retrieved,
        min_relevance_score=min_relevance_score,
        strong_relevance_score=strong_relevance_score
    )

    relevant_papers = filter_relevant_papers(
        retrieved,
        min_relevance_score=min_relevance_score
    )

    context = build_research_context(
        normalized_question,
        relevant_papers,
        max_chars=max_context_chars
    )

    citations = build_citations(
        relevant_papers
    )

    return {
        "question": normalized_question,
        "retrieval": {
            **assessment,
            "requested_top_k": top_k,
            "min_relevance_score": float(
                min_relevance_score
            ),
            "strong_relevance_score": float(
                strong_relevance_score
            )
        },
        "evidence": relevant_papers,
        "context": context,
        "citations": citations
    }