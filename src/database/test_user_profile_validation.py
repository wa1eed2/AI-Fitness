from src.database.validate_user_profile import validate_user_profile

valid_profile = {"age": 25}
validate_user_profile(valid_profile)
print("PASS: Valid age accepted")


invalid_profile = {"age": 0}
try:
    validate_user_profile(invalid_profile)
except ValueError as error:
    if "greater than 0" in str(error):
        print("PASS: Zero age rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Zero age was not rejected")


invalid_profile = {"age": "25"}
try:
    validate_user_profile(invalid_profile)
except ValueError as error:
    if "integer" in str(error):
        print("PASS: Non-integer age rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Non-integer age was not rejected")

valid_profile = {
    "height_cm": 175.5,
    "weight_kg": 75.0,
    "training_days_per_week": 4,
    "session_duration_minutes": 60
}

validate_user_profile(valid_profile)
print("PASS: Valid numeric profile values accepted")


invalid_profile = {"height_cm": -175}

try:
    validate_user_profile(invalid_profile)
except ValueError as error:
    if "Height must be greater than 0" in str(error):
        print("PASS: Invalid height rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Invalid height was not rejected")


invalid_profile = {"weight_kg": 0}

try:
    validate_user_profile(invalid_profile)
except ValueError as error:
    if "Weight must be greater than 0" in str(error):
        print("PASS: Invalid weight rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Invalid weight was not rejected")


invalid_profile = {"training_days_per_week": 8}

try:
    validate_user_profile(invalid_profile)
except ValueError as error:
    if "Training days must be between 0 and 7" in str(error):
        print("PASS: Invalid training days rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Invalid training days were not rejected")


invalid_profile = {"session_duration_minutes": 0}

try:
    validate_user_profile(invalid_profile)
except ValueError as error:
    if "Session duration must be greater than 0" in str(error):
        print("PASS: Invalid session duration rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Invalid session duration was not rejected")


valid_profile = {
    "fitness_level": "Intermediate",
    "primary_goal": "Strength",
    "preferred_environment": "Gym"
}

validate_user_profile(valid_profile)
print("PASS: Valid categorical profile values accepted")


invalid_profile = {"fitness_level": "Expert"}

try:
    validate_user_profile(invalid_profile)
except ValueError as error:
    if "Invalid fitness level" in str(error):
        print("PASS: Invalid fitness level rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Invalid fitness level was not rejected")


invalid_profile = {"primary_goal": "Become Huge"}

try:
    validate_user_profile(invalid_profile)
except ValueError as error:
    if "Invalid primary goal" in str(error):
        print("PASS: Invalid primary goal rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Invalid primary goal was not rejected")


invalid_profile = {"preferred_environment": "Outside"}

try:
    validate_user_profile(invalid_profile)
except ValueError as error:
    if "Invalid preferred environment" in str(error):
        print("PASS: Invalid preferred environment rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Invalid preferred environment was not rejected")

valid_profile = {"sex": "Female"}

validate_user_profile(valid_profile)
print("PASS: Valid sex value accepted")


invalid_profile = {"sex": "Unknown Value"}

try:
    validate_user_profile(invalid_profile)
except ValueError as error:
    if "Invalid sex value" in str(error):
        print("PASS: Invalid sex value rejected")
    else:
        raise
else:
    raise ValueError("FAIL: Invalid sex value was not rejected")