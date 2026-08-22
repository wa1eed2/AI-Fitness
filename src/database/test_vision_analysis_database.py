from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.database.query_vision_analysis_database import (
    count_user_vision_analyses,
    create_vision_analysis,
    delete_vision_analysis,
    get_user_vision_analyses,
    get_vision_analysis
)

from src.database.setup_vision_database import (
    setup_vision_database
)


def build_analysis_result(
    rep_count=2,
    status="analyzed"
):
    return {
        "status": status,
        "exercise": "squat",
        "source": "video",
        "pose_backend": "mediapipe_pose_landmarker",
        "rep_count": rep_count,
        "video": {
            "fps": 30.0,
            "reported_frame_count": 120,
            "decoded_frame_count": 120,
            "sampled_frame_count": 120,
            "sample_every_n_frames": 1,
            "width": 1280,
            "height": 720,
            "reported_duration_seconds": 4.0
        },
        "detection_summary": {
            "pose_detected_frame_count": 100,
            "no_pose_frame_count": 20,
            "insufficient_landmark_frame_count": 0
        },
        "repetitions": [
            {
                "repetition_number": index + 1,
                "duration_seconds": 2.0,
                "knee_range_of_motion_degrees": 75.0
            }
            for index in range(
                rep_count
            )
        ],
        "summary": {
            "average_rep_duration_seconds": (
                2.0
                if rep_count
                else None
            ),
            "average_range_of_motion_degrees": (
                75.0
                if rep_count
                else None
            ),
            "variability_classification": (
                "low_variability"
                if rep_count >= 2
                else "insufficient_repetitions"
            )
        },
        "limitations": [
            "Observed 2D geometry does not determine medical safety."
        ]
    }


def test_vision_analysis_can_be_stored_and_retrieved():
    user_id = create_user()

    try:
        created = create_vision_analysis(
            user_id=user_id,
            source_filename="squat.mp4",
            file_size_bytes=1024,
            sample_every_n_frames=1,
            analysis_result=build_analysis_result()
        )

        loaded = get_vision_analysis(
            user_id,
            created[
                "analysis_id"
            ]
        )

        if loaded is None:
            raise ValueError(
                "FAIL: Stored vision analysis could not be retrieved"
            )

        if loaded["rep_count"] != 2:
            raise ValueError(
                "FAIL: Stored rep count did not round-trip"
            )

        print("PASS: Vision analysis can be stored and retrieved")

    finally:
        delete_user(
            user_id
        )


def test_structured_vision_json_round_trips():
    user_id = create_user()

    try:
        created = create_vision_analysis(
            user_id=user_id,
            source_filename="geometry.mp4",
            file_size_bytes=2048,
            sample_every_n_frames=2,
            analysis_result=build_analysis_result()
        )

        result = created[
            "analysis_result"
        ]

        if result[
            "summary"
        ][
            "average_range_of_motion_degrees"
        ] != 75.0:
            raise ValueError(
                "FAIL: Structured vision metrics did not round-trip"
            )

        if len(
            result[
                "repetitions"
            ]
        ) != 2:
            raise ValueError(
                "FAIL: Repetition JSON did not round-trip"
            )

        print("PASS: Structured vision result round-trips through SQLite")

    finally:
        delete_user(
            user_id
        )


def test_vision_analysis_is_owner_scoped():
    owner_id = create_user()
    other_user_id = create_user()

    try:
        created = create_vision_analysis(
            user_id=owner_id,
            source_filename="owner.mp4",
            file_size_bytes=500,
            sample_every_n_frames=1,
            analysis_result=build_analysis_result()
        )

        hidden = get_vision_analysis(
            other_user_id,
            created[
                "analysis_id"
            ]
        )

        if hidden is not None:
            raise ValueError(
                "FAIL: Cross-user vision analysis was visible"
            )

        print("PASS: Vision analysis persistence is owner scoped")

    finally:
        delete_user(
            owner_id
        )

        delete_user(
            other_user_id
        )


def test_vision_analysis_history_can_be_listed():
    user_id = create_user()

    try:
        create_vision_analysis(
            user_id=user_id,
            source_filename="first.mp4",
            file_size_bytes=500,
            sample_every_n_frames=1,
            analysis_result=build_analysis_result(
                rep_count=1
            )
        )

        create_vision_analysis(
            user_id=user_id,
            source_filename="second.mp4",
            file_size_bytes=600,
            sample_every_n_frames=1,
            analysis_result=build_analysis_result(
                rep_count=3
            )
        )

        history = get_user_vision_analyses(
            user_id
        )

        if len(
            history
        ) != 2:
            raise ValueError(
                "FAIL: Vision analysis history has wrong count"
            )

        print("PASS: User vision analysis history can be listed")

    finally:
        delete_user(
            user_id
        )


def test_vision_analysis_count_is_user_scoped():
    user_id = create_user()

    try:
        create_vision_analysis(
            user_id=user_id,
            source_filename="count.mp4",
            file_size_bytes=500,
            sample_every_n_frames=1,
            analysis_result=build_analysis_result()
        )

        count = count_user_vision_analyses(
            user_id
        )

        if count != 1:
            raise ValueError(
                f"FAIL: Expected 1 stored vision analysis, got {count}"
            )

        print("PASS: Vision analysis count is user scoped")

    finally:
        delete_user(
            user_id
        )


def test_vision_analysis_can_be_deleted():
    user_id = create_user()

    try:
        created = create_vision_analysis(
            user_id=user_id,
            source_filename="delete.mp4",
            file_size_bytes=500,
            sample_every_n_frames=1,
            analysis_result=build_analysis_result()
        )

        deleted = delete_vision_analysis(
            user_id,
            created[
                "analysis_id"
            ]
        )

        if deleted is not True:
            raise ValueError(
                "FAIL: Vision analysis was not deleted"
            )

        if get_vision_analysis(
            user_id,
            created[
                "analysis_id"
            ]
        ) is not None:
            raise ValueError(
                "FAIL: Deleted vision analysis still exists"
            )

        print("PASS: Vision analysis can be explicitly deleted")

    finally:
        delete_user(
            user_id
        )


def test_cross_user_delete_is_blocked():
    owner_id = create_user()
    other_user_id = create_user()

    try:
        created = create_vision_analysis(
            user_id=owner_id,
            source_filename="private.mp4",
            file_size_bytes=500,
            sample_every_n_frames=1,
            analysis_result=build_analysis_result()
        )

        deleted = delete_vision_analysis(
            other_user_id,
            created[
                "analysis_id"
            ]
        )

        if deleted:
            raise ValueError(
                "FAIL: Cross-user vision analysis deletion succeeded"
            )

        if get_vision_analysis(
            owner_id,
            created[
                "analysis_id"
            ]
        ) is None:
            raise ValueError(
                "FAIL: Cross-user deletion removed owner's analysis"
            )

        print("PASS: Vision analysis deletion is owner scoped")

    finally:
        delete_user(
            owner_id
        )

        delete_user(
            other_user_id
        )


if __name__ == "__main__":
    setup_vision_database()

    test_vision_analysis_can_be_stored_and_retrieved()
    test_structured_vision_json_round_trips()
    test_vision_analysis_is_owner_scoped()
    test_vision_analysis_history_can_be_listed()
    test_vision_analysis_count_is_user_scoped()
    test_vision_analysis_can_be_deleted()
    test_cross_user_delete_is_blocked()