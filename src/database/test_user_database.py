import sqlite3
from src.database.query_user_database import create_user, create_user_profile,  get_user_profile, update_user_profile, delete_user, add_exercise_preference, get_user_exercise_preferences, remove_exercise_preference, add_user_limitation, get_user_limitations, remove_user_limitation, add_equipment_access, get_user_equipment_access, remove_equipment_access, create_user_nutrition_target, get_user_nutrition_target, update_user_nutrition_target, delete_user_nutrition_target
from src.database.setup_exercise_database import db_path


connection = sqlite3.connect(db_path)
cursor = connection.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

cursor.execute("PRAGMA table_info(user_profiles)")
profile_columns = cursor.fetchall()

for column in profile_columns:
    print(column)

cursor.execute("PRAGMA foreign_key_list(user_profiles)")
foreign_keys = cursor.fetchall()

print("Foreign keys:", foreign_keys)

if len(profile_columns) > 0:
    print("PASS: User profiles table exists")
else:
    raise ValueError("FAIL: User profiles table does not exist")

if len(foreign_keys) > 0:
    print("PASS: User profiles foreign key exists")
else:
    raise ValueError("FAIL: User profiles foreign key does not exist")

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")

tables = cursor.fetchone()

if tables is not None:
    print("PASS: Users table exists")
else:
    raise ValueError("FAIL: Users table does not exist")

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

cursor.execute(
    "SELECT * FROM user_profiles WHERE user_id = ?",
    (test_user_id,)
)

profile = cursor.fetchone()

if profile is not None:
    print("PASS: User profile linked to user successfully")
else:
    raise ValueError("FAIL: User profile was not linked to user")

try:
    cursor.execute(
        "INSERT INTO user_profiles (user_id) VALUES (?)",
        (test_user_id,)
    )
except sqlite3.IntegrityError:
    print("PASS: Duplicate user profile rejected")
else:
    raise ValueError("FAIL: User was allowed to have multiple profiles")

cursor.execute(
    "DELETE FROM users WHERE user_id = ?",
    (test_user_id,)
)

cursor.execute(
    "SELECT * FROM user_profiles WHERE user_id = ?",
    (test_user_id,)
)

deleted_profile = cursor.fetchone()

if deleted_profile is None:
    print("PASS: User profile deleted automatically with user")
else:
    raise ValueError("FAIL: User profile was not deleted with user")

connection.rollback()

connection.close()

test_user_id = create_user()

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

cursor.execute(
    "SELECT user_id FROM users WHERE user_id = ?",
    (test_user_id,)
)

user = cursor.fetchone()

if user is not None:
    print("PASS: create_user created a user successfully")
else:
    raise ValueError("FAIL: create_user did not create a user")

cursor.execute(
    "DELETE FROM users WHERE user_id = ?",
    (test_user_id,)
)

connection.commit()
connection.close()

# Test create_user_profile with valid data

test_user_id = create_user()

valid_profile = {
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

profile_id = create_user_profile(test_user_id, valid_profile)

connection = sqlite3.connect(db_path)
cursor = connection.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

cursor.execute(
    "SELECT * FROM user_profiles WHERE profile_id = ?",
    (profile_id,)
)

profile = cursor.fetchone()

if profile is not None:
    print("PASS: create_user_profile created profile successfully")
else:
    raise ValueError("FAIL: create_user_profile did not create profile")

cursor.execute(
    "DELETE FROM users WHERE user_id = ?",
    (test_user_id,)
)

connection.commit()
connection.close()

# Test create_user_profile with invalid data

test_user_id = create_user()

invalid_profile = {
    "age": 0,
    "fitness_level": "Beginner"
}

try:
    create_user_profile(test_user_id, invalid_profile)
except ValueError:
    print("PASS: create_user_profile rejected invalid profile")
else:
    raise ValueError("FAIL: create_user_profile accepted invalid profile")

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

cursor.execute(
    "DELETE FROM users WHERE user_id = ?",
    (test_user_id,)
)

connection.commit()
connection.close()

# Test get_user_profile with existing profile

test_user_id = create_user()

valid_profile = {
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

create_user_profile(test_user_id, valid_profile)

profile = get_user_profile(test_user_id)

if (
    profile is not None
    and profile["user_id"] == test_user_id
    and profile["age"] == 25
    and profile["primary_goal"] == "Muscle Gain"
):
    print("PASS: Existing user profile retrieved successfully")
else:
    raise ValueError("FAIL: Existing user profile was not retrieved correctly")

missing_profile = get_user_profile(999999)

if missing_profile is None:
    print("PASS: Missing user profile returns None")
else:
    raise ValueError("FAIL: Missing user profile should return None")

connection = sqlite3.connect(db_path)
cursor = connection.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

cursor.execute(
    "DELETE FROM users WHERE user_id = ?",
    (test_user_id,)
)

connection.commit()
connection.close()

# Test update_user_profile

test_user_id = create_user()

valid_profile = {
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

create_user_profile(test_user_id, valid_profile)

updated = update_user_profile(
    test_user_id,
    {
        "weight_kg": 72.5,
        "primary_goal": "Strength"
    }
)

profile = get_user_profile(test_user_id)

if (
    updated
    and profile["weight_kg"] == 72.5
    and profile["primary_goal"] == "Strength"
    and profile["age"] == 25
):
    print("PASS: User profile partially updated successfully")
else:
    raise ValueError("FAIL: User profile update failed")

connection = sqlite3.connect(db_path)
cursor = connection.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

cursor.execute(
    "DELETE FROM users WHERE user_id = ?",
    (test_user_id,)
)

connection.commit()
connection.close()

# Test invalid profile update

test_user_id = create_user()

valid_profile = {
    "age": 25,
    "fitness_level": "Beginner"
}

create_user_profile(test_user_id, valid_profile)

try:
    update_user_profile(
        test_user_id,
        {
            "training_days_per_week": 10
        }
    )
except ValueError:
    print("PASS: Invalid user profile update rejected")
else:
    raise ValueError("FAIL: Invalid user profile update was accepted")

connection = sqlite3.connect(db_path)
cursor = connection.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

cursor.execute(
    "DELETE FROM users WHERE user_id = ?",
    (test_user_id,)
)

connection.commit()
connection.close()

# Test updating user with no profile

test_user_id = create_user()

updated = update_user_profile(
    test_user_id,
    {
        "weight_kg": 70.0
    }
)

if updated is False:
    print("PASS: Updating missing user profile returns False")
else:
    raise ValueError("FAIL: Missing user profile update should return False")

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

cursor.execute(
    "DELETE FROM users WHERE user_id = ?",
    (test_user_id,)
)

connection.commit()
connection.close()

# Test delete_user with existing user

test_user_id = create_user()

valid_profile = {
    "age": 25,
    "fitness_level": "Beginner"
}

create_user_profile(test_user_id, valid_profile)

deleted = delete_user(test_user_id)

user_profile = get_user_profile(test_user_id)

if deleted and user_profile is None:
    print("PASS: User deleted successfully with profile cascade")
else:
    raise ValueError("FAIL: User deletion or cascade failed")

# Test delete_user with missing user

deleted = delete_user(999999)

if deleted is False:
    print("PASS: Deleting missing user returns False")
else:
    raise ValueError("FAIL: Missing user deletion should return False")

# Test add_exercise_preference

test_user_id = create_user()

preference_id = add_exercise_preference(
    test_user_id,
    "E001",
    "Preferred"
)

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

cursor.execute("""
    SELECT user_id, exercise_id, preference
    FROM user_exercise_preferences
    WHERE preference_id = ?
""", (preference_id,))

preference = cursor.fetchone()

connection.close()

if preference == (test_user_id, "E001", "Preferred"):
    print("PASS: Exercise preference added successfully")
else:
    raise ValueError("FAIL: Exercise preference was not added correctly")

delete_user(test_user_id)

# Test get_user_exercise_preferences

test_user_id = create_user()

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

preferences = get_user_exercise_preferences(test_user_id)

if (
    len(preferences) == 2
    and preferences[0]["user_id"] == test_user_id
    and preferences[1]["user_id"] == test_user_id
):
    print("PASS: Multiple exercise preferences retrieved successfully")
else:
    raise ValueError("FAIL: Exercise preferences were not retrieved correctly")

delete_user(test_user_id)

# Test invalid exercise preference value

test_user_id = create_user()

try:
    add_exercise_preference(
        test_user_id,
        "E001",
        "Favorite"
    )
except sqlite3.IntegrityError:
    print("PASS: Invalid exercise preference rejected")
else:
    raise ValueError("FAIL: Invalid exercise preference was accepted")

delete_user(test_user_id)
# Test duplicate exercise preference

test_user_id = create_user()

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
    print("PASS: Duplicate exercise preference rejected")
else:
    raise ValueError("FAIL: Duplicate exercise preference was accepted")

delete_user(test_user_id)


# Test remove_exercise_preference

test_user_id = create_user()

add_exercise_preference(
    test_user_id,
    "E001",
    "Preferred"
)

deleted = remove_exercise_preference(
    test_user_id,
    "E001"
)

preferences = get_user_exercise_preferences(test_user_id)

if deleted and len(preferences) == 0:
    print("PASS: Exercise preference removed successfully")
else:
    raise ValueError("FAIL: Exercise preference was not removed correctly")

delete_user(test_user_id)


# Test removing missing exercise preference

test_user_id = create_user()

deleted = remove_exercise_preference(
    test_user_id,
    "E001"
)

if deleted is False:
    print("PASS: Removing missing exercise preference returns False")
else:
    raise ValueError("FAIL: Missing exercise preference should return False")

delete_user(test_user_id)


# Test add_user_limitation

test_user_id = create_user()

limitation_id = add_user_limitation(
    test_user_id,
    "Knee",
    "Pain",
    "Pain during deep squats"
)

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

cursor.execute("""
    SELECT user_id, body_area, limitation_type, notes
    FROM user_limitations
    WHERE limitation_id = ?
""", (limitation_id,))

limitation = cursor.fetchone()

connection.close()

if limitation == (
    test_user_id,
    "Knee",
    "Pain",
    "Pain during deep squats"
):
    print("PASS: User limitation added successfully")
else:
    raise ValueError("FAIL: User limitation was not added correctly")

delete_user(test_user_id)


# Test get_user_limitations

test_user_id = create_user()

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

if (
    len(limitations) == 2
    and limitations[0]["user_id"] == test_user_id
    and limitations[1]["user_id"] == test_user_id
):
    print("PASS: Multiple user limitations retrieved successfully")
else:
    raise ValueError("FAIL: User limitations were not retrieved correctly")

delete_user(test_user_id)


# Test invalid body area

test_user_id = create_user()

try:
    add_user_limitation(
        test_user_id,
        "Banana",
        "Pain"
    )
except ValueError:
    print("PASS: Invalid body area rejected")
else:
    raise ValueError("FAIL: Invalid body area was accepted")

delete_user(test_user_id)


# Test invalid limitation type

test_user_id = create_user()

try:
    add_user_limitation(
        test_user_id,
        "Knee",
        "Random Problem"
    )
except ValueError:
    print("PASS: Invalid limitation type rejected")
else:
    raise ValueError("FAIL: Invalid limitation type was accepted")

delete_user(test_user_id)


# Test invalid notes type

test_user_id = create_user()

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
    raise ValueError("FAIL: Invalid limitation notes were accepted")

delete_user(test_user_id)

# Test remove_user_limitation

test_user_id = create_user()

limitation_id = add_user_limitation(
    test_user_id,
    "Knee",
    "Pain",
    "Pain during deep squats"
)

deleted = remove_user_limitation(limitation_id)

limitations = get_user_limitations(test_user_id)

if deleted and len(limitations) == 0:
    print("PASS: User limitation removed successfully")
else:
    raise ValueError("FAIL: User limitation was not removed correctly")

delete_user(test_user_id)


# Test removing missing user limitation

deleted = remove_user_limitation(999999)

if deleted is False:
    print("PASS: Removing missing user limitation returns False")
else:
    raise ValueError("FAIL: Missing user limitation should return False")

# Test add_equipment_access

test_user_id = create_user()

access_id = add_equipment_access(
    test_user_id,
    "Dumbbell",
    "Available"
)

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

cursor.execute("""
    SELECT user_id, equipment, access_status
    FROM user_equipment_access
    WHERE access_id = ?
""", (access_id,))

equipment_access = cursor.fetchone()

connection.close()

if equipment_access == (
    test_user_id,
    "Dumbbell",
    "Available"
):
    print("PASS: Equipment access added successfully")
else:
    raise ValueError("FAIL: Equipment access was not added correctly")

delete_user(test_user_id)


# Test get_user_equipment_access

test_user_id = create_user()

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

equipment_access = get_user_equipment_access(test_user_id)

if (
    len(equipment_access) == 2
    and equipment_access[0]["user_id"] == test_user_id
    and equipment_access[1]["user_id"] == test_user_id
):
    print("PASS: Multiple equipment access entries retrieved successfully")
else:
    raise ValueError("FAIL: Equipment access entries were not retrieved correctly")

delete_user(test_user_id)


# Test invalid equipment

test_user_id = create_user()

try:
    add_equipment_access(
        test_user_id,
        "Spaceship",
        "Available"
    )
except ValueError:
    print("PASS: Invalid equipment rejected")
else:
    raise ValueError("FAIL: Invalid equipment was accepted")

delete_user(test_user_id)


# Test invalid equipment access status

test_user_id = create_user()

try:
    add_equipment_access(
        test_user_id,
        "Dumbbell",
        "Maybe"
    )
except ValueError:
    print("PASS: Invalid equipment access status rejected")
else:
    raise ValueError("FAIL: Invalid equipment access status was accepted")

delete_user(test_user_id)


# Test remove_equipment_access

test_user_id = create_user()

add_equipment_access(
    test_user_id,
    "Dumbbell",
    "Available"
)

deleted = remove_equipment_access(
    test_user_id,
    "Dumbbell"
)

equipment_access = get_user_equipment_access(test_user_id)

if deleted and len(equipment_access) == 0:
    print("PASS: Equipment access removed successfully")
else:
    raise ValueError("FAIL: Equipment access was not removed correctly")

delete_user(test_user_id)


# Test removing missing equipment access

test_user_id = create_user()

deleted = remove_equipment_access(
    test_user_id,
    "Dumbbell"
)

if deleted is False:
    print("PASS: Removing missing equipment access returns False")
else:
    raise ValueError("FAIL: Missing equipment access should return False")

delete_user(test_user_id)

# Test create_user_nutrition_target

test_user_id = create_user()

target = {
    "activity_level": "Moderately Active",
    "nutrition_goal": "Muscle Gain",
    "bmr": 1723.75,
    "tdee": 2671.81,
    "calorie_target": 2938.99,
    "protein_g": 150.0,
    "fat_g": 81.64,
    "carbs_g": 400.0
}

nutrition_target_id = create_user_nutrition_target(
    test_user_id,
    target
)

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

cursor.execute("""
    SELECT user_id, activity_level, nutrition_goal, calorie_target
    FROM user_nutrition_targets
    WHERE nutrition_target_id = ?
""", (nutrition_target_id,))

nutrition_target = cursor.fetchone()

connection.close()

if nutrition_target == (
    test_user_id,
    "Moderately Active",
    "Muscle Gain",
    2938.99
):
    print("PASS: User nutrition target created successfully")
else:
    raise ValueError("FAIL: User nutrition target was not created correctly")

delete_user(test_user_id)

# Test get_user_nutrition_target

test_user_id = create_user()

target = {
    "activity_level": "Moderately Active",
    "nutrition_goal": "Muscle Gain",
    "bmr": 1723.75,
    "tdee": 2671.81,
    "calorie_target": 2938.99,
    "protein_g": 150.0,
    "fat_g": 81.64,
    "carbs_g": 400.0
}

create_user_nutrition_target(
    test_user_id,
    target
)

nutrition_target = get_user_nutrition_target(test_user_id)

if (
    nutrition_target is not None
    and nutrition_target["user_id"] == test_user_id
    and nutrition_target["nutrition_goal"] == "Muscle Gain"
    and nutrition_target["calorie_target"] == 2938.99
):
    print("PASS: User nutrition target retrieved successfully")
else:
    raise ValueError("FAIL: User nutrition target was not retrieved correctly")

delete_user(test_user_id)


# Test update_user_nutrition_target

test_user_id = create_user()

target = {
    "activity_level": "Moderately Active",
    "nutrition_goal": "Muscle Gain",
    "bmr": 1723.75,
    "tdee": 2671.81,
    "calorie_target": 2938.99,
    "protein_g": 150.0,
    "fat_g": 81.64,
    "carbs_g": 400.0
}

create_user_nutrition_target(
    test_user_id,
    target
)

updated = update_user_nutrition_target(
    test_user_id,
    {
        "calorie_target": 2800.0,
        "protein_g": 160.0
    }
)

nutrition_target = get_user_nutrition_target(test_user_id)

if (
    updated
    and nutrition_target["calorie_target"] == 2800.0
    and nutrition_target["protein_g"] == 160.0
    and nutrition_target["nutrition_goal"] == "Muscle Gain"
    and nutrition_target["activity_level"] == "Moderately Active"
):
    print("PASS: User nutrition target partially updated successfully")
else:
    raise ValueError("FAIL: User nutrition target update failed")

delete_user(test_user_id)


# Test invalid nutrition activity level

test_user_id = create_user()

invalid_target = {
    "activity_level": "Super Active",
    "nutrition_goal": "Muscle Gain",
    "bmr": 1723.75,
    "tdee": 2671.81,
    "calorie_target": 2938.99,
    "protein_g": 150.0,
    "fat_g": 81.64,
    "carbs_g": 400.0
}

try:
    create_user_nutrition_target(
        test_user_id,
        invalid_target
    )
except ValueError:
    print("PASS: Invalid nutrition activity level rejected")
else:
    raise ValueError(
        "FAIL: Invalid nutrition activity level was accepted"
    )

delete_user(test_user_id)


# Test invalid nutrition numeric value

test_user_id = create_user()

invalid_target = {
    "activity_level": "Moderately Active",
    "nutrition_goal": "Muscle Gain",
    "bmr": -100,
    "tdee": 2671.81,
    "calorie_target": 2938.99,
    "protein_g": 150.0,
    "fat_g": 81.64,
    "carbs_g": 400.0
}

try:
    create_user_nutrition_target(
        test_user_id,
        invalid_target
    )
except ValueError:
    print("PASS: Invalid nutrition numeric value rejected")
else:
    raise ValueError(
        "FAIL: Invalid nutrition numeric value was accepted"
    )

delete_user(test_user_id)

# Test invalid partial nutrition numeric update

test_user_id = create_user()

target = {
    "activity_level": "Moderately Active",
    "nutrition_goal": "Muscle Gain",
    "bmr": 1723.75,
    "tdee": 2671.81,
    "calorie_target": 2938.99,
    "protein_g": 150.0,
    "fat_g": 81.64,
    "carbs_g": 400.0
}

create_user_nutrition_target(
    test_user_id,
    target
)

try:
    update_user_nutrition_target(
        test_user_id,
        {
            "calorie_target": -500
        }
    )
except ValueError:
    print("PASS: Invalid partial nutrition numeric update rejected")
else:
    raise ValueError(
        "FAIL: Invalid partial nutrition numeric update was accepted"
    )

delete_user(test_user_id)

# Test invalid partial nutrition goal update

test_user_id = create_user()

create_user_nutrition_target(
    test_user_id,
    target
)

try:
    update_user_nutrition_target(
        test_user_id,
        {
            "nutrition_goal": "Extreme Bulk"
        }
    )
except ValueError:
    print("PASS: Invalid partial nutrition goal update rejected")
else:
    raise ValueError(
        "FAIL: Invalid partial nutrition goal update was accepted"
    )

delete_user(test_user_id)

# Test delete_user_nutrition_target

test_user_id = create_user()

target = {
    "activity_level": "Moderately Active",
    "nutrition_goal": "Muscle Gain",
    "bmr": 1723.75,
    "tdee": 2671.81,
    "calorie_target": 2938.99,
    "protein_g": 150.0,
    "fat_g": 81.64,
    "carbs_g": 400.0
}

create_user_nutrition_target(
    test_user_id,
    target
)

deleted = delete_user_nutrition_target(test_user_id)

nutrition_target = get_user_nutrition_target(test_user_id)

if deleted and nutrition_target is None:
    print("PASS: User nutrition target deleted successfully")
else:
    raise ValueError("FAIL: User nutrition target was not deleted correctly")

delete_user(test_user_id)

# Test deleting missing nutrition target

test_user_id = create_user()

deleted = delete_user_nutrition_target(test_user_id)

if deleted is False:
    print("PASS: Deleting missing nutrition target returns False")
else:
    raise ValueError("FAIL: Missing nutrition target deletion should return False")

delete_user(test_user_id)