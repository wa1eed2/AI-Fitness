import sqlite3
import pandas as pd

db_path = r"C:\Users\HP\PycharmProjects\AI-Fitness\data\database\ai_fitness.db"
csv_path = r"C:\Users\HP\PycharmProjects\AI-Fitness\data\exercises\exercises.csv"

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

required_exercise_values = [
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

def validate_exercise_data(data):
    missing_columns = [column for column in exercise_columns if column not in data.columns]

    if missing_columns:
        raise ValueError(f"Missing exercise columns: {missing_columns}")

    columns_with_missing = data[required_exercise_values].columns[data[required_exercise_values].isna().any()].tolist()
    if columns_with_missing:
        raise ValueError(f"Missing required exercise values in: {columns_with_missing}")

    blank_mask = data[required_exercise_values].astype(str).apply(lambda column: column.str.strip().eq(""))
    blank_required_values = blank_mask.any().any()

    if blank_required_values:
        raise ValueError("Blank values found in required exercise fields")

    valid_categories = [
        "Strength",
        "Cardio",
        "Mobility",
        "Stretching",
        "Balance",
        "Plyometric",
        "Yoga"
    ]

    invalid_categories = data[~data["category"].isin(valid_categories)]["category"].unique().tolist()

    if invalid_categories:
        raise ValueError(f"Invalid categories: {invalid_categories}")

    valid_exercise_types = [
        "Compound",
        "Isolation"
    ]

    strength_exercises = data["category"] == "Strength"

    invalid_exercise_types = data[
        strength_exercises & ~data["exercise_type"].isin(valid_exercise_types)
        ]["exercise_type"].unique().tolist()

    if invalid_exercise_types:
        raise ValueError(f"Invalid exercise types: {invalid_exercise_types}")

    valid_difficulty_levels = ["Beginner", "Intermediate", "Advanced"]
    invalid_difficulty_levels = data[~data["difficulty_level"].isin(valid_difficulty_levels)][
        "difficulty_level"].unique().tolist()

    if invalid_difficulty_levels:
        raise ValueError(f"Invalid difficulty levels: {invalid_difficulty_levels}")

    scores = pd.to_numeric(data["difficulty_score"], errors="coerce")
    invalid_scores = data[scores.isna() | ~scores.between(1, 5)]["difficulty_score"].unique().tolist()

    if invalid_scores:
        raise ValueError(f"Invalid difficulty scores: {invalid_scores}")

    valid_environments = ["Home", "Gym", "Both"]
    invalid_environments = data[~data["environment"].isin(valid_environments)]["environment"].unique().tolist()

    if invalid_environments:
        raise ValueError(f"Invalid environments: {invalid_environments}")

    duplicate_exercise_ids = data[data["exercise_id"].duplicated(keep=False)]["exercise_id"].unique().tolist()
    if duplicate_exercise_ids:
        raise ValueError(f"Duplicate exercise ids: {duplicate_exercise_ids}")

    invalid_exercise_ids = data[~data["exercise_id"].astype(str).str.fullmatch(r"E\d+")][
        "exercise_id"].unique().tolist()
    if invalid_exercise_ids:
        raise ValueError(f"Invalid exercise IDs: {invalid_exercise_ids}")


def setup_exercise_database():
    data = pd.read_csv(csv_path)
    validate_exercise_data(data)

    data = data.astype(object).where(pd.notna(data), None)
    exercise_rows = list(data[exercise_columns].itertuples(index=False, name=None))

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS exercises (
                    exercise_id TEXT PRIMARY KEY NOT NULL,   
                    name TEXT NOT NULL, 
                    category TEXT NOT NULL, 
                    exercise_type TEXT,
                    primary_muscle TEXT NOT NULL, 
                    secondary_muscles TEXT, 
                    stabilizer_muscles TEXT, 
                    joints_involved TEXT,
                    equipment TEXT, 
                    difficulty_level TEXT NOT NULL CHECK (difficulty_level IN ('Beginner', 'Intermediate', 'Advanced')), 
                    difficulty_score INTEGER NOT NULL CHECK (difficulty_score BETWEEN 1 AND 5), 
                    movement_pattern TEXT NOT NULL, body_position TEXT NOT NULL,
                    instructions TEXT NOT NULL,
                    precautions TEXT,
                    common_mistakes TEXT,
                    environment TEXT NOT NULL CHECK (environment IN ('Home', 'Gym', 'Both')))""")

    cursor.executemany("""INSERT INTO exercises (
                        exercise_id,
                        name,
                        category,
                        exercise_type,
                        primary_muscle,
                        secondary_muscles,
                        stabilizer_muscles,
                        joints_involved,
                        equipment,
                        difficulty_level,
                        difficulty_score,
                        movement_pattern,
                        body_position,
                        instructions,
                        precautions,
                        common_mistakes,
                        environment)
                        Values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(exercise_id) DO UPDATE SET
                        name = excluded.name,
                         category = excluded.category,
                         exercise_type = excluded.exercise_type,
                         primary_muscle = excluded.primary_muscle,
                         secondary_muscles = excluded.secondary_muscles,
                         stabilizer_muscles = excluded.stabilizer_muscles,
                         joints_involved = excluded.joints_involved,
                         equipment = excluded.equipment,
                         difficulty_level = excluded.difficulty_level,
                         difficulty_score = excluded.difficulty_score,
                         movement_pattern = excluded.movement_pattern,
                         body_position = excluded.body_position,
                         instructions = excluded.instructions,
                         precautions = excluded.precautions,
                         common_mistakes = excluded.common_mistakes,
                         environment = excluded.environment
                         """, exercise_rows)

    connection.commit()
    connection.close()

if __name__ == "__main__":
    setup_exercise_database()