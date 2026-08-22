import src.research.tfidf_search as tfidf_search

from src.research.tfidf_search import (
    build_tfidf_index,
    load_research_csv,
    search_tfidf,
    text_columns
)


def test_import_has_no_loaded_dataframe():
    if hasattr(tfidf_search, "df"):
        raise ValueError("FAIL: TF-IDF module still loads a global DataFrame during import")

    print("PASS: TF-IDF module has no import-time research DataFrame")


def test_research_csv_loads_explicitly():
    data = load_research_csv()

    if data.empty:
        raise ValueError("FAIL: Explicit research CSV loading returned no data")

    if "paper_id" not in data.columns:
        raise ValueError("FAIL: Loaded research CSV does not contain paper_id")

    print("PASS: Research CSV loads explicitly when requested")


def test_tfidf_index_builds():
    data = load_research_csv()

    indexed_data, vectorizer, matrix = build_tfidf_index(
        data,
        text_columns
    )

    if len(indexed_data) != len(data):
        raise ValueError("FAIL: TF-IDF indexed row count is incorrect")

    if matrix.shape[0] != len(data):
        raise ValueError("FAIL: TF-IDF matrix row count is incorrect")

    if not vectorizer.get_feature_names_out().size:
        raise ValueError("FAIL: TF-IDF vocabulary is empty")

    print("PASS: TF-IDF index builds as reusable library functionality")


def test_exact_title_search_still_works():
    data = load_research_csv()

    indexed_data, vectorizer, matrix = build_tfidf_index(
        data,
        text_columns
    )

    expected = data.iloc[
        0
    ]

    result = search_tfidf(
        indexed_data,
        vectorizer,
        matrix,
        expected["title"],
        top_n=1
    )

    if result.empty:
        raise ValueError("FAIL: Exact-title TF-IDF search returned no results")

    if result.iloc[0]["paper_id"] != expected["paper_id"]:
        raise ValueError("FAIL: Exact-title TF-IDF search did not rank expected paper first")

    print("PASS: Existing TF-IDF ranking behavior remains functional")


def test_unknown_vocabulary_still_rejected():
    data = load_research_csv()

    indexed_data, vectorizer, matrix = build_tfidf_index(
        data,
        text_columns
    )

    try:
        search_tfidf(
            indexed_data,
            vectorizer,
            matrix,
            "zzzxqvplmnkjhgfd"
        )

    except ValueError:
        print("PASS: TF-IDF library still detects unknown query vocabulary")
        return

    raise ValueError("FAIL: Unknown TF-IDF vocabulary was accepted")


if __name__ == "__main__":
    test_import_has_no_loaded_dataframe()
    test_research_csv_loads_explicitly()
    test_tfidf_index_builds()
    test_exact_title_search_still_works()
    test_unknown_vocabulary_still_rejected()