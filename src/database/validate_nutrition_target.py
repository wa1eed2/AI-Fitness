def validate_nutrition_target(target):
    valid_activity_levels = [
        "Sedentary",
        "Lightly Active",
        "Moderately Active",
        "Very Active",
        "Extra Active"
    ]

    valid_nutrition_goals = [
        "Fat Loss",
        "Maintenance",
        "Muscle Gain"
    ]

    activity_level = target.get("activity_level")

    if activity_level not in valid_activity_levels:
        raise ValueError(
            f"Invalid activity level: {activity_level}"
        )

    nutrition_goal = target.get("nutrition_goal")

    if nutrition_goal not in valid_nutrition_goals:
        raise ValueError(
            f"Invalid nutrition goal: {nutrition_goal}"
        )

    bmr = target.get("bmr")

    if not isinstance(bmr, (int, float)):
        raise ValueError("BMR must be a number")

    if bmr <= 0:
        raise ValueError("BMR must be greater than 0")

    tdee = target.get("tdee")

    if not isinstance(tdee, (int, float)):
        raise ValueError("TDEE must be a number")

    if tdee <= 0:
        raise ValueError("TDEE must be greater than 0")

    calorie_target = target.get("calorie_target")

    if not isinstance(calorie_target, (int, float)):
        raise ValueError("Calorie target must be a number")

    if calorie_target <= 0:
        raise ValueError(
            "Calorie target must be greater than 0"
        )

    protein_g = target.get("protein_g")

    if not isinstance(protein_g, (int, float)):
        raise ValueError("Protein must be a number")

    if protein_g <= 0:
        raise ValueError(
            "Protein must be greater than 0"
        )

    fat_g = target.get("fat_g")

    if not isinstance(fat_g, (int, float)):
        raise ValueError("Fat must be a number")

    if fat_g <= 0:
        raise ValueError(
            "Fat must be greater than 0"
        )

    carbs_g = target.get("carbs_g")

    if not isinstance(carbs_g, (int, float)):
        raise ValueError("Carbohydrates must be a number")

    if carbs_g < 0:
        raise ValueError(
            "Carbohydrates cannot be negative"
        )


def validate_nutrition_target_update(target):
    valid_activity_levels = [
        "Sedentary",
        "Lightly Active",
        "Moderately Active",
        "Very Active",
        "Extra Active"
    ]

    valid_nutrition_goals = [
        "Fat Loss",
        "Maintenance",
        "Muscle Gain"
    ]

    if "activity_level" in target:
        if target["activity_level"] not in valid_activity_levels:
            raise ValueError(
                f"Invalid activity level: {target['activity_level']}"
            )

    if "nutrition_goal" in target:
        if target["nutrition_goal"] not in valid_nutrition_goals:
            raise ValueError(
                f"Invalid nutrition goal: {target['nutrition_goal']}"
            )

    positive_fields = [
        "bmr",
        "tdee",
        "calorie_target",
        "protein_g",
        "fat_g"
    ]

    for field in positive_fields:
        if field in target:
            value = target[field]

            if not isinstance(value, (int, float)):
                raise ValueError(f"{field} must be a number")

            if value <= 0:
                raise ValueError(f"{field} must be greater than 0")

    if "carbs_g" in target:
        carbs_g = target["carbs_g"]

        if not isinstance(carbs_g, (int, float)):
            raise ValueError("carbs_g must be a number")

        if carbs_g < 0:
            raise ValueError("carbs_g cannot be negative")