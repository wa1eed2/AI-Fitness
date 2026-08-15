import pandas as pd

csv_path = r"C:\Users\HP\PycharmProjects\AI-Fitness\data\research\research_papers.csv"

df = pd.read_csv(csv_path)


def search_papers(
    data,
    topic=None,
    subtopic=None,
    keyword=None,
    min_year=None,
    max_year=None,
    study_design=None
):
    result = data.copy()

    if min_year is not None and max_year is not None and min_year > max_year:
        raise ValueError("min_year cannot be greater than max_year")

    if topic:
        result = result[
            result["research_topic"].str.casefold() == topic.casefold()
        ]

    if subtopic:
        result = result[
            result["subtopic"].str.contains(
                subtopic,
                case=False,
                na=False,
                regex=False
            )
        ]

    if keyword:
        search_columns = [
            "paper_id",
            "title",
            "authors",
            "study_design",
            "research_topic",
            "subtopic",
            "results_summary"
        ]

        keyword_matches = pd.Series(False, index=result.index)

        for column in search_columns:
            keyword_matches = keyword_matches | result[column].str.contains(
                keyword,
                case=False,
                na=False,
                regex=False
            )

        result = result[keyword_matches]

    if min_year is not None:
        result = result[
            result["publication_year"] >= min_year
        ]

    if max_year is not None:
        result = result[
            result["publication_year"] <= max_year
        ]

    if study_design:
        result = result[
            result["study_design"].str.casefold()
            == study_design.casefold()
        ]

    return result


if __name__ == "__main__":
    result = search_papers(
        df,
        topic="training",
        subtopic="hypertrophy",
        keyword="volume",
        min_year=2020,
        max_year=2022
    )

    print(result)