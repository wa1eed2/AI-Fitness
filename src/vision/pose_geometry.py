import math


DEFAULT_VISIBILITY = 1.0


def validate_numeric(
    value,
    field_name
):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric")

    if not math.isfinite(
        float(
            value
        )
    ):
        raise ValueError(f"{field_name} must be finite")

    return float(
        value
    )


def validate_landmark(
    landmark,
    field_name="landmark"
):
    if not isinstance(landmark, dict):
        raise ValueError(f"{field_name} must be a dictionary")

    if "x" not in landmark or "y" not in landmark:
        raise ValueError(f"{field_name} requires x and y coordinates")

    x = validate_numeric(
        landmark[
            "x"
        ],
        f"{field_name}.x"
    )

    y = validate_numeric(
        landmark[
            "y"
        ],
        f"{field_name}.y"
    )

    visibility = landmark.get(
        "visibility",
        DEFAULT_VISIBILITY
    )

    visibility = validate_numeric(
        visibility,
        f"{field_name}.visibility"
    )

    if visibility < 0 or visibility > 1:
        raise ValueError(f"{field_name}.visibility must be between 0 and 1")

    return {
        "x": x,
        "y": y,
        "visibility": visibility
    }


def calculate_distance(
    first,
    second
):
    first = validate_landmark(
        first,
        "first"
    )

    second = validate_landmark(
        second,
        "second"
    )

    delta_x = (
        second[
            "x"
        ]
        - first[
            "x"
        ]
    )

    delta_y = (
        second[
            "y"
        ]
        - first[
            "y"
        ]
    )

    return math.sqrt(
        delta_x ** 2
        + delta_y ** 2
    )


def calculate_angle_degrees(
    first,
    vertex,
    third
):
    first = validate_landmark(
        first,
        "first"
    )

    vertex = validate_landmark(
        vertex,
        "vertex"
    )

    third = validate_landmark(
        third,
        "third"
    )

    vector_a = (
        first[
            "x"
        ]
        - vertex[
            "x"
        ],
        first[
            "y"
        ]
        - vertex[
            "y"
        ]
    )

    vector_b = (
        third[
            "x"
        ]
        - vertex[
            "x"
        ],
        third[
            "y"
        ]
        - vertex[
            "y"
        ]
    )

    magnitude_a = math.sqrt(
        vector_a[
            0
        ] ** 2
        + vector_a[
            1
        ] ** 2
    )

    magnitude_b = math.sqrt(
        vector_b[
            0
        ] ** 2
        + vector_b[
            1
        ] ** 2
    )

    if magnitude_a == 0 or magnitude_b == 0:
        raise ValueError("Cannot calculate angle from overlapping landmarks")

    dot_product = (
        vector_a[
            0
        ]
        * vector_b[
            0
        ]
        + vector_a[
            1
        ]
        * vector_b[
            1
        ]
    )

    cosine = (
        dot_product
        / (
            magnitude_a
            * magnitude_b
        )
    )

    cosine = max(
        -1.0,
        min(
            1.0,
            cosine
        )
    )

    angle_radians = math.acos(
        cosine
    )

    return round(
        math.degrees(
            angle_radians
        ),
        2
    )


def calculate_landmark_visibility(
    landmarks
):
    if not isinstance(landmarks, list):
        raise ValueError("landmarks must be a list")

    if not landmarks:
        raise ValueError("landmarks cannot be empty")

    normalized_landmarks = [
        validate_landmark(
            landmark,
            f"landmarks[{index}]"
        )
        for index, landmark in enumerate(
            landmarks
        )
    ]

    return round(
        sum(
            landmark[
                "visibility"
            ]
            for landmark in normalized_landmarks
        )
        / len(
            normalized_landmarks
        ),
        4
    )