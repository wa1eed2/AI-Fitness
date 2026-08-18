import sqlite3
from src.database.query_user_database import create_user, create_user_profile,  get_user_profile, update_user_profile, delete_user
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