from src.rag.citation_builder import (
    build_citation,
    build_citations
)

from src.rag.context_builder import (
    build_research_context
)

from src.rag.research_retriever import (
    build_research_index,
    get_research_corpus,
    retrieve_research
)


def get_test_paper():
    papers = get_research_corpus()

    if not papers:
        raise ValueError("FAIL: Research database contains no papers")

    return papers[0]


def test_research_corpus_loads_from_database():
    papers = get_research_corpus()

    if not papers:
        raise ValueError("FAIL: Research corpus is empty")

    required_fields = {
        "paper_id",
        "title",
        "authors",
        "publication_year",
        "study_design",
        "research_topic",
        "subtopic",
        "main_findings",
        "practical_interpretation",
        "limitations",
        "original_summary",
        "source_url",
        "license"
    }

    if not required_fields.issubset(papers[0].keys()):
        raise ValueError("FAIL: Research corpus is missing evidence fields")

    print("PASS: RAG research corpus loads full evidence records from SQLite")


def test_research_index_builds_from_database_corpus():
    papers = get_research_corpus()

    indexed_data, vectorizer, matrix = build_research_index(
        papers
    )

    if len(indexed_data) != len(papers):
        raise ValueError("FAIL: TF-IDF index row count does not match database corpus")

    if "search_text" not in indexed_data.columns:
        raise ValueError("FAIL: TF-IDF index does not contain search_text")

    if matrix.shape[0] != len(papers):
        raise ValueError("FAIL: TF-IDF matrix row count is incorrect")

    if len(vectorizer.get_feature_names_out()) == 0:
        raise ValueError("FAIL: TF-IDF vocabulary is empty")

    print("PASS: RAG builds TF-IDF index from SQLite research corpus")


def test_exact_title_query_retrieves_expected_paper():
    paper = get_test_paper()

    results = retrieve_research(
        paper["title"],
        top_k=3
    )

    if not results:
        raise ValueError("FAIL: Exact-title retrieval returned no papers")

    if results[0]["paper_id"] != paper["paper_id"]:
        raise ValueError("FAIL: Exact-title query did not rank the matching paper first")

    print("PASS: Exact paper title ranks matching evidence first")


def test_retriever_returns_full_evidence_record():
    paper = get_test_paper()

    results = retrieve_research(
        paper["title"],
        top_k=1
    )

    result = results[0]

    required_fields = {
        "paper_id",
        "title",
        "authors",
        "publication_year",
        "study_design",
        "research_topic",
        "research_question",
        "population",
        "results_summary",
        "main_findings",
        "practical_interpretation",
        "limitations",
        "original_summary",
        "doi",
        "source_url",
        "license",
        "license_url",
        "similarity_score"
    }

    if not required_fields.issubset(result.keys()):
        raise ValueError("FAIL: Retriever did not hydrate the complete evidence record")

    print("PASS: Retriever hydrates ranked papers with full evidence metadata")


def test_similarity_scores_are_ranked_descending():
    paper = get_test_paper()

    results = retrieve_research(
        paper["title"],
        top_k=5
    )

    scores = [
        result["similarity_score"]
        for result in results
    ]

    if scores != sorted(scores, reverse=True):
        raise ValueError("FAIL: Research results are not ranked by similarity")

    if any(score < 0 or score > 1 for score in scores):
        raise ValueError("FAIL: Similarity score is outside expected range")

    print("PASS: Research retrieval returns descending similarity scores")


def test_top_k_limits_retrieval():
    paper = get_test_paper()

    results = retrieve_research(
        paper["title"],
        top_k=1
    )

    if len(results) != 1:
        raise ValueError("FAIL: top_k did not limit retrieval to one paper")

    print("PASS: Research retrieval respects top_k")


def test_topic_filter_is_applied():
    paper = get_test_paper()

    results = retrieve_research(
        paper["title"],
        top_k=5,
        topic=paper["research_topic"]
    )

    if not results:
        raise ValueError("FAIL: Topic-filtered retrieval returned no papers")

    if any(result["research_topic"].casefold() != paper["research_topic"].casefold() for result in results):
        raise ValueError("FAIL: Topic filter returned evidence from another topic")

    print("PASS: Research retrieval applies metadata filters")


def test_empty_query_rejected():
    try:
        retrieve_research(
            "   "
        )

    except ValueError:
        print("PASS: Research retrieval rejects empty query")
        return

    raise ValueError("FAIL: Empty research query was accepted")


def test_invalid_top_k_rejected():
    try:
        retrieve_research(
            "training",
            top_k=0
        )

    except ValueError:
        print("PASS: Research retrieval rejects invalid top_k")
        return

    raise ValueError("FAIL: Invalid top_k was accepted")


def test_invalid_min_score_rejected():
    try:
        retrieve_research(
            "training",
            min_score=1.5
        )

    except ValueError:
        print("PASS: Research retrieval rejects invalid minimum score")
        return

    raise ValueError("FAIL: Invalid minimum similarity score was accepted")


def test_unknown_vocabulary_query_rejected():
    try:
        retrieve_research(
            "zzzxqvplmnkjhgfd"
        )

    except ValueError:
        print("PASS: Research retrieval detects query with no indexed vocabulary")
        return

    raise ValueError("FAIL: Unknown-vocabulary query was accepted")


def test_context_contains_research_evidence():
    paper = get_test_paper()

    results = retrieve_research(
        paper["title"],
        top_k=1
    )

    question = "What does this research suggest?"

    context = build_research_context(
        question,
        results
    )

    if question not in context:
        raise ValueError("FAIL: Research context does not contain the question")

    if results[0]["paper_id"] not in context:
        raise ValueError("FAIL: Research context does not identify the source paper")

    if results[0]["title"] not in context:
        raise ValueError("FAIL: Research context does not contain the evidence title")

    if "Limitations:" not in context:
        raise ValueError("FAIL: Research context omitted study limitations")

    print("PASS: Context builder creates structured evidence context")


def test_context_respects_character_limit():
    paper = get_test_paper()

    results = retrieve_research(
        paper["title"],
        top_k=5
    )

    context = build_research_context(
        "Summarize the available evidence.",
        results,
        max_chars=500
    )

    if len(context) > 500:
        raise ValueError("FAIL: Research context exceeded max_chars")

    print("PASS: Research context respects character budget")


def test_citation_contains_source_and_license_metadata():
    paper = get_test_paper()

    results = retrieve_research(
        paper["title"],
        top_k=1
    )

    citation = build_citation(
        results[0]
    )

    if citation["paper_id"] != results[0]["paper_id"]:
        raise ValueError("FAIL: Citation contains incorrect paper ID")

    if citation["citation_id"] != f"[{results[0]['paper_id']}]":
        raise ValueError("FAIL: Citation marker is incorrect")

    if citation["source_url"] != results[0]["source_url"]:
        raise ValueError("FAIL: Citation lost source URL")

    if citation["license"] != results[0]["license"]:
        raise ValueError("FAIL: Citation lost license metadata")

    print("PASS: Citation builder preserves source and license metadata")


def test_citation_builder_deduplicates_papers():
    paper = get_test_paper()

    results = retrieve_research(
        paper["title"],
        top_k=1
    )

    citations = build_citations(
        [
            results[0],
            results[0]
        ]
    )

    if len(citations) != 1:
        raise ValueError("FAIL: Citation builder did not deduplicate paper IDs")

    print("PASS: Citation builder removes duplicate paper citations")


if __name__ == "__main__":
    test_research_corpus_loads_from_database()
    test_research_index_builds_from_database_corpus()

    test_exact_title_query_retrieves_expected_paper()
    test_retriever_returns_full_evidence_record()
    test_similarity_scores_are_ranked_descending()
    test_top_k_limits_retrieval()
    test_topic_filter_is_applied()

    test_empty_query_rejected()
    test_invalid_top_k_rejected()
    test_invalid_min_score_rejected()
    test_unknown_vocabulary_query_rejected()

    test_context_contains_research_evidence()
    test_context_respects_character_limit()

    test_citation_contains_source_and_license_metadata()
    test_citation_builder_deduplicates_papers()