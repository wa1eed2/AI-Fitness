import os
import tempfile

from src.vision.real_world_validation import (
    build_validation_expectation,
    calculate_pose_detection_ratio,
    evaluate_real_world_analysis,
    run_real_world_validation_case,
    run_real_world_validation_suite
)

from src.vision.squat_movement_metrics import (
    VIEW_BILATERAL_OBSERVABLE,
    VIEW_SINGLE_SIDE_OBSERVABLE
)


def build_result(
    rep_count=5,
    pose_detected_frames=90,
    sampled_frames=100,
    observable_frame_ratio=0.90,
    view_classification=VIEW_BILATERAL_OBSERVABLE,
    average_rep_confidence=0.88,
    status="analyzed"
):
    return {
        "status": status,
        "exercise": "squat",
        "source": "video",
        "rep_count": rep_count,
        "video": {
            "sampled_frame_count": sampled_frames,
            "fps": 30.0
        },
        "detection_summary": {
            "pose_detected_frame_count": pose_detected_frames,
            "no_pose_frame_count": (
                sampled_frames
                - pose_detected_frames
            ),
            "insufficient_landmark_frame_count": 0
        },
        "view_suitability_summary": {
            "classification": view_classification,
            "observable_frame_ratio": observable_frame_ratio
        },
        "rep_confidence_summary": {
            "average_rep_confidence": average_rep_confidence,
            "high_confidence_rep_count": rep_count,
            "moderate_confidence_rep_count": 0,
            "low_confidence_rep_count": 0,
            "unavailable_confidence_rep_count": 0
        },
        "summary": {},
        "repetitions": [],
        "limitations": []
    }


def temporary_video():
    handle = tempfile.NamedTemporaryFile(
        suffix=".mp4",
        delete=False
    )

    handle.write(
        b"local-validation-video"
    )

    path = handle.name

    handle.close()

    return path


def test_pose_detection_ratio_is_calculated():
    result = build_result(
        pose_detected_frames=80,
        sampled_frames=100
    )

    ratio = calculate_pose_detection_ratio(
        result
    )

    if ratio != 0.8:
        raise ValueError(
            f"FAIL: Expected detection ratio 0.8, got {ratio}"
        )

    print("PASS: Real-world validation calculates pose-detection coverage")


def test_valid_expectation_is_normalized():
    expectation = build_validation_expectation(
        minimum_reps=4,
        maximum_reps=6,
        minimum_pose_detection_ratio=0.8,
        minimum_observable_frame_ratio=0.75,
        minimum_average_rep_confidence=0.7
    )

    if expectation["minimum_reps"] != 4:
        raise ValueError(
            "FAIL: Minimum rep expectation changed"
        )

    if expectation["maximum_reps"] != 6:
        raise ValueError(
            "FAIL: Maximum rep expectation changed"
        )

    print("PASS: Real-world validation uses explicit pre-declared expectations")


def test_expected_real_world_result_passes():
    result = build_result()

    expectation = build_validation_expectation(
        minimum_reps=4,
        maximum_reps=6,
        minimum_pose_detection_ratio=0.80,
        minimum_observable_frame_ratio=0.80,
        minimum_average_rep_confidence=0.70
    )

    report = evaluate_real_world_analysis(
        result,
        expectation
    )

    if report["passed"] is not True:
        raise ValueError(
            f"FAIL: Expected validation case failed: {report['checks']}"
        )

    print("PASS: Real-world validation accepts result inside broad expected bounds")


def test_unexpected_rep_count_fails_validation():
    result = build_result(
        rep_count=9
    )

    expectation = build_validation_expectation(
        minimum_reps=4,
        maximum_reps=6
    )

    report = evaluate_real_world_analysis(
        result,
        expectation
    )

    if report["passed"]:
        raise ValueError(
            "FAIL: Unexpected repetition count passed validation"
        )

    failed_checks = [
        check[
            "name"
        ]
        for check in report[
            "checks"
        ]
        if not check[
            "passed"
        ]
    ]

    if "rep_count_range" not in failed_checks:
        raise ValueError(
            "FAIL: Rep-count failure was not identified"
        )

    print("PASS: Real-world validation detects unexpected repetition count")


def test_low_pose_detection_coverage_fails():
    result = build_result(
        pose_detected_frames=40,
        sampled_frames=100
    )

    expectation = build_validation_expectation(
        minimum_reps=4,
        maximum_reps=6,
        minimum_pose_detection_ratio=0.80
    )

    report = evaluate_real_world_analysis(
        result,
        expectation
    )

    if report["passed"]:
        raise ValueError(
            "FAIL: Poor pose-detection coverage passed validation"
        )

    print("PASS: Real-world validation detects poor pose-estimation coverage")


def test_single_side_camera_view_can_be_allowed():
    result = build_result(
        view_classification=VIEW_SINGLE_SIDE_OBSERVABLE
    )

    expectation = build_validation_expectation(
        minimum_reps=4,
        maximum_reps=6,
        allowed_views=[
            VIEW_SINGLE_SIDE_OBSERVABLE
        ]
    )

    report = evaluate_real_world_analysis(
        result,
        expectation
    )

    if not report["passed"]:
        raise ValueError(
            "FAIL: Explicitly allowed single-side view failed validation"
        )

    print("PASS: Validation contracts can explicitly allow single-side camera views")


def test_low_rep_confidence_can_fail_validation():
    result = build_result(
        average_rep_confidence=0.55
    )

    expectation = build_validation_expectation(
        minimum_reps=4,
        maximum_reps=6,
        minimum_average_rep_confidence=0.75
    )

    report = evaluate_real_world_analysis(
        result,
        expectation
    )

    if report["passed"]:
        raise ValueError(
            "FAIL: Low-confidence repetition set passed required confidence threshold"
        )

    print("PASS: Real-world validation detects low average repetition confidence")


def test_invalid_rep_expectation_is_rejected():
    try:
        build_validation_expectation(
            minimum_reps=8,
            maximum_reps=4
        )

    except ValueError:
        print("PASS: Real-world validation rejects impossible expectation ranges")
        return

    raise ValueError(
        "FAIL: Invalid expected repetition range was accepted"
    )


def test_validation_case_does_not_request_frame_observations():
    video_path = temporary_video()

    calls = []

    def analyzer(
        **kwargs
    ):
        calls.append(
            kwargs
        )

        return build_result()

    try:
        expectation = build_validation_expectation(
            minimum_reps=4,
            maximum_reps=6
        )

        report = run_real_world_validation_case(
            video_path=video_path,
            model_path="unused.task",
            expectation=expectation,
            sample_every_n_frames=2,
            max_analyzed_frames=500,
            analyzer=analyzer
        )

        if not report["passed"]:
            raise ValueError(
                "FAIL: Injected validation case unexpectedly failed"
            )

        if len(calls) != 1:
            raise ValueError(
                "FAIL: Analyzer call count is incorrect"
            )

        call = calls[
            0
        ]

        if call["include_frame_observations"] is not False:
            raise ValueError(
                "FAIL: Real-world validation requested raw frame observations"
            )

        if report[
            "source_filename"
        ] != os.path.basename(
            video_path
        ):
            raise ValueError(
                "FAIL: Validation report did not retain safe basename"
            )

        print("PASS: Real-world validation runs video analysis without raw frame output")

    finally:
        os.remove(
            video_path
        )


def test_validation_suite_reports_failed_cases_separately():
    first_video = temporary_video()
    second_video = temporary_video()

    call_count = {
        "value": 0
    }

    def analyzer(
        **kwargs
    ):
        call_count[
            "value"
        ] += 1

        if call_count[
            "value"
        ] == 1:
            return build_result(
                rep_count=5
            )

        return build_result(
            rep_count=10
        )

    try:
        expectation = build_validation_expectation(
            minimum_reps=4,
            maximum_reps=6
        )

        suite = run_real_world_validation_suite(
            cases=[
                {
                    "video_path": first_video,
                    "expectation": expectation
                },
                {
                    "video_path": second_video,
                    "expectation": expectation
                }
            ],
            model_path="unused.task",
            analyzer=analyzer
        )

        if suite["case_count"] != 2:
            raise ValueError(
                "FAIL: Validation suite case count is incorrect"
            )

        if suite["passed_case_count"] != 1:
            raise ValueError(
                "FAIL: Validation suite passed-case count is incorrect"
            )

        if suite["failed_case_count"] != 1:
            raise ValueError(
                "FAIL: Validation suite failed-case count is incorrect"
            )

        if suite["passed"]:
            raise ValueError(
                "FAIL: Suite passed despite one failed case"
            )

        print("PASS: Real-world validation suite keeps clip failures explicit")

    finally:
        os.remove(
            first_video
        )

        os.remove(
            second_video
        )


if __name__ == "__main__":
    test_pose_detection_ratio_is_calculated()
    test_valid_expectation_is_normalized()
    test_expected_real_world_result_passes()
    test_unexpected_rep_count_fails_validation()
    test_low_pose_detection_coverage_fails()
    test_single_side_camera_view_can_be_allowed()
    test_low_rep_confidence_can_fail_validation()
    test_invalid_rep_expectation_is_rejected()
    test_validation_case_does_not_request_frame_observations()
    test_validation_suite_reports_failed_cases_separately()