def validate_user_limitation(body_area, limitation_type, notes=None):
    valid_body_areas = [
        "Neck",
        "Shoulder",
        "Elbow",
        "Wrist",
        "Hand",
        "Upper Back",
        "Lower Back",
        "Hip",
        "Knee",
        "Ankle",
        "Foot",
        "Other"
    ]

    valid_limitation_types = [
        "Pain",
        "Limited ROM",
        "Injury History",
        "Medical Restriction",
        "Other"
    ]

    if body_area not in valid_body_areas:
        raise ValueError(f"Invalid body area: {body_area}")

    if limitation_type not in valid_limitation_types:
        raise ValueError(f"Invalid limitation type: {limitation_type}")

    if notes is not None and not isinstance(notes, str):
        raise ValueError("Notes must be a string")