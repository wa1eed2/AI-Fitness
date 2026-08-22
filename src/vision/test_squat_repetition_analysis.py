import math

from src.vision.squat_repetition_analysis import (
    SEQUENCE_STATUS_ANALYZED,
    analyze_squat_angle_sequence,
    analyze_squat_pose_sequence
)


def angle_frame(
    timestamp,
    angle,
    confidence=0.95,
    side="left"
):
    return {
        "timestamp_seconds": timestamp,
        "knee_angle_degrees": angle,
        "confidence": confidence,
        "selected_side": side
    }


def complete_rep_frames(
    start_time=0.0,
    side="left"
):
    return [
        angle_frame(
            start_time + 0.0,
            170,
            side=side
        ),
        angle_frame(
            start_time + 0.5,
            150,
            side=side
        ),
        angle_frame(
            start_time + 1.0,
            130,
            side=side
        ),
        angle_frame(
            start_time + 1.5,
            110,
            side=side
        ),
        angle_frame(
            start_time + 2.0,
            90,
            side=side
        ),
        angle_frame(
            start_time + 2.5,
            120,
            side=side
        ),
        angle_frame(
            start_time + 3.0,
            145,
            side=side
        ),
        angle_frame(
            start_time + 3.5,
            160,
            side=side
        )
    ]


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
        }
    }


def test_complete_threshold_cycle_counts_one_rep():
    result = analyze_squat_angle_sequence(
        complete_rep_frames()
    )

    if result["status"] != SEQUENCE_STATUS_ANALYZED:
        raise ValueError("FAIL: Valid squat sequence was not analyzed")

    if result["rep_count"] != 1:
        raise ValueError(f"FAIL: Expected 1 repetition, got {result['rep_count']}")

    print("PASS: Temporal squat analyzer counts one complete threshold cycle")


def test_rep_timing_is_measured():
    result = analyze_squat_angle_sequence(
        complete_rep_frames()
    )

    repetition = result[
        "repetitions"
    ][
        0
    ]

    if repetition["duration_seconds"] != 3.5:
        raise ValueError(f"FAIL: Expected 3.5-second repetition, got {repetition['duration_seconds']}")

    if repetition["descent_duration_seconds"] != 2.0:
        raise ValueError(f"FAIL: Expected 2-second descent, got {repetition['descent_duration_seconds']}")

    if repetition["ascent_duration_seconds"] != 1.5:
        raise ValueError(f"FAIL: Expected 1.5-second ascent, got {repetition['ascent_duration_seconds']}")

    print("PASS: Temporal squat analyzer measures descent, ascent, and total rep duration")


def test_rep_range_of_motion_is_measured():
    result = analyze_squat_angle_sequence(
        complete_rep_frames()
    )

    repetition = result[
        "repetitions"
    ][
        0
    ]

    if repetition["minimum_knee_angle_degrees"] != 90:
        raise ValueError("FAIL: Minimum knee angle was not retained")

    if repetition["maximum_knee_angle_degrees"] != 170:
        raise ValueError("FAIL: Maximum knee angle was not retained")

    if repetition["knee_range_of_motion_degrees"] != 80:
        raise ValueError(f"FAIL: Expected 80-degree range, got {repetition['knee_range_of_motion_degrees']}")

    print("PASS: Temporal squat analyzer measures observable knee-angle range")


def test_shallow_attempt_is_not_counted_as_rep():
    frames = [
        angle_frame(
            0.0,
            170
        ),
        angle_frame(
            0.5,
            145
        ),
        angle_frame(
            1.0,
            130
        ),
        angle_frame(
            1.5,
            145
        ),
        angle_frame(
            2.0,
            160
        )
    ]

    result = analyze_squat_angle_sequence(
        frames
    )

    if result["rep_count"] != 0:
        raise ValueError("FAIL: Shallow threshold cycle was counted as complete repetition")

    if result["incomplete_attempt_count"] != 1:
        raise ValueError("FAIL: Shallow attempt was not recorded as incomplete")

    print("PASS: Temporal analyzer does not count a cycle that never reaches bottom threshold")


def test_unfinished_sequence_is_not_counted():
    frames = [
        angle_frame(
            0.0,
            170
        ),
        angle_frame(
            0.5,
            145
        ),
        angle_frame(
            1.0,
            110
        ),
        angle_frame(
            1.5,
            90
        ),
        angle_frame(
            2.0,
            120
        )
    ]

    result = analyze_squat_angle_sequence(
        frames
    )

    if result["rep_count"] != 0:
        raise ValueError("FAIL: Unfinished squat attempt was counted as completed")

    if result["incomplete_attempt_count"] != 1:
        raise ValueError("FAIL: Unfinished attempt was not retained")

    print("PASS: Temporal analyzer requires return to standing before counting repetition")


def test_low_confidence_frame_can_be_skipped_without_destroying_short_sequence():
    frames = complete_rep_frames()

    frames.insert(
        3,
        angle_frame(
            1.25,
            120,
            confidence=0.20
        )
    )

    result = analyze_squat_angle_sequence(
        frames
    )

    if result["rep_count"] != 1:
        raise ValueError("FAIL: One low-confidence intermediate frame destroyed valid repetition")

    if result["low_confidence_frame_count"] != 1:
        raise ValueError("FAIL: Low-confidence frame was not tracked")

    print("PASS: Short low-confidence observation is skipped and explicitly tracked")


def test_large_active_gap_invalidates_rep_attempt():
    frames = [
        angle_frame(
            0.0,
            170
        ),
        angle_frame(
            0.5,
            145
        ),
        angle_frame(
            2.0,
            105
        ),
        angle_frame(
            2.5,
            90
        ),
        angle_frame(
            3.0,
            120
        ),
        angle_frame(
            3.5,
            160
        )
    ]

    result = analyze_squat_angle_sequence(
        frames,
        max_active_frame_gap_seconds=1.0
    )

    if result["rep_count"] != 0:
        raise ValueError("FAIL: Rep was counted across large unobserved frame gap")

    if result["incomplete_attempt_count"] < 1:
        raise ValueError("FAIL: Large-gap invalidation was not tracked")

    print("PASS: Temporal analyzer refuses to bridge large unobserved gaps during a rep")


def test_side_switch_during_attempt_invalidates_rep():
    frames = [
        angle_frame(
            0.0,
            170,
            side="left"
        ),
        angle_frame(
            0.5,
            145,
            side="left"
        ),
        angle_frame(
            1.0,
            110,
            side="right"
        ),
        angle_frame(
            1.5,
            90,
            side="right"
        ),
        angle_frame(
            2.0,
            120,
            side="right"
        ),
        angle_frame(
            2.5,
            160,
            side="right"
        )
    ]

    result = analyze_squat_angle_sequence(
        frames
    )

    if result["rep_count"] != 0:
        raise ValueError("FAIL: Analyzer counted repetition across body-side switch")

    if result["side_switch_count"] != 1:
        raise ValueError("FAIL: Body-side switch was not tracked")

    print("PASS: Temporal analyzer does not merge different visible body sides into one rep")


def test_two_similar_reps_produce_low_variability_summary():
    frames = (
        complete_rep_frames(
            0.0
        )
        + complete_rep_frames(
            4.0
        )
    )

    result = analyze_squat_angle_sequence(
        frames
    )

    if result["rep_count"] != 2:
        raise ValueError(f"FAIL: Expected 2 repetitions, got {result['rep_count']}")

    summary = result[
        "summary"
    ]

    if summary["average_rep_duration_seconds"] != 3.5:
        raise ValueError("FAIL: Average repetition duration is incorrect")

    if summary["average_range_of_motion_degrees"] != 80:
        raise ValueError("FAIL: Average repetition range of motion is incorrect")

    if summary["variability_classification"] != "low_variability":
        raise ValueError(f"FAIL: Matching reps returned {summary['variability_classification']}")

    print("PASS: Rep-to-rep timing and geometry variability are summarized deterministically")


def test_pose_landmark_sequence_connects_frame_analysis_to_rep_counter():
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

    frames = [
        {
            "timestamp_seconds": index * 0.5,
            "pose_landmarks": pose_for_knee_angle(
                angle
            )
        }
        for index, angle in enumerate(
            angles
        )
    ]

    result = analyze_squat_pose_sequence(
        frames
    )

    if result["source"] != "pose_landmarks":
        raise ValueError("FAIL: Pose-sequence source metadata was lost")

    if result["rep_count"] != 1:
        raise ValueError(f"FAIL: Pose landmarks produced {result['rep_count']} repetitions")

    if len(
        result[
            "frame_analyses"
        ]
    ) != len(
        frames
    ):
        raise ValueError("FAIL: Per-frame geometry analyses were not retained")

    print("PASS: Pose landmark sequence feeds deterministic temporal repetition analysis")


def test_temporal_output_avoids_unsupported_form_claims():
    result = analyze_squat_angle_sequence(
        complete_rep_frames()
    )

    combined_text = " ".join(
        result[
            "limitations"
        ]
    ).casefold()

    forbidden_claims = {
        "perfect form",
        "bad form",
        "injury risk",
        "unsafe squat"
    }

    for claim in forbidden_claims:
        if claim in combined_text:
            raise ValueError(f"FAIL: Temporal analysis generated unsupported claim: {claim}")

    print("PASS: Temporal analysis reports measurements without unsupported safety judgment")


def test_non_monotonic_timestamps_are_rejected():
    frames = [
        angle_frame(
            0.0,
            170
        ),
        angle_frame(
            1.0,
            130
        ),
        angle_frame(
            0.5,
            90
        )
    ]

    try:
        analyze_squat_angle_sequence(
            frames
        )

    except ValueError:
        print("PASS: Temporal analyzer rejects non-monotonic frame timestamps")
        return

    raise ValueError("FAIL: Non-monotonic timestamps were accepted")


if __name__ == "__main__":
    test_complete_threshold_cycle_counts_one_rep()
    test_rep_timing_is_measured()
    test_rep_range_of_motion_is_measured()
    test_shallow_attempt_is_not_counted_as_rep()
    test_unfinished_sequence_is_not_counted()
    test_low_confidence_frame_can_be_skipped_without_destroying_short_sequence()
    test_large_active_gap_invalidates_rep_attempt()
    test_side_switch_during_attempt_invalidates_rep()
    test_two_similar_reps_produce_low_variability_summary()
    test_pose_landmark_sequence_connects_frame_analysis_to_rep_counter()
    test_temporal_output_avoids_unsupported_form_claims()
    test_non_monotonic_timestamps_are_rejected()