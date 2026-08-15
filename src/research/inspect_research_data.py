import pandas as pd
from datetime import datetime

csv_path = r"C:\Users\HP\PycharmProjects\AI-Fitness\data\research\research_papers.csv"

df = pd.read_csv(csv_path)

required_columns = [
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

required_value_columns = [
    "paper_id",
    "title",
    "authors",
    "publication_year",
    "study_design",
    "research_topic",
    "subtopic",
    "original_summary",
    "source_url",
    "license"
]

def inspect_data(data):
    print("\n-----------------------DATASET OVERVIEW-----------------------")
    print(data.head())
    print(data.columns.tolist())
    print(data.shape)
    print("Number of papers:", len(data))
    print("Number of columns:", len(data.columns))

    print("\n-------------------------DATA TYPES-------------------------")
    print(data.dtypes)

    print("\n-----------------------MISSING VALUES-----------------------")
    print(data.isna().sum())
    print("Total missing values:", data.isna().sum().sum())

    print("\n-------------------------DUPLICATES-------------------------")
    print("duplicate paper IDs:", count_duplicates(data, "paper_id"))
    print("duplicate doi IDs:", count_duplicates(data, "doi", ignore_missing=True, normalize_text=True))
    print("duplicate titles:", count_duplicates(data, "title", normalize_text=True))

    print("\n-----------------------PUBLICATION YEAR-----------------------")
    print("Oldest publication year:", data["publication_year"].min())
    print("Newest publication year:", data["publication_year"].max())

    print("\n--------------------------CATEGORIES--------------------------")
    print(data["study_design"].unique())
    print(data["study_design"].value_counts())
    print(data["research_topic"].value_counts())
    print(data["subtopic"].value_counts())

def count_duplicates(data, column_name, ignore_missing=False, normalize_text=False):
    values = data[column_name]

    if ignore_missing:
        values = values.dropna()
        values = values[values.astype(str).str.strip() != ""]

    if normalize_text:
        values = values.astype(str).str.strip().str.casefold()

    return values.duplicated().sum()

def check_duplicates(data, column_name, ignore_missing=False, normalize_text=False):
    duplicate_count = count_duplicates(data, column_name, ignore_missing, normalize_text)

    if duplicate_count > 0:
        raise ValueError(f"There are duplicate {column_name} values in the dataset.")
    else:
        print(f"PASS: No duplicate values in {column_name}")


def check_missing_values(data, required_values):
    invalid_count = 0

    for column in required_values:
        values = data[column]

        invalid_values = values.isna() | values.fillna("").astype(str).str.strip().eq("")
        invalid_count += invalid_values.sum()

    if invalid_count > 0:
        raise ValueError(f"There are {invalid_count} missing or blank values in required fields.")
    else:
        print("PASS: No missing or blank values in required fields.")


def check_required_columns(data, required):
    missing_columns = []

    for column in required:
        if column not in data.columns:
            missing_columns.append(column)

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    else:
        print("PASS: All required columns are present")

def check_paper_id_format(data):
    valid_ids = data["paper_id"].astype(str).str.strip().str.fullmatch(r"P\d+")
    invalid_rows = data[~valid_ids]

    if not invalid_rows.empty:
        raise ValueError(f"There are invalid paper IDs:\n{invalid_rows[['paper_id']]}")
    else:
        print("PASS: All paper IDs have a valid format")

def check_url_format(data, column_name, ignore_missing=False):
    values = data[column_name]

    if ignore_missing:
        values = values.dropna()
        values = values[values.astype(str).str.strip() != ""]

    valid_urls = values.astype(str).str.strip().str.startswith(("http://", "https://"))
    invalid_values = values[~valid_urls]

    if not invalid_values.empty:
        raise ValueError(f"There are invalid URLs in {column_name}:\n{invalid_values}")
    else:
        print(f"PASS: All URLs in {column_name} have a valid format")

def check_doi_format(data):
    values = data["doi"].dropna()
    values = values[values.astype(str).str.strip() != ""]
    values = values.astype(str).str.strip()

    valid_dois = values.str.fullmatch(r"10\.\d{4,9}/\S+")
    invalid_values = values[~valid_dois]

    if not invalid_values.empty:
        raise ValueError(f"There are invalid DOI values:\n{invalid_values}")
    else:
        print("PASS: All DOI values have a valid format")

def check_publication_year(data):
    current_year = datetime.now().year
    years = pd.to_numeric(data["publication_year"], errors="coerce")

    invalid_years = years.isna() | (years < 1900) | (years > current_year)
    invalid_rows = data[invalid_years]

    if invalid_years.any():
        raise ValueError(f"There are invalid publication years:\n{invalid_rows[['paper_id', 'publication_year']]}")
    else:
        print("PASS: All publication years are valid")

def validate_research_data(data, required, required_values):
    print("\n-------------------------VALIDATION-------------------------")

    check_required_columns(data, required)
    check_missing_values(data, required_values)
    check_paper_id_format(data)
    check_duplicates(data, "paper_id")
    check_duplicates(data, "doi", ignore_missing=True, normalize_text=True)
    check_doi_format(data)
    check_duplicates(data, "title", normalize_text=True)
    check_publication_year(data)
    check_url_format(data, "source_url")
    check_url_format(data, "license_url", ignore_missing=True)

if __name__ == "__main__":
    validate_research_data(df, required_columns, required_value_columns)
    inspect_data(df)
