def calculate_bmi(weight_kg, height_cm):
    if weight_kg <= 0:
        raise ValueError("Weight must be greater than 0")

    if height_cm <= 0:
        raise ValueError("Height must be greater than 0")

    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)

    return bmi


def calculate_bmr(weight_kg, height_cm, age, sex):
    if weight_kg <= 0:
        raise ValueError("Weight must be greater than 0")

    if height_cm <= 0:
        raise ValueError("Height must be greater than 0")

    if age <= 0:
        raise ValueError("Age must be greater than 0")

    if sex == "Male":
        bmr = (10 * weight_kg + 6.25 * height_cm - 5 * age + 5)

    elif sex == "Female":
        bmr = (10 * weight_kg + 6.25 * height_cm - 5 * age - 161)

    else:
        raise ValueError("Sex must be 'Male' or 'Female' for BMR calculation")

    return bmr

def calculate_tdee(bmr, activity_level):
    if bmr <= 0:
        raise ValueError("BMR must be greater than 0")

    activity_factors = {
        "Sedentary": 1.2,
        "Lightly Active": 1.375,
        "Moderately Active": 1.55,
        "Very Active": 1.725,
        "Extra Active": 1.9
    }

    if activity_level not in activity_factors:
        raise ValueError(f"Invalid activity level: {activity_level}")

    activity_factor = activity_factors[activity_level]

    tdee = bmr * activity_factor

    return tdee

def calculate_calorie_target(tdee, goal):
    if tdee <= 0:
        raise ValueError("TDEE must be greater than 0")

    goal_multipliers = {
        "Fat Loss": 0.85,
        "Maintenance": 1.0,
        "Muscle Gain": 1.10
    }

    if goal not in goal_multipliers:
        raise ValueError(f"Invalid goal: {goal}")

    multiplier = goal_multipliers[goal]

    calorie_target = tdee * multiplier

    return calorie_target

def calculate_macros(calorie_target, weight_kg, protein_g_per_kg, fat_percentage):
    if calorie_target <= 0:
        raise ValueError("Calorie target must be greater than 0")

    if weight_kg <= 0:
        raise ValueError("Weight must be greater than 0")

    if protein_g_per_kg <= 0:
        raise ValueError("Protein per kg must be greater than 0")

    if not 0 < fat_percentage < 1:
        raise ValueError("Fat percentage must be between 0 and 1")

    protein_g = weight_kg * protein_g_per_kg
    protein_calories = protein_g * 4

    fat_calories = calorie_target * fat_percentage
    fat_g = fat_calories / 9

    remaining_calories = (calorie_target - protein_calories - fat_calories)

    if remaining_calories < 0:
        raise ValueError(
            "Protein and fat targets exceed calorie target"
        )

    carbs_g = remaining_calories / 4

    return {
        "protein_g": protein_g,
        "fat_g": fat_g,
        "carbs_g": carbs_g
    }