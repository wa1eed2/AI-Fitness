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

def inspect_data():
    print("\n-----------------------DATASET OVERVIEW-----------------------")
    print(df.head())
    print(df.columns.tolist())
    print(df.shape)
    print("Number of papers:", len(df))
    print("Number of columns:", len(df.columns))

    print("\n-------------------------DATA TYPES-------------------------")
    print(df.dtypes)

    print("\n-----------------------MISSING VALUES-----------------------")
    print(df.isna().sum())
    print("Total missing values:", df.isna().sum().sum())


    print("\n-------------------------DUPLICATES-------------------------")
    print("duplicate paper IDs:", df["paper_id"].duplicated().sum())
    print("duplicate doi IDs:", df["doi"].duplicated().sum())
    print("duplicate titles:", df["title"].duplicated().sum())

    print("\n-----------------------PUBLICATION YEAR-----------------------")
    print("Oldest publication year:", df["publication_year"].min())
    print("Newest publication year:", df["publication_year"].max())

    print("\n--------------------------CATEGORIES--------------------------")
    print(df["study_design"].unique())
    print(df["study_design"].value_counts())
    print(df["research_topic"].value_counts())
    print(df["subtopic"].value_counts())

def check_duplicates(column_name):
    duplicate_count = df[column_name].duplicated().sum()
    if duplicate_count > 0:
        raise ValueError(f"There are duplicate {column_name} values in the dataset.")
    else:
        print(f"PASS: No duplicate values in {column_name}")


def check_missing_values():
    missing_values = df.isna().sum().sum()

    if missing_values > 0:
        raise ValueError(f"There are {missing_values} missing values in the dataset.")
    else:
        print("PASS: No missing values in dataset")


def check_required_columns():
    missing_columns = []
    for column in required_columns:
        if column not in df.columns:
            missing_columns.append(column)

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    else:
        print("PASS: All required columns are present")


def check_publication_year():
    current_year = datetime.now().year
    invalid_years = (df["publication_year"] < 1900) | (df["publication_year"] > current_year)
    invalid_rows = df[invalid_years]

    if invalid_years.any():
        raise ValueError(f"There are invalid publication years:\n{invalid_rows[['paper_id', 'publication_year']]}")
    else:
        print("PASS: All publication years are valid")

print("\n-------------------------VALIDATION-------------------------")

check_required_columns()
check_missing_values()
check_duplicates("paper_id")
check_duplicates("doi")
check_duplicates("title")
check_publication_year()

inspect_data()