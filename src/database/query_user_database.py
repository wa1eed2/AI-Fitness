import sqlite3

from src.database.setup_exercise_database import db_path
from src.database.validate_user_profile import validate_user_profile


def create_user():
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("INSERT INTO users DEFAULT VALUES")

    user_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return user_id


def create_user_profile(user_id, profile):
    validate_user_profile(profile)

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("""
        INSERT INTO user_profiles (
            user_id,
            age,
            sex,
            height_cm,
            weight_kg,
            fitness_level,
            primary_goal,
            training_days_per_week,
            session_duration_minutes,
            preferred_environment
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        profile.get("age"),
        profile.get("sex"),
        profile.get("height_cm"),
        profile.get("weight_kg"),
        profile.get("fitness_level"),
        profile.get("primary_goal"),
        profile.get("training_days_per_week"),
        profile.get("session_duration_minutes"),
        profile.get("preferred_environment")
    ))

    profile_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return profile_id

def get_user_profile(user_id):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
    profile = cursor.fetchone()

    connection.close()

    if profile is None:
        return None

    return dict(profile)

def update_user_profile(user_id, profile):
    validate_user_profile(profile)

    allowed_fields = [
        "age",
        "sex",
        "height_cm",
        "weight_kg",
        "fitness_level",
        "primary_goal",
        "training_days_per_week",
        "session_duration_minutes",
        "preferred_environment"
    ]

    updates = []
    parameters = []

    for field in allowed_fields:
        if field in profile:
            updates.append(f"{field} = ?")
            parameters.append(profile[field])

    if not updates:
        return False

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    query = f"""
        UPDATE user_profiles
        SET {", ".join(updates)}
        WHERE user_id = ?
    """

    parameters.append(user_id)

    cursor.execute(query, parameters)

    updated = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return updated


def delete_user(user_id):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute(
        "DELETE FROM users WHERE user_id = ?",
        (user_id,)
    )

    deleted = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return deleted