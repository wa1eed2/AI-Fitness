import sqlite3
from src.database.validate_user_limitation import validate_user_limitation
from src.database.setup_exercise_database import db_path
from src.database.validate_user_profile import validate_user_profile
from src.database.validate_user_equipment import validate_user_equipment
from src.database.validate_nutrition_target import validate_nutrition_target, validate_nutrition_target_update
from src.database.validate_food_allergy import validate_food_allergy
from src.database.validate_food import validate_food

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

def add_food_allergy(user_id, allergen, notes=None):
    validate_food_allergy(allergen, notes)

    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("""
            INSERT INTO user_food_allergies (
                user_id,
                allergen,
                notes
            )
            VALUES (?, ?, ?)""", (user_id, allergen, notes))

        allergy_id = cursor.lastrowid

        connection.commit()

        return allergy_id

    except:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_user_food_allergies(user_id):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM user_food_allergies
        WHERE user_id = ?
    """, (user_id,))

    allergies = cursor.fetchall()

    connection.close()

    return [dict(allergy) for allergy in allergies]


def remove_food_allergy(user_id, allergen):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM user_food_allergies
        WHERE user_id = ? AND allergen = ?
    """, (
        user_id,
        allergen
    ))

    deleted = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return deleted


def create_food(
    name,
    serving_size_g,
    calories,
    protein_g,
    carbs_g,
    fat_g
):
    validate_food(
        name,
        serving_size_g,
        calories,
        protein_g,
        carbs_g,
        fat_g
    )

    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO foods (
                name,
                serving_size_g,
                calories,
                protein_g,
                carbs_g,
                fat_g
            )
            VALUES (?, ?, ?, ?, ?, ?)""", (name, serving_size_g, calories, protein_g, carbs_g, fat_g))

        food_id = cursor.lastrowid

        connection.commit()

        return food_id

    except:
        connection.rollback()
        raise

    finally:
        connection.close()

def add_food_allergen(food_id, allergen):
    validate_food_allergy(allergen)

    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("""
            INSERT INTO food_allergens (
                food_id,
                allergen
            )
            VALUES (?, ?)
        """, (
            food_id,
            allergen
        ))

        food_allergen_id = cursor.lastrowid

        connection.commit()

        return food_allergen_id

    except:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_safe_foods_for_user(user_id):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM foods
        WHERE food_id NOT IN (
            SELECT fa.food_id
            FROM food_allergens fa
            JOIN user_food_allergies ufa
                ON fa.allergen = ufa.allergen
            WHERE ufa.user_id = ?
        )
    """, (user_id,))

    foods = cursor.fetchall()

    connection.close()

    return [dict(food) for food in foods]

def get_food_by_id(food_id):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""SELECT * FROM foods WHERE food_id = ?""", (food_id,))
    food = cursor.fetchone()
    connection.close()

    if food is None:
        return None

    return dict(food)

def search_foods(
    name=None,
    min_protein_g=None,
    max_calories=None
):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    query = """
        SELECT *
        FROM foods
        WHERE 1 = 1
    """

    parameters = []

    if name:
        query += " AND name LIKE ?"
        parameters.append(f"%{name}%")

    if min_protein_g is not None:
        query += " AND protein_g >= ?"
        parameters.append(min_protein_g)

    if max_calories is not None:
        query += " AND calories <= ?"
        parameters.append(max_calories)

    cursor.execute(query, parameters)

    foods = cursor.fetchall()
    connection.close()

    return [dict(food) for food in foods]

def create_meal(user_id, name, meal_type):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Meal name must be a non-empty string")

    valid_meal_types = {
        "Breakfast",
        "Lunch",
        "Dinner",
        "Snack"
    }

    if meal_type not in valid_meal_types:
        raise ValueError("Invalid meal type")

    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("""
            INSERT INTO meals (
                user_id,
                name,
                meal_type
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            name,
            meal_type
        ))

        connection.commit()
        return cursor.lastrowid

    except:
        connection.rollback()
        raise

    finally:
        connection.close()


def add_food_to_meal(meal_id, food_id, servings):
    if not isinstance(servings, (int, float)):
        raise ValueError("Servings must be a number")

    if servings <= 0:
        raise ValueError("Servings must be greater than 0")

    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("""
            INSERT INTO meal_foods (
                meal_id,
                food_id,
                servings
            )
            VALUES (?, ?, ?)
        """, (
            meal_id,
            food_id,
            servings
        ))

        connection.commit()
        return cursor.lastrowid

    except:
        connection.rollback()
        raise

    finally:
        connection.close()

def get_meal_foods(meal_id):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            mf.meal_food_id,
            mf.meal_id,
            mf.food_id,
            mf.servings,
            f.name,
            f.serving_size_g,
            f.calories,
            f.protein_g,
            f.carbs_g,
            f.fat_g
        FROM meal_foods mf
        JOIN foods f
            ON mf.food_id = f.food_id
        WHERE mf.meal_id = ?
    """, (meal_id,))

    foods = cursor.fetchall()
    connection.close()

    return [dict(food) for food in foods]

def get_meal_nutrition(meal_id):
    foods = get_meal_foods(meal_id)

    totals = {
        "calories": 0,
        "protein_g": 0,
        "carbs_g": 0,
        "fat_g": 0
    }

    for food in foods:
        servings = food["servings"]

        totals["calories"] += food["calories"] * servings
        totals["protein_g"] += food["protein_g"] * servings
        totals["carbs_g"] += food["carbs_g"] * servings
        totals["fat_g"] += food["fat_g"] * servings

    return totals


def get_meal_by_id(meal_id):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM meals
        WHERE meal_id = ?
    """, (meal_id,))

    meal = cursor.fetchone()
    connection.close()

    if meal is None:
        return None

    meal = dict(meal)

    meal["foods"] = get_meal_foods(meal_id)
    meal["nutrition"] = get_meal_nutrition(meal_id)

    return meal

def get_user_meals(user_id):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM meals
        WHERE user_id = ?
        ORDER BY meal_id
    """, (user_id,))

    meals = cursor.fetchall()
    connection.close()

    return [dict(meal) for meal in meals]

def remove_food_from_meal(meal_id, food_id):
    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("""
            DELETE FROM meal_foods
            WHERE meal_id = ?
            AND food_id = ?
        """, (
            meal_id,
            food_id
        ))

        connection.commit()

        return cursor.rowcount > 0

    except:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_meal_food_servings(meal_id, food_id, servings):
    if not isinstance(servings, (int, float)):
        raise ValueError("Servings must be a number")

    if servings <= 0:
        raise ValueError("Servings must be greater than 0")

    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("""
            UPDATE meal_foods
            SET servings = ?
            WHERE meal_id = ?
            AND food_id = ?
        """, (
            servings,
            meal_id,
            food_id
        ))

        connection.commit()

        return cursor.rowcount > 0

    except:
        connection.rollback()
        raise

    finally:
        connection.close()

def delete_meal(meal_id):
    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("""
            DELETE FROM meals
            WHERE meal_id = ?
        """, (meal_id,))

        connection.commit()

        return cursor.rowcount > 0

    except:
        connection.rollback()
        raise

    finally:
        connection.close()

def update_meal(meal_id, updates):
    if not isinstance(updates, dict) or not updates:
        raise ValueError("Updates must be a non-empty dictionary")

    allowed_fields = {
        "name",
        "meal_type"
    }

    invalid_fields = set(updates) - allowed_fields

    if invalid_fields:
        raise ValueError(
            f"Invalid meal fields: {invalid_fields}"
        )

    if "name" in updates:
        name = updates["name"]

        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                "Meal name must be a non-empty string"
            )

    if "meal_type" in updates:
        valid_meal_types = {
            "Breakfast",
            "Lunch",
            "Dinner",
            "Snack"
        }

        if updates["meal_type"] not in valid_meal_types:
            raise ValueError("Invalid meal type")

    set_parts = []
    parameters = []

    for field, value in updates.items():
        set_parts.append(f"{field} = ?")
        parameters.append(value)

    parameters.append(meal_id)

    query = f"""
        UPDATE meals
        SET {", ".join(set_parts)}
        WHERE meal_id = ?
    """

    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute(
            query,
            parameters
        )

        connection.commit()

        return cursor.rowcount > 0

    except:
        connection.rollback()
        raise

    finally:
        connection.close()