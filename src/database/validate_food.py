def validate_food(
    name,
    serving_size_g,
    calories,
    protein_g,
    carbs_g,
    fat_g
):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Food name must be a non-empty string")

    if not isinstance(serving_size_g, (int, float)):
        raise ValueError("Serving size must be a number")

    if serving_size_g <= 0:
        raise ValueError("Serving size must be greater than 0")

    nutrient_values = {
        "Calories": calories,
        "Protein": protein_g,
        "Carbohydrates": carbs_g,
        "Fat": fat_g
    }

    for nutrient, value in nutrient_values.items():
        if not isinstance(value, (int, float)):
            raise ValueError(f"{nutrient} must be a number")

        if value < 0:
            raise ValueError(f"{nutrient} cannot be negative")