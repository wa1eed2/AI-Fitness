from src.vision.pose_geometry import (
    calculate_angle_degrees,
    calculate_distance,
    calculate_landmark_visibility,
    validate_landmark
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


def test_valid_landmark_is_normalized():
    result = validate_landmark(
        landmark(
            0.25,
            0.75,
            0.9
        )
    )

    if result != {
        "x": 0.25,
        "y": 0.75,
        "visibility": 0.9
    }:
        raise ValueError("FAIL: Valid landmark was normalized incorrectly")

    print("PASS: Pose landmark coordinates and visibility are validated")


def test_default_visibility_is_supported():
    result = validate_landmark(
        {
            "x": 1,
            "y": 2
        }
    )

    if result["visibility"] != 1.0:
        raise ValueError("FAIL: Missing visibility did not use deterministic default")

    print("PASS: Pose geometry supports landmarks without explicit visibility")


def test_invalid_visibility_is_rejected():
    try:
        validate_landmark(
            landmark(
                0,
                0,
                1.5
            )
        )

    except ValueError:
        print("PASS: Pose geometry rejects invalid landmark visibility")
        return

    raise ValueError("FAIL: Invalid landmark visibility was accepted")


def test_distance_is_calculated():
    result = calculate_distance(
        landmark(
            0,
            0
        ),
        landmark(
            3,
            4
        )
    )

    if result != 5:
        raise ValueError(f"FAIL: Expected distance 5, got {result}")

    print("PASS: Pose geometry calculates Euclidean landmark distance")


def test_straight_joint_is_180_degrees():
    result = calculate_angle_degrees(
        landmark(
            0,
            -1
        ),
        landmark(
            0,
            0
        ),
        landmark(
            0,
            1
        )
    )

    if result != 180:
        raise ValueError(f"FAIL: Expected 180-degree angle, got {result}")

    print("PASS: Pose geometry calculates straight joint angle")


def test_right_angle_is_90_degrees():
    result = calculate_angle_degrees(
        landmark(
            0,
            1
        ),
        landmark(
            0,
            0
        ),
        landmark(
            1,
            0
        )
    )

    if result != 90:
        raise ValueError(f"FAIL: Expected 90-degree angle, got {result}")

    print("PASS: Pose geometry calculates right-angle joint geometry")


def test_overlapping_landmarks_are_rejected():
    try:
        calculate_angle_degrees(
            landmark(
                0,
                0
            ),
            landmark(
                0,
                0
            ),
            landmark(
                1,
                1
            )
        )

    except ValueError:
        print("PASS: Pose geometry rejects zero-length angle vectors")
        return

    raise ValueError("FAIL: Overlapping landmarks produced invalid joint angle")


def test_average_visibility_is_calculated():
    result = calculate_landmark_visibility(
        [
            landmark(
                0,
                0,
                1.0
            ),
            landmark(
                1,
                1,
                0.8
            ),
            landmark(
                2,
                2,
                0.6
            )
        ]
    )

    if result != 0.8:
        raise ValueError(f"FAIL: Expected average visibility 0.8, got {result}")

    print("PASS: Pose geometry calculates landmark visibility confidence")


if __name__ == "__main__":
    test_valid_landmark_is_normalized()
    test_default_visibility_is_supported()
    test_invalid_visibility_is_rejected()
    test_distance_is_calculated()
    test_straight_joint_is_180_degrees()
    test_right_angle_is_90_degrees()
    test_overlapping_landmarks_are_rejected()
    test_average_visibility_is_calculated()