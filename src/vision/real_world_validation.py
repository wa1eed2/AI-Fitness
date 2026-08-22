import math
import os
from numbers import Real

from src.vision.squat_movement_metrics import (
    VIEW_BILATERAL_OBSERVABLE,
    VIEW_INSUFFICIENT,
    VIEW_SINGLE_SIDE_OBSERVABLE
)

from src.vision.video_squat_pipeline import (
    analyze_squat_video
)


VALID_ANALYSIS_STATUSES = {
    "analyzed",
    "insufficient_data"
}


VALID_VIEW_CLASSIFICATIONS = {
    VIEW_BILATERAL_OBSERVABLE,
    VIEW_SINGLE_SIDE_OBSERVABLE,
    VIEW_INSUFFICIENT
}


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
        raise ValueError(
            f"{field_name} must be between 0 and 1"
        )

    return normalized


def validate_nonnegative_integer(
    value,
    field_name
):
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")

    if value < 0:
        raise ValueError(f"{field_name} cannot be negative")

    return value


def validate_positive_integer(
    value,
    field_name
):
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")

    if value < 1:
        raise ValueError(f"{field_name} must be positive")

    return value


def validate_video_analysis_result(
    result
):
    if not isinstance(result, dict):
        raise ValueError(
            "Video analysis result must be a dictionary"
        )

    status = result.get(
        "status"
    )

    if status not in VALID_ANALYSIS_STATUSES:
        raise ValueError(
            "Video analysis contains unsupported status"
        )

    if result.get(
        "exercise"
    ) != "squat":
        raise ValueError(
            "Real-world validation currently supports squat analysis only"
        )

    rep_count = result.get(
        "rep_count"
    )

    validate_nonnegative_integer(
        rep_count,
        "rep_count"
    )

    video = result.get(
        "video"
    )

    if not isinstance(video, dict):
        raise ValueError(
            "Video analysis result requires video metadata"
        )

    sampled_frame_count = video.get(
        "sampled_frame_count"
    )

    validate_positive_integer(
        sampled_frame_count,
        "sampled_frame_count"
    )

    detection_summary = result.get(
        "detection_summary"
    )

    if not isinstance(detection_summary, dict):
        raise ValueError(
            "Video analysis result requires detection_summary"
        )

    validate_nonnegative_integer(
        detection_summary.get(
            "pose_detected_frame_count"
        ),
        "pose_detected_frame_count"
    )

    validate_nonnegative_integer(
        detection_summary.get(
            "no_pose_frame_count"
        ),
        "no_pose_frame_count"
    )

    view_summary = result.get(
        "view_suitability_summary"
    )

    if not isinstance(view_summary, dict):
        raise ValueError(
            "Video analysis result requires view_suitability_summary"
        )

    view_classification = view_summary.get(
        "classification"
    )

    if view_classification not in VALID_VIEW_CLASSIFICATIONS:
        raise ValueError(
            "Video analysis contains invalid view classification"
        )

    validate_probability(
        view_summary.get(
            "observable_frame_ratio"
        ),
        "observable_frame_ratio"
    )

    rep_confidence_summary = result.get(
        "rep_confidence_summary"
    )

    if not isinstance(rep_confidence_summary, dict):
        raise ValueError(
            "Video analysis result requires rep_confidence_summary"
        )

    average_rep_confidence = rep_confidence_summary.get(
        "average_rep_confidence"
    )

    if average_rep_confidence is not None:
        validate_probability(
            average_rep_confidence,
            "average_rep_confidence"
        )

    return result


def validate_expected_rep_range(
    minimum_reps,
    maximum_reps
):
    validate_nonnegative_integer(
        minimum_reps,
        "minimum_reps"
    )

    validate_nonnegative_integer(
        maximum_reps,
        "maximum_reps"
    )

    if minimum_reps > maximum_reps:
        raise ValueError(
            "minimum_reps cannot exceed maximum_reps"
        )


def validate_allowed_views(
    allowed_views
):
    if not isinstance(allowed_views, list):
        raise ValueError(
            "allowed_views must be a list"
        )

    if not allowed_views:
        raise ValueError(
            "allowed_views cannot be empty"
        )

    normalized = []

    for view in allowed_views:
        if view not in VALID_VIEW_CLASSIFICATIONS:
            raise ValueError(
                f"Unsupported allowed view classification: {view}"
            )

        if view not in normalized:
            normalized.append(
                view
            )

    return normalized


def build_validation_expectation(
    minimum_reps,
    maximum_reps,
    minimum_pose_detection_ratio=0.70,
    minimum_observable_frame_ratio=0.70,
    minimum_average_rep_confidence=None,
    allowed_views=None,
    expected_status="analyzed"
):
    validate_expected_rep_range(
        minimum_reps,
        maximum_reps
    )

    minimum_pose_detection_ratio = validate_probability(
        minimum_pose_detection_ratio,
        "minimum_pose_detection_ratio"
    )

    minimum_observable_frame_ratio = validate_probability(
        minimum_observable_frame_ratio,
        "minimum_observable_frame_ratio"
    )

    if minimum_average_rep_confidence is not None:
        minimum_average_rep_confidence = validate_probability(
            minimum_average_rep_confidence,
            "minimum_average_rep_confidence"
        )

    if allowed_views is None:
        allowed_views = [
            VIEW_BILATERAL_OBSERVABLE,
            VIEW_SINGLE_SIDE_OBSERVABLE
        ]

    allowed_views = validate_allowed_views(
        allowed_views
    )

    if expected_status not in VALID_ANALYSIS_STATUSES:
        raise ValueError(
            "expected_status is invalid"
        )

    return {
        "minimum_reps": minimum_reps,
        "maximum_reps": maximum_reps,
        "minimum_pose_detection_ratio": minimum_pose_detection_ratio,
        "minimum_observable_frame_ratio": minimum_observable_frame_ratio,
        "minimum_average_rep_confidence": minimum_average_rep_confidence,
        "allowed_views": allowed_views,
        "expected_status": expected_status
    }


def calculate_pose_detection_ratio(
    result
):
    validate_video_analysis_result(
        result
    )

    sampled_frame_count = result[
        "video"
    ][
        "sampled_frame_count"
    ]

    detected_count = result[
        "detection_summary"
    ][
        "pose_detected_frame_count"
    ]

    if detected_count > sampled_frame_count:
        raise ValueError(
            "pose_detected_frame_count cannot exceed sampled_frame_count"
        )

    return round(
        detected_count
        / sampled_frame_count,
        4
    )


def build_validation_check(
    name,
    passed,
    observed,
    expected
):
    if not isinstance(name, str) or not name:
        raise ValueError(
            "Validation check requires name"
        )

    if not isinstance(passed, bool):
        raise ValueError(
            "Validation check passed value must be boolean"
        )

    return {
        "name": name,
        "passed": passed,
        "observed": observed,
        "expected": expected
    }


def evaluate_real_world_analysis(
    result,
    expectation
):
    validate_video_analysis_result(
        result
    )

    if not isinstance(expectation, dict):
        raise ValueError(
            "expectation must be a dictionary"
        )

    normalized_expectation = build_validation_expectation(
        minimum_reps=expectation.get(
            "minimum_reps"
        ),
        maximum_reps=expectation.get(
            "maximum_reps"
        ),
        minimum_pose_detection_ratio=expectation.get(
            "minimum_pose_detection_ratio",
            0.70
        ),
        minimum_observable_frame_ratio=expectation.get(
            "minimum_observable_frame_ratio",
            0.70
        ),
        minimum_average_rep_confidence=expectation.get(
            "minimum_average_rep_confidence"
        ),
        allowed_views=expectation.get(
            "allowed_views"
        ),
        expected_status=expectation.get(
            "expected_status",
            "analyzed"
        )
    )

    pose_detection_ratio = calculate_pose_detection_ratio(
        result
    )

    observable_frame_ratio = result[
        "view_suitability_summary"
    ][
        "observable_frame_ratio"
    ]

    view_classification = result[
        "view_suitability_summary"
    ][
        "classification"
    ]

    average_rep_confidence = result[
        "rep_confidence_summary"
    ][
        "average_rep_confidence"
    ]

    rep_count = result[
        "rep_count"
    ]

    checks = []

    checks.append(
        build_validation_check(
            name="analysis_status",
            passed=(
                result[
                    "status"
                ]
                == normalized_expectation[
                    "expected_status"
                ]
            ),
            observed=result[
                "status"
            ],
            expected=normalized_expectation[
                "expected_status"
            ]
        )
    )

    checks.append(
        build_validation_check(
            name="rep_count_range",
            passed=(
                normalized_expectation[
                    "minimum_reps"
                ]
                <= rep_count
                <= normalized_expectation[
                    "maximum_reps"
                ]
            ),
            observed=rep_count,
            expected={
                "minimum": normalized_expectation[
                    "minimum_reps"
                ],
                "maximum": normalized_expectation[
                    "maximum_reps"
                ]
            }
        )
    )

    checks.append(
        build_validation_check(
            name="pose_detection_ratio",
            passed=(
                pose_detection_ratio
                >= normalized_expectation[
                    "minimum_pose_detection_ratio"
                ]
            ),
            observed=pose_detection_ratio,
            expected={
                "minimum": normalized_expectation[
                    "minimum_pose_detection_ratio"
                ]
            }
        )
    )

    checks.append(
        build_validation_check(
            name="observable_frame_ratio",
            passed=(
                observable_frame_ratio
                >= normalized_expectation[
                    "minimum_observable_frame_ratio"
                ]
            ),
            observed=observable_frame_ratio,
            expected={
                "minimum": normalized_expectation[
                    "minimum_observable_frame_ratio"
                ]
            }
        )
    )

    checks.append(
        build_validation_check(
            name="view_suitability",
            passed=(
                view_classification
                in normalized_expectation[
                    "allowed_views"
                ]
            ),
            observed=view_classification,
            expected={
                "allowed": normalized_expectation[
                    "allowed_views"
                ]
            }
        )
    )

    required_confidence = normalized_expectation[
        "minimum_average_rep_confidence"
    ]

    if required_confidence is not None:
        confidence_passed = (
            average_rep_confidence is not None
            and average_rep_confidence
            >= required_confidence
        )

        checks.append(
            build_validation_check(
                name="average_rep_confidence",
                passed=confidence_passed,
                observed=average_rep_confidence,
                expected={
                    "minimum": required_confidence
                }
            )
        )

    passed = all(
        check[
            "passed"
        ]
        for check in checks
    )

    return {
        "passed": passed,
        "exercise": "squat",
        "metrics": {
            "rep_count": rep_count,
            "pose_detection_ratio": pose_detection_ratio,
            "observable_frame_ratio": observable_frame_ratio,
            "view_suitability": view_classification,
            "average_rep_confidence": average_rep_confidence
        },
        "expectation": normalized_expectation,
        "checks": checks,
        "limitations": [
            (
                "This validation compares deterministic computer-vision output "
                "against broad expected observations for a known video."
            ),
            (
                "Passing this validation does not establish that the movement is "
                "safe, optimal, medically appropriate, or injury-free."
            ),
            (
                "Expected rep ranges and visibility thresholds should be defined "
                "before reviewing model output to reduce threshold tuning around "
                "individual clips."
            )
        ]
    }


def validate_local_video_path(
    video_path
):
    if not isinstance(video_path, str) or not video_path.strip():
        raise ValueError(
            "video_path must be a non-empty string"
        )

    normalized = os.path.abspath(
        video_path.strip()
    )

    if not os.path.isfile(
        normalized
    ):
        raise ValueError(
            f"Validation video was not found: {normalized}"
        )

    return normalized


def run_real_world_validation_case(
    video_path,
    model_path,
    expectation,
    sample_every_n_frames=1,
    max_analyzed_frames=None,
    analyzer=None
):
    normalized_video_path = validate_local_video_path(
        video_path
    )

    validate_positive_integer(
        sample_every_n_frames,
        "sample_every_n_frames"
    )

    if max_analyzed_frames is not None:
        validate_positive_integer(
            max_analyzed_frames,
            "max_analyzed_frames"
        )

    if analyzer is None:
        analyzer = analyze_squat_video

    if not callable(
        analyzer
    ):
        raise ValueError(
            "analyzer must be callable"
        )

    result = analyzer(
        video_path=normalized_video_path,
        model_path=model_path,
        sample_every_n_frames=sample_every_n_frames,
        max_analyzed_frames=max_analyzed_frames,
        include_frame_observations=False
    )

    report = evaluate_real_world_analysis(
        result,
        expectation
    )

    report[
        "source_filename"
    ] = os.path.basename(
        normalized_video_path
    )

    return report


def run_real_world_validation_suite(
    cases,
    model_path,
    analyzer=None
):
    if not isinstance(cases, list):
        raise ValueError(
            "cases must be a list"
        )

    if not cases:
        raise ValueError(
            "cases cannot be empty"
        )

    reports = []

    for index, case in enumerate(
        cases
    ):
        if not isinstance(case, dict):
            raise ValueError(
                f"cases[{index}] must be a dictionary"
            )

        report = run_real_world_validation_case(
            video_path=case.get(
                "video_path"
            ),
            model_path=model_path,
            expectation=case.get(
                "expectation"
            ),
            sample_every_n_frames=case.get(
                "sample_every_n_frames",
                1
            ),
            max_analyzed_frames=case.get(
                "max_analyzed_frames"
            ),
            analyzer=analyzer
        )

        reports.append(
            report
        )

    passed_case_count = sum(
        1
        for report in reports
        if report[
            "passed"
        ]
    )

    return {
        "passed": (
            passed_case_count
            == len(
                reports
            )
        ),
        "case_count": len(
            reports
        ),
        "passed_case_count": passed_case_count,
        "failed_case_count": (
            len(
                reports
            )
            - passed_case_count
        ),
        "reports": reports
    }