import sqlite3
from src.database.validate_user_limitation import validate_user_limitation
from src.database.setup_exercise_database import db_path
from src.database.validate_user_profile import validate_user_profile
from src.database.validate_user_equipment import validate_user_equipment
from src.database.validate_nutrition_target import validate_nutrition_target, validate_nutrition_target_update


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

def add_exercise_preference(user_id, exercise_id, preference):
    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.cursor()

        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("""
            INSERT INTO user_exercise_preferences (
                user_id,
                exercise_id,
                preference
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            exercise_id,
            preference
        ))

        preference_id = cursor.lastrowid

        connection.commit()

        return preference_id

    except:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_user_exercise_preferences(user_id):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM user_exercise_preferences
        WHERE user_id = ?
    """, (user_id,))

    preferences = cursor.fetchall()

    connection.close()

    return [dict(preference) for preference in preferences]


def remove_exercise_preference(user_id, exercise_id):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""DELETE FROM user_exercise_preferences WHERE user_id = ? AND exercise_id = ?""", (user_id, exercise_id))
    deleted = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return deleted

def add_user_limitation(user_id, body_area, limitation_type, notes=None):
    validate_user_limitation(body_area, limitation_type, notes)
    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("""
            INSERT INTO user_limitations (
                user_id,
                body_area,
                limitation_type,
                 notes)VALUES (?, ?, ?, ?)""",
                (user_id, body_area, limitation_type, notes ))

        limitation_id = cursor.lastrowid

        connection.commit()
        return limitation_id

    except:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_user_limitations(user_id):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""SELECT * FROM user_limitations WHERE user_id = ? """, (user_id,))

    limitations = cursor.fetchall()

    connection.close()

    return [dict(limitation) for limitation in limitations]


def remove_user_limitation(limitation_id):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM user_limitations
        WHERE limitation_id = ?
    """, (limitation_id,))

    deleted = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return deleted

def add_equipment_access(user_id, equipment, access_status):
    validate_user_equipment(equipment, access_status)
    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("""
            INSERT INTO user_equipment_access (
                user_id,
                equipment,
                access_status
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            equipment,
            access_status
        ))

        access_id = cursor.lastrowid

        connection.commit()

        return access_id

    except:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_user_equipment_access(user_id):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM user_equipment_access
        WHERE user_id = ?
    """, (user_id,))

    equipment_access = cursor.fetchall()

    connection.close()

    return [dict(item) for item in equipment_access]


def remove_equipment_access(user_id, equipment):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM user_equipment_access
        WHERE user_id = ? AND equipment = ?
    """, (
        user_id,
        equipment
    ))

    deleted = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return deleted


def create_user_nutrition_target(user_id, target):
    validate_nutrition_target(target)

    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("""
            INSERT INTO user_nutrition_targets (
                user_id,
                activity_level,
                nutrition_goal,
                bmr,
                tdee,
                calorie_target,
                protein_g,
                fat_g,
                carbs_g
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            target.get("activity_level"),
            target.get("nutrition_goal"),
            target.get("bmr"),
            target.get("tdee"),
            target.get("calorie_target"),
            target.get("protein_g"),
            target.get("fat_g"),
            target.get("carbs_g")
        ))

        nutrition_target_id = cursor.lastrowid

        connection.commit()

        return nutrition_target_id

    except:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_user_nutrition_target(user_id):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM user_nutrition_targets
        WHERE user_id = ?
    """, (user_id,))

    target = cursor.fetchone()

    connection.close()

    if target is None:
        return None

    return dict(target)

def update_user_nutrition_target(user_id, target):
    validate_nutrition_target_update(target)

    allowed_fields = [
        "activity_level",
        "nutrition_goal",
        "bmr",
        "tdee",
        "calorie_target",
        "protein_g",
        "fat_g",
        "carbs_g"
    ]

    updates = []
    parameters = []

    for field in allowed_fields:
        if field in target:
            updates.append(f"{field} = ?")
            parameters.append(target[field])

    if not updates:
        return False

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    query = f"""
            UPDATE user_nutrition_targets
            SET {", ".join(updates)}
            WHERE user_id = ?
        """

    parameters.append(user_id)

    cursor.execute(query, parameters)

    updated = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return updated


def delete_user_nutrition_target(user_id):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM user_nutrition_targets
        WHERE user_id = ?
    """, (user_id,))

    deleted = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return deleted