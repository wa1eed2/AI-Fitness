def validate_user_equipment(equipment, access_status):
    valid_equipment = [
        "Bodyweight",
        "Dumbbell",
        "Barbell",
        "Kettlebell",
        "Resistance Band",
        "Cable Machine",
        "Smith Machine",
        "Pull-Up Bar",
        "Bench",
        "Treadmill",
        "Stationary Bike",
        "Rowing Machine",
        "Other"
    ]

    valid_access_statuses = [
        "Available",
        "Unavailable"
    ]

    if equipment not in valid_equipment:
        raise ValueError(f"Invalid equipment: {equipment}")

    if access_status not in valid_access_statuses:
        raise ValueError(f"Invalid access status: {access_status}")