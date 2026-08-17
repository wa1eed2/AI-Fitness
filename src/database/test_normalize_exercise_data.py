import tempfile
from pathlib import Path

import pandas as pd

from src.database.normalize_exercise_data import (
    load_raw_exercise_data,
    normalize_columns,
    add_missing_columns,
    add_exercise_ids,
    find_duplicate_exercises,
    remove_duplicate_exercises,
    find_missing_required_values,
    find_incomplete_exercises,
    get_next_exercise_number,
    import_processed_exercises,
)


exercise_columns = [
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


valid_exercise = {
    "exercise_id": "E001",
    "name": "Test Squat",
    "category": "Strength",
    "exercise_type": "Compound",
    "primary_muscle": "Quadriceps",
    "secondary_muscles": None,
    "stabilizer_muscles": None,
    "joints_involved": "Hip,Knee",
    "equipment": "Dumbbell",
    "difficulty_level": "Beginner",
    "difficulty_score": 2,
    "movement_pattern": "Squat",
    "body_position": "Standing",
    "instructions": "Perform the movement under control.",
    "precautions": None,
    "common_mistakes": None,
    "environment": "Both"
}


# TEST 1: load_raw_exercise_data()

with tempfile.TemporaryDirectory() as temp_directory:
    file_path = Path(temp_directory) / "raw.csv"

    pd.DataFrame([
        {
            "name": "Push-Up",
            "target": "Chest",
            "difficulty": "Beginner"
        }
    ]).to_csv(file_path, index=False)

    loaded_data = load_raw_exercise_data(file_path)

    if len(loaded_data) == 1 and loaded_data.iloc[0]["name"] == "Push-Up":
        print("PASS: Raw exercise CSV loaded correctly")
    else:
        raise ValueError("FAIL: Raw exercise CSV was not loaded correctly")


# TEST 2: normalize_columns()

raw_data = pd.DataFrame([
    {
        "name": "Test Exercise",
        "target": "Chest",
        "difficulty": "Beginner"
    }
])

normalized_data = normalize_columns(raw_data)

if (
    "primary_muscle" in normalized_data.columns
    and "difficulty_level" in normalized_data.columns
    and "target" not in normalized_data.columns
    and "difficulty" not in normalized_data.columns
):
    print("PASS: Raw columns normalized correctly")
else:
    raise ValueError("FAIL: Raw columns were not normalized correctly")


# TEST 3: add_missing_columns()

test_data = pd.DataFrame([
    {
        "name": "Test Exercise",
        "category": "Strength",
        "primary_muscle": "Chest",
        "difficulty_level": "Beginner"
    }
])

completed_data = add_missing_columns(test_data)

if completed_data.columns.tolist() == exercise_columns:
    print("PASS: Missing schema columns added correctly")
else:
    raise ValueError("FAIL: Exercise schema columns were not added correctly")


# TEST 4: add_exercise_ids()

test_data = pd.DataFrame([
    {"name": "Exercise A"},
    {"name": "Exercise B"}
])

data_with_ids = add_exercise_ids(test_data, 13)

if (
    data_with_ids.iloc[0]["exercise_id"] == "E013"
    and data_with_ids.iloc[1]["exercise_id"] == "E014"
):
    print("PASS: Exercise IDs generated correctly")
else:
    raise ValueError("FAIL: Exercise IDs were not generated correctly")


# TEST 5: find_duplicate_exercises()

with tempfile.TemporaryDirectory() as temp_directory:
    existing_path = Path(temp_directory) / "existing.csv"

    pd.DataFrame([
        {"name": "Push-Up"},
        {"name": "Pull-Up"}
    ]).to_csv(existing_path, index=False)

    incoming_data = pd.DataFrame([
        {"name": " push-up "},
        {"name": "Goblet Squat"}
    ])

    duplicates = find_duplicate_exercises(
        incoming_data,
        existing_path
    )

    if len(duplicates) == 1 and duplicates.iloc[0]["name"].strip().lower() == "push-up":
        print("PASS: Duplicate exercise detected correctly")
    else:
        raise ValueError("FAIL: Duplicate exercise was not detected correctly")


# TEST 6: remove_duplicate_exercises()

with tempfile.TemporaryDirectory() as temp_directory:
    existing_path = Path(temp_directory) / "existing.csv"

    pd.DataFrame([
        {"name": "Push-Up"},
        {"name": "Pull-Up"}
    ]).to_csv(existing_path, index=False)

    incoming_data = pd.DataFrame([
        {"name": "Push-Up"},
        {"name": "Goblet Squat"}
    ])

    filtered_data = remove_duplicate_exercises(
        incoming_data,
        existing_path
    )

    if len(filtered_data) == 1 and filtered_data.iloc[0]["name"] == "Goblet Squat":
        print("PASS: Duplicate exercises removed correctly")
    else:
        raise ValueError("FAIL: Duplicate exercises were not removed correctly")


# TEST 7: find_missing_required_values()

incomplete_exercise = valid_exercise.copy()
incomplete_exercise["exercise_type"] = None
incomplete_exercise["difficulty_score"] = None
incomplete_exercise["instructions"] = None

incomplete_data = pd.DataFrame([incomplete_exercise])

missing_fields = find_missing_required_values(incomplete_data)

expected_missing_fields = {
    "exercise_type",
    "difficulty_score",
    "instructions"
}

if expected_missing_fields.issubset(set(missing_fields)):
    print("PASS: Missing required fields detected correctly")
else:
    raise ValueError(
        f"FAIL: Missing required fields not detected correctly: {missing_fields}"
    )


# TEST 8: find_incomplete_exercises()

complete_exercise = valid_exercise.copy()
complete_exercise["exercise_id"] = "E100"

incomplete_exercise = valid_exercise.copy()
incomplete_exercise["exercise_id"] = "E101"
incomplete_exercise["difficulty_score"] = None

test_data = pd.DataFrame([
    complete_exercise,
    incomplete_exercise
])

incomplete_results = find_incomplete_exercises(test_data)

if (
    len(incomplete_results) == 1
    and incomplete_results.iloc[0]["exercise_id"] == "E101"
):
    print("PASS: Incomplete exercise detected correctly")
else:
    raise ValueError("FAIL: Incomplete exercise detection failed")


# TEST 9: get_next_exercise_number()

with tempfile.TemporaryDirectory() as temp_directory:
    existing_path = Path(temp_directory) / "existing.csv"

    pd.DataFrame([
        {"exercise_id": "E001"},
        {"exercise_id": "E005"},
        {"exercise_id": "E012"}
    ]).to_csv(existing_path, index=False)

    next_number = get_next_exercise_number(existing_path)

    if next_number == 13:
        print("PASS: Next exercise number calculated correctly")
    else:
        raise ValueError(
            f"FAIL: Expected next exercise number 13, got {next_number}"
        )


# TEST 10: import_processed_exercises()

with tempfile.TemporaryDirectory() as temp_directory:
    existing_path = Path(temp_directory) / "exercises.csv"
    processed_path = Path(temp_directory) / "processed.csv"

    existing_exercise = valid_exercise.copy()
    existing_exercise["exercise_id"] = "E001"
    existing_exercise["name"] = "Existing Exercise"

    processed_exercise = valid_exercise.copy()
    processed_exercise["exercise_id"] = "E002"
    processed_exercise["name"] = "New Exercise"

    pd.DataFrame([existing_exercise]).to_csv(
        existing_path,
        index=False
    )

    pd.DataFrame([processed_exercise]).to_csv(
        processed_path,
        index=False
    )

    import_processed_exercises(
        existing_path,
        processed_path
    )

    imported_data = pd.read_csv(existing_path)

    if (
        len(imported_data) == 2
        and "E001" in imported_data["exercise_id"].values
        and "E002" in imported_data["exercise_id"].values
    ):
        print("PASS: Processed exercise imported correctly")
    else:
        raise ValueError("FAIL: Processed exercise import failed")


print("\nPASS: All exercise normalization tests completed")