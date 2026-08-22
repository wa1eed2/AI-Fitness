from src.vision.squat_movement_metrics import (
    REP_CONFIDENCE_HIGH,
    REP_CONFIDENCE_LOW,
    REP_CONFIDENCE_MODERATE,
    VIEW_BILATERAL_OBSERVABLE,
    VIEW_INSUFFICIENT,
    VIEW_SINGLE_SIDE_OBSERVABLE,
    analyze_bilateral_squat_frame,
    calculate_trunk_inclination_degrees,
    classify_rep_confidence,
    enrich_repetitions_with_confidence,
    summarize_bilateral_frame_metrics
)


def landmark(
    x,
    y,
    visibility=0.95
):
    return {
        "x": x,
        "y": y,
        "visibility": visibility
    }


def bilateral_pose(
    right_knee_x=2.0,
    right_ankle_x=2.0,
    visibility=0.95
):
    return {
        "left_shoulder": landmark(
            0,
            0,
            visibility
        ),
        "left_hip": landmark(
            0,
            1,
            visibility
        ),
        "left_knee": landmark(
            0,
            2,
            visibility
        ),
        "left_ankle": landmark(
            1,
            2,
            visibility
        ),
        "right_shoulder": landmark(
            2,
            0,
            visibility
        ),
        "right_hip": landmark(
            2,
            1,
            visibility
        ),
        "right_knee": landmark(
            right_knee_x,
            2,
            visibility
        ),
        "right_ankle": landmark(
            right_ankle_x,
            3,
            visibility
        )
    }


def test_vertical_trunk_has_zero_inclination():
    angle = calculate_trunk_inclination_degrees(
        landmark(
            0,
            0
        ),
        landmark(
            0,
            1
        )
    )

    if angle != 0:
        raise ValueError(
            f"FAIL: Expected 0-degree trunk inclination, got {angle}"
        )

    print("PASS: Trunk inclination measures vertical projected torso geometry")


def test_diagonal_trunk_has_45_degree_inclination():
    angle = calculate_trunk_inclination_degrees(
        landmark(
            0,
            0
        ),
        landmark(
            1,
            1
        )
    )

    if angle != 45:
        raise ValueError(
            f"FAIL: Expected 45-degree trunk inclination, got {angle}"
        )

    print("PASS: Trunk inclination measures observable torso projection")


def test_bilateral_pose_reports_both_sides():
    result = analyze_bilateral_squat_frame(
        bilateral_pose()
    )

    if result["view_suitability"] != VIEW_BILATERAL_OBSERVABLE:
        raise ValueError(
            "FAIL: Fully visible bilateral pose was not classified as bilateral"
        )

    if not result["left"]["available"]:
        raise ValueError(
            "FAIL: Left side geometry was unavailable"
        )

    if not result["right"]["available"]:
        raise ValueError(
            "FAIL: Right side geometry was unavailable"
        )

    print("PASS: Bilateral squat geometry is measured when both sides are visible")


def test_single_visible_side_remains_analyzable():
    pose = bilateral_pose()

    for key in (
        "right_shoulder",
        "right_hip",
        "right_knee",
        "right_ankle"
    ):
        pose[
            key
        ][
            "visibility"
        ] = 0.2

    result = analyze_bilateral_squat_frame(
        pose
    )

    if result["view_suitability"] != VIEW_SINGLE_SIDE_OBSERVABLE:
        raise ValueError(
            "FAIL: Single-side pose suitability was classified incorrectly"
        )

    if result["selected_side"] != "left":
        raise ValueError(
            "FAIL: Best visible side was not retained"
        )

    print("PASS: Rich movement metrics degrade safely to one visible side")


def test_low_visibility_pose_returns_insufficient_view():
    pose = bilateral_pose(
        visibility=0.2
    )

    result = analyze_bilateral_squat_frame(
        pose
    )

    if result["view_suitability"] != VIEW_INSUFFICIENT:
        raise ValueError(
            "FAIL: Low-confidence pose was treated as suitable"
        )

    print("PASS: Movement metrics refuse insufficient landmark visibility")


def test_bilateral_difference_is_observable_not_diagnostic():
    result = analyze_bilateral_squat_frame(
        bilateral_pose()
    )

    difference = result[
        "bilateral_differences"
    ][
        "knee_angle_difference_degrees"
    ]

    if difference is None:
        raise ValueError(
            "FAIL: Bilateral knee-angle difference was not calculated"
        )

    text = " ".join(
        result[
            "observations"
        ]
        + result[
            "limitations"
        ]
    ).casefold()

    forbidden_claims = {
        "genetic",
        "injury risk",
        "bad form",
        "perfect form"
    }

    for claim in forbidden_claims:
        if claim in text:
            raise ValueError(
                f"FAIL: Bilateral analysis generated unsupported claim: {claim}"
            )

    print("PASS: Bilateral differences remain cautious observable measurements")


def test_rep_confidence_classification():
    if classify_rep_confidence(
        0.90
    ) != REP_CONFIDENCE_HIGH:
        raise ValueError(
            "FAIL: High-confidence repetition classified incorrectly"
        )

    if classify_rep_confidence(
        0.75
    ) != REP_CONFIDENCE_MODERATE:
        raise ValueError(
            "FAIL: Moderate-confidence repetition classified incorrectly"
        )

    if classify_rep_confidence(
        0.50
    ) != REP_CONFIDENCE_LOW:
        raise ValueError(
            "FAIL: Low-confidence repetition classified incorrectly"
        )

    print("PASS: Repetition confidence is classified from observed landmark confidence")


def test_repetition_enrichment_preserves_original_result():
    original = {
        "repetitions": [
            {
                "repetition_number": 1,
                "mean_confidence": 0.90
            },
            {
                "repetition_number": 2,
                "mean_confidence": 0.75
            }
        ]
    }

    enriched = enrich_repetitions_with_confidence(
        original
    )

    if "confidence_classification" in original[
        "repetitions"
    ][
        0
    ]:
        raise ValueError(
            "FAIL: Confidence enrichment mutated original sequence result"
        )

    if enriched[
        "rep_confidence_summary"
    ][
        "average_rep_confidence"
    ] != 0.825:
        raise ValueError(
            "FAIL: Average repetition confidence is incorrect"
        )

    print("PASS: Repetition confidence enrichment is deterministic and non-mutating")


def test_frame_metric_summary_aggregates_observations():
    first = analyze_bilateral_squat_frame(
        bilateral_pose()
    )

    second_pose = bilateral_pose()

    for key in (
        "right_shoulder",
        "right_hip",
        "right_knee",
        "right_ankle"
    ):
        second_pose[
            key
        ][
            "visibility"
        ] = 0.2

    second = analyze_bilateral_squat_frame(
        second_pose
    )

    summary = summarize_bilateral_frame_metrics(
        [
            first,
            second
        ]
    )

    if summary["frame_count"] != 2:
        raise ValueError(
            "FAIL: Frame metric count is incorrect"
        )

    if summary["bilateral_observable_frame_count"] != 1:
        raise ValueError(
            "FAIL: Bilateral frame count is incorrect"
        )

    if summary["single_side_observable_frame_count"] != 1:
        raise ValueError(
            "FAIL: Single-side frame count is incorrect"
        )

    print("PASS: Movement geometry is summarized across frames deterministically")


if __name__ == "__main__":
    test_vertical_trunk_has_zero_inclination()
    test_diagonal_trunk_has_45_degree_inclination()
    test_bilateral_pose_reports_both_sides()
    test_single_visible_side_remains_analyzable()
    test_low_visibility_pose_returns_insufficient_view()
    test_bilateral_difference_is_observable_not_diagnostic()
    test_rep_confidence_classification()
    test_repetition_enrichment_preserves_original_result()
    test_frame_metric_summary_aggregates_observations()