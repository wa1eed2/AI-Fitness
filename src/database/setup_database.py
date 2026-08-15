import sqlite3
import pandas as pd
from src.research.inspect_research_data import validate_research_data, required_columns, required_value_columns


db_path = r"C:\Users\HP\PycharmProjects\AI-Fitness\data\database\ai_fitness.db"
csv_path = r"C:\Users\HP\PycharmProjects\AI-Fitness\data\research\research_papers.csv"


research_columns = [
    "paper_id",
    "title",
    "authors",
    "publication_year",
    "journal",
    "study_design",
    "research_topic",
    "subtopic",
    "research_question",
    "population",
    "sample_size",
    "intervention",
    "comparison",
    "study_duration",
    "outcome_measures",
    "results_summary",
    "main_findings",
    "practical_interpretation",
    "limitations",
    "original_summary",
    "doi",
    "source_url",
    "license",
    "license_url"
]


def sync_research_database():
    data = pd.read_csv(csv_path)

    validate_research_data(data, required_columns, required_value_columns)

    data = data.astype(object).where(pd.notna(data), None)

    paper_rows = list(data[research_columns].itertuples(index=False, name=None))

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS research_papers (
        paper_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        authors TEXT NOT NULL,
        publication_year INTEGER NOT NULL,
        journal TEXT,
        study_design TEXT NOT NULL,
        research_topic TEXT NOT NULL,
        subtopic TEXT NOT NULL,
        research_question TEXT,
        population TEXT,
        sample_size TEXT,
        intervention TEXT,
        comparison TEXT,
        study_duration TEXT,
        outcome_measures TEXT,
        results_summary TEXT,
        main_findings TEXT,
        practical_interpretation TEXT,
        limitations TEXT,
        original_summary TEXT NOT NULL,
        doi TEXT,
        source_url TEXT NOT NULL,
        license TEXT NOT NULL,
        license_url TEXT
    )
    """)

    cursor.executemany("INSERT INTO research_papers (paper_id, title, authors, publication_year, journal, study_design, research_topic, subtopic, research_question, population, sample_size, intervention, comparison, study_duration, outcome_measures, results_summary, main_findings, practical_interpretation, limitations, original_summary, doi, source_url, license, license_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(paper_id) DO UPDATE SET title = excluded.title, authors = excluded.authors, publication_year = excluded.publication_year, journal = excluded.journal, study_design = excluded.study_design, research_topic = excluded.research_topic, subtopic = excluded.subtopic, research_question = excluded.research_question, population = excluded.population, sample_size = excluded.sample_size, intervention = excluded.intervention, comparison = excluded.comparison, study_duration = excluded.study_duration, outcome_measures = excluded.outcome_measures, results_summary = excluded.results_summary, main_findings = excluded.main_findings, practical_interpretation = excluded.practical_interpretation, limitations = excluded.limitations, original_summary = excluded.original_summary, doi = excluded.doi, source_url = excluded.source_url, license = excluded.license, license_url = excluded.license_url", paper_rows)

    connection.commit()
    connection.close()

    print(f"Research database synchronized successfully: {len(paper_rows)} papers")


if __name__ == "__main__":
    sync_research_database()