import pandas as pd
from src.database.setup_exercise_database import validate_exercise_data


def load_raw_exercise_data(file_path):
    data = pd.read_csv(file_path)
    return data


def normalize_columns(data):
    data = data.rename(
        columns={
            "target": "primary_muscle",
            "difficulty": "difficulty_level"
        }
    )

    return data

def add_missing_columns(data):
    required_columns = [
        "exercise_id",
        "name",
        "category",
        "exercise_type",
        "primary_muscle",
        "secondary_muscles",
        "stabilizer_muscles",
        "joints_involved",
        "equipment",
        "difficulty_level",
        "difficulty_score",
        "movement_pattern",
        "body_position",
        "instructions",
        "precautions",
        "common_mistakes",
        "environment"
    ]

    for column in required_columns:
        if column not in data.columns:
            data[column] = None

    return data[required_columns]

def add_exercise_ids(data, start_number):
    data = data.copy()

    data["exercise_id"] = [
        f"E{number:03d}"
        for number in range(start_number, start_number + len(data))
    ]

    return data

def find_duplicate_exercises(data, existing_file_path):
    existing_data = pd.read_csv(existing_file_path)
    existing_name = existing_data["name"].str.strip().str.lower()
    incoming_name = data["name"].str.strip().str.lower()

    duplicate_mask = incoming_name.isin(existing_name)
    return data[duplicate_mask]

def remove_duplicate_exercises(data, existing_file_path):
    existing_data = pd.read_csv(existing_file_path)

    existing_names = existing_data["name"].str.strip().str.lower()
    incoming_names = data["name"].str.strip().str.lower()

    duplicate_mask = incoming_names.isin(existing_names)

    return data[~duplicate_mask].copy()

def find_missing_required_values(data):
    required_columns = [
        "exercise_id",
        "name",
        "category",
        "primary_muscle",
        "difficulty_level",
        "difficulty_score",
        "movement_pattern",
        "body_position",
        "instructions",
        "environment"
    ]

    missing = data[required_columns].isna().any()
    missing_fields = missing[missing].index.tolist()

    strength_missing_type = data[
        (data["category"] == "Strength") &
        (data["exercise_type"].isna())
    ]

    if not strength_missing_type.empty:
        missing_fields.append("exercise_type")

    return missing_fields

def find_incomplete_exercises(data):
    required_columns = [
        "exercise_id",
        "name",
        "category",
        "primary_muscle",
        "difficulty_level",
        "difficulty_score",
        "movement_pattern",
        "body_position",
        "instructions",
        "environment"
    ]

    missing_required = data[required_columns].isna().any(axis=1)

    strength_missing_type = (
        (data["category"] == "Strength") &
        (data["exercise_type"].isna())
    )

    incomplete_mask = missing_required | strength_missing_type

    return data[incomplete_mask].copy()

def find_complete_exercises(data):
    incomplete_exercises = find_incomplete_exercises(data)

    complete_exercises = data[
        ~data["exercise_id"].isin(incomplete_exercises["exercise_id"])
    ].copy()

    if not complete_exercises.empty:
        validate_exercise_data(complete_exercises)
        print("PASS: Exercises ready for import passed validation")

        processed_path = "data/exercises/processed/exercises_ready_for_import.csv"

        complete_exercises.to_csv(processed_path, index=False)

        print(f"Saved {len(complete_exercises)} exercises ready for import")

    return complete_exercises

def get_next_exercise_number(existing_file_path):
    existing_data = pd.read_csv(existing_file_path)

    numbers = (existing_data["exercise_id"].str.replace("E", "", regex=False).astype(int))
    return numbers.max() + 1

def import_processed_exercises(existing_file_path, processed_file_path):
    existing_data = pd.read_csv(existing_file_path)
    processed_data = pd.read_csv(processed_file_path)

    combined_data = pd.concat(
        [existing_data, processed_data],
        ignore_index=True
    )

    combined_data["difficulty_score"] = combined_data["difficulty_score"].astype(int)

    validate_exercise_data(combined_data)

    combined_data.to_csv(existing_file_path, index=False)

if __name__ == "__main__":
    raw_path = "data/exercises/raw/sample_exercises.csv"
    existing_path = "data/exercises/exercises.csv"

    data = load_raw_exercise_data(raw_path)
    data = normalize_columns(data)
    data = add_missing_columns(data)

    duplicates = find_duplicate_exercises(data, existing_path)

    data = remove_duplicate_exercises(data, existing_path)
    next_number = get_next_exercise_number(existing_path)
    data = add_exercise_ids(data, next_number)
    missing_fields = find_missing_required_values(data)

    incomplete_exercises = find_incomplete_exercises(data)

    review_path = "data/exercises/review/exercises_needing_review.csv"

    incomplete_exercises.to_csv(review_path, index=False)

    complete_exercises = find_complete_exercises(data)
    processed_path = "data/exercises/processed/exercises_ready_for_import.csv"

    if not complete_exercises.empty:
        import_processed_exercises(existing_path, processed_path)
        print(f"Imported {len(complete_exercises)} exercises into main dataset")

    print("Exercises ready for import:")
    print(complete_exercises[["exercise_id", "name"]])

    print(f"Saved {len(incomplete_exercises)} exercises for review")

    print("Exercises needing review:")
    print(incomplete_exercises[["exercise_id", "name"]])

    print("Missing required fields:", missing_fields)

    print(data)
    print("Rows:", len(data))
    print("Columns:", data.columns.tolist())

    print("Duplicate exercises:")
    print(duplicates[["name"]])

    print("Rows remaining:", len(data))
