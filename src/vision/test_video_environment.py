from pathlib import Path

import numpy as np

from src.vision.mediapipe_pose_adapter import (
    DETECTION_STATUS_NO_POSE,
    DETECTION_STATUS_POSE_DETECTED,
    RUNNING_MODE_VIDEO,
    MediaPipePoseAdapter
)

from src.vision.video_squat_pipeline import (
    load_cv2_module
)


MODEL_PATH = Path(
    "data/models/pose_landmarker_lite.task"
)


def test_opencv_video_backend_is_available():
    cv2 = load_cv2_module()

    version = getattr(
        cv2,
        "__version__",
        None
    )

    if not isinstance(version, str) or not version:
        raise ValueError(
            "FAIL: OpenCV version metadata is unavailable"
        )

    if not hasattr(
        cv2,
        "VideoCapture"
    ):
        raise ValueError(
            "FAIL: OpenCV VideoCapture is unavailable"
        )

    print(
        f"PASS: OpenCV video backend is available ({version})"
    )


def test_opencv_bgr_to_rgb_conversion_executes():
    cv2 = load_cv2_module()

    bgr_frame = np.zeros(
        (
            16,
            16,
            3
        ),
        dtype=np.uint8
    )

    bgr_frame[
        :,
        :
    ] = [
        10,
        20,
        30
    ]

    rgb_frame = cv2.cvtColor(
        bgr_frame,
        cv2.COLOR_BGR2RGB
    )

    pixel = rgb_frame[
        0,
        0
    ].tolist()

    if pixel != [
        30,
        20,
        10
    ]:
        raise ValueError(
            f"FAIL: OpenCV BGR-to-RGB conversion returned {pixel}"
        )

    print("PASS: OpenCV BGR-to-RGB conversion works in local environment")


def test_mediapipe_video_mode_accepts_increasing_timestamps():
    if not MODEL_PATH.is_file():
        raise ValueError(
            f"FAIL: Missing pose model: {MODEL_PATH}"
        )

    first_frame = np.zeros(
        (
            256,
            256,
            3
        ),
        dtype=np.uint8
    )

    second_frame = np.zeros(
        (
            256,
            256,
            3
        ),
        dtype=np.uint8
    )

    with MediaPipePoseAdapter(
        model_path=str(
            MODEL_PATH
        ),
        running_mode=RUNNING_MODE_VIDEO
    ) as adapter:
        first_result = adapter.detect_video_frame_rgb(
            first_frame,
            0.0
        )

        second_result = adapter.detect_video_frame_rgb(
            second_frame,
            0.033
        )

    allowed_statuses = {
        DETECTION_STATUS_NO_POSE,
        DETECTION_STATUS_POSE_DETECTED
    }

    if first_result["status"] not in allowed_statuses:
        raise ValueError(
            "FAIL: First VIDEO-mode inference returned unknown status"
        )

    if second_result["status"] not in allowed_statuses:
        raise ValueError(
            "FAIL: Second VIDEO-mode inference returned unknown status"
        )

    if first_result["timestamp_seconds"] != 0.0:
        raise ValueError(
            "FAIL: First VIDEO-mode timestamp was not retained"
        )

    if second_result["timestamp_seconds"] != 0.033:
        raise ValueError(
            "FAIL: Second VIDEO-mode timestamp was not retained"
        )

    print("PASS: MediaPipe VIDEO mode accepts strictly increasing local timestamps")


if __name__ == "__main__":
    test_opencv_video_backend_is_available()
    test_opencv_bgr_to_rgb_conversion_executes()
    test_mediapipe_video_mode_accepts_increasing_timestamps()