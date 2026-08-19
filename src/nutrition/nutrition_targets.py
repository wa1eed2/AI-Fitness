from src.database.query_user_database import (
    get_user_profile,
    get_user_nutrition_target,
    create_user_nutrition_target,
    update_user_nutrition_target
)

from src.nutrition.calculations import (
    calculate_bmr,
    calculate_tdee,
    calculate_calorie_target,
    calculate_macros
)

def determine_activity_level(training_days_per_week):
    if training_days_per_week <= 1:
        return "Sedentary"

    if training_days_per_week <= 3:
        return "Lightly Active"

    if training_days_per_week <= 5:
        return "Moderately Active"

    if training_days_per_week == 6:
        return "Very Active"

    return "Extra Active"

def determine_nutrition_goal(primary_goal):
    if primary_goal == "Muscle Gain":
        return "Muscle Gain"

    if primary_goal == "Fat Loss":
        return "Fat Loss"

    return "Maintenance"

def generate_nutrition_target_for_user(
    user_id,
    nutrition_goal=None,
    activity_level=None,
    protein_g_per_kg=1.6,
    fat_percentage=0.25
):
    profile = get_user_profile(user_id)

    if profile is None:
        raise ValueError("User profile not found.")

    age = profile["age"]
    sex = profile["sex"]
    height_cm = profile["height_cm"]
    weight_kg = profile["weight_kg"]

    training_days_per_week = profile["training_days_per_week"]
    primary_goal = profile["primary_goal"]

    if activity_level is None:
        activity_level = determine_activity_level(training_days_per_week)

    if nutrition_goal is None:
        nutrition_goal = determine_nutrition_goal(primary_goal)

    bmr = calculate_bmr(
        weight_kg=weight_kg,
        height_cm=height_cm,
        age=age,
        sex=sex
    )

    tdee = calculate_tdee(bmr=bmr, activity_level=activity_level)
    calorie_target = calculate_calorie_target(tdee=tdee, goal=nutrition_goal)
    macros = calculate_macros(
        calorie_target=calorie_target,
        weight_kg=weight_kg,
        protein_g_per_kg=protein_g_per_kg,
        fat_percentage=fat_percentage
    )

    target = {
        "activity_level": activity_level,
        "nutrition_goal": nutrition_goal,
        "bmr": bmr,
        "tdee": tdee,
        "calorie_target": calorie_target,
        "protein_g": macros["protein_g"],
        "fat_g": macros["fat_g"],
        "carbs_g": macros["carbs_g"]
    }

    existing_target = get_user_nutrition_target(user_id)

    if existing_target is None:
        nutrition_target_id = create_user_nutrition_target(user_id, target)

    else:
        update_user_nutrition_target(user_id, target)

        nutrition_target_id = existing_target["nutrition_target_id"]


    return {
        "nutrition_target_id": nutrition_target_id,
        "target": target
    }