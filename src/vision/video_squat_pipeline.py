import math
import os
from numbers import Real

import numpy as np

from src.vision.mediapipe_pose_adapter import (
    BACKEND_NAME,
    DETECTION_STATUS_NO_POSE,
    DETECTION_STATUS_POSE_DETECTED,
    RUNNING_MODE_VIDEO,
    MediaPipePoseAdapter
)

from src.vision.squat_analysis import (
    ANALYSIS_STATUS_ANALYZABLE,
    MIN_REQUIRED_VISIBILITY,
    analyze_squat_frame
)

from src.vision.squat_movement_metrics import (
    VIEW_BILATERAL_OBSERVABLE,
    VIEW_INSUFFICIENT,
    VIEW_SINGLE_SIDE_OBSERVABLE,
    analyze_bilateral_squat_frame,
    enrich_repetitions_with_confidence,
    summarize_bilateral_frame_metrics
)

from src.vision.squat_repetition_analysis import (
    BOTTOM_ANGLE_MAX,
    MAX_ACTIVE_FRAME_GAP_SECONDS,
    MAX_REP_DURATION_SECONDS,
    MIN_FRAME_CONFIDENCE,
    MIN_REP_DURATION_SECONDS,
    MIN_REP_RANGE_OF_MOTION_DEGREES,
    STANDING_ANGLE_MIN,
    analyze_squat_angle_sequence
)


VIDEO_SOURCE = "video"


class VideoBackendUnavailableError(RuntimeError):
    pass


class VideoOpenError(ValueError):
    pass


class VideoMetadataError(ValueError):
    pass


class VideoDecodeError(ValueError):
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


def validate_positive_integer(
    value,
    field_name
):
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")

    if value < 1:
        raise ValueError(f"{field_name} must be at least 1")

    return value


def validate_nonnegative_integer(
    value,
    field_name
):
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")

    if value < 0:
        raise ValueError(f"{field_name} cannot be negative")

    return value


def validate_optional_positive_integer(
    value,
    field_name
):
    if value is None:
        return None

    return validate_positive_integer(
        value,
        field_name
    )


def validate_video_path(
    video_path
):
    if not isinstance(video_path, str) or not video_path.strip():
        raise ValueError("video_path must be a non-empty string")

    normalized = os.path.abspath(
        video_path.strip()
    )

    if not os.path.isfile(
        normalized
    ):
        raise VideoOpenError(
            f"Video file was not found: {normalized}"
        )

    return normalized


def load_cv2_module():
    try:
        import cv2

    except ImportError as error:
        raise VideoBackendUnavailableError(
            "OpenCV is not installed or could not be imported"
        ) from error

    required_symbols = (
        "VideoCapture",
        "cvtColor",
        "COLOR_BGR2RGB",
        "CAP_PROP_FPS",
        "CAP_PROP_FRAME_COUNT",
        "CAP_PROP_FRAME_WIDTH",
        "CAP_PROP_FRAME_HEIGHT"
    )

    for symbol in required_symbols:
        if not hasattr(
            cv2,
            symbol
        ):
            raise VideoBackendUnavailableError(
                f"Installed OpenCV package does not expose {symbol}"
            )

    return cv2


def validate_bgr_frame(
    frame
):
    if not isinstance(frame, np.ndarray):
        raise VideoDecodeError(
            "Decoded video frame must be a NumPy array"
        )

    if frame.ndim != 3:
        raise VideoDecodeError(
            "Decoded video frame must have height, width, and channel dimensions"
        )

    if frame.shape[
        2
    ] != 3:
        raise VideoDecodeError(
            "Decoded video frame must contain exactly three BGR channels"
        )

    if (
        frame.shape[
            0
        ] < 1
        or frame.shape[
            1
        ] < 1
    ):
        raise VideoDecodeError(
            "Decoded video frame must have non-zero dimensions"
        )

    if frame.dtype != np.uint8:
        raise VideoDecodeError(
            "Decoded video frame must use uint8 pixels"
        )

    return np.ascontiguousarray(
        frame
    )


def convert_bgr_to_rgb(
    frame,
    cv2_module
):
    normalized = validate_bgr_frame(
        frame
    )

    converted = cv2_module.cvtColor(
        normalized,
        cv2_module.COLOR_BGR2RGB
    )

    if not isinstance(converted, np.ndarray):
        raise VideoDecodeError(
            "OpenCV color conversion returned invalid frame data"
        )

    return np.ascontiguousarray(
        converted
    )


def read_video_metadata(
    capture,
    cv2_module
):
    fps = validate_numeric(
        capture.get(
            cv2_module.CAP_PROP_FPS
        ),
        "video_fps"
    )

    if fps <= 0:
        raise VideoMetadataError(
            "Video FPS metadata must be greater than 0"
        )

    frame_count_raw = validate_numeric(
        capture.get(
            cv2_module.CAP_PROP_FRAME_COUNT
        ),
        "video_frame_count"
    )

    width_raw = validate_numeric(
        capture.get(
            cv2_module.CAP_PROP_FRAME_WIDTH
        ),
        "video_width"
    )

    height_raw = validate_numeric(
        capture.get(
            cv2_module.CAP_PROP_FRAME_HEIGHT
        ),
        "video_height"
    )

    frame_count = (
        int(
            round(
                frame_count_raw
            )
        )
        if frame_count_raw > 0
        else None
    )

    width = (
        int(
            round(
                width_raw
            )
        )
        if width_raw > 0
        else None
    )

    height = (
        int(
            round(
                height_raw
            )
        )
        if height_raw > 0
        else None
    )

    duration_seconds = None

    if frame_count is not None:
        duration_seconds = round(
            frame_count
            / fps,
            3
        )

    return {
        "fps": fps,
        "reported_frame_count": frame_count,
        "width": width,
        "height": height,
        "reported_duration_seconds": duration_seconds
    }


def build_frame_timestamp(
    frame_index,
    fps,
    previous_timestamp_ms=None
):
    validate_positive_integer(
        frame_index + 1,
        "frame_index_plus_one"
    )

    fps = validate_numeric(
        fps,
        "fps"
    )

    if fps <= 0:
        raise ValueError(
            "fps must be greater than 0"
        )

    raw_timestamp_ms = int(
        round(
            (
                frame_index
                / fps
            )
            * 1000
        )
    )

    if (
        previous_timestamp_ms is not None
        and raw_timestamp_ms <= previous_timestamp_ms
    ):
        timestamp_ms = (
            previous_timestamp_ms
            + 1
        )

    else:
        timestamp_ms = raw_timestamp_ms

    return {
        "timestamp_ms": timestamp_ms,
        "timestamp_seconds": (
            timestamp_ms
            / 1000
        )
    }


def build_angle_observation_from_detection(
    detection,
    timestamp_seconds,
    minimum_visibility=MIN_REQUIRED_VISIBILITY
):
    if not isinstance(detection, dict):
        raise ValueError(
            "Pose adapter detection must be a dictionary"
        )

    status = detection.get(
        "status"
    )

    if status == DETECTION_STATUS_NO_POSE:
        return {
            "timestamp_seconds": timestamp_seconds,
            "analyzable": False,
            "selected_side": None,
            "frame_analysis_status": "no_pose"
        }

    if status != DETECTION_STATUS_POSE_DETECTED:
        raise ValueError(
            f"Unsupported pose detection status: {status}"
        )

    pose_landmarks = detection.get(
        "pose_landmarks"
    )

    if not isinstance(pose_landmarks, dict):
        raise ValueError(
            "Detected pose requires pose_landmarks dictionary"
        )

    frame_analysis = analyze_squat_frame(
        pose_landmarks,
        minimum_visibility=minimum_visibility
    )

    if frame_analysis[
        "status"
    ] != ANALYSIS_STATUS_ANALYZABLE:
        return {
            "timestamp_seconds": timestamp_seconds,
            "analyzable": False,
            "selected_side": frame_analysis.get(
                "selected_side"
            ),
            "frame_analysis_status": frame_analysis[
                "status"
            ]
        }

    return {
        "timestamp_seconds": timestamp_seconds,
        "analyzable": True,
        "knee_angle_degrees": frame_analysis[
            "measurements"
        ][
            "knee_angle_degrees"
        ],
        "confidence": frame_analysis[
            "confidence"
        ],
        "selected_side": frame_analysis[
            "selected_side"
        ],
        "frame_analysis_status": frame_analysis[
            "status"
        ]
    }


def build_movement_metric_from_detection(
    detection,
    minimum_visibility=MIN_REQUIRED_VISIBILITY
):
    if not isinstance(detection, dict):
        raise ValueError(
            "Pose adapter detection must be a dictionary"
        )

    status = detection.get(
        "status"
    )

    if status == DETECTION_STATUS_NO_POSE:
        return analyze_bilateral_squat_frame(
            {},
            minimum_visibility=minimum_visibility
        )

    if status != DETECTION_STATUS_POSE_DETECTED:
        raise ValueError(
            f"Unsupported pose detection status: {status}"
        )

    pose_landmarks = detection.get(
        "pose_landmarks"
    )

    if not isinstance(pose_landmarks, dict):
        raise ValueError(
            "Detected pose requires pose_landmarks dictionary"
        )

    return analyze_bilateral_squat_frame(
        pose_landmarks,
        minimum_visibility=minimum_visibility
    )


def build_view_suitability_summary(
    movement_metrics_summary
):
    if not isinstance(
        movement_metrics_summary,
        dict
    ):
        raise ValueError(
            "movement_metrics_summary must be a dictionary"
        )

    frame_count = validate_nonnegative_integer(
        movement_metrics_summary.get(
            "frame_count"
        ),
        "frame_count"
    )

    bilateral_count = validate_nonnegative_integer(
        movement_metrics_summary.get(
            "bilateral_observable_frame_count"
        ),
        "bilateral_observable_frame_count"
    )

    single_side_count = validate_nonnegative_integer(
        movement_metrics_summary.get(
            "single_side_observable_frame_count"
        ),
        "single_side_observable_frame_count"
    )

    insufficient_count = validate_nonnegative_integer(
        movement_metrics_summary.get(
            "insufficient_landmark_frame_count"
        ),
        "insufficient_landmark_frame_count"
    )

    if (
        bilateral_count
        + single_side_count
        + insufficient_count
        != frame_count
    ):
        raise ValueError(
            "Movement frame counts must equal frame_count"
        )

    if frame_count == 0:
        return {
            "classification": VIEW_INSUFFICIENT,
            "observable_frame_count": 0,
            "observable_frame_ratio": 0.0,
            "bilateral_frame_ratio": 0.0,
            "single_side_frame_ratio": 0.0,
            "insufficient_frame_ratio": 0.0
        }

    observable_count = (
        bilateral_count
        + single_side_count
    )

    observable_ratio = (
        observable_count
        / frame_count
    )

    bilateral_ratio = (
        bilateral_count
        / frame_count
    )

    single_side_ratio = (
        single_side_count
        / frame_count
    )

    insufficient_ratio = (
        insufficient_count
        / frame_count
    )

    if bilateral_ratio >= 0.50:
        classification = VIEW_BILATERAL_OBSERVABLE

    elif observable_ratio >= 0.50:
        classification = VIEW_SINGLE_SIDE_OBSERVABLE

    else:
        classification = VIEW_INSUFFICIENT

    return {
        "classification": classification,
        "observable_frame_count": observable_count,
        "observable_frame_ratio": round(
            observable_ratio,
            4
        ),
        "bilateral_frame_ratio": round(
            bilateral_ratio,
            4
        ),
        "single_side_frame_ratio": round(
            single_side_ratio,
            4
        ),
        "insufficient_frame_ratio": round(
            insufficient_ratio,
            4
        )
    }


def create_pose_adapter(
    pose_adapter_factory,
    model_path
):
    if pose_adapter_factory is None:
        pose_adapter_factory = MediaPipePoseAdapter

    if not callable(
        pose_adapter_factory
    ):
        raise ValueError(
            "pose_adapter_factory must be callable"
        )

    return pose_adapter_factory(
        model_path=model_path,
        running_mode=RUNNING_MODE_VIDEO
    )


def close_pose_adapter(
    adapter
):
    if adapter is None:
        return

    close_method = getattr(
        adapter,
        "close",
        None
    )

    if callable(
        close_method
    ):
        close_method()


def analyze_squat_video(
    video_path,
    model_path,
    sample_every_n_frames=1,
    max_analyzed_frames=None,
    minimum_visibility=MIN_REQUIRED_VISIBILITY,
    standing_angle_min=STANDING_ANGLE_MIN,
    bottom_angle_max=BOTTOM_ANGLE_MAX,
    minimum_frame_confidence=MIN_FRAME_CONFIDENCE,
    min_rep_duration_seconds=MIN_REP_DURATION_SECONDS,
    max_rep_duration_seconds=MAX_REP_DURATION_SECONDS,
    minimum_rep_range_of_motion_degrees=MIN_REP_RANGE_OF_MOTION_DEGREES,
    max_active_frame_gap_seconds=MAX_ACTIVE_FRAME_GAP_SECONDS,
    include_frame_observations=False,
    pose_adapter_factory=None,
    cv2_module=None
):
    normalized_video_path = validate_video_path(
        video_path
    )

    sample_every_n_frames = validate_positive_integer(
        sample_every_n_frames,
        "sample_every_n_frames"
    )

    max_analyzed_frames = validate_optional_positive_integer(
        max_analyzed_frames,
        "max_analyzed_frames"
    )

    if not isinstance(
        include_frame_observations,
        bool
    ):
        raise ValueError(
            "include_frame_observations must be a boolean"
        )

    if cv2_module is None:
        cv2_module = load_cv2_module()

    capture = cv2_module.VideoCapture(
        normalized_video_path
    )

    adapter = None

    try:
        if not capture.isOpened():
            raise VideoOpenError(
                f"OpenCV could not open video: {normalized_video_path}"
            )

        metadata = read_video_metadata(
            capture,
            cv2_module
        )

        adapter = create_pose_adapter(
            pose_adapter_factory,
            model_path
        )

        angle_observations = []
        movement_frame_metrics = []

        decoded_frame_count = 0
        sampled_frame_count = 0
        pose_detected_frame_count = 0
        no_pose_frame_count = 0
        insufficient_landmark_frame_count = 0

        frame_index = 0
        previous_timestamp_ms = None

        while True:
            if (
                max_analyzed_frames is not None
                and sampled_frame_count
                >= max_analyzed_frames
            ):
                break

            success, frame = capture.read()

            if not success:
                break

            decoded_frame_count += 1

            should_sample = (
                frame_index
                % sample_every_n_frames
                == 0
            )

            if not should_sample:
                frame_index += 1
                continue

            timestamp = build_frame_timestamp(
                frame_index=frame_index,
                fps=metadata[
                    "fps"
                ],
                previous_timestamp_ms=previous_timestamp_ms
            )

            previous_timestamp_ms = timestamp[
                "timestamp_ms"
            ]

            rgb_frame = convert_bgr_to_rgb(
                frame,
                cv2_module
            )

            detection = adapter.detect_video_frame_rgb(
                rgb_frame,
                timestamp[
                    "timestamp_seconds"
                ]
            )

            observation = build_angle_observation_from_detection(
                detection,
                timestamp_seconds=timestamp[
                    "timestamp_seconds"
                ],
                minimum_visibility=minimum_visibility
            )

            movement_metric = build_movement_metric_from_detection(
                detection,
                minimum_visibility=minimum_visibility
            )

            angle_observations.append(
                observation
            )

            movement_frame_metrics.append(
                movement_metric
            )

            sampled_frame_count += 1

            if detection.get(
                "status"
            ) == DETECTION_STATUS_POSE_DETECTED:
                pose_detected_frame_count += 1

            elif detection.get(
                "status"
            ) == DETECTION_STATUS_NO_POSE:
                no_pose_frame_count += 1

            if (
                detection.get(
                    "status"
                ) == DETECTION_STATUS_POSE_DETECTED
                and not observation[
                    "analyzable"
                ]
            ):
                insufficient_landmark_frame_count += 1

            frame_index += 1

        if decoded_frame_count == 0:
            raise VideoDecodeError(
                "Video opened successfully but no frames could be decoded"
            )

        if not angle_observations:
            raise VideoDecodeError(
                "No video frames were selected for pose analysis"
            )

        sequence_result = analyze_squat_angle_sequence(
            frames=angle_observations,
            standing_angle_min=standing_angle_min,
            bottom_angle_max=bottom_angle_max,
            minimum_frame_confidence=minimum_frame_confidence,
            min_rep_duration_seconds=min_rep_duration_seconds,
            max_rep_duration_seconds=max_rep_duration_seconds,
            minimum_rep_range_of_motion_degrees=minimum_rep_range_of_motion_degrees,
            max_active_frame_gap_seconds=max_active_frame_gap_seconds
        )

        enriched_sequence_result = enrich_repetitions_with_confidence(
            sequence_result
        )

        movement_metrics_summary = summarize_bilateral_frame_metrics(
            movement_frame_metrics
        )

        view_suitability_summary = build_view_suitability_summary(
            movement_metrics_summary
        )

        result = dict(
            enriched_sequence_result
        )

        result[
            "source"
        ] = VIDEO_SOURCE

        result[
            "pose_backend"
        ] = BACKEND_NAME

        result[
            "video"
        ] = {
            "path": normalized_video_path,
            "fps": metadata[
                "fps"
            ],
            "reported_frame_count": metadata[
                "reported_frame_count"
            ],
            "decoded_frame_count": decoded_frame_count,
            "sampled_frame_count": sampled_frame_count,
            "sample_every_n_frames": sample_every_n_frames,
            "width": metadata[
                "width"
            ],
            "height": metadata[
                "height"
            ],
            "reported_duration_seconds": metadata[
                "reported_duration_seconds"
            ]
        }

        result[
            "detection_summary"
        ] = {
            "pose_detected_frame_count": pose_detected_frame_count,
            "no_pose_frame_count": no_pose_frame_count,
            "insufficient_landmark_frame_count": insufficient_landmark_frame_count
        }

        result[
            "movement_metrics_summary"
        ] = movement_metrics_summary

        result[
            "view_suitability_summary"
        ] = view_suitability_summary

        if include_frame_observations:
            result[
                "frame_observations"
            ] = angle_observations

        return result

    finally:
        close_pose_adapter(
            adapter
        )

        release_method = getattr(
            capture,
            "release",
            None
        )

        if callable(
            release_method
        ):
            release_method()