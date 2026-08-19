def validate_food_allergy(allergen, notes=None):
    valid_allergens = [
        "Peanuts",
        "Tree Nuts",
        "Milk",
        "Eggs",
        "Wheat",
        "Soy",
        "Fish",
        "Shellfish",
        "Sesame",
        "Other"
    ]

    if allergen not in valid_allergens:
        raise ValueError(f"Invalid allergen: {allergen}")

    if notes is not None and not isinstance(notes, str):
        raise ValueError("Notes must be a string")