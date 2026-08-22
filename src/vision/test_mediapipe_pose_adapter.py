import numpy as np

from src.vision.mediapipe_pose_adapter import (
    DETECTION_STATUS_NO_POSE,
    DETECTION_STATUS_POSE_DETECTED,
    PoseModelNotFoundError,
    convert_pose_landmarker_result,
    convert_pose_landmarks,
    timestamp_seconds_to_milliseconds,
    validate_model_path,
    validate_rgb_frame
)


class FakeLandmark:
    def __init__(
        self,
        x=0.0,
        y=0.0,
        visibility=0.9,
        presence=0.8
    ):
        self.x = x
        self.y = y
        self.visibility = visibility
        self.presence = presence


class FakeResult:
    def __init__(
        self,
        pose_landmarks
    ):
        self.pose_landmarks = pose_landmarks


def build_fake_pose():
    landmarks = [
        FakeLandmark(
            x=index / 100,
            y=index / 200,
            visibility=0.9,
            presence=0.8
        )
        for index in range(
            33
        )
    ]

    return landmarks


def test_rgb_frame_validation_accepts_uint8_three_channel_image():
    frame = np.zeros(
        (
            100,
            200,
            3
        ),
        dtype=np.uint8
    )

    validated = validate_rgb_frame(
        frame
    )

    if validated.shape != (
        100,
        200,
        3
    ):
        raise ValueError("FAIL: RGB frame shape changed during validation")

    if validated.dtype != np.uint8:
        raise ValueError("FAIL: RGB frame dtype changed during validation")

    if not validated.flags[
        "C_CONTIGUOUS"
    ]:
        raise ValueError("FAIL: Validated RGB frame is not contiguous")

    print("PASS: MediaPipe adapter validates contiguous uint8 RGB images")


def test_non_uint8_frame_is_rejected():
    frame = np.zeros(
        (
            20,
            20,
            3
        ),
        dtype=np.float32
    )

    try:
        validate_rgb_frame(
            frame
        )

    except ValueError:
        print("PASS: MediaPipe adapter rejects unsupported image dtype")
        return

    raise ValueError("FAIL: Non-uint8 frame was accepted")


def test_wrong_channel_count_is_rejected():
    frame = np.zeros(
        (
            20,
            20,
            4
        ),
        dtype=np.uint8
    )

    try:
        validate_rgb_frame(
            frame
        )

    except ValueError:
        print("PASS: MediaPipe adapter requires exactly three RGB channels")
        return

    raise ValueError("FAIL: Four-channel frame was accepted as RGB")


def test_empty_pose_result_is_normalized():
    result = convert_pose_landmarker_result(
        FakeResult(
            []
        )
    )

    if result["status"] != DETECTION_STATUS_NO_POSE:
        raise ValueError("FAIL: Empty MediaPipe result was not classified as no-pose")

    if result["pose_count"] != 0:
        raise ValueError("FAIL: Empty MediaPipe result reported detected poses")

    if result["pose_landmarks"] is not None:
        raise ValueError("FAIL: Empty MediaPipe result created pose landmarks")

    print("PASS: MediaPipe adapter handles frames without a detected pose")


def test_relevant_pose_landmark_indexes_are_mapped():
    landmarks = build_fake_pose()

    converted = convert_pose_landmarks(
        landmarks
    )

    expected_keys = {
        "left_shoulder",
        "right_shoulder",
        "left_hip",
        "right_hip",
        "left_knee",
        "right_knee",
        "left_ankle",
        "right_ankle"
    }

    if set(
        converted
    ) != expected_keys:
        raise ValueError("FAIL: MediaPipe landmark mapping returned wrong joint set")

    if converted["left_shoulder"]["x"] != 0.11:
        raise ValueError("FAIL: LEFT_SHOULDER index mapping is incorrect")

    if converted["left_hip"]["x"] != 0.23:
        raise ValueError("FAIL: LEFT_HIP index mapping is incorrect")

    if converted["left_knee"]["x"] != 0.25:
        raise ValueError("FAIL: LEFT_KNEE index mapping is incorrect")

    if converted["left_ankle"]["x"] != 0.27:
        raise ValueError("FAIL: LEFT_ANKLE index mapping is incorrect")

    print("PASS: MediaPipe 33-landmark result maps to AI-Fitness joint names")


def test_visibility_and_presence_use_conservative_confidence():
    landmarks = build_fake_pose()

    landmarks[
        11
    ].visibility = 0.95

    landmarks[
        11
    ].presence = 0.70

    converted = convert_pose_landmarks(
        landmarks
    )

    if converted["left_shoulder"]["visibility"] != 0.70:
        raise ValueError(
            "FAIL: Adapter did not use conservative visibility/presence confidence"
        )

    print("PASS: MediaPipe adapter combines visibility and presence conservatively")


def test_missing_landmark_confidence_fails_closed():
    landmarks = build_fake_pose()

    landmarks[
        11
    ].visibility = None

    landmarks[
        11
    ].presence = None

    converted = convert_pose_landmarks(
        landmarks
    )

    if converted["left_shoulder"]["visibility"] != 0.0:
        raise ValueError("FAIL: Missing landmark confidence was treated as trusted")

    print("PASS: Missing MediaPipe confidence fails closed instead of assuming visibility")


def test_coordinates_outside_image_range_remain_observable():
    landmarks = build_fake_pose()

    landmarks[
        11
    ].x = 1.2

    landmarks[
        11
    ].y = -0.1

    converted = convert_pose_landmarks(
        landmarks
    )

    if converted["left_shoulder"]["x"] != 1.2:
        raise ValueError("FAIL: Adapter incorrectly clamped normalized x coordinate")

    if converted["left_shoulder"]["y"] != -0.1:
        raise ValueError("FAIL: Adapter incorrectly clamped normalized y coordinate")

    print("PASS: MediaPipe adapter preserves finite landmarks outside image boundary")


def test_incomplete_mediapipe_landmark_set_is_rejected():
    landmarks = [
        FakeLandmark()
        for _ in range(
            20
        )
    ]

    try:
        convert_pose_landmarks(
            landmarks
        )

    except ValueError:
        print("PASS: MediaPipe adapter rejects incomplete 33-landmark results")
        return

    raise ValueError("FAIL: Incomplete landmark result was accepted")


def test_detected_pose_result_is_normalized():
    result = convert_pose_landmarker_result(
        FakeResult(
            [
                build_fake_pose()
            ]
        )
    )

    if result["status"] != DETECTION_STATUS_POSE_DETECTED:
        raise ValueError("FAIL: Valid MediaPipe result was not classified as detected")

    if result["pose_count"] != 1:
        raise ValueError("FAIL: Valid MediaPipe result has wrong pose count")

    if not isinstance(
        result["pose_landmarks"],
        dict
    ):
        raise ValueError("FAIL: Valid MediaPipe result was not converted to dictionary")

    print("PASS: MediaPipe pose result converts to backend-independent landmark format")


def test_timestamp_conversion_is_deterministic():
    result = timestamp_seconds_to_milliseconds(
        1.234
    )

    if result != 1234:
        raise ValueError(f"FAIL: Expected 1234 milliseconds, got {result}")

    print("PASS: Pose video timestamps convert deterministically to milliseconds")


def test_missing_model_path_is_rejected_before_inference():
    try:
        validate_model_path(
            "this-model-does-not-exist.task"
        )

    except PoseModelNotFoundError:
        print("PASS: Pose backend refuses to start without explicit model asset")
        return

    raise ValueError("FAIL: Missing pose model was accepted")


if __name__ == "__main__":
    test_rgb_frame_validation_accepts_uint8_three_channel_image()
    test_non_uint8_frame_is_rejected()
    test_wrong_channel_count_is_rejected()
    test_empty_pose_result_is_normalized()
    test_relevant_pose_landmark_indexes_are_mapped()
    test_visibility_and_presence_use_conservative_confidence()
    test_missing_landmark_confidence_fails_closed()
    test_coordinates_outside_image_range_remain_observable()
    test_incomplete_mediapipe_landmark_set_is_rejected()
    test_detected_pose_result_is_normalized()
    test_timestamp_conversion_is_deterministic()
    test_missing_model_path_is_rejected_before_inference()