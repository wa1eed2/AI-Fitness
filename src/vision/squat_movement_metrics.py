import copy
import math
from numbers import Real

from src.vision.pose_geometry import (
    calculate_angle_degrees,
    validate_landmark
)

from src.vision.squat_analysis import (
    MIN_REQUIRED_VISIBILITY,
    SIDE_LEFT,
    SIDE_RIGHT,
    calculate_side_visibility,
    get_side_landmarks,
    select_best_visible_side
)


VIEW_BILATERAL_OBSERVABLE = "bilateral_observable"
VIEW_SINGLE_SIDE_OBSERVABLE = "single_side_observable"
VIEW_INSUFFICIENT = "insufficient_landmarks"


REP_CONFIDENCE_HIGH = "high"
REP_CONFIDENCE_MODERATE = "moderate"
REP_CONFIDENCE_LOW = "low"
REP_CONFIDENCE_UNAVAILABLE = "unavailable"


HIGH_REP_CONFIDENCE_THRESHOLD = 0.85
MODERATE_REP_CONFIDENCE_THRESHOLD = 0.70


def validate_numeric(
    value,
    field_name
):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field_name} must be numeric")

    normalized = float(
        value
    )

    if not math.isfinite(
        normalized
    ):
        raise ValueError(f"{field_name} must be finite")

    return normalized


def validate_probability(
    value,
    field_name
):
    normalized = validate_numeric(
        value,
        field_name
    )

    if normalized < 0 or normalized > 1:
        raise ValueError(f"{field_name} must be between 0 and 1")

    return normalized


def calculate_trunk_inclination_degrees(
    shoulder,
    hip
):
    shoulder = validate_landmark(
        shoulder,
        "shoulder"
    )

    hip = validate_landmark(
        hip,
        "hip"
    )

    delta_x = (
        shoulder[
            "x"
        ]
        - hip[
            "x"
        ]
    )

    delta_y = (
        shoulder[
            "y"
        ]
        - hip[
            "y"
        ]
    )

    if delta_x == 0 and delta_y == 0:
        raise ValueError(
            "Cannot calculate trunk inclination from overlapping landmarks"
        )

    inclination = math.degrees(
        math.atan2(
            abs(
                delta_x
            ),
            abs(
                delta_y
            )
        )
    )

    return round(
        inclination,
        2
    )


def analyze_side_geometry(
    pose_landmarks,
    side,
    minimum_visibility=MIN_REQUIRED_VISIBILITY
):
    minimum_visibility = validate_probability(
        minimum_visibility,
        "minimum_visibility"
    )

    side_landmarks = get_side_landmarks(
        pose_landmarks,
        side
    )

    if side_landmarks is None:
        return {
            "side": side,
            "available": False,
            "visibility": None,
            "measurements": {}
        }

    visibility = calculate_side_visibility(
        side_landmarks
    )

    if visibility < minimum_visibility:
        return {
            "side": side,
            "available": False,
            "visibility": visibility,
            "measurements": {}
        }

    knee_angle = calculate_angle_degrees(
        side_landmarks[
            "hip"
        ],
        side_landmarks[
            "knee"
        ],
        side_landmarks[
            "ankle"
        ]
    )

    hip_angle = calculate_angle_degrees(
        side_landmarks[
            "shoulder"
        ],
        side_landmarks[
            "hip"
        ],
        side_landmarks[
            "knee"
        ]
    )

    trunk_inclination = calculate_trunk_inclination_degrees(
        side_landmarks[
            "shoulder"
        ],
        side_landmarks[
            "hip"
        ]
    )

    return {
        "side": side,
        "available": True,
        "visibility": visibility,
        "measurements": {
            "knee_angle_degrees": knee_angle,
            "hip_angle_degrees": hip_angle,
            "trunk_inclination_degrees": trunk_inclination
        }
    }


def classify_view_suitability(
    left_analysis,
    right_analysis
):
    left_available = (
        left_analysis[
            "available"
        ]
        is True
    )

    right_available = (
        right_analysis[
            "available"
        ]
        is True
    )

    if left_available and right_available:
        return VIEW_BILATERAL_OBSERVABLE

    if left_available or right_available:
        return VIEW_SINGLE_SIDE_OBSERVABLE

    return VIEW_INSUFFICIENT


def calculate_bilateral_difference(
    left_analysis,
    right_analysis,
    measurement_name
):
    if not left_analysis[
        "available"
    ]:
        return None

    if not right_analysis[
        "available"
    ]:
        return None

    left_value = left_analysis[
        "measurements"
    ][
        measurement_name
    ]

    right_value = right_analysis[
        "measurements"
    ][
        measurement_name
    ]

    return round(
        abs(
            left_value
            - right_value
        ),
        2
    )


def build_frame_observations(
    view_suitability,
    bilateral_differences
):
    observations = []

    if view_suitability == VIEW_BILATERAL_OBSERVABLE:
        observations.append(
            "Both left and right landmark sets are sufficiently visible in this frame."
        )

    elif view_suitability == VIEW_SINGLE_SIDE_OBSERVABLE:
        observations.append(
            "Only one complete side is sufficiently visible for geometric analysis in this frame."
        )

    else:
        observations.append(
            "Neither body side has sufficiently visible shoulder, hip, knee, and ankle landmarks."
        )

    knee_difference = bilateral_differences.get(
        "knee_angle_difference_degrees"
    )

    if knee_difference is not None:
        observations.append(
            (
                "The observed left-to-right knee-angle difference in this 2D frame "
                f"is {knee_difference} degrees."
            )
        )

    return observations


def analyze_bilateral_squat_frame(
    pose_landmarks,
    minimum_visibility=MIN_REQUIRED_VISIBILITY
):
    if not isinstance(pose_landmarks, dict):
        raise ValueError(
            "pose_landmarks must be a dictionary"
        )

    left_analysis = analyze_side_geometry(
        pose_landmarks,
        SIDE_LEFT,
        minimum_visibility=minimum_visibility
    )

    right_analysis = analyze_side_geometry(
        pose_landmarks,
        SIDE_RIGHT,
        minimum_visibility=minimum_visibility
    )

    view_suitability = classify_view_suitability(
        left_analysis,
        right_analysis
    )

    selected = select_best_visible_side(
        pose_landmarks,
        minimum_visibility=minimum_visibility
    )

    bilateral_differences = {
        "knee_angle_difference_degrees": calculate_bilateral_difference(
            left_analysis,
            right_analysis,
            "knee_angle_degrees"
        ),
        "hip_angle_difference_degrees": calculate_bilateral_difference(
            left_analysis,
            right_analysis,
            "hip_angle_degrees"
        ),
        "trunk_inclination_difference_degrees": calculate_bilateral_difference(
            left_analysis,
            right_analysis,
            "trunk_inclination_degrees"
        )
    }

    return {
        "exercise": "squat",
        "view_suitability": view_suitability,
        "selected_side": (
            selected[
                "side"
            ]
            if selected is not None
            else None
        ),
        "left": left_analysis,
        "right": right_analysis,
        "bilateral_differences": bilateral_differences,
        "observations": build_frame_observations(
            view_suitability,
            bilateral_differences
        ),
        "limitations": [
            (
                "Left-to-right differences describe projected 2D landmark geometry "
                "and are not evidence of structural asymmetry."
            ),
            (
                "Camera position, perspective, occlusion, clothing, and landmark "
                "estimation error can change apparent bilateral measurements."
            ),
            (
                "These measurements do not determine whether an injury or medical "
                "condition is present."
            )
        ]
    }


def classify_rep_confidence(
    mean_confidence
):
    if mean_confidence is None:
        return REP_CONFIDENCE_UNAVAILABLE

    confidence = validate_probability(
        mean_confidence,
        "mean_confidence"
    )

    if confidence >= HIGH_REP_CONFIDENCE_THRESHOLD:
        return REP_CONFIDENCE_HIGH

    if confidence >= MODERATE_REP_CONFIDENCE_THRESHOLD:
        return REP_CONFIDENCE_MODERATE

    return REP_CONFIDENCE_LOW


def enrich_repetitions_with_confidence(
    sequence_result
):
    if not isinstance(sequence_result, dict):
        raise ValueError(
            "sequence_result must be a dictionary"
        )

    repetitions = sequence_result.get(
        "repetitions"
    )

    if not isinstance(repetitions, list):
        raise ValueError(
            "sequence_result requires repetitions list"
        )

    enriched = copy.deepcopy(
        sequence_result
    )

    confidence_counts = {
        REP_CONFIDENCE_HIGH: 0,
        REP_CONFIDENCE_MODERATE: 0,
        REP_CONFIDENCE_LOW: 0,
        REP_CONFIDENCE_UNAVAILABLE: 0
    }

    available_confidences = []

    for repetition in enriched[
        "repetitions"
    ]:
        if not isinstance(repetition, dict):
            raise ValueError(
                "Each repetition must be a dictionary"
            )

        mean_confidence = repetition.get(
            "mean_confidence"
        )

        classification = classify_rep_confidence(
            mean_confidence
        )

        repetition[
            "confidence_classification"
        ] = classification

        confidence_counts[
            classification
        ] += 1

        if mean_confidence is not None:
            available_confidences.append(
                validate_probability(
                    mean_confidence,
                    "mean_confidence"
                )
            )

    average_confidence = None

    if available_confidences:
        average_confidence = round(
            sum(
                available_confidences
            )
            / len(
                available_confidences
            ),
            4
        )

    enriched[
        "rep_confidence_summary"
    ] = {
        "average_rep_confidence": average_confidence,
        "high_confidence_rep_count": confidence_counts[
            REP_CONFIDENCE_HIGH
        ],
        "moderate_confidence_rep_count": confidence_counts[
            REP_CONFIDENCE_MODERATE
        ],
        "low_confidence_rep_count": confidence_counts[
            REP_CONFIDENCE_LOW
        ],
        "unavailable_confidence_rep_count": confidence_counts[
            REP_CONFIDENCE_UNAVAILABLE
        ]
    }

    return enriched


def average_optional_values(
    values
):
    available = [
        float(
            value
        )
        for value in values
        if value is not None
    ]

    if not available:
        return None

    return round(
        sum(
            available
        )
        / len(
            available
        ),
        3
    )


def summarize_bilateral_frame_metrics(
    frame_metrics
):
    if not isinstance(frame_metrics, list):
        raise ValueError(
            "frame_metrics must be a list"
        )

    bilateral_count = 0
    single_side_count = 0
    insufficient_count = 0

    knee_differences = []
    hip_differences = []
    trunk_differences = []
    selected_trunk_inclinations = []

    for metric in frame_metrics:
        if not isinstance(metric, dict):
            raise ValueError(
                "Each frame metric must be a dictionary"
            )

        suitability = metric.get(
            "view_suitability"
        )

        if suitability == VIEW_BILATERAL_OBSERVABLE:
            bilateral_count += 1

        elif suitability == VIEW_SINGLE_SIDE_OBSERVABLE:
            single_side_count += 1

        elif suitability == VIEW_INSUFFICIENT:
            insufficient_count += 1

        else:
            raise ValueError(
                "Frame metric contains invalid view_suitability"
            )

        differences = metric.get(
            "bilateral_differences",
            {}
        )

        knee_differences.append(
            differences.get(
                "knee_angle_difference_degrees"
            )
        )

        hip_differences.append(
            differences.get(
                "hip_angle_difference_degrees"
            )
        )

        trunk_differences.append(
            differences.get(
                "trunk_inclination_difference_degrees"
            )
        )

        selected_side = metric.get(
            "selected_side"
        )

        if selected_side in {
            SIDE_LEFT,
            SIDE_RIGHT
        }:
            selected_analysis = metric.get(
                selected_side
            )

            if (
                isinstance(
                    selected_analysis,
                    dict
                )
                and selected_analysis.get(
                    "available"
                )
            ):
                selected_trunk_inclinations.append(
                    selected_analysis[
                        "measurements"
                    ][
                        "trunk_inclination_degrees"
                    ]
                )

    return {
        "frame_count": len(
            frame_metrics
        ),
        "bilateral_observable_frame_count": bilateral_count,
        "single_side_observable_frame_count": single_side_count,
        "insufficient_landmark_frame_count": insufficient_count,
        "average_knee_angle_difference_degrees": average_optional_values(
            knee_differences
        ),
        "average_hip_angle_difference_degrees": average_optional_values(
            hip_differences
        ),
        "average_trunk_inclination_difference_degrees": average_optional_values(
            trunk_differences
        ),
        "average_selected_side_trunk_inclination_degrees": average_optional_values(
            selected_trunk_inclinations
        )
    }