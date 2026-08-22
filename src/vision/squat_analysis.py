from src.vision.pose_geometry import (
    calculate_angle_degrees,
    calculate_landmark_visibility,
    validate_landmark
)


ANALYSIS_STATUS_ANALYZABLE = "analyzable"
ANALYSIS_STATUS_INSUFFICIENT_LANDMARKS = "insufficient_landmarks"


SIDE_LEFT = "left"
SIDE_RIGHT = "right"


MIN_REQUIRED_VISIBILITY = 0.60


KNEE_DEEP_FLEXION_MAX = 110.0
KNEE_MODERATE_FLEXION_MAX = 140.0


REQUIRED_JOINTS = (
    "shoulder",
    "hip",
    "knee",
    "ankle"
)


def validate_pose_landmarks(
    pose_landmarks
):
    if not isinstance(pose_landmarks, dict):
        raise ValueError("pose_landmarks must be a dictionary")

    return pose_landmarks


def get_side_landmarks(
    pose_landmarks,
    side
):
    validate_pose_landmarks(
        pose_landmarks
    )

    if side not in {
        SIDE_LEFT,
        SIDE_RIGHT
    }:
        raise ValueError("side must be left or right")

    landmarks = {}

    for joint in REQUIRED_JOINTS:
        key = f"{side}_{joint}"

        landmark = pose_landmarks.get(
            key
        )

        if landmark is None:
            return None

        landmarks[
            joint
        ] = validate_landmark(
            landmark,
            key
        )

    return landmarks


def calculate_side_visibility(
    side_landmarks
):
    if side_landmarks is None:
        return None

    return calculate_landmark_visibility(
        [
            side_landmarks[
                joint
            ]
            for joint in REQUIRED_JOINTS
        ]
    )


def select_best_visible_side(
    pose_landmarks,
    minimum_visibility=MIN_REQUIRED_VISIBILITY
):
    if isinstance(minimum_visibility, bool) or not isinstance(minimum_visibility, (int, float)):
        raise ValueError("minimum_visibility must be numeric")

    if minimum_visibility < 0 or minimum_visibility > 1:
        raise ValueError("minimum_visibility must be between 0 and 1")

    left_landmarks = get_side_landmarks(
        pose_landmarks,
        SIDE_LEFT
    )

    right_landmarks = get_side_landmarks(
        pose_landmarks,
        SIDE_RIGHT
    )

    left_visibility = calculate_side_visibility(
        left_landmarks
    )

    right_visibility = calculate_side_visibility(
        right_landmarks
    )

    candidates = []

    if (
        left_landmarks is not None
        and left_visibility is not None
        and left_visibility >= minimum_visibility
    ):
        candidates.append(
            (
                SIDE_LEFT,
                left_landmarks,
                left_visibility
            )
        )

    if (
        right_landmarks is not None
        and right_visibility is not None
        and right_visibility >= minimum_visibility
    ):
        candidates.append(
            (
                SIDE_RIGHT,
                right_landmarks,
                right_visibility
            )
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda candidate: (
            candidate[
                2
            ],
            candidate[
                0
            ] == SIDE_LEFT
        ),
        reverse=True
    )

    side, landmarks, visibility = candidates[
        0
    ]

    return {
        "side": side,
        "landmarks": landmarks,
        "visibility": visibility
    }


def classify_knee_flexion_angle(
    knee_angle_degrees
):
    if isinstance(knee_angle_degrees, bool) or not isinstance(knee_angle_degrees, (int, float)):
        raise ValueError("knee_angle_degrees must be numeric")

    if knee_angle_degrees < 0 or knee_angle_degrees > 180:
        raise ValueError("knee_angle_degrees must be between 0 and 180")

    if knee_angle_degrees <= KNEE_DEEP_FLEXION_MAX:
        return "deep_flexion"

    if knee_angle_degrees <= KNEE_MODERATE_FLEXION_MAX:
        return "moderate_flexion"

    return "standing_or_shallow_flexion"


def build_observation_notes(
    knee_classification
):
    if knee_classification == "deep_flexion":
        return [
            (
                "This frame shows substantial knee flexion on the selected visible "
                "side."
            ),
            (
                "A single 2D frame cannot determine whether squat depth or technique "
                "is appropriate for this individual."
            )
        ]

    if knee_classification == "moderate_flexion":
        return [
            (
                "This frame shows moderate knee flexion on the selected visible side."
            ),
            (
                "Movement phase, camera angle, anatomy, and exercise variation can "
                "change the observed angle."
            )
        ]

    return [
        (
            "This frame shows relatively little knee flexion on the selected visible "
            "side."
        ),
        (
            "A single frame cannot establish whether this represents the beginning, "
            "end, or full depth of a squat repetition."
        )
    ]


def analyze_squat_frame(
    pose_landmarks,
    minimum_visibility=MIN_REQUIRED_VISIBILITY
):
    selected = select_best_visible_side(
        pose_landmarks,
        minimum_visibility=minimum_visibility
    )

    if selected is None:
        return {
            "status": ANALYSIS_STATUS_INSUFFICIENT_LANDMARKS,
            "exercise": "squat",
            "selected_side": None,
            "confidence": None,
            "measurements": {},
            "observations": [
                (
                    "There are not enough sufficiently visible shoulder, hip, knee, "
                    "and ankle landmarks on one side to analyze this frame."
                )
            ],
            "limitations": [
                (
                    "No movement-quality conclusion was generated from insufficient "
                    "landmark data."
                )
            ]
        }

    landmarks = selected[
        "landmarks"
    ]

    knee_angle = calculate_angle_degrees(
        landmarks[
            "hip"
        ],
        landmarks[
            "knee"
        ],
        landmarks[
            "ankle"
        ]
    )

    hip_angle = calculate_angle_degrees(
        landmarks[
            "shoulder"
        ],
        landmarks[
            "hip"
        ],
        landmarks[
            "knee"
        ]
    )

    knee_classification = classify_knee_flexion_angle(
        knee_angle
    )

    return {
        "status": ANALYSIS_STATUS_ANALYZABLE,
        "exercise": "squat",
        "selected_side": selected[
            "side"
        ],
        "confidence": selected[
            "visibility"
        ],
        "measurements": {
            "knee_angle_degrees": knee_angle,
            "hip_angle_degrees": hip_angle,
            "knee_flexion_classification": knee_classification
        },
        "observations": build_observation_notes(
            knee_classification
        ),
        "limitations": [
            (
                "This is a geometric observation from one 2D frame and is not a "
                "medical assessment. It cannot determine whether an injury or "
                "medical condition is present."
            ),
            (
                "Camera position, lens perspective, landmark-estimation error, body "
                "proportions, exercise variation, and movement phase can affect the "
                "measured angles."
            ),
            (
                "Temporal repetition analysis is required before making conclusions "
                "about movement consistency."
            )
        ]
    }