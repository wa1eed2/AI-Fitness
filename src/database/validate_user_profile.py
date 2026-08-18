def validate_user_profile(profile):
    age = profile.get("age")

    if age is not None:
        if not isinstance(age, int):
            raise ValueError("Age must be an integer")

        if age <= 0:
            raise ValueError("Age must be greater than 0")

    height_cm = profile.get("height_cm")
    if height_cm is not None:
        if not isinstance(height_cm, (int, float)):
            raise ValueError("Height must be an integer")

        if height_cm <= 0:
            raise ValueError("Height must be greater than 0")


    weight_kg = profile.get("weight_kg")
    if weight_kg is not None:
        if not isinstance(weight_kg, (int, float)):
            raise ValueError("Weight must be a number")

        if weight_kg <= 0:
            raise ValueError("Weight must be greater than 0")


    training_days = profile.get("training_days_per_week")
    if training_days is not None:
        if not isinstance(training_days, int):
            raise ValueError("Training days must be an integer")

        if not 0<= training_days <= 7:
            raise ValueError("Training days must be between 0 and 7")

    fitness_level = profile.get("fitness_level")
    valid_fitness_levels = ["Beginner", "Intermediate", "Advanced"]

    if fitness_level is not None and fitness_level not in valid_fitness_levels:
        raise ValueError(f"Invalid fitness level: {fitness_level}")

    primary_goal = profile.get("primary_goal")
    valid_primary_goals = ["Muscle Gain", "Fat loss", "Strength", "Endurance", "General Fitness"]
    if primary_goal is not None and primary_goal not in valid_primary_goals:
        raise ValueError(f"Invalid primary goal: {primary_goal}")

    preferred_environment = profile.get("preferred_environment")

    valid_environments = ["Home", "Gym", "Both"]

    if preferred_environment is not None and preferred_environment not in valid_environments:
        raise ValueError(f"Invalid preferred environment: {preferred_environment}")

    session_duration = profile.get("session_duration_minutes")
    if session_duration is not None:
        if not isinstance(session_duration, int):
            raise ValueError("Session duration must be an integer")

        if session_duration <= 0:
            raise ValueError("Session duration must be greater than 0")

    sex = profile.get("sex")

    valid_sex_values = [
        "Male",
        "Female",
        "Prefer not to say"
    ]

    if sex is not None and sex not in valid_sex_values:
        raise ValueError(f"Invalid sex value: {sex}")