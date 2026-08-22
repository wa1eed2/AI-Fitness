import math
import os
from numbers import Real

import numpy as np


BACKEND_NAME = "mediapipe_pose_landmarker"

RUNNING_MODE_IMAGE = "image"
RUNNING_MODE_VIDEO = "video"

DETECTION_STATUS_POSE_DETECTED = "pose_detected"
DETECTION_STATUS_NO_POSE = "no_pose"

EXPECTED_POSE_LANDMARK_COUNT = 33


LANDMARK_INDEX_MAP = {
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28
}


class PoseBackendUnavailableError(RuntimeError):
    pass


class PoseModelNotFoundError(FileNotFoundError):
    pass


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
        raise ValueError(f"{field_name} must be between 0 and 1")

    return normalized


def validate_running_mode(
    running_mode
):
    if running_mode not in {
        RUNNING_MODE_IMAGE,
        RUNNING_MODE_VIDEO
    }:
        raise ValueError("running_mode must be image or video")

    return running_mode


def validate_model_path(
    model_path
):
    if not isinstance(model_path, str) or not model_path.strip():
        raise ValueError("model_path must be a non-empty string")

    normalized = os.path.abspath(
        model_path.strip()
    )

    if not os.path.isfile(
        normalized
    ):
        raise PoseModelNotFoundError(
            f"Pose model was not found: {normalized}"
        )

    return normalized


def validate_num_poses(
    num_poses
):
    if not isinstance(num_poses, int) or isinstance(num_poses, bool):
        raise ValueError("num_poses must be an integer")

    if num_poses != 1:
        raise ValueError(
            "AI-Fitness currently requires num_poses=1 to avoid multi-person ambiguity"
        )

    return num_poses


def validate_rgb_frame(
    rgb_frame
):
    if not isinstance(rgb_frame, np.ndarray):
        raise ValueError("rgb_frame must be a NumPy array")

    if rgb_frame.ndim != 3:
        raise ValueError("rgb_frame must have height, width, and channel dimensions")

    if rgb_frame.shape[
        2
    ] != 3:
        raise ValueError("rgb_frame must contain exactly 3 RGB channels")

    if rgb_frame.shape[
        0
    ] < 1 or rgb_frame.shape[
        1
    ] < 1:
        raise ValueError("rgb_frame must have non-zero dimensions")

    if rgb_frame.dtype != np.uint8:
        raise ValueError("rgb_frame must use uint8 pixel values")

    return np.ascontiguousarray(
        rgb_frame
    )


def load_mediapipe_module():
    try:
        import mediapipe as mp

    except ImportError as error:
        raise PoseBackendUnavailableError(
            "MediaPipe is not installed or could not be imported"
        ) from error

    tasks = getattr(
        mp,
        "tasks",
        None
    )

    if tasks is None:
        raise PoseBackendUnavailableError(
            "Installed MediaPipe package does not expose the Tasks API"
        )

    vision = getattr(
        tasks,
        "vision",
        None
    )

    if vision is None:
        raise PoseBackendUnavailableError(
            "Installed MediaPipe package does not expose vision tasks"
        )

    required_symbols = (
        "PoseLandmarker",
        "PoseLandmarkerOptions",
        "RunningMode"
    )

    for symbol in required_symbols:
        if not hasattr(
            vision,
            symbol
        ):
            raise PoseBackendUnavailableError(
                f"Installed MediaPipe package does not expose vision.{symbol}"
            )

    if not hasattr(
        tasks,
        "BaseOptions"
    ):
        raise PoseBackendUnavailableError(
            "Installed MediaPipe package does not expose BaseOptions"
        )

    if not hasattr(
        mp,
        "Image"
    ) or not hasattr(
        mp,
        "ImageFormat"
    ):
        raise PoseBackendUnavailableError(
            "Installed MediaPipe package does not expose image containers"
        )

    return mp


def normalize_optional_confidence(
    value,
    field_name
):
    if value is None:
        return None

    return validate_probability(
        value,
        field_name
    )


def get_landmark_confidence(
    landmark
):
    visibility = normalize_optional_confidence(
        getattr(
            landmark,
            "visibility",
            None
        ),
        "landmark.visibility"
    )

    presence = normalize_optional_confidence(
        getattr(
            landmark,
            "presence",
            None
        ),
        "landmark.presence"
    )

    available_scores = [
        value
        for value in (
            visibility,
            presence
        )
        if value is not None
    ]

    if not available_scores:
        return 0.0

    return min(
        available_scores
    )


def convert_mediapipe_landmark(
    landmark
):
    if landmark is None:
        raise ValueError("MediaPipe landmark cannot be None")

    x = validate_numeric(
        getattr(
            landmark,
            "x",
            None
        ),
        "landmark.x"
    )

    y = validate_numeric(
        getattr(
            landmark,
            "y",
            None
        ),
        "landmark.y"
    )

    return {
        "x": x,
        "y": y,
        "visibility": get_landmark_confidence(
            landmark
        )
    }


def convert_pose_landmarks(
    landmarks
):
    if landmarks is None:
        raise ValueError("Pose landmarks cannot be None")

    try:
        landmark_count = len(
            landmarks
        )

    except TypeError as error:
        raise ValueError(
            "Pose landmarks must be an indexed collection"
        ) from error

    if landmark_count < EXPECTED_POSE_LANDMARK_COUNT:
        raise ValueError(
            f"Pose result requires at least {EXPECTED_POSE_LANDMARK_COUNT} landmarks"
        )

    converted = {}

    for name, index in LANDMARK_INDEX_MAP.items():
        converted[
            name
        ] = convert_mediapipe_landmark(
            landmarks[
                index
            ]
        )

    return converted


def convert_pose_landmarker_result(
    result
):
    if result is None:
        raise ValueError("Pose Landmarker result cannot be None")

    detected_poses = getattr(
        result,
        "pose_landmarks",
        None
    )

    if detected_poses is None:
        raise ValueError("Pose Landmarker result does not contain pose_landmarks")

    pose_count = len(
        detected_poses
    )

    if pose_count == 0:
        return {
            "status": DETECTION_STATUS_NO_POSE,
            "pose_count": 0,
            "pose_landmarks": None
        }

    converted = convert_pose_landmarks(
        detected_poses[
            0
        ]
    )

    return {
        "status": DETECTION_STATUS_POSE_DETECTED,
        "pose_count": pose_count,
        "pose_landmarks": converted
    }


def create_mediapipe_image(
    rgb_frame,
    mediapipe_module=None
):
    frame = validate_rgb_frame(
        rgb_frame
    )

    if mediapipe_module is None:
        mediapipe_module = load_mediapipe_module()

    return mediapipe_module.Image(
        image_format=mediapipe_module.ImageFormat.SRGB,
        data=frame
    )


def timestamp_seconds_to_milliseconds(
    timestamp_seconds
):
    timestamp = validate_numeric(
        timestamp_seconds,
        "timestamp_seconds"
    )

    if timestamp < 0:
        raise ValueError("timestamp_seconds cannot be negative")

    return int(
        round(
            timestamp
            * 1000
        )
    )


def build_pose_landmarker(
    model_path,
    running_mode=RUNNING_MODE_IMAGE,
    min_pose_detection_confidence=0.5,
    min_pose_presence_confidence=0.5,
    min_tracking_confidence=0.5,
    num_poses=1,
    mediapipe_module=None
):
    normalized_model_path = validate_model_path(
        model_path
    )

    running_mode = validate_running_mode(
        running_mode
    )

    validate_num_poses(
        num_poses
    )

    detection_confidence = validate_probability(
        min_pose_detection_confidence,
        "min_pose_detection_confidence"
    )

    presence_confidence = validate_probability(
        min_pose_presence_confidence,
        "min_pose_presence_confidence"
    )

    tracking_confidence = validate_probability(
        min_tracking_confidence,
        "min_tracking_confidence"
    )

    if mediapipe_module is None:
        mediapipe_module = load_mediapipe_module()

    vision = mediapipe_module.tasks.vision

    if running_mode == RUNNING_MODE_IMAGE:
        vision_running_mode = vision.RunningMode.IMAGE

    else:
        vision_running_mode = vision.RunningMode.VIDEO

    options = vision.PoseLandmarkerOptions(
        base_options=mediapipe_module.tasks.BaseOptions(
            model_asset_path=normalized_model_path
        ),
        running_mode=vision_running_mode,
        num_poses=num_poses,
        min_pose_detection_confidence=detection_confidence,
        min_pose_presence_confidence=presence_confidence,
        min_tracking_confidence=tracking_confidence,
        output_segmentation_masks=False
    )

    return vision.PoseLandmarker.create_from_options(
        options
    )


class MediaPipePoseAdapter:
    def __init__(
        self,
        model_path,
        running_mode=RUNNING_MODE_IMAGE,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        num_poses=1
    ):
        self.model_path = validate_model_path(
            model_path
        )

        self.running_mode = validate_running_mode(
            running_mode
        )

        self._mediapipe = load_mediapipe_module()

        self._task = build_pose_landmarker(
            model_path=self.model_path,
            running_mode=self.running_mode,
            min_pose_detection_confidence=min_pose_detection_confidence,
            min_pose_presence_confidence=min_pose_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
            num_poses=num_poses,
            mediapipe_module=self._mediapipe
        )

        self._last_timestamp_ms = None
        self._closed = False

    def ensure_open(self):
        if self._closed:
            raise RuntimeError("Pose adapter is already closed")

    def detect_image_rgb(
        self,
        rgb_frame
    ):
        self.ensure_open()

        if self.running_mode != RUNNING_MODE_IMAGE:
            raise ValueError("detect_image_rgb requires image running mode")

        image = create_mediapipe_image(
            rgb_frame,
            mediapipe_module=self._mediapipe
        )

        result = self._task.detect(
            image
        )

        normalized = convert_pose_landmarker_result(
            result
        )

        normalized[
            "backend"
        ] = BACKEND_NAME

        normalized[
            "running_mode"
        ] = self.running_mode

        normalized[
            "timestamp_seconds"
        ] = None

        return normalized

    def detect_video_frame_rgb(
        self,
        rgb_frame,
        timestamp_seconds
    ):
        self.ensure_open()

        if self.running_mode != RUNNING_MODE_VIDEO:
            raise ValueError("detect_video_frame_rgb requires video running mode")

        timestamp_ms = timestamp_seconds_to_milliseconds(
            timestamp_seconds
        )

        if (
            self._last_timestamp_ms is not None
            and timestamp_ms <= self._last_timestamp_ms
        ):
            raise ValueError(
                "Video timestamps must remain strictly increasing after millisecond conversion"
            )

        image = create_mediapipe_image(
            rgb_frame,
            mediapipe_module=self._mediapipe
        )

        result = self._task.detect_for_video(
            image,
            timestamp_ms
        )

        self._last_timestamp_ms = timestamp_ms

        normalized = convert_pose_landmarker_result(
            result
        )

        normalized[
            "backend"
        ] = BACKEND_NAME

        normalized[
            "running_mode"
        ] = self.running_mode

        normalized[
            "timestamp_seconds"
        ] = float(
            timestamp_seconds
        )

        return normalized

    def close(self):
        if self._closed:
            return

        self._task.close()

        self._closed = True

    def __enter__(self):
        self.ensure_open()

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ):
        self.close()