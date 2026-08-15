import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


csv_path = r"C:\Users\HP\PycharmProjects\AI-Fitness\data\research\research_papers.csv"

df = pd.read_csv(csv_path)


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

def build_tfidf_index(data, columns):
    indexed_data = data.copy()

    indexed_data["search_text"] = indexed_data[columns].fillna("").astype(str).agg(" ".join, axis=1)

    vectorizer_model = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer_model.fit_transform(indexed_data["search_text"])

    return indexed_data, vectorizer_model, matrix

def validate_search_inputs(query,top_n,min_score,min_year,max_year):
    if not query.strip():
        raise ValueError("Query cannot be empty")

    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    if min_score < 0 or min_score > 1:
        raise ValueError("min_score must be between 0 and 1")

    if min_year is not None and max_year is not None and min_year > max_year:
        raise ValueError("min_year cannot be greater than max_year")

def apply_filters(result, topic=None, subtopic=None, min_year=None, max_year=None, study_design=None):
    if topic:
        result = result[result["research_topic"].str.casefold() == topic.casefold()]

    if subtopic:
        result = result[result["subtopic"].str.contains(subtopic, case=False, na=False, regex=False)]

    if min_year is not None:
        result = result[result["publication_year"] >= min_year]

    if max_year is not None:
        result = result[result["publication_year"] <= max_year]

    if study_design:
        result = result[result["study_design"].str.casefold() == study_design.casefold()]

    return result


def search_tfidf(data, vectorizer_model, matrix, query, top_n=5, min_score=0.0, topic=None, subtopic=None, min_year=None, max_year=None, study_design=None):
    validate_search_inputs(query,top_n,min_score,min_year,max_year)

    query_vector = vectorizer_model.transform([query])

    if query_vector.nnz == 0:
        raise ValueError("No query terms were found in the research vocabulary")

    similarity_scores = cosine_similarity(query_vector,matrix)
    result = data.copy()
    result["similarity_score"] = similarity_scores[0]

    result = apply_filters(
        result, topic=topic,
        subtopic=subtopic,
        min_year=min_year,
        max_year=max_year,
        study_design=study_design)

    if result.empty:
        return result[result_columns]

    result = result[result["similarity_score"] >= min_score]

    ranked_result = result.sort_values(by="similarity_score",ascending=False)
    return ranked_result[result_columns].head(top_n)

if __name__ == "__main__":
    indexed_df, vectorizer, tfidf_matrix = build_tfidf_index(df, text_columns)
    while True:
        query = input("Please enter a search query (or 'exit' to quit): ")

        if query.casefold() == "exit":
            break
        try:
            result = search_tfidf(indexed_df, vectorizer, tfidf_matrix, query, top_n=5)

            if result.empty:
                print("No matching research papers found.")
            else:
                print(result)
        except ValueError as error:
            print(error)
