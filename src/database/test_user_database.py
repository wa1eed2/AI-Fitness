import sqlite3

from src.database.setup_exercise_database import db_path
from src.database.setup_user_database import setup_user_database

from src.database.query_user_database import (
    create_user,
    create_user_profile,
    get_user_profile,
    update_user_profile,
    delete_user,
    add_exercise_preference,
    get_user_exercise_preferences,
    remove_exercise_preference,
    add_user_limitation,
    get_user_limitations,
    remove_user_limitation,
    add_equipment_access,
    get_user_equipment_access,
    remove_equipment_access,
    create_user_nutrition_target,
    get_user_nutrition_target,
    update_user_nutrition_target,
    delete_user_nutrition_target,
    add_food_allergy,
    get_user_food_allergies,
    remove_food_allergy,
    create_food,
    add_food_allergen,
    get_safe_foods_for_user,
    get_food_by_id,
    search_foods,
    create_meal,
    add_food_to_meal,
    get_meal_foods,
    get_meal_nutrition,
    get_meal_by_id,
    get_user_meals,
    remove_food_from_meal,
    update_meal_food_servings,
    delete_meal,
    update_meal
)


# ============================================================
# SETUP / HELPERS
# ============================================================

setup_user_database()


def get_connection():
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def check(condition, pass_message, fail_message):
    if condition:
        print(f"PASS: {pass_message}")
    else:
        raise ValueError(f"FAIL: {fail_message}")


def cleanup_foods_by_name(names):
    connection = get_connection()
    cursor = connection.cursor()

    placeholders = ", ".join(["?"] * len(names))

    cursor.execute(
        f"DELETE FROM foods WHERE name IN ({placeholders})",
        names
    )

    connection.commit()
    connection.close()


VALID_PROFILE = {
    "age": 25,
    "sex": "Male",
    "height_cm": 175.0,
    "weight_kg": 75.0,
    "fitness_level": "Beginner",
    "primary_goal": "Muscle Gain",
    "training_days_per_week": 4,
    "session_duration_minutes": 60,
    "preferred_environment": "Gym"
}


VALID_NUTRITION_TARGET = {
    "activity_level": "Moderately Active",
    "nutrition_goal": "Muscle Gain",
    "bmr": 1723.75,
    "tdee": 2671.81,
    "calorie_target": 2938.99,
    "protein_g": 150.0,
    "fat_g": 81.64,
    "carbs_g": 400.0
}


# ============================================================
# USER TABLE / PROFILE TESTS
# ============================================================

def test_user_profile_schema():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("PRAGMA table_info(user_profiles)")
    profile_columns = cursor.fetchall()

    for column in profile_columns:
        print(column)

    cursor.execute("PRAGMA foreign_key_list(user_profiles)")
    foreign_keys = cursor.fetchall()

    print("Foreign keys:", foreign_keys)

    check(
        len(profile_columns) > 0,
        "User profiles table exists",
        "User profiles table does not exist"
    )

    check(
        len(foreign_keys) > 0,
        "User profiles foreign key exists",
        "User profiles foreign key does not exist"
    )

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'users'
    """)

    users_table = cursor.fetchone()

    check(
        users_table is not None,
        "Users table exists",
        "Users table does not exist"
    )

    connection.close()


def test_user_profile_relationship():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("INSERT INTO users DEFAULT VALUES")
    test_user_id = cursor.lastrowid

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
        test_user_id,
        25,
        "Male",
        175.0,
        75.0,
        "Beginner",
        "Muscle Gain",
        4,
        60,
        "Gym"
    ))

    connection.commit()

    cursor.execute(
        "SELECT * FROM user_profiles WHERE user_id = ?",
        (test_user_id,)
    )

    profile = cursor.fetchone()

    check(
        profile is not None,
        "User profile linked to user successfully",
        "User profile was not linked to user"
    )

    try:
        cursor.execute(
            "INSERT INTO user_profiles (user_id) VALUES (?)",
            (test_user_id,)
        )

        connection.commit()

    except sqlite3.IntegrityError:
        connection.rollback()
        print("PASS: Duplicate user profile rejected")

    else:
        connection.close()
        raise ValueError(
            "FAIL: User was allowed to have multiple profiles"
        )

    cursor.execute(
        "DELETE FROM users WHERE user_id = ?",
        (test_user_id,)
    )

    connection.commit()

    cursor.execute(
        "SELECT * FROM user_profiles WHERE user_id = ?",
        (test_user_id,)
    )

    deleted_profile = cursor.fetchone()

    check(
        deleted_profile is None,
        "User profile deleted automatically with user",
        "User profile was not deleted with user"
    )

    connection.close()


def test_create_user():
    test_user_id = create_user()

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (test_user_id,)
        )

        user = cursor.fetchone()
        connection.close()

        check(
            user is not None,
            "create_user created a user successfully",
            "create_user did not create a user"
        )

    finally:
        delete_user(test_user_id)


def test_create_user_profile_valid():
    test_user_id = create_user()

    try:
        profile_id = create_user_profile(
            test_user_id,
            VALID_PROFILE.copy()
        )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM user_profiles WHERE profile_id = ?",
            (profile_id,)
        )

        profile = cursor.fetchone()
        connection.close()

        check(
            profile is not None,
            "create_user_profile created profile successfully",
            "create_user_profile did not create profile"
        )

    finally:
        delete_user(test_user_id)


def test_create_user_profile_invalid():
    test_user_id = create_user()

    invalid_profile = {
        "age": 0,
        "fitness_level": "Beginner"
    }

    try:
        try:
            create_user_profile(
                test_user_id,
                invalid_profile
            )

        except ValueError:
            print(
                "PASS: create_user_profile rejected invalid profile"
            )

        else:
            raise ValueError(
                "FAIL: create_user_profile accepted invalid profile"
            )

    finally:
        delete_user(test_user_id)


def test_get_user_profile():
    test_user_id = create_user()

    try:
        create_user_profile(
            test_user_id,
            VALID_PROFILE.copy()
        )

        profile = get_user_profile(test_user_id)

        check(
            profile is not None
            and profile["user_id"] == test_user_id
            and profile["age"] == 25
            and profile["primary_goal"] == "Muscle Gain",
            "Existing user profile retrieved successfully",
            "Existing user profile was not retrieved correctly"
        )

        missing_profile = get_user_profile(999999)

        check(
            missing_profile is None,
            "Missing user profile returns None",
            "Missing user profile should return None"
        )

    finally:
        delete_user(test_user_id)


def test_update_user_profile():
    test_user_id = create_user()

    try:
        create_user_profile(
            test_user_id,
            VALID_PROFILE.copy()
        )

        updated = update_user_profile(
            test_user_id,
            {
                "weight_kg": 72.5,
                "primary_goal": "Strength"
            }
        )

        profile = get_user_profile(test_user_id)

        check(
            updated
            and profile["weight_kg"] == 72.5
            and profile["primary_goal"] == "Strength"
            and profile["age"] == 25,
            "User profile partially updated successfully",
            "User profile update failed"
        )

    finally:
        delete_user(test_user_id)


def test_invalid_user_profile_update():
    test_user_id = create_user()

    try:
        create_user_profile(
            test_user_id,
            {
                "age": 25,
                "fitness_level": "Beginner"
            }
        )

        try:
            update_user_profile(
                test_user_id,
                {
                    "training_days_per_week": 10
                }
            )

        except ValueError:
            print(
                "PASS: Invalid user profile update rejected"
            )

        else:
            raise ValueError(
                "FAIL: Invalid user profile update was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_update_missing_user_profile():
    test_user_id = create_user()

    try:
        updated = update_user_profile(
            test_user_id,
            {
                "weight_kg": 70.0
            }
        )

        check(
            updated is False,
            "Updating missing user profile returns False",
            "Missing user profile update should return False"
        )

    finally:
        delete_user(test_user_id)


def test_delete_user():
    test_user_id = create_user()

    create_user_profile(
        test_user_id,
        {
            "age": 25,
            "fitness_level": "Beginner"
        }
    )

    deleted = delete_user(test_user_id)
    profile = get_user_profile(test_user_id)

    check(
        deleted and profile is None,
        "User deleted successfully with profile cascade",
        "User deletion or cascade failed"
    )

    deleted = delete_user(999999)

    check(
        deleted is False,
        "Deleting missing user returns False",
        "Missing user deletion should return False"
    )


# ============================================================
# EXERCISE PREFERENCE TESTS
# ============================================================

def test_add_exercise_preference():
    test_user_id = create_user()

    try:
        preference_id = add_exercise_preference(
            test_user_id,
            "E001",
            "Preferred"
        )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT user_id, exercise_id, preference
            FROM user_exercise_preferences
            WHERE preference_id = ?
        """, (preference_id,))

        preference = cursor.fetchone()
        connection.close()

        check(
            preference == (
                test_user_id,
                "E001",
                "Preferred"
            ),
            "Exercise preference added successfully",
            "Exercise preference was not added correctly"
        )

    finally:
        delete_user(test_user_id)


def test_multiple_exercise_preferences():
    test_user_id = create_user()

    try:
        add_exercise_preference(
            test_user_id,
            "E001",
            "Preferred"
        )

        add_exercise_preference(
            test_user_id,
            "E002",
            "Disliked"
        )

        preferences = get_user_exercise_preferences(
            test_user_id
        )

        check(
            len(preferences) == 2
            and all(
                preference["user_id"] == test_user_id
                for preference in preferences
            ),
            "Multiple exercise preferences retrieved successfully",
            "Exercise preferences were not retrieved correctly"
        )

    finally:
        delete_user(test_user_id)


def test_invalid_exercise_preference():
    test_user_id = create_user()

    try:
        try:
            add_exercise_preference(
                test_user_id,
                "E001",
                "Favorite"
            )

        except sqlite3.IntegrityError:
            print(
                "PASS: Invalid exercise preference rejected"
            )

        else:
            raise ValueError(
                "FAIL: Invalid exercise preference was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_duplicate_exercise_preference():
    test_user_id = create_user()

    try:
        add_exercise_preference(
            test_user_id,
            "E001",
            "Preferred"
        )

        try:
            add_exercise_preference(
                test_user_id,
                "E001",
                "Disliked"
            )

        except sqlite3.IntegrityError:
            print(
                "PASS: Duplicate exercise preference rejected"
            )

        else:
            raise ValueError(
                "FAIL: Duplicate exercise preference was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_remove_exercise_preference():
    test_user_id = create_user()

    try:
        add_exercise_preference(
            test_user_id,
            "E001",
            "Preferred"
        )

        deleted = remove_exercise_preference(
            test_user_id,
            "E001"
        )

        preferences = get_user_exercise_preferences(
            test_user_id
        )

        check(
            deleted and len(preferences) == 0,
            "Exercise preference removed successfully",
            "Exercise preference was not removed correctly"
        )

    finally:
        delete_user(test_user_id)


def test_remove_missing_exercise_preference():
    test_user_id = create_user()

    try:
        deleted = remove_exercise_preference(
            test_user_id,
            "E001"
        )

        check(
            deleted is False,
            "Removing missing exercise preference returns False",
            "Missing exercise preference should return False"
        )

    finally:
        delete_user(test_user_id)


# ============================================================
# USER LIMITATION TESTS
# ============================================================

def test_add_user_limitation():
    test_user_id = create_user()

    try:
        limitation_id = add_user_limitation(
            test_user_id,
            "Knee",
            "Pain",
            "Pain during deep squats"
        )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT user_id, body_area, limitation_type, notes
            FROM user_limitations
            WHERE limitation_id = ?
        """, (limitation_id,))

        limitation = cursor.fetchone()
        connection.close()

        check(
            limitation == (
                test_user_id,
                "Knee",
                "Pain",
                "Pain during deep squats"
            ),
            "User limitation added successfully",
            "User limitation was not added correctly"
        )

    finally:
        delete_user(test_user_id)


def test_multiple_user_limitations():
    test_user_id = create_user()

    try:
        add_user_limitation(
            test_user_id,
            "Knee",
            "Pain",
            "Pain during deep squats"
        )

        add_user_limitation(
            test_user_id,
            "Shoulder",
            "Limited ROM",
            "Avoid overhead pressing"
        )

        limitations = get_user_limitations(test_user_id)

        check(
            len(limitations) == 2
            and all(
                limitation["user_id"] == test_user_id
                for limitation in limitations
            ),
            "Multiple user limitations retrieved successfully",
            "User limitations were not retrieved correctly"
        )

    finally:
        delete_user(test_user_id)


def test_invalid_body_area():
    test_user_id = create_user()

    try:
        try:
            add_user_limitation(
                test_user_id,
                "Banana",
                "Pain"
            )

        except ValueError:
            print("PASS: Invalid body area rejected")

        else:
            raise ValueError(
                "FAIL: Invalid body area was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_invalid_limitation_type():
    test_user_id = create_user()

    try:
        try:
            add_user_limitation(
                test_user_id,
                "Knee",
                "Random Problem"
            )

        except ValueError:
            print("PASS: Invalid limitation type rejected")

        else:
            raise ValueError(
                "FAIL: Invalid limitation type was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_invalid_limitation_notes():
    test_user_id = create_user()

    try:
        try:
            add_user_limitation(
                test_user_id,
                "Knee",
                "Pain",
                123
            )

        except ValueError:
            print("PASS: Invalid limitation notes rejected")

        else:
            raise ValueError(
                "FAIL: Invalid limitation notes were accepted"
            )

    finally:
        delete_user(test_user_id)


def test_remove_user_limitation():
    test_user_id = create_user()

    try:
        limitation_id = add_user_limitation(
            test_user_id,
            "Knee",
            "Pain",
            "Pain during deep squats"
        )

        deleted = remove_user_limitation(
            limitation_id
        )

        limitations = get_user_limitations(
            test_user_id
        )

        check(
            deleted and len(limitations) == 0,
            "User limitation removed successfully",
            "User limitation was not removed correctly"
        )

    finally:
        delete_user(test_user_id)


def test_remove_missing_user_limitation():
    deleted = remove_user_limitation(999999)

    check(
        deleted is False,
        "Removing missing user limitation returns False",
        "Missing user limitation should return False"
    )


# ============================================================
# EQUIPMENT ACCESS TESTS
# ============================================================

def test_add_equipment_access():
    test_user_id = create_user()

    try:
        access_id = add_equipment_access(
            test_user_id,
            "Dumbbell",
            "Available"
        )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT user_id, equipment, access_status
            FROM user_equipment_access
            WHERE access_id = ?
        """, (access_id,))

        equipment_access = cursor.fetchone()
        connection.close()

        check(
            equipment_access == (
                test_user_id,
                "Dumbbell",
                "Available"
            ),
            "Equipment access added successfully",
            "Equipment access was not added correctly"
        )

    finally:
        delete_user(test_user_id)


def test_multiple_equipment_access():
    test_user_id = create_user()

    try:
        add_equipment_access(
            test_user_id,
            "Dumbbell",
            "Available"
        )

        add_equipment_access(
            test_user_id,
            "Barbell",
            "Unavailable"
        )

        equipment_access = get_user_equipment_access(
            test_user_id
        )

        check(
            len(equipment_access) == 2
            and all(
                item["user_id"] == test_user_id
                for item in equipment_access
            ),
            "Multiple equipment access entries retrieved successfully",
            "Equipment access entries were not retrieved correctly"
        )

    finally:
        delete_user(test_user_id)


def test_invalid_equipment():
    test_user_id = create_user()

    try:
        try:
            add_equipment_access(
                test_user_id,
                "Spaceship",
                "Available"
            )

        except ValueError:
            print("PASS: Invalid equipment rejected")

        else:
            raise ValueError(
                "FAIL: Invalid equipment was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_invalid_equipment_status():
    test_user_id = create_user()

    try:
        try:
            add_equipment_access(
                test_user_id,
                "Dumbbell",
                "Maybe"
            )

        except ValueError:
            print(
                "PASS: Invalid equipment access status rejected"
            )

        else:
            raise ValueError(
                "FAIL: Invalid equipment access status was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_remove_equipment_access():
    test_user_id = create_user()

    try:
        add_equipment_access(
            test_user_id,
            "Dumbbell",
            "Available"
        )

        deleted = remove_equipment_access(
            test_user_id,
            "Dumbbell"
        )

        equipment_access = get_user_equipment_access(
            test_user_id
        )

        check(
            deleted and len(equipment_access) == 0,
            "Equipment access removed successfully",
            "Equipment access was not removed correctly"
        )

    finally:
        delete_user(test_user_id)


def test_remove_missing_equipment_access():
    test_user_id = create_user()

    try:
        deleted = remove_equipment_access(
            test_user_id,
            "Dumbbell"
        )

        check(
            deleted is False,
            "Removing missing equipment access returns False",
            "Missing equipment access should return False"
        )

    finally:
        delete_user(test_user_id)


# ============================================================
# NUTRITION TARGET TESTS
# ============================================================

def test_create_nutrition_target():
    test_user_id = create_user()

    try:
        nutrition_target_id = create_user_nutrition_target(
            test_user_id,
            VALID_NUTRITION_TARGET.copy()
        )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                user_id,
                activity_level,
                nutrition_goal,
                calorie_target
            FROM user_nutrition_targets
            WHERE nutrition_target_id = ?
        """, (nutrition_target_id,))

        target = cursor.fetchone()
        connection.close()

        check(
            target == (
                test_user_id,
                "Moderately Active",
                "Muscle Gain",
                2938.99
            ),
            "User nutrition target created successfully",
            "User nutrition target was not created correctly"
        )

    finally:
        delete_user(test_user_id)


def test_get_nutrition_target():
    test_user_id = create_user()

    try:
        create_user_nutrition_target(
            test_user_id,
            VALID_NUTRITION_TARGET.copy()
        )

        target = get_user_nutrition_target(
            test_user_id
        )

        check(
            target is not None
            and target["user_id"] == test_user_id
            and target["nutrition_goal"] == "Muscle Gain"
            and target["calorie_target"] == 2938.99,
            "User nutrition target retrieved successfully",
            "User nutrition target was not retrieved correctly"
        )

    finally:
        delete_user(test_user_id)


def test_update_nutrition_target():
    test_user_id = create_user()

    try:
        create_user_nutrition_target(
            test_user_id,
            VALID_NUTRITION_TARGET.copy()
        )

        updated = update_user_nutrition_target(
            test_user_id,
            {
                "calorie_target": 2800.0,
                "protein_g": 160.0
            }
        )

        target = get_user_nutrition_target(
            test_user_id
        )

        check(
            updated
            and target["calorie_target"] == 2800.0
            and target["protein_g"] == 160.0
            and target["nutrition_goal"] == "Muscle Gain"
            and target["activity_level"] == "Moderately Active",
            "User nutrition target partially updated successfully",
            "User nutrition target update failed"
        )

    finally:
        delete_user(test_user_id)


def test_invalid_nutrition_activity_level():
    test_user_id = create_user()

    target = VALID_NUTRITION_TARGET.copy()
    target["activity_level"] = "Super Active"

    try:
        try:
            create_user_nutrition_target(
                test_user_id,
                target
            )

        except ValueError:
            print(
                "PASS: Invalid nutrition activity level rejected"
            )

        else:
            raise ValueError(
                "FAIL: Invalid nutrition activity level was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_invalid_nutrition_numeric_value():
    test_user_id = create_user()

    target = VALID_NUTRITION_TARGET.copy()
    target["bmr"] = -100

    try:
        try:
            create_user_nutrition_target(
                test_user_id,
                target
            )

        except ValueError:
            print(
                "PASS: Invalid nutrition numeric value rejected"
            )

        else:
            raise ValueError(
                "FAIL: Invalid nutrition numeric value was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_invalid_partial_nutrition_numeric_update():
    test_user_id = create_user()

    try:
        create_user_nutrition_target(
            test_user_id,
            VALID_NUTRITION_TARGET.copy()
        )

        try:
            update_user_nutrition_target(
                test_user_id,
                {
                    "calorie_target": -500
                }
            )

        except ValueError:
            print(
                "PASS: Invalid partial nutrition numeric update rejected"
            )

        else:
            raise ValueError(
                "FAIL: Invalid partial nutrition numeric update was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_invalid_partial_nutrition_goal():
    test_user_id = create_user()

    try:
        create_user_nutrition_target(
            test_user_id,
            VALID_NUTRITION_TARGET.copy()
        )

        try:
            update_user_nutrition_target(
                test_user_id,
                {
                    "nutrition_goal": "Extreme Bulk"
                }
            )

        except ValueError:
            print(
                "PASS: Invalid partial nutrition goal update rejected"
            )

        else:
            raise ValueError(
                "FAIL: Invalid partial nutrition goal update was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_delete_nutrition_target():
    test_user_id = create_user()

    try:
        create_user_nutrition_target(
            test_user_id,
            VALID_NUTRITION_TARGET.copy()
        )

        deleted = delete_user_nutrition_target(
            test_user_id
        )

        target = get_user_nutrition_target(
            test_user_id
        )

        check(
            deleted and target is None,
            "User nutrition target deleted successfully",
            "User nutrition target was not deleted correctly"
        )

    finally:
        delete_user(test_user_id)


def test_delete_missing_nutrition_target():
    test_user_id = create_user()

    try:
        deleted = delete_user_nutrition_target(
            test_user_id
        )

        check(
            deleted is False,
            "Deleting missing nutrition target returns False",
            "Missing nutrition target deletion should return False"
        )

    finally:
        delete_user(test_user_id)


# ============================================================
# FOOD ALLERGY TESTS
# ============================================================

def test_add_food_allergy():
    test_user_id = create_user()

    try:
        allergy_id = add_food_allergy(
            test_user_id,
            "Peanuts",
            "Avoid all peanut-containing foods"
        )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT user_id, allergen, notes
            FROM user_food_allergies
            WHERE allergy_id = ?
        """, (allergy_id,))

        allergy = cursor.fetchone()
        connection.close()

        check(
            allergy == (
                test_user_id,
                "Peanuts",
                "Avoid all peanut-containing foods"
            ),
            "Food allergy added successfully",
            "Food allergy was not added correctly"
        )

    finally:
        delete_user(test_user_id)


def test_duplicate_food_allergy():
    test_user_id = create_user()

    try:
        add_food_allergy(
            test_user_id,
            "Peanuts"
        )

        try:
            add_food_allergy(
                test_user_id,
                "Peanuts"
            )

        except sqlite3.IntegrityError:
            print(
                "PASS: Duplicate food allergy rejected"
            )

        else:
            raise ValueError(
                "FAIL: Duplicate food allergy was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_multiple_food_allergies():
    test_user_id = create_user()

    try:
        add_food_allergy(
            test_user_id,
            "Peanuts"
        )

        add_food_allergy(
            test_user_id,
            "Shellfish",
            "Avoid shellfish completely"
        )

        allergies = get_user_food_allergies(
            test_user_id
        )

        check(
            len(allergies) == 2
            and all(
                allergy["user_id"] == test_user_id
                for allergy in allergies
            ),
            "Multiple food allergies retrieved successfully",
            "Food allergies were not retrieved correctly"
        )

    finally:
        delete_user(test_user_id)


def test_invalid_food_allergen():
    test_user_id = create_user()

    try:
        try:
            add_food_allergy(
                test_user_id,
                "Chocolate"
            )

        except ValueError:
            print("PASS: Invalid food allergen rejected")

        else:
            raise ValueError(
                "FAIL: Invalid food allergen was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_remove_food_allergy():
    test_user_id = create_user()

    try:
        add_food_allergy(
            test_user_id,
            "Peanuts"
        )

        deleted = remove_food_allergy(
            test_user_id,
            "Peanuts"
        )

        allergies = get_user_food_allergies(
            test_user_id
        )

        check(
            deleted and len(allergies) == 0,
            "Food allergy removed successfully",
            "Food allergy was not removed correctly"
        )

    finally:
        delete_user(test_user_id)


def test_remove_missing_food_allergy():
    test_user_id = create_user()

    try:
        deleted = remove_food_allergy(
            test_user_id,
            "Peanuts"
        )

        check(
            deleted is False,
            "Removing missing food allergy returns False",
            "Missing food allergy should return False"
        )

    finally:
        delete_user(test_user_id)


# ============================================================
# FOOD DATABASE TESTS
# ============================================================

def test_create_food_and_allergen():
    food_name = "Peanut Butter Allergen Test"

    cleanup_foods_by_name([
        food_name
    ])

    try:
        food_id = create_food(
            food_name,
            100,
            588,
            25,
            20,
            50
        )

        food_allergen_id = add_food_allergen(
            food_id,
            "Peanuts"
        )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT name, calories, protein_g
            FROM foods
            WHERE food_id = ?
        """, (food_id,))

        food = cursor.fetchone()

        cursor.execute("""
            SELECT food_id, allergen
            FROM food_allergens
            WHERE food_allergen_id = ?
        """, (food_allergen_id,))

        food_allergen = cursor.fetchone()

        connection.close()

        check(
            food == (
                food_name,
                588.0,
                25.0
            )
            and food_allergen == (
                food_id,
                "Peanuts"
            ),
            "Food created and allergen attached successfully",
            "Food or food allergen was not created correctly"
        )

    finally:
        cleanup_foods_by_name([
            food_name
        ])


def test_safe_food_filter():
    safe_food_name = "Chicken Breast Safe Filter Test"
    unsafe_food_name = "Peanut Butter Safe Filter Test"

    cleanup_foods_by_name([
        safe_food_name,
        unsafe_food_name
    ])

    test_user_id = create_user()

    try:
        safe_food_id = create_food(
            safe_food_name,
            100,
            165,
            31,
            0,
            3.6
        )

        unsafe_food_id = create_food(
            unsafe_food_name,
            100,
            588,
            25,
            20,
            50
        )

        add_food_allergen(
            unsafe_food_id,
            "Peanuts"
        )

        add_food_allergy(
            test_user_id,
            "Peanuts"
        )

        safe_foods = get_safe_foods_for_user(
            test_user_id
        )

        safe_food_ids = [
            food["food_id"]
            for food in safe_foods
        ]

        check(
            safe_food_id in safe_food_ids
            and unsafe_food_id not in safe_food_ids,
            "Allergenic food excluded from safe foods",
            "Safe food filtering did not exclude allergenic food"
        )

    finally:
        cleanup_foods_by_name([
            safe_food_name,
            unsafe_food_name
        ])

        delete_user(test_user_id)

def test_invalid_food_name():
    try:
        create_food(
            "",
            100,
            165,
            31,
            0,
            3.6
        )

    except ValueError:
        print("PASS: Blank food name rejected")

    else:
        raise ValueError(
            "FAIL: Blank food name was accepted"
        )


def test_invalid_food_serving_size():
    try:
        create_food(
            "Invalid Serving Test",
            0,
            165,
            31,
            0,
            3.6
        )

    except ValueError:
        print("PASS: Invalid food serving size rejected")

    else:
        raise ValueError(
            "FAIL: Invalid food serving size was accepted"
        )


def test_negative_food_calories():
    try:
        create_food(
            "Negative Calories Test",
            100,
            -10,
            31,
            0,
            3.6
        )

    except ValueError:
        print("PASS: Negative food calories rejected")

    else:
        raise ValueError(
            "FAIL: Negative food calories were accepted"
        )


def test_negative_food_macros():
    try:
        create_food(
            "Negative Protein Test",
            100,
            165,
            -5,
            0,
            3.6
        )

    except ValueError:
        print("PASS: Negative food macro rejected")

    else:
        raise ValueError(
            "FAIL: Negative food macro was accepted"
        )


def test_get_food_by_id():
    food_name = "Food Lookup Test"

    cleanup_foods_by_name([
        food_name
    ])

    try:
        food_id = create_food(
            food_name,
            100,
            165,
            31,
            0,
            3.6
        )

        food = get_food_by_id(food_id)

        check(
            food is not None
            and food["food_id"] == food_id
            and food["name"] == food_name,
            "Food retrieved by ID successfully",
            "Food lookup by ID failed"
        )

        missing_food = get_food_by_id(999999)

        check(
            missing_food is None,
            "Missing food lookup returns None",
            "Missing food lookup should return None"
        )

    finally:
        cleanup_foods_by_name([
            food_name
        ])


def test_search_foods():
    food_names = [
        "Search Chicken Test",
        "Search Rice Test"
    ]

    cleanup_foods_by_name(food_names)

    try:
        create_food(
            "Search Chicken Test",
            100,
            165,
            31,
            0,
            3.6
        )

        create_food(
            "Search Rice Test",
            100,
            130,
            2.7,
            28,
            0.3
        )

        results = search_foods("Chicken")

        result_names = [
            food["name"]
            for food in results
        ]

        check(
            "Search Chicken Test" in result_names
            and "Search Rice Test" not in result_names,
            "Food search returned matching food",
            "Food search returned incorrect results"
        )

    finally:
        cleanup_foods_by_name(food_names)


def test_search_foods_nutrition_filters():
    food_names = [
        "Protein Chicken Test",
        "Protein Rice Test",
        "Protein Yogurt Test"
    ]

    cleanup_foods_by_name(food_names)

    try:
        create_food(
            "Protein Chicken Test",
            100,
            165,
            31,
            0,
            3.6
        )

        create_food(
            "Protein Rice Test",
            100,
            130,
            2.7,
            28,
            0.3
        )

        create_food(
            "Protein Yogurt Test",
            100,
            350,
            25,
            20,
            18
        )

        results = search_foods(
            min_protein_g=20,
            max_calories=300
        )

        result_names = [
            food["name"]
            for food in results
        ]

        check(
            "Protein Chicken Test" in result_names
            and "Protein Rice Test" not in result_names
            and "Protein Yogurt Test" not in result_names,
            "Food nutrition filters returned correct results",
            "Food nutrition filters returned incorrect results"
        )

    finally:
        cleanup_foods_by_name(food_names)


def test_create_meal():
    test_user_id = create_user()

    try:
        meal_id = create_meal(
            test_user_id,
            "High Protein Breakfast",
            "Breakfast"
        )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT user_id, name, meal_type
            FROM meals
            WHERE meal_id = ?
        """, (meal_id,))

        meal = cursor.fetchone()
        connection.close()

        check(
            meal == (
                test_user_id,
                "High Protein Breakfast",
                "Breakfast"
            ),
            "Meal created successfully",
            "Meal was not created correctly"
        )

    finally:
        delete_user(test_user_id)

def test_invalid_meal_name():
    test_user_id = create_user()

    try:
        try:
            create_meal(
                test_user_id,
                "",
                "Breakfast"
            )

        except ValueError:
            print("PASS: Invalid meal name rejected")

        else:
            raise ValueError(
                "FAIL: Invalid meal name was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_invalid_meal_type():
    test_user_id = create_user()

    try:
        try:
            create_meal(
                test_user_id,
                "Test Meal",
                "Brunch"
            )

        except ValueError:
            print("PASS: Invalid meal type rejected")

        else:
            raise ValueError(
                "FAIL: Invalid meal type was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_add_food_to_meal():
    food_name = "Meal Food Test"

    cleanup_foods_by_name([
        food_name
    ])

    test_user_id = create_user()

    try:
        meal_id = create_meal(
            test_user_id,
            "Test Breakfast",
            "Breakfast"
        )

        food_id = create_food(
            food_name,
            100,
            165,
            31,
            0,
            3.6
        )

        meal_food_id = add_food_to_meal(
            meal_id,
            food_id,
            1.5
        )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT meal_id, food_id, servings
            FROM meal_foods
            WHERE meal_food_id = ?
        """, (meal_food_id,))

        meal_food = cursor.fetchone()
        connection.close()

        check(
            meal_food == (
                meal_id,
                food_id,
                1.5
            ),
            "Food added to meal successfully",
            "Food was not added to meal correctly"
        )

    finally:
        cleanup_foods_by_name([
            food_name
        ])

        delete_user(test_user_id)


def test_invalid_meal_food_servings():
    food_name = "Invalid Servings Food Test"

    cleanup_foods_by_name([
        food_name
    ])

    test_user_id = create_user()

    try:
        meal_id = create_meal(
            test_user_id,
            "Test Meal",
            "Lunch"
        )

        food_id = create_food(
            food_name,
            100,
            165,
            31,
            0,
            3.6
        )

        try:
            add_food_to_meal(
                meal_id,
                food_id,
                0
            )

        except ValueError:
            print("PASS: Invalid meal food servings rejected")

        else:
            raise ValueError(
                "FAIL: Invalid meal food servings were accepted"
            )

    finally:
        cleanup_foods_by_name([
            food_name
        ])

        delete_user(test_user_id)


def test_duplicate_food_in_meal():
    food_name = "Duplicate Meal Food Test"

    cleanup_foods_by_name([
        food_name
    ])

    test_user_id = create_user()

    try:
        meal_id = create_meal(
            test_user_id,
            "Test Dinner",
            "Dinner"
        )

        food_id = create_food(
            food_name,
            100,
            165,
            31,
            0,
            3.6
        )

        add_food_to_meal(
            meal_id,
            food_id,
            1.0
        )

        try:
            add_food_to_meal(
                meal_id,
                food_id,
                2.0
            )

        except sqlite3.IntegrityError:
            print("PASS: Duplicate food in meal rejected")

        else:
            raise ValueError(
                "FAIL: Duplicate food in meal was accepted"
            )

    finally:
        cleanup_foods_by_name([
            food_name
        ])

        delete_user(test_user_id)

def test_get_meal_foods():
    food_names = [
        "Meal Chicken Test",
        "Meal Rice Test"
    ]

    cleanup_foods_by_name(food_names)

    test_user_id = create_user()

    try:
        meal_id = create_meal(
            test_user_id,
            "Chicken Rice Meal",
            "Lunch"
        )

        chicken_id = create_food(
            "Meal Chicken Test",
            100,
            165,
            31,
            0,
            3.6
        )

        rice_id = create_food(
            "Meal Rice Test",
            100,
            130,
            2.7,
            28,
            0.3
        )

        add_food_to_meal(
            meal_id,
            chicken_id,
            1.5
        )

        add_food_to_meal(
            meal_id,
            rice_id,
            2.0
        )

        foods = get_meal_foods(meal_id)

        food_names_found = [
            food["name"]
            for food in foods
        ]

        check(
            len(foods) == 2
            and "Meal Chicken Test" in food_names_found
            and "Meal Rice Test" in food_names_found,
            "Meal foods retrieved successfully",
            "Meal foods were not retrieved correctly"
        )

    finally:
        cleanup_foods_by_name(food_names)
        delete_user(test_user_id)

def test_get_meal_nutrition():
    food_names = [
        "Nutrition Chicken Test",
        "Nutrition Rice Test"
    ]

    cleanup_foods_by_name(food_names)

    test_user_id = create_user()

    try:
        meal_id = create_meal(
            test_user_id,
            "Nutrition Test Meal",
            "Lunch"
        )

        chicken_id = create_food(
            "Nutrition Chicken Test",
            100,
            165,
            31,
            0,
            3.6
        )

        rice_id = create_food(
            "Nutrition Rice Test",
            100,
            130,
            2.7,
            28,
            0.3
        )

        add_food_to_meal(
            meal_id,
            chicken_id,
            1.5
        )

        add_food_to_meal(
            meal_id,
            rice_id,
            2.0
        )

        nutrition = get_meal_nutrition(meal_id)

        check(
            nutrition["calories"] == 507.5
            and nutrition["protein_g"] == 51.9
            and nutrition["carbs_g"] == 56.0
            and nutrition["fat_g"] == 6.0,
            "Meal nutrition calculated successfully",
            "Meal nutrition calculation was incorrect"
        )

    finally:
        cleanup_foods_by_name(food_names)
        delete_user(test_user_id)

def test_get_meal_by_id():
    food_name = "Meal Details Chicken Test"

    cleanup_foods_by_name([
        food_name
    ])

    test_user_id = create_user()

    try:
        meal_id = create_meal(
            test_user_id,
            "Meal Details Test",
            "Dinner"
        )

        food_id = create_food(
            food_name,
            100,
            165,
            31,
            0,
            3.6
        )

        add_food_to_meal(
            meal_id,
            food_id,
            2.0
        )

        meal = get_meal_by_id(meal_id)

        check(
            meal is not None
            and meal["meal_id"] == meal_id
            and meal["name"] == "Meal Details Test"
            and len(meal["foods"]) == 1
            and meal["nutrition"]["calories"] == 330,
            "Meal retrieved with foods and nutrition",
            "Meal details were not retrieved correctly"
        )

        missing_meal = get_meal_by_id(999999)

        check(
            missing_meal is None,
            "Missing meal lookup returns None",
            "Missing meal lookup should return None"
        )

    finally:
        cleanup_foods_by_name([
            food_name
        ])

        delete_user(test_user_id)

def test_get_user_meals():
    test_user_id = create_user()

    try:
        create_meal(
            test_user_id,
            "Breakfast Test Meal",
            "Breakfast"
        )

        create_meal(
            test_user_id,
            "Dinner Test Meal",
            "Dinner"
        )

        meals = get_user_meals(test_user_id)

        meal_names = [
            meal["name"]
            for meal in meals
        ]

        check(
            len(meals) == 2
            and "Breakfast Test Meal" in meal_names
            and "Dinner Test Meal" in meal_names,
            "User meals retrieved successfully",
            "User meals were not retrieved correctly"
        )

    finally:
        delete_user(test_user_id)

def test_remove_food_from_meal():
    food_name = "Remove Meal Food Test"

    cleanup_foods_by_name([
        food_name
    ])

    test_user_id = create_user()

    try:
        meal_id = create_meal(
            test_user_id,
            "Remove Food Test Meal",
            "Dinner"
        )

        food_id = create_food(
            food_name,
            100,
            165,
            31,
            0,
            3.6
        )

        add_food_to_meal(
            meal_id,
            food_id,
            1.0
        )

        removed = remove_food_from_meal(
            meal_id,
            food_id
        )

        foods = get_meal_foods(meal_id)

        check(
            removed
            and len(foods) == 0,
            "Food removed from meal successfully",
            "Food was not removed from meal correctly"
        )

        missing_removed = remove_food_from_meal(
            meal_id,
            food_id
        )

        check(
            missing_removed is False,
            "Removing missing meal food returns False",
            "Removing missing meal food should return False"
        )

    finally:
        cleanup_foods_by_name([
            food_name
        ])

        delete_user(test_user_id)

def test_update_meal_food_servings():
    food_name = "Update Meal Servings Test"

    cleanup_foods_by_name([
        food_name
    ])

    test_user_id = create_user()

    try:
        meal_id = create_meal(
            test_user_id,
            "Update Servings Test Meal",
            "Lunch"
        )

        food_id = create_food(
            food_name,
            100,
            165,
            31,
            0,
            3.6
        )

        add_food_to_meal(
            meal_id,
            food_id,
            1.0
        )

        updated = update_meal_food_servings(
            meal_id,
            food_id,
            2.5
        )

        foods = get_meal_foods(meal_id)

        check(
            updated
            and len(foods) == 1
            and foods[0]["servings"] == 2.5,
            "Meal food servings updated successfully",
            "Meal food servings were not updated correctly"
        )

        missing_updated = update_meal_food_servings(
            meal_id,
            999999,
            1.0
        )

        check(
            missing_updated is False,
            "Updating missing meal food returns False",
            "Updating missing meal food should return False"
        )

    finally:
        cleanup_foods_by_name([
            food_name
        ])

        delete_user(test_user_id)

def test_delete_meal():
    food_name = "Delete Meal Food Test"

    cleanup_foods_by_name([
        food_name
    ])

    test_user_id = create_user()

    try:
        meal_id = create_meal(
            test_user_id,
            "Delete Meal Test",
            "Dinner"
        )

        food_id = create_food(
            food_name,
            100,
            165,
            31,
            0,
            3.6
        )

        add_food_to_meal(
            meal_id,
            food_id,
            1.0
        )

        deleted = delete_meal(meal_id)

        meal = get_meal_by_id(meal_id)
        meal_foods = get_meal_foods(meal_id)

        check(
            deleted
            and meal is None
            and len(meal_foods) == 0,
            "Meal deleted with meal foods cascade",
            "Meal deletion or cascade failed"
        )

        missing_deleted = delete_meal(999999)

        check(
            missing_deleted is False,
            "Deleting missing meal returns False",
            "Deleting missing meal should return False"
        )

    finally:
        cleanup_foods_by_name([
            food_name
        ])

        delete_user(test_user_id)

def test_update_meal():
    test_user_id = create_user()

    try:
        meal_id = create_meal(
            test_user_id,
            "Original Meal",
            "Lunch"
        )

        updated = update_meal(
            meal_id,
            {
                "name": "Updated Meal",
                "meal_type": "Dinner"
            }
        )

        meal = get_meal_by_id(meal_id)

        check(
            updated
            and meal["name"] == "Updated Meal"
            and meal["meal_type"] == "Dinner",
            "Meal updated successfully",
            "Meal was not updated correctly"
        )

        missing_updated = update_meal(
            999999,
            {
                "name": "Missing Meal"
            }
        )

        check(
            missing_updated is False,
            "Updating missing meal returns False",
            "Updating missing meal should return False"
        )

    finally:
        delete_user(test_user_id)

def test_invalid_meal_update_name():
    test_user_id = create_user()

    try:
        meal_id = create_meal(
            test_user_id,
            "Valid Meal",
            "Lunch"
        )

        try:
            update_meal(
                meal_id,
                {
                    "name": ""
                }
            )

        except ValueError:
            print("PASS: Invalid meal update name rejected")

        else:
            raise ValueError(
                "FAIL: Invalid meal update name was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_invalid_meal_update_type():
    test_user_id = create_user()

    try:
        meal_id = create_meal(
            test_user_id,
            "Valid Meal",
            "Lunch"
        )

        try:
            update_meal(
                meal_id,
                {
                    "meal_type": "Brunch"
                }
            )

        except ValueError:
            print("PASS: Invalid meal update type rejected")

        else:
            raise ValueError(
                "FAIL: Invalid meal update type was accepted"
            )

    finally:
        delete_user(test_user_id)


def test_invalid_meal_update_field():
    test_user_id = create_user()

    try:
        meal_id = create_meal(
            test_user_id,
            "Valid Meal",
            "Lunch"
        )

        try:
            update_meal(
                meal_id,
                {
                    "calories": 500
                }
            )

        except ValueError:
            print("PASS: Invalid meal update field rejected")

        else:
            raise ValueError(
                "FAIL: Invalid meal update field was accepted"
            )

    finally:
        delete_user(test_user_id)


# ============================================================
# RUN ALL TESTS
# ============================================================

def run_all_tests():
    test_user_profile_schema()
    test_user_profile_relationship()

    test_create_user()
    test_create_user_profile_valid()
    test_create_user_profile_invalid()
    test_get_user_profile()
    test_update_user_profile()
    test_invalid_user_profile_update()
    test_update_missing_user_profile()
    test_delete_user()

    test_add_exercise_preference()
    test_multiple_exercise_preferences()
    test_invalid_exercise_preference()
    test_duplicate_exercise_preference()
    test_remove_exercise_preference()
    test_remove_missing_exercise_preference()

    test_add_user_limitation()
    test_multiple_user_limitations()
    test_invalid_body_area()
    test_invalid_limitation_type()
    test_invalid_limitation_notes()
    test_remove_user_limitation()
    test_remove_missing_user_limitation()

    test_add_equipment_access()
    test_multiple_equipment_access()
    test_invalid_equipment()
    test_invalid_equipment_status()
    test_remove_equipment_access()
    test_remove_missing_equipment_access()

    test_create_nutrition_target()
    test_get_nutrition_target()
    test_update_nutrition_target()
    test_invalid_nutrition_activity_level()
    test_invalid_nutrition_numeric_value()
    test_invalid_partial_nutrition_numeric_update()
    test_invalid_partial_nutrition_goal()
    test_delete_nutrition_target()
    test_delete_missing_nutrition_target()

    test_add_food_allergy()
    test_duplicate_food_allergy()
    test_multiple_food_allergies()
    test_invalid_food_allergen()
    test_remove_food_allergy()
    test_remove_missing_food_allergy()

    test_create_food_and_allergen()
    test_safe_food_filter()

    test_invalid_food_name()
    test_invalid_food_serving_size()
    test_negative_food_calories()
    test_negative_food_macros()

    test_get_food_by_id()
    test_search_foods()
    test_search_foods_nutrition_filters()
    test_create_meal()
    test_invalid_meal_name()
    test_invalid_meal_type()
    test_add_food_to_meal()
    test_invalid_meal_food_servings()
    test_duplicate_food_in_meal()
    test_get_meal_foods()
    test_get_meal_nutrition()
    test_get_meal_by_id()
    test_get_user_meals()
    test_remove_food_from_meal()
    test_update_meal_food_servings()
    test_delete_meal()
    test_update_meal()

    test_invalid_meal_update_name()
    test_invalid_meal_update_type()
    test_invalid_meal_update_field()

    print("\nPASS: All user database tests completed")


if __name__ == "__main__":
    run_all_tests()