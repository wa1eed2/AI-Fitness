import json
import os
from pathlib import Path


from src.database.query_vision_analysis_database import (
    create_vision_analysis
)

from src.vision.video_squat_pipeline import (
    analyze_squat_video
)


ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv"
}


MAX_VIDEO_UPLOAD_BYTES = (
    50
    * 1024
    * 1024
)


MAX_SAMPLE_EVERY_N_FRAMES = 30
MAX_ANALYZED_FRAMES = 10000


VALID_ANALYSIS_STATUSES = {
    "analyzed",
    "insufficient_data"
}


def validate_upload_filename(
    filename
):
    if not isinstance(filename, str):
        raise ValueError("filename must be a string")

    normalized = filename.strip()

    if not normalized:
        raise ValueError("filename cannot be empty")

    if len(normalized) > 255:
        raise ValueError("filename cannot exceed 255 characters")

    if "/" in normalized or "\\" in normalized:
        raise ValueError(
            "filename must not contain path separators"
        )

    extension = Path(
        normalized
    ).suffix.casefold()

    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValueError(
            "Unsupported video extension"
        )

    return normalized


def get_video_extension(
    filename
):
    normalized = validate_upload_filename(
        filename
    )

    return Path(
        normalized
    ).suffix.casefold()


def validate_upload_size(
    file_size_bytes
):
    if not isinstance(file_size_bytes, int) or isinstance(file_size_bytes, bool):
        raise ValueError("file_size_bytes must be an integer")

    if file_size_bytes < 1:
        raise ValueError("Uploaded video cannot be empty")

    if file_size_bytes > MAX_VIDEO_UPLOAD_BYTES:
        raise ValueError(
            "Uploaded video exceeds maximum allowed size"
        )

    return file_size_bytes


def validate_sample_every_n_frames(
    sample_every_n_frames
):
    if not isinstance(sample_every_n_frames, int) or isinstance(sample_every_n_frames, bool):
        raise ValueError("sample_every_n_frames must be an integer")

    if (
        sample_every_n_frames < 1
        or sample_every_n_frames > MAX_SAMPLE_EVERY_N_FRAMES
    ):
        raise ValueError(
            f"sample_every_n_frames must be between 1 and {MAX_SAMPLE_EVERY_N_FRAMES}"
        )

    return sample_every_n_frames


def validate_max_analyzed_frames(
    max_analyzed_frames
):
    if max_analyzed_frames is None:
        return None

    if not isinstance(max_analyzed_frames, int) or isinstance(max_analyzed_frames, bool):
        raise ValueError("max_analyzed_frames must be an integer")

    if (
        max_analyzed_frames < 1
        or max_analyzed_frames > MAX_ANALYZED_FRAMES
    ):
        raise ValueError(
            f"max_analyzed_frames must be between 1 and {MAX_ANALYZED_FRAMES}"
        )

    return max_analyzed_frames


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
            "Temporary video file does not exist"
        )

    return normalized


def validate_model_path_value(
    model_path
):
    if not isinstance(model_path, str) or not model_path.strip():
        raise ValueError(
            "model_path must be a non-empty string"
        )

    return model_path.strip()


def validate_analyzer(
    analyzer
):
    if analyzer is None:
        return analyze_squat_video

    if not callable(
        analyzer
    ):
        raise ValueError(
            "analyzer must be callable"
        )

    return analyzer


def ensure_json_serializable(
    result
):
    try:
        serialized = json.dumps(
            result,
            ensure_ascii=False
        )

        deserialized = json.loads(
            serialized
        )

    except (
        TypeError,
        ValueError
    ) as error:
        raise ValueError(
            "Vision analysis result must be JSON serializable"
        ) from error

    return deserialized


def sanitize_vision_analysis_result(
    result
):
    if not isinstance(result, dict):
        raise ValueError(
            "Vision analyzer must return a dictionary"
        )

    sanitized = ensure_json_serializable(
        result
    )

    sanitized.pop(
        "frame_observations",
        None
    )

    if sanitized.get(
        "exercise"
    ) != "squat":
        raise ValueError(
            "Vision analyzer returned unsupported exercise"
        )

    if sanitized.get(
        "source"
    ) != "video":
        raise ValueError(
            "Vision analyzer returned unsupported source"
        )

    if sanitized.get(
        "status"
    ) not in VALID_ANALYSIS_STATUSES:
        raise ValueError(
            "Vision analyzer returned unsupported status"
        )

    rep_count = sanitized.get(
        "rep_count"
    )

    if not isinstance(rep_count, int) or isinstance(rep_count, bool):
        raise ValueError(
            "Vision analyzer rep_count must be an integer"
        )

    if rep_count < 0:
        raise ValueError(
            "Vision analyzer rep_count cannot be negative"
        )

    video_metadata = sanitized.get(
        "video"
    )

    if not isinstance(video_metadata, dict):
        raise ValueError(
            "Vision analyzer result requires video metadata"
        )

    video_metadata.pop(
        "path",
        None
    )

    if not isinstance(
        sanitized.get(
            "detection_summary"
        ),
        dict
    ):
        raise ValueError(
            "Vision analyzer result requires detection_summary"
        )

    if not isinstance(
        sanitized.get(
            "summary"
        ),
        dict
    ):
        raise ValueError(
            "Vision analyzer result requires summary"
        )

    if not isinstance(
        sanitized.get(
            "repetitions"
        ),
        list
    ):
        raise ValueError(
            "Vision analyzer result requires repetitions"
        )

    if not isinstance(
        sanitized.get(
            "limitations"
        ),
        list
    ):
        raise ValueError(
            "Vision analyzer result requires limitations"
        )

    return sanitized


def analyze_and_store_squat_video(
    user_id,
    video_path,
    original_filename,
    file_size_bytes,
    model_path,
    sample_every_n_frames=1,
    max_analyzed_frames=None,
    analyzer=None
):
    normalized_video_path = validate_local_video_path(
        video_path
    )

    normalized_filename = validate_upload_filename(
        original_filename
    )

    validate_upload_size(
        file_size_bytes
    )

    validate_sample_every_n_frames(
        sample_every_n_frames
    )

    validate_max_analyzed_frames(
        max_analyzed_frames
    )

    normalized_model_path = validate_model_path_value(
        model_path
    )

    analyzer = validate_analyzer(
        analyzer
    )

    result = analyzer(
        video_path=normalized_video_path,
        model_path=normalized_model_path,
        sample_every_n_frames=sample_every_n_frames,
        max_analyzed_frames=max_analyzed_frames,
        include_frame_observations=False
    )

    sanitized_result = sanitize_vision_analysis_result(
        result
    )

    return create_vision_analysis(
        user_id=user_id,
        source_filename=normalized_filename,
        file_size_bytes=file_size_bytes,
        sample_every_n_frames=sample_every_n_frames,
        analysis_result=sanitized_result
    )