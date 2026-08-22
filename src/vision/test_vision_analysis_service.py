import os
import tempfile


from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.database.setup_vision_database import (
    setup_vision_database
)

from src.vision.vision_analysis_service import (
    analyze_and_store_squat_video,
    sanitize_vision_analysis_result,
    validate_upload_filename,
    validate_upload_size
)


def build_result(
    video_path
):
    return {
        "status": "analyzed",
        "exercise": "squat",
        "source": "video",
        "pose_backend": "fake_pose_backend",
        "rep_count": 1,
        "video": {
            "path": video_path,
            "fps": 30.0,
            "reported_frame_count": 90,
            "decoded_frame_count": 90,
            "sampled_frame_count": 90,
            "sample_every_n_frames": 1,
            "width": 640,
            "height": 480,
            "reported_duration_seconds": 3.0
        },
        "detection_summary": {
            "pose_detected_frame_count": 80,
            "no_pose_frame_count": 10,
            "insufficient_landmark_frame_count": 0
        },
        "rep_count": 1,
        "repetitions": [
            {
                "repetition_number": 1,
                "duration_seconds": 2.5,
                "knee_range_of_motion_degrees": 70.0
            }
        ],
        "summary": {
            "average_rep_duration_seconds": 2.5,
            "average_range_of_motion_degrees": 70.0,
            "variability_classification": "insufficient_repetitions"
        },
        "limitations": [
            "Observed geometry does not establish medical safety."
        ],
        "frame_observations": [
            {
                "timestamp_seconds": 0.0,
                "analyzable": True
            }
        ]
    }


def temporary_video_file():
    handle = tempfile.NamedTemporaryFile(
        suffix=".mp4",
        delete=False
    )

    handle.write(
        b"fake-video-data"
    )

    path = handle.name

    handle.close()

    return path


def test_upload_filename_validation():
    if validate_upload_filename(
        "squat.mp4"
    ) != "squat.mp4":
        raise ValueError(
            "FAIL: Valid upload filename changed"
        )

    print("PASS: Vision service validates supported upload filename")


def test_upload_filename_rejects_paths():
    try:
        validate_upload_filename(
            "../private/video.mp4"
        )

    except ValueError:
        print("PASS: Vision service rejects client-supplied filesystem paths")
        return

    raise ValueError(
        "FAIL: Client filesystem path was accepted as filename"
    )


def test_upload_size_is_bounded():
    try:
        validate_upload_size(
            50
            * 1024
            * 1024
            + 1
        )

    except ValueError:
        print("PASS: Vision service enforces bounded video upload size")
        return

    raise ValueError(
        "FAIL: Oversized video upload was accepted"
    )


def test_sanitizer_removes_temporary_path_and_frame_observations():
    result = sanitize_vision_analysis_result(
        build_result(
            "C:/temporary/private-file.mp4"
        )
    )

    if "path" in result[
        "video"
    ]:
        raise ValueError(
            "FAIL: Temporary filesystem path survived sanitization"
        )

    if "frame_observations" in result:
        raise ValueError(
            "FAIL: Per-frame observations survived persistence sanitization"
        )

    print("PASS: Vision persistence strips temporary paths and per-frame observations")


def test_analyzer_is_called_with_privacy_safe_options():
    user_id = create_user()
    video_path = temporary_video_file()

    calls = []

    def analyzer(
        **kwargs
    ):
        calls.append(
            kwargs
        )

        return build_result(
            kwargs[
                "video_path"
            ]
        )

    try:
        analyze_and_store_squat_video(
            user_id=user_id,
            video_path=video_path,
            original_filename="squat.mp4",
            file_size_bytes=os.path.getsize(
                video_path
            ),
            model_path="unused.task",
            sample_every_n_frames=2,
            max_analyzed_frames=100,
            analyzer=analyzer
        )

        if len(
            calls
        ) != 1:
            raise ValueError(
                "FAIL: Vision analyzer call count is incorrect"
            )

        call = calls[
            0
        ]

        if call["include_frame_observations"] is not False:
            raise ValueError(
                "FAIL: Persistence workflow requested raw frame observations"
            )

        if call["sample_every_n_frames"] != 2:
            raise ValueError(
                "FAIL: Sampling option was not passed deterministically"
            )

        if call["max_analyzed_frames"] != 100:
            raise ValueError(
                "FAIL: Frame bound was not passed to analyzer"
            )

        print("PASS: Vision service calls analyzer with bounded privacy-safe options")

    finally:
        if os.path.isfile(
            video_path
        ):
            os.remove(
                video_path
            )

        delete_user(
            user_id
        )


def test_sanitized_analysis_is_persisted():
    user_id = create_user()
    video_path = temporary_video_file()

    def analyzer(
        **kwargs
    ):
        return build_result(
            kwargs[
                "video_path"
            ]
        )

    try:
        saved = analyze_and_store_squat_video(
            user_id=user_id,
            video_path=video_path,
            original_filename="user-squat.mp4",
            file_size_bytes=os.path.getsize(
                video_path
            ),
            model_path="unused.task",
            analyzer=analyzer
        )

        result = saved[
            "analysis_result"
        ]

        if saved["source_filename"] != "user-squat.mp4":
            raise ValueError(
                "FAIL: Original safe filename was not retained"
            )

        if result["rep_count"] != 1:
            raise ValueError(
                "FAIL: Structured analysis was not persisted"
            )

        if "path" in result[
            "video"
        ]:
            raise ValueError(
                "FAIL: Temporary path was persisted"
            )

        if "frame_observations" in result:
            raise ValueError(
                "FAIL: Per-frame observations were persisted"
            )

        print("PASS: Vision service persists only sanitized structured analysis")

    finally:
        if os.path.isfile(
            video_path
        ):
            os.remove(
                video_path
            )

        delete_user(
            user_id
        )


if __name__ == "__main__":
    setup_vision_database()

    test_upload_filename_validation()
    test_upload_filename_rejects_paths()
    test_upload_size_is_bounded()
    test_sanitizer_removes_temporary_path_and_frame_observations()
    test_analyzer_is_called_with_privacy_safe_options()
    test_sanitized_analysis_is_persisted()