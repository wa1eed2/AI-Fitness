import sqlite3
from src.database.setup_exercise_database import db_path
from src.database.query_exercise_database import get_exercise_by_id, search_exercises

connection = sqlite3.connect(db_path)
cursor = connection.cursor()
cursor.execute("PRAGMA table_info(exercises)")
columns = cursor.fetchall()

for column in columns:
    print(column)

cursor.execute("SELECT COUNT(*) FROM exercises")
count = cursor.fetchone()[0]
print("Exercise count:", count)

if count >= 5:
    print("PASS: Exercise database contains starter dataset")
else:
    raise ValueError("FAIL: Exercise database contains fewer than 5 exercises")

connection.close()

exercise = get_exercise_by_id("E001")

if exercise is not None and exercise["exercise_id"] == "E001":
    print("PASS: Existing exercise retrieved successfully")
else:
    raise ValueError("FAIL: Existing exercise could not be retrieved")

exercise = get_exercise_by_id("E999")

if exercise is None:
    print("PASS: Missing exercise returns None")
else:
    raise ValueError("FAIL: Missing exercise should return None")

result = search_exercises(primary_muscle="Chest")
if len(result) > 0:
    print("PASS: Chest exercise search returned results")
else:
    raise ValueError("FAIL: Chest exercise search returned no results")

result = search_exercises(category="Strength")
if len(result) > 0:
    print("PASS: Strength exercise search returned results")
else:
    raise ValueError("FAIL: Strength exercise search returned no results")

result = search_exercises(environment="Both")
if len(result) > 0:
    print("PASS: Environment search returned results")
else:
    raise ValueError("FAIL: Both exercise search returned no results")

result = search_exercises(primary_muscle="Chest", category="Strength", environment="Both")

if len(result) > 0:
    print("PASS: Combined exercise filters returned results")
else:
    raise ValueError("FAIL: Combined exercise filters returned no results")

result = search_exercises(difficulty_level="Beginner")
if len(result) > 0:
    print("PASS: Beginner exercise filter returned results")
else:
    raise ValueError("FAIL: Beginner exercise filter returned no results")

result = search_exercises(exercise_type="Compound", movement_pattern="Push", body_position="Lying", difficulty_score=1)
if len(result) > 0:
    print("PASS: Multiple exercise filters returned results")
else:
    raise ValueError("FAIL: Compound exercise filter returned no results")

exercise = get_exercise_by_id("E001")
if exercise["equipment"] == "Bodyweight" and exercise["body_position"] == "Lying":
    print("PASS: Exercise CSV sync updated E001")
else:
    raise ValueError("FAIL: Exercise CSV sync did not update E001")

result = search_exercises(primary_muscle="Back")

if any(exercise["exercise_id"] == "E003" for exercise in result):
    print("PASS: Back search returned Pull-Up")
else:
    raise ValueError("FAIL: Back search did not return Pull-Up")


result = search_exercises(primary_muscle="Shoulders")

if any(exercise["exercise_id"] == "E004" for exercise in result):
    print("PASS: Shoulder search returned Dumbbell Lateral Raise")
else:
    raise ValueError("FAIL: Shoulder search did not return Dumbbell Lateral Raise")


result = search_exercises(equipment="Barbell")

if any(exercise["exercise_id"] == "E002" for exercise in result):
    print("PASS: Barbell search returned Barbell Squat")
else:
    raise ValueError("FAIL: Barbell search did not return Barbell Squat")


result = search_exercises(movement_pattern="Lunge")

if any(exercise["exercise_id"] == "E005" for exercise in result):
    print("PASS: Lunge search returned Reverse Lunge")
else:
    raise ValueError("FAIL: Lunge search did not return Reverse Lunge")

result = search_exercises(category="Cardio")

if any(exercise["exercise_id"] == "E006" for exercise in result):
    print("PASS: Cardio search returned Brisk Walking")
else:
    raise ValueError("FAIL: Cardio search did not return Brisk Walking")


exercise = get_exercise_by_id("E006")

if exercise["exercise_type"] is None:
    print("PASS: Cardio exercise type stored as NULL")
else:
    raise ValueError("FAIL: Cardio exercise type should be NULL")