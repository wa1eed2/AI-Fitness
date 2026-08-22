from src.rag.rag_service import (
    assess_retrieval,
    filter_relevant_papers,
    prepare_research_rag
)

from src.rag.research_retriever import (
    get_research_corpus
)


def get_test_paper():
    papers = get_research_corpus()

    if not papers:
        raise ValueError("FAIL: Research database contains no papers")

    return papers[
        0
    ]


def test_rag_service_returns_complete_object():
    paper = get_test_paper()

    result = prepare_research_rag(
        paper["title"]
    )

    required = {
        "question",
        "retrieval",
        "evidence",
        "context",
        "citations"
    }

    if set(result.keys()) != required:
        raise ValueError("FAIL: RAG service returned unexpected top-level structure")

    print("PASS: RAG service returns structured preparation object")


def test_rag_service_preserves_question():
    paper = get_test_paper()

    question = f"  {paper['title']}  "

    result = prepare_research_rag(
        question
    )

    if result["question"] != paper["title"]:
        raise ValueError("FAIL: RAG service did not normalize question whitespace")

    print("PASS: RAG service normalizes user question")


def test_exact_title_allows_evidence_generation():
    paper = get_test_paper()

    result = prepare_research_rag(
        paper["title"]
    )

    if not result["retrieval"]["generation_allowed"]:
        raise ValueError("FAIL: Exact-title evidence was incorrectly blocked")

    if not result["evidence"]:
        raise ValueError("FAIL: Exact-title RAG preparation returned no evidence")

    print("PASS: Relevant research allows evidence-backed generation")


def test_evidence_and_citations_are_aligned():
    paper = get_test_paper()

    result = prepare_research_rag(
        paper["title"]
    )

    evidence_ids = [
        item["paper_id"]
        for item in result["evidence"]
    ]

    citation_ids = [
        item["paper_id"]
        for item in result["citations"]
    ]

    if evidence_ids != citation_ids:
        raise ValueError("FAIL: Citation order does not match retrieved evidence order")

    print("PASS: RAG citations stay aligned with retrieved evidence")


def test_context_contains_only_selected_evidence_ids():
    paper = get_test_paper()

    result = prepare_research_rag(
        paper["title"],
        top_k=1
    )

    if len(result["evidence"]) != 1:
        raise ValueError("FAIL: top_k=1 did not produce exactly one relevant evidence record")

    paper_id = result["evidence"][0]["paper_id"]

    if paper_id not in result["context"]:
        raise ValueError("FAIL: Selected evidence paper is missing from RAG context")

    print("PASS: RAG context contains selected evidence")


def test_unknown_vocabulary_becomes_no_evidence_state():
    result = prepare_research_rag(
        "zzzxqvplmnkjhgfd"
    )

    if result["retrieval"]["status"] != "no_relevant_evidence":
        raise ValueError("FAIL: Unknown vocabulary did not produce no-evidence state")

    if result["retrieval"]["generation_allowed"]:
        raise ValueError("FAIL: Generation was allowed without relevant evidence")

    if result["evidence"] != []:
        raise ValueError("FAIL: Unknown vocabulary produced evidence")

    if result["citations"] != []:
        raise ValueError("FAIL: Unknown vocabulary produced citations")

    print("PASS: Unknown research question vocabulary fails safely")


def test_no_evidence_context_is_explicit():
    result = prepare_research_rag(
        "zzzxqvplmnkjhgfd"
    )

    expected = "No research evidence was retrieved for this question."

    if expected not in result["context"]:
        raise ValueError("FAIL: Empty-evidence RAG context is not explicit")

    print("PASS: Empty RAG context explicitly reports missing evidence")


def test_filter_relevant_papers_is_deterministic():
    papers = [
        {
            "paper_id": "A",
            "similarity_score": 0.50
        },
        {
            "paper_id": "B",
            "similarity_score": 0.04
        },
        {
            "paper_id": "C",
            "similarity_score": 0.10
        }
    ]

    relevant = filter_relevant_papers(
        papers,
        min_relevance_score=0.05
    )

    ids = [
        paper["paper_id"]
        for paper in relevant
    ]

    if ids != ["A", "C"]:
        raise ValueError("FAIL: Relevance threshold filtering returned incorrect papers")

    print("PASS: RAG relevance gate removes low-score evidence")


def test_high_relevance_assessment():
    papers = [
        {
            "paper_id": "A",
            "similarity_score": 0.75
        }
    ]

    result = assess_retrieval(
        papers,
        min_relevance_score=0.05,
        strong_relevance_score=0.20
    )

    if result["status"] != "high_relevance":
        raise ValueError("FAIL: High-similarity evidence was not classified as high relevance")

    if not result["generation_allowed"]:
        raise ValueError("FAIL: High-relevance evidence did not allow generation")

    print("PASS: RAG service identifies high textual relevance")


def test_limited_relevance_assessment():
    papers = [
        {
            "paper_id": "A",
            "similarity_score": 0.10
        }
    ]

    result = assess_retrieval(
        papers,
        min_relevance_score=0.05,
        strong_relevance_score=0.20
    )

    if result["status"] != "limited_relevance":
        raise ValueError("FAIL: Moderate similarity was not classified as limited relevance")

    if not result["generation_allowed"]:
        raise ValueError("FAIL: Relevant evidence was incorrectly blocked")

    print("PASS: RAG service distinguishes limited textual relevance")


def test_no_relevance_assessment():
    papers = [
        {
            "paper_id": "A",
            "similarity_score": 0.01
        }
    ]

    result = assess_retrieval(
        papers,
        min_relevance_score=0.05,
        strong_relevance_score=0.20
    )

    if result["status"] != "no_relevant_evidence":
        raise ValueError("FAIL: Low-similarity evidence was not rejected")

    if result["generation_allowed"]:
        raise ValueError("FAIL: Generation was allowed for irrelevant evidence")

    print("PASS: RAG service blocks generation without relevant evidence")


def test_topic_filter_flows_through_service():
    paper = get_test_paper()

    result = prepare_research_rag(
        paper["title"],
        topic=paper["research_topic"]
    )

    if not result["evidence"]:
        raise ValueError("FAIL: Topic-filtered RAG service returned no expected evidence")

    if any(item["research_topic"].casefold() != paper["research_topic"].casefold() for item in result["evidence"]):
        raise ValueError("FAIL: RAG service ignored topic filter")

    print("PASS: RAG service preserves research metadata filters")


def test_context_character_budget_flows_through_service():
    paper = get_test_paper()

    result = prepare_research_rag(
        paper["title"],
        max_context_chars=500
    )

    if len(result["context"]) > 500:
        raise ValueError("FAIL: RAG service exceeded context character budget")

    print("PASS: RAG service enforces bounded context size")


def test_empty_question_rejected():
    try:
        prepare_research_rag(
            "   "
        )

    except ValueError:
        print("PASS: RAG service rejects empty questions")
        return

    raise ValueError("FAIL: Empty RAG question was accepted")


def test_invalid_relevance_threshold_rejected():
    try:
        prepare_research_rag(
            "training",
            min_relevance_score=1.5
        )

    except ValueError:
        print("PASS: RAG service rejects invalid relevance threshold")
        return

    raise ValueError("FAIL: Invalid RAG relevance threshold was accepted")


def test_strong_threshold_cannot_be_below_minimum():
    try:
        prepare_research_rag(
            "training",
            min_relevance_score=0.30,
            strong_relevance_score=0.20
        )

    except ValueError:
        print("PASS: RAG service validates relevance threshold ordering")
        return

    raise ValueError("FAIL: Invalid relevance threshold ordering was accepted")


if __name__ == "__main__":
    test_rag_service_returns_complete_object()
    test_rag_service_preserves_question()

    test_exact_title_allows_evidence_generation()
    test_evidence_and_citations_are_aligned()
    test_context_contains_only_selected_evidence_ids()

    test_unknown_vocabulary_becomes_no_evidence_state()
    test_no_evidence_context_is_explicit()

    test_filter_relevant_papers_is_deterministic()
    test_high_relevance_assessment()
    test_limited_relevance_assessment()
    test_no_relevance_assessment()

    test_topic_filter_flows_through_service()
    test_context_character_budget_flows_through_service()

    test_empty_question_rejected()
    test_invalid_relevance_threshold_rejected()
    test_strong_threshold_cannot_be_below_minimum()