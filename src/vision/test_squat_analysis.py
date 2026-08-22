from src.vision.squat_analysis import (
    ANALYSIS_STATUS_ANALYZABLE,
    ANALYSIS_STATUS_INSUFFICIENT_LANDMARKS,
    analyze_squat_frame,
    classify_knee_flexion_angle,
    select_best_visible_side
)


def landmark(
    x,
    y,
    visibility=1.0
):
    return {
        "x": x,
        "y": y,
        "visibility": visibility
    }


def standing_pose():
    return {
        "left_shoulder": landmark(
            0,
            0,
            0.9
        ),
        "left_hip": landmark(
            0,
            1,
            0.9
        ),
        "left_knee": landmark(
            0,
            2,
            0.9
        ),
        "left_ankle": landmark(
            0,
            3,
            0.9
        ),
        "right_shoulder": landmark(
            2,
            0,
            0.5
        ),
        "right_hip": landmark(
            2,
            1,
            0.5
        ),
        "right_knee": landmark(
            2,
            2,
            0.5
        ),
        "right_ankle": landmark(
            2,
            3,
            0.5
        )
    }


def deep_flexion_pose():
    return {
        "left_shoulder": landmark(
            0,
            0,
            0.95
        ),
        "left_hip": landmark(
            0,
            1,
            0.95
        ),
        "left_knee": landmark(
            1,
            1,
            0.95
        ),
        "left_ankle": landmark(
            1,
            2,
            0.95
        )
    }


def test_deep_flexion_classification():
    if classify_knee_flexion_angle(
        100
    ) != "deep_flexion":
        raise ValueError("FAIL: Deep knee flexion was classified incorrectly")

    print("PASS: Squat analyzer classifies substantial knee flexion")


def test_moderate_flexion_classification():
    if classify_knee_flexion_angle(
        125
    ) != "moderate_flexion":
        raise ValueError("FAIL: Moderate knee flexion was classified incorrectly")

    print("PASS: Squat analyzer classifies moderate knee flexion")


def test_shallow_flexion_classification():
    if classify_knee_flexion_angle(
        160
    ) != "standing_or_shallow_flexion":
        raise ValueError("FAIL: Shallow knee flexion was classified incorrectly")

    print("PASS: Squat analyzer classifies standing or shallow knee flexion")


def test_best_visible_side_is_selected():
    selected = select_best_visible_side(
        standing_pose()
    )

    if selected["side"] != "left":
        raise ValueError("FAIL: Squat analyzer did not choose most visible body side")

    print("PASS: Squat analyzer chooses the better-visible body side")


def test_low_visibility_pose_is_rejected():
    pose = standing_pose()

    for landmark_data in pose.values():
        landmark_data[
            "visibility"
        ] = 0.2

    result = analyze_squat_frame(
        pose
    )

    if result["status"] != ANALYSIS_STATUS_INSUFFICIENT_LANDMARKS:
        raise ValueError("FAIL: Low-confidence pose was treated as analyzable")

    print("PASS: Squat analyzer refuses low-confidence landmark data")


def test_missing_required_landmarks_are_rejected():
    result = analyze_squat_frame(
        {
            "left_hip": landmark(
                0,
                1
            ),
            "left_knee": landmark(
                1,
                1
            )
        }
    )

    if result["status"] != ANALYSIS_STATUS_INSUFFICIENT_LANDMARKS:
        raise ValueError("FAIL: Incomplete pose produced form analysis")

    print("PASS: Squat analyzer requires complete visible side landmarks")


def test_standing_pose_produces_straight_knee_measurement():
    result = analyze_squat_frame(
        standing_pose()
    )

    if result["status"] != ANALYSIS_STATUS_ANALYZABLE:
        raise ValueError("FAIL: Valid standing pose was not analyzable")

    if result["measurements"]["knee_angle_degrees"] != 180:
        raise ValueError(
            f"FAIL: Expected standing knee angle 180, got "
            f"{result['measurements']['knee_angle_degrees']}"
        )

    if result["measurements"]["knee_flexion_classification"] != "standing_or_shallow_flexion":
        raise ValueError("FAIL: Standing pose knee classification is incorrect")

    print("PASS: Squat analyzer extracts deterministic standing knee geometry")


def test_deep_pose_produces_observable_geometry_without_form_judgment():
    result = analyze_squat_frame(
        deep_flexion_pose()
    )

    if result["status"] != ANALYSIS_STATUS_ANALYZABLE:
        raise ValueError("FAIL: Valid squat pose was not analyzable")

    if result["measurements"]["knee_angle_degrees"] != 90:
        raise ValueError(
            f"FAIL: Expected knee angle 90, got "
            f"{result['measurements']['knee_angle_degrees']}"
        )

    if result["measurements"]["knee_flexion_classification"] != "deep_flexion":
        raise ValueError("FAIL: Deep squat geometry was classified incorrectly")

    combined_text = " ".join(
        result[
            "observations"
        ]
        + result[
            "limitations"
        ]
    ).casefold()

    forbidden_claims = {
        "perfect form",
        "bad form",
        "injury risk",
        "you are injured",
        "diagnosis"
    }

    for claim in forbidden_claims:
        if claim in combined_text:
            raise ValueError(f"FAIL: Squat analysis generated unsupported claim: {claim}")

    print("PASS: Squat analysis reports observable geometry without unsupported diagnosis")


if __name__ == "__main__":
    test_deep_flexion_classification()
    test_moderate_flexion_classification()
    test_shallow_flexion_classification()
    test_best_visible_side_is_selected()
    test_low_visibility_pose_is_rejected()
    test_missing_required_landmarks_are_rejected()
    test_standing_pose_produces_straight_knee_measurement()
    test_deep_pose_produces_observable_geometry_without_form_judgment()