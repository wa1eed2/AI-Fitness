from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


DEFAULT_CSV_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "research"
    / "research_papers.csv"
)


text_columns = [
    "title",
    "journal",
    "research_topic",
    "subtopic",
    "research_question",
    "intervention",
    "comparison",
    "study_duration",
    "outcome_measures",
    "results_summary",
    "main_findings",
    "practical_interpretation",
    "limitations",
    "original_summary"
]


result_columns = [
    "paper_id",
    "title",
    "authors",
    "publication_year",
    "study_design",
    "research_topic",
    "subtopic",
    "main_findings",
    "doi",
    "source_url",
    "similarity_score"
]


def load_research_csv(
    csv_path=DEFAULT_CSV_PATH
):
    path = Path(
        csv_path
    )

    if not path.exists():
        raise ValueError(f"Research CSV does not exist: {path}")

    return pd.read_csv(
        path
    )


def validate_index_inputs(
    data,
    columns
):
    if not isinstance(data, pd.DataFrame):
        raise ValueError("data must be a pandas DataFrame")

    if data.empty:
        raise ValueError("Research data cannot be empty")

    if not isinstance(columns, list) or not columns:
        raise ValueError("columns must be a non-empty list")

    missing_columns = [
        column
        for column in columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(f"Research data is missing required columns: {missing_columns}")


def build_tfidf_index(
    data,
    columns
):
    validate_index_inputs(
        data,
        columns
    )

    indexed_data = data.copy()

    indexed_data[
        "search_text"
    ] = (
        indexed_data[
            columns
        ]
        .fillna("")
        .astype(str)
        .agg(
            " ".join,
            axis=1
        )
    )

    vectorizer_model = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2)
    )

    matrix = vectorizer_model.fit_transform(
        indexed_data[
            "search_text"
        ]
    )

    return (
        indexed_data,
        vectorizer_model,
        matrix
    )


def validate_search_inputs(
    query,
    top_n,
    min_score,
    min_year,
    max_year
):
    if not isinstance(query, str):
        raise ValueError("Query must be a string")

    if not query.strip():
        raise ValueError("Query cannot be empty")

    if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n < 1:
        raise ValueError("top_n must be a positive integer")

    if not isinstance(min_score, (int, float)) or isinstance(min_score, bool):
        raise ValueError("min_score must be numeric")

    if min_score < 0 or min_score > 1:
        raise ValueError("min_score must be between 0 and 1")

    if min_year is not None and (not isinstance(min_year, int) or isinstance(min_year, bool)):
        raise ValueError("min_year must be an integer")

    if max_year is not None and (not isinstance(max_year, int) or isinstance(max_year, bool)):
        raise ValueError("max_year must be an integer")

    if min_year is not None and max_year is not None and min_year > max_year:
        raise ValueError("min_year cannot be greater than max_year")


def apply_filters(
    result,
    topic=None,
    subtopic=None,
    min_year=None,
    max_year=None,
    study_design=None
):
    filtered = result.copy()

    if topic:
        filtered = filtered[
            filtered[
                "research_topic"
            ].str.casefold()
            == topic.casefold()
        ]

    if subtopic:
        filtered = filtered[
            filtered[
                "subtopic"
            ].str.contains(
                subtopic,
                case=False,
                na=False,
                regex=False
            )
        ]

    if min_year is not None:
        filtered = filtered[
            filtered[
                "publication_year"
            ] >= min_year
        ]

    if max_year is not None:
        filtered = filtered[
            filtered[
                "publication_year"
            ] <= max_year
        ]

    if study_design:
        filtered = filtered[
            filtered[
                "study_design"
            ].str.casefold()
            == study_design.casefold()
        ]

    return filtered


def search_tfidf(
    data,
    vectorizer_model,
    matrix,
    query,
    top_n=5,
    min_score=0.0,
    topic=None,
    subtopic=None,
    min_year=None,
    max_year=None,
    study_design=None
):
    validate_search_inputs(
        query,
        top_n,
        min_score,
        min_year,
        max_year
    )

    query_vector = vectorizer_model.transform(
        [
            query.strip()
        ]
    )

    if query_vector.nnz == 0:
        raise ValueError("No query terms were found in the research vocabulary")

    similarity_scores = cosine_similarity(
        query_vector,
        matrix
    )

    result = data.copy()

    result[
        "similarity_score"
    ] = similarity_scores[
        0
    ]

    result = apply_filters(
        result,
        topic=topic,
        subtopic=subtopic,
        min_year=min_year,
        max_year=max_year,
        study_design=study_design
    )

    if result.empty:
        return result[
            result_columns
        ]

    result = result[
        result[
            "similarity_score"
        ] >= min_score
    ]

    ranked_result = result.sort_values(
        by="similarity_score",
        ascending=False
    )

    return ranked_result[
        result_columns
    ].head(
        top_n
    )


def main():
    data = load_research_csv()

    indexed_data, vectorizer, tfidf_matrix = build_tfidf_index(
        data,
        text_columns
    )

    while True:
        query = input(
            "Please enter a search query (or 'exit' to quit): "
        )

        if query.casefold() == "exit":
            break

        try:
            result = search_tfidf(
                indexed_data,
                vectorizer,
                tfidf_matrix,
                query,
                top_n=5
            )

            if result.empty:
                print("No matching research papers found.")
            else:
                print(result)

        except ValueError as error:
            print(error)


if __name__ == "__main__":
    main()