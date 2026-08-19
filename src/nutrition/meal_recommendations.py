from src.database.query_user_database import (
    get_safe_foods_for_user,
    get_user_nutrition_target
)


def recommend_foods_for_user(
        user_id,
        min_protein_g=None,
        max_calories=None
):
    foods = get_safe_foods_for_user(user_id)

    recommendations = []

    for food in foods:
        if (
                min_protein_g is not None
                and food["protein_g"] < min_protein_g
        ):
            continue

        if (
                max_calories is not None
                and food["calories"] > max_calories
        ):
            continue

        recommendations.append(food)

    # Primary ranking:
    # higher protein first
    #
    # Secondary ranking:
    # lower calories first
    recommendations.sort(key=lambda food: (-food["protein_g"], food["calories"]))

    return recommendations

def calculate_macro_score(
    food,
    remaining_protein,
    remaining_carbs,
    remaining_fat,
    protein_weight=1.0,
    carb_weight=1.0,
    fat_weight=1.0
):
    score = 0

    if remaining_protein > 0:
        score += (min(food["protein_g"], remaining_protein) / remaining_protein * protein_weight)

    if remaining_carbs is not None and remaining_carbs > 0:
        score += (min(food["carbs_g"], remaining_carbs) / remaining_carbs * carb_weight)

    if remaining_fat is not None and remaining_fat > 0:
        score += (min(food["fat_g"], remaining_fat) / remaining_fat * fat_weight)

    return score

def rank_foods_by_macros(
    foods,
    remaining_protein,
    remaining_carbs,
    remaining_fat,
    protein_weight=1.0,
    carb_weight=1.0,
    fat_weight=1.0
):
    return sorted(
        foods,
        key=lambda food: calculate_macro_score(
            food,
            remaining_protein,
            remaining_carbs,
            remaining_fat,
            protein_weight=protein_weight,
            carb_weight=carb_weight,
            fat_weight=fat_weight
        ),
        reverse=True
    )


def build_meal_recommendation(
    user_id,
    target_calories,
    target_protein_g,
    target_carbs_g=None,
    target_fat_g=None,
    protein_weight=1.0,
    carb_weight=1.0,
    fat_weight=1.0
):
    # ========================================================
    # VALIDATION
    # ========================================================

    weights = {
        "Protein weight": protein_weight,
        "Carb weight": carb_weight,
        "Fat weight": fat_weight
    }

    for name, value in weights.items():
        if not isinstance(value, (int, float)):
            raise ValueError(
                f"{name} must be a number"
            )

        if value < 0:
            raise ValueError(
                f"{name} cannot be negative"
            )

    if not isinstance(
            target_calories,
            (int, float)
    ):
        raise ValueError(
            "Target calories must be a number"
        )

    if target_calories <= 0:
        raise ValueError(
            "Target calories must be greater than 0"
        )

    if not isinstance(
            target_protein_g,
            (int, float)
    ):
        raise ValueError(
            "Target protein must be a number"
        )

    if target_protein_g <= 0:
        raise ValueError(
            "Target protein must be greater than 0"
        )

    if target_carbs_g is not None:
        if not isinstance(target_carbs_g, (int, float)):
            raise ValueError(
                "Target carbohydrates must be a number"
            )

        if target_carbs_g < 0:
            raise ValueError(
                "Target carbohydrates cannot be negative"
            )

    if target_fat_g is not None:
        if not isinstance(target_fat_g, (int, float)):
            raise ValueError(
                "Target fat must be a number"
            )

        if target_fat_g < 0:
            raise ValueError(
                "Target fat cannot be negative"
            )

    # ========================================================
    # GET SAFE FOODS
    # ========================================================

    # Allergy filtering happens inside
    # get_safe_foods_for_user().
    #
    # This means unsafe foods are removed before
    # recommendation logic begins.
    foods = recommend_foods_for_user(
        user_id=user_id,
        max_calories=target_calories
    )

    selected_foods = []

    total_calories = 0.0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0

    # Current project rule:
    # reaching 80% of requested calories counts
    # as reaching the meal calorie target.
    minimum_calories = (target_calories * 0.8)

    # ========================================================
    # PHASE 1
    # REACH THE PROTEIN TARGET WITH DYNAMIC RE-RANKING
    # ========================================================

    remaining_foods = foods.copy()

    while remaining_foods:
        remaining_protein = (target_protein_g - total_protein)

        remaining_carbs = (max(target_carbs_g - total_carbs, 0) if target_carbs_g is not None else None)

        remaining_fat = (max(target_fat_g - total_fat, 0) if target_fat_g is not None else None)

        remaining_calories = (target_calories - total_calories)

        if remaining_protein <= 0:
            break

        if remaining_calories <= 0:
            break

        ranked_foods = rank_foods_by_macros(
            remaining_foods,
            remaining_protein,
            remaining_carbs,
            remaining_fat,
            protein_weight=protein_weight,
            carb_weight=carb_weight,
            fat_weight=fat_weight
        )

        food = ranked_foods[0]

        # Remove it so Phase 1 does not select
        # the same food again.
        remaining_foods.remove(food)

        if food["protein_g"] <= 0:
            continue

        servings_for_protein = (remaining_protein / food["protein_g"])

        if food["calories"] > 0:
            max_servings_for_calories = (remaining_calories / food["calories"])
        else:
            max_servings_for_calories = (servings_for_protein)

        servings = min(servings_for_protein, max_servings_for_calories)

        if servings <= 0:
            continue

        calories_added = (food["calories"] * servings)

        protein_added = (food["protein_g"] * servings)

        carbs_added = (food["carbs_g"] * servings)

        fat_added = (food["fat_g"] * servings)

        selected_food = food.copy()

        selected_food["servings"] = round(servings, 4)

        selected_foods.append(selected_food)

        total_calories += calories_added
        total_protein += protein_added
        total_carbs += carbs_added
        total_fat += fat_added

    # ========================================================
    # PHASE 2
    # FILL THE CALORIE TARGET
    # ========================================================

    if total_calories < minimum_calories:
        remaining_foods = foods.copy()

        while (total_calories < minimum_calories and remaining_foods):
            remaining_carbs = (max(target_carbs_g - total_carbs, 0) if target_carbs_g is not None else None)

            remaining_fat = (max(target_fat_g - total_fat, 0) if target_fat_g is not None
                else None
            )

            remaining_calories = (target_calories - total_calories)

            if remaining_calories <= 0:
                break

            ranked_foods = rank_foods_by_macros(
                remaining_foods,
                remaining_protein=0,
                remaining_carbs=remaining_carbs,
                remaining_fat=remaining_fat,
                protein_weight=protein_weight,
                carb_weight=carb_weight,
                fat_weight=fat_weight
            )

            food = ranked_foods[0]
            remaining_foods.remove(food)

            if food["calories"] <= 0:
                continue

            remaining_to_minimum = (minimum_calories - total_calories)

            servings_needed = (remaining_to_minimum / food["calories"])

            max_servings = (remaining_calories / food["calories"])

            servings = min(servings_needed, max_servings)

            if servings <= 0:
                continue

            calories_added = (food["calories"] * servings)

            protein_added = (food["protein_g"] * servings)

            carbs_added = (food["carbs_g"] * servings)

            fat_added = (food["fat_g"] * servings)

            existing_food = next(
                (
                    selected
                    for selected in selected_foods
                    if selected["food_id"]
                       == food["food_id"]
                ),
                None
            )

            if existing_food is not None:
                existing_food["servings"] = round(existing_food["servings"] + servings, 4)

            else:
                selected_food = food.copy()

                selected_food["servings"] = round(servings, 4)

                selected_foods.append(selected_food)

            total_calories += calories_added
            total_protein += protein_added
            total_carbs += carbs_added
            total_fat += fat_added

    # ========================================================
    # TARGET STATUS
    # ========================================================

    protein_target_met = (total_protein >= target_protein_g)

    calorie_target_met = (minimum_calories <= total_calories <= target_calories)

    carb_target_met = (target_carbs_g is None or total_carbs >= target_carbs_g)

    fat_target_met = (target_fat_g is None or total_fat >= target_fat_g)

    # ========================================================
    # RESULT
    # ========================================================

    return {
        "foods": selected_foods,
        "total_calories": round(total_calories, 2),
        "total_protein_g": round(total_protein, 2),
        "total_carbs_g": round(total_carbs, 2),
        "total_fat_g": round(total_fat, 2),
        "protein_target_met": protein_target_met,
        "calorie_target_met": calorie_target_met,
        "carb_target_met": carb_target_met,
        "fat_target_met": fat_target_met

    }

def build_meal_from_user_target(
    user_id,
    meal_fraction=0.25
):
    if (
            isinstance(meal_fraction, bool)
            or not isinstance(meal_fraction, (int, float))
    ):
        raise ValueError("Meal fraction must be a number")

    if not 0 < meal_fraction <= 1:
        raise ValueError("Meal fraction must be greater than 0 and at most 1")

    nutrition_target = get_user_nutrition_target(
        user_id
    )

    if nutrition_target is None:
        raise ValueError(
            "User nutrition target not found"
        )

    meal_calories = (nutrition_target["calorie_target"] * meal_fraction)

    meal_protein_g = (nutrition_target["protein_g"] * meal_fraction)

    meal_carbs_g = (nutrition_target["carbs_g"] * meal_fraction)

    meal_fat_g = (nutrition_target["fat_g"] * meal_fraction)

    return build_meal_recommendation(
        user_id=user_id,
        target_calories=meal_calories,
        target_protein_g=meal_protein_g,
        target_carbs_g=meal_carbs_g,
        target_fat_g=meal_fat_g
    )