from pathlib import Path

import numpy as np

from src.vision.mediapipe_pose_adapter import (
    DETECTION_STATUS_NO_POSE,
    DETECTION_STATUS_POSE_DETECTED,
    RUNNING_MODE_IMAGE,
    MediaPipePoseAdapter,
    load_mediapipe_module
)


MODEL_PATH = Path(
    "data/models/pose_landmarker_lite.task"
)


def test_mediapipe_tasks_api_is_available():
    mp = load_mediapipe_module()

    if not hasattr(
        mp.tasks.vision,
        "PoseLandmarker"
    ):
        raise ValueError("FAIL: MediaPipe PoseLandmarker is unavailable")

    if not hasattr(
        mp.tasks.vision,
        "PoseLandmarkerOptions"
    ):
        raise ValueError("FAIL: MediaPipe PoseLandmarkerOptions is unavailable")

    if not hasattr(
        mp.tasks.vision,
        "RunningMode"
    ):
        raise ValueError("FAIL: MediaPipe vision RunningMode is unavailable")

    print("PASS: Installed MediaPipe exposes current Pose Landmarker Tasks API")


def test_pose_model_asset_exists():
    if not MODEL_PATH.is_file():
        raise ValueError(
            f"FAIL: Download pose model to {MODEL_PATH} before running environment smoke test"
        )

    if MODEL_PATH.stat().st_size <= 0:
        raise ValueError("FAIL: Pose model asset is empty")

    print("PASS: Local Pose Landmarker model asset is available")


def test_pose_landmarker_can_initialize():
    with MediaPipePoseAdapter(
        model_path=str(
            MODEL_PATH
        ),
        running_mode=RUNNING_MODE_IMAGE
    ) as adapter:
        if adapter.running_mode != RUNNING_MODE_IMAGE:
            raise ValueError("FAIL: Pose Landmarker initialized in wrong mode")

    print("PASS: MediaPipe Pose Landmarker initializes and closes successfully")


def test_blank_rgb_inference_executes_locally():
    frame = np.zeros(
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
        running_mode=RUNNING_MODE_IMAGE
    ) as adapter:
        result = adapter.detect_image_rgb(
            frame
        )

    if result["status"] not in {
        DETECTION_STATUS_NO_POSE,
        DETECTION_STATUS_POSE_DETECTED
    }:
        raise ValueError("FAIL: Local pose inference returned unknown status")

    if result["backend"] != "mediapipe_pose_landmarker":
        raise ValueError("FAIL: Pose inference backend metadata is incorrect")

    if result["running_mode"] != RUNNING_MODE_IMAGE:
        raise ValueError("FAIL: Pose inference mode metadata is incorrect")

    print("PASS: MediaPipe performs local RGB pose inference without external API")


if __name__ == "__main__":
    test_mediapipe_tasks_api_is_available()
    test_pose_model_asset_exists()
    test_pose_landmarker_can_initialize()
    test_blank_rgb_inference_executes_locally()