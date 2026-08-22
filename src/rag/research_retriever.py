import sqlite3
from pathlib import Path

import pandas as pd

from src.research.tfidf_search import (
    build_tfidf_index,
    search_tfidf
)


DB_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "database"
    / "ai_fitness.db"
)


SEARCH_TEXT_COLUMNS = [
    "title",
    "journal",
    "study_design",
    "research_topic",
    "subtopic",
    "research_question",
    "population",
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


def get_research_corpus():
    connection = sqlite3.connect(
        DB_PATH
    )

    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM research_papers
            ORDER BY paper_id ASC
            """
        ).fetchall()

        return [
            dict(
                row
            )
            for row in rows
        ]

    finally:
        connection.close()


def validate_retrieval_inputs(
    query,
    top_k,
    min_score,
    min_year,
    max_year
):
    if not isinstance(query, str):
        raise ValueError("Query must be a string")

    if not query.strip():
        raise ValueError("Query cannot be empty")

    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer")

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


def build_research_index(
    papers=None
):
    if papers is None:
        papers = get_research_corpus()

    if not papers:
        raise ValueError("Research corpus is empty")

    data = pd.DataFrame(
        papers
    )

    missing_columns = [
        column
        for column in SEARCH_TEXT_COLUMNS
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(f"Research corpus is missing required columns: {missing_columns}")

    return build_tfidf_index(
        data,
        SEARCH_TEXT_COLUMNS
    )


def convert_to_python_value(
    value
):
    if pd.isna(
        value
    ):
        return None

    if hasattr(
        value,
        "item"
    ):
        try:
            return value.item()
        except (ValueError, AttributeError):
            pass

    return value


def hydrate_ranked_result(
    indexed_data,
    ranked_row
):
    paper_id = ranked_row[
        "paper_id"
    ]

    matching_rows = indexed_data[
        indexed_data["paper_id"] == paper_id
    ]

    if matching_rows.empty:
        raise ValueError(f"Ranked research paper was not found in corpus: {paper_id}")

    paper = matching_rows.iloc[
        0
    ].to_dict()

    paper.pop(
        "search_text",
        None
    )

    hydrated = {
        key: convert_to_python_value(
            value
        )
        for key, value in paper.items()
    }

    hydrated[
        "similarity_score"
    ] = float(
        ranked_row[
            "similarity_score"
        ]
    )

    return hydrated


def retrieve_research(
    query,
    top_k=5,
    min_score=0.0,
    topic=None,
    subtopic=None,
    min_year=None,
    max_year=None,
    study_design=None
):
    validate_retrieval_inputs(
        query,
        top_k,
        min_score,
        min_year,
        max_year
    )

    papers = get_research_corpus()

    indexed_data, vectorizer_model, matrix = build_research_index(
        papers
    )

    ranked = search_tfidf(
        indexed_data,
        vectorizer_model,
        matrix,
        query.strip(),
        top_n=top_k,
        min_score=min_score,
        topic=topic,
        subtopic=subtopic,
        min_year=min_year,
        max_year=max_year,
        study_design=study_design
    )

    if ranked.empty:
        return []

    results = []

    for _, ranked_row in ranked.iterrows():
        results.append(
            hydrate_ranked_result(
                indexed_data,
                ranked_row
            )
        )

    return results