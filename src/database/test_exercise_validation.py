import pandas as pd
from src.database.setup_exercise_database import validate_exercise_data

valid_exercise = {
    "exercise_id": "E001",
    "name": "Push-Up",
    "category": "Strength",
    "exercise_type": "Compound",
    "primary_muscle": "Chest",
    "secondary_muscles": None,
    "stabilizer_muscles": None,
    "joints_involved": None,
    "equipment": "Bodyweight",
    "difficulty_level": "Beginner",
    "difficulty_score": 1,
    "movement_pattern": "Push",
    "body_position": "Lying",
    "instructions": "Perform a controlled push-up.",
    "precautions": None,
    "common_mistakes": None,
    "environment": "Both"
}

data = pd.DataFrame([valid_exercise])
validate_exercise_data(data)
print("PASS: Valid exercise data accepted")


invalid_exercise = valid_exercise.copy()
invalid_exercise["exercise_id"] = "X001"
invalid_data = pd.DataFrame([invalid_exercise])

try:
    validate_exercise_data(invalid_data)
except ValueError as error:
    if "Invalid exercise IDs" in str(error):
        print("PASS: Invalid exercise ID rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Invalid exercise ID was not rejected")


invalid_exercise = valid_exercise.copy()
invalid_exercise["difficulty_level"] = "Expert"
invalid_data = pd.DataFrame([invalid_exercise])

try:
    validate_exercise_data(invalid_data)
except ValueError as error:
    if "Invalid difficulty levels" in str(error):
        print("PASS: Invalid difficulty level rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Invalid difficulty level was not rejected")


invalid_exercise = valid_exercise.copy()
invalid_exercise["difficulty_score"] = 99
invalid_data = pd.DataFrame([invalid_exercise])

try:
    validate_exercise_data(invalid_data)
except ValueError as error:
    if "Invalid difficulty scores" in str(error):
        print("PASS: Invalid difficulty score rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Invalid difficulty score was not rejected")


invalid_exercise = valid_exercise.copy()
invalid_exercise["environment"] = "Outside"
invalid_data = pd.DataFrame([invalid_exercise])

try:
    validate_exercise_data(invalid_data)
except ValueError as error:
    if "Invalid environments" in str(error):
        print("PASS: Invalid environment rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Invalid environment was not rejected")


exercise1 = valid_exercise.copy()
exercise2 = valid_exercise.copy()
duplicate_data = pd.DataFrame([exercise1, exercise2])

try:
    validate_exercise_data(duplicate_data)
except ValueError as error:
    if "Duplicate exercise ids" in str(error):
        print("PASS: Duplicate exercise IDs rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Duplicate exercise IDs were not rejected")


invalid_exercise = valid_exercise.copy()
invalid_exercise["name"] = None
invalid_data = pd.DataFrame([invalid_exercise])

try:
    validate_exercise_data(invalid_data)
except ValueError as error:
    if "Missing required exercise values" in str(error):
        print("PASS: Missing required value rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Missing required value was not rejected")


invalid_exercise = valid_exercise.copy()
invalid_exercise["name"] = "   "
invalid_data = pd.DataFrame([invalid_exercise])

try:
    validate_exercise_data(invalid_data)
except ValueError as error:
    if "Blank values found in required exercise fields" in str(error):
        print("PASS: Blank required value rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Blank required value was not rejected")


invalid_data = pd.DataFrame([valid_exercise]).drop(columns=["name"])

try:
    validate_exercise_data(invalid_data)
except ValueError as error:
    if "Missing exercise columns" in str(error):
        print("PASS: Missing exercise column rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Missing exercise column was not rejected")


invalid_exercise = valid_exercise.copy()
invalid_exercise["category"] = "Swimming"
invalid_data = pd.DataFrame([invalid_exercise])

try:
    validate_exercise_data(invalid_data)
except ValueError as error:
    if "Invalid categories" in str(error):
        print("PASS: Invalid category rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Invalid category was not rejected")


invalid_exercise = valid_exercise.copy()
invalid_exercise["exercise_type"] = "Hybrid"
invalid_data = pd.DataFrame([invalid_exercise])

try:
    validate_exercise_data(invalid_data)
except ValueError as error:
    if "Invalid exercise types" in str(error):
        print("PASS: Invalid exercise type rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Invalid exercise type was not rejected")

invalid_exercise = valid_exercise.copy()
invalid_exercise["exercise_type"] = None
invalid_data = pd.DataFrame([invalid_exercise])

try:
    validate_exercise_data(invalid_data)
except ValueError as error:
    if "Invalid exercise types" in str(error):
        print("PASS: Strength exercise without type rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Strength exercise without type was not rejected")

cardio_exercise = valid_exercise.copy()
cardio_exercise["exercise_id"] = "E100"
cardio_exercise["category"] = "Cardio"
cardio_exercise["exercise_type"] = None

cardio_data = pd.DataFrame([cardio_exercise])

validate_exercise_data(cardio_data)
print("PASS: Cardio exercise without type accepted")