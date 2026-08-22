import math

from src.vision.squat_sequence_metrics import (
    analyze_squat_pose_sequence_with_metrics
)


def pose_for_knee_angle(
    angle_degrees,
    visibility=0.95
):
    angle_radians = math.radians(
        angle_degrees
    )

    return {
        "left_shoulder": {
            "x": 2.0,
            "y": 0.0,
            "visibility": visibility
        },
        "left_hip": {
            "x": 1.0,
            "y": 0.0,
            "visibility": visibility
        },
        "left_knee": {
            "x": 0.0,
            "y": 0.0,
            "visibility": visibility
        },
        "left_ankle": {
            "x": math.cos(
                angle_radians
            ),
            "y": math.sin(
                angle_radians
            ),
            "visibility": visibility
        },
        "right_shoulder": {
            "x": 4.0,
            "y": 0.0,
            "visibility": visibility
        },
        "right_hip": {
            "x": 3.0,
            "y": 0.0,
            "visibility": visibility
        },
        "right_knee": {
            "x": 2.0,
            "y": 0.0,
            "visibility": visibility
        },
        "right_ankle": {
            "x": (
                2.0
                + math.cos(
                    angle_radians
                )
            ),
            "y": math.sin(
                angle_radians
            ),
            "visibility": visibility
        }
    }


def build_rep_sequence():
    angles = [
        170,
        150,
        130,
        110,
        90,
        120,
        145,
        160
    ]

    return [
        {
            "timestamp_seconds": (
                index
                * 0.5
            ),
            "pose_landmarks": pose_for_knee_angle(
                angle
            )
        }
        for index, angle in enumerate(
            angles
        )
    ]


def test_rich_sequence_still_counts_rep():
    result = analyze_squat_pose_sequence_with_metrics(
        build_rep_sequence()
    )

    if result["rep_count"] != 1:
        raise ValueError(
            f"FAIL: Expected one repetition, got {result['rep_count']}"
        )

    print("PASS: Rich metrics preserve deterministic temporal rep counting")


def test_repetition_receives_confidence_classification():
    result = analyze_squat_pose_sequence_with_metrics(
        build_rep_sequence()
    )

    repetition = result[
        "repetitions"
    ][
        0
    ]

    if repetition[
        "confidence_classification"
    ] != "high":
        raise ValueError(
            "FAIL: High-confidence pose sequence did not produce high-confidence rep"
        )

    print("PASS: Temporal repetitions include per-rep confidence classification")


def test_sequence_contains_confidence_summary():
    result = analyze_squat_pose_sequence_with_metrics(
        build_rep_sequence()
    )

    summary = result[
        "rep_confidence_summary"
    ]

    if summary["high_confidence_rep_count"] != 1:
        raise ValueError(
            "FAIL: Rep confidence summary has wrong high-confidence count"
        )

    if summary["average_rep_confidence"] != 0.95:
        raise ValueError(
            "FAIL: Average repetition confidence is incorrect"
        )

    print("PASS: Sequence includes deterministic repetition-confidence summary")


def test_sequence_contains_bilateral_metric_summary():
    result = analyze_squat_pose_sequence_with_metrics(
        build_rep_sequence()
    )

    summary = result[
        "movement_metrics_summary"
    ]

    if summary["frame_count"] != 8:
        raise ValueError(
            "FAIL: Movement metric frame count is incorrect"
        )

    if summary[
        "bilateral_observable_frame_count"
    ] != 8:
        raise ValueError(
            "FAIL: Bilateral observation count is incorrect"
        )

    print("PASS: Sequence summarizes bilateral geometry across frames")


def test_frame_metrics_are_private_by_default():
    result = analyze_squat_pose_sequence_with_metrics(
        build_rep_sequence()
    )

    if "frame_movement_metrics" in result:
        raise ValueError(
            "FAIL: Per-frame movement metrics were returned by default"
        )

    print("PASS: Rich sequence keeps detailed per-frame metrics opt-in")


def test_frame_metrics_can_be_explicitly_requested():
    result = analyze_squat_pose_sequence_with_metrics(
        build_rep_sequence(),
        include_frame_metrics=True
    )

    if len(
        result[
            "frame_movement_metrics"
        ]
    ) != 8:
        raise ValueError(
            "FAIL: Explicit frame metrics request returned wrong count"
        )

    print("PASS: Detailed frame metrics are available only when explicitly requested")


if __name__ == "__main__":
    test_rich_sequence_still_counts_rep()
    test_repetition_receives_confidence_classification()
    test_sequence_contains_confidence_summary()
    test_sequence_contains_bilateral_metric_summary()
    test_frame_metrics_are_private_by_default()
    test_frame_metrics_can_be_explicitly_requested()