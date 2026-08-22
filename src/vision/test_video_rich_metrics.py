import math
import os
import tempfile

import numpy as np

from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.database.query_vision_analysis_database import (
    create_vision_analysis
)

from src.database.setup_vision_database import (
    setup_vision_database
)

from src.vision.mediapipe_pose_adapter import (
    DETECTION_STATUS_NO_POSE,
    DETECTION_STATUS_POSE_DETECTED
)

from src.vision.squat_movement_metrics import (
    VIEW_BILATERAL_OBSERVABLE,
    VIEW_INSUFFICIENT,
    VIEW_SINGLE_SIDE_OBSERVABLE
)

from src.vision.video_squat_pipeline import (
    analyze_squat_video,
    build_view_suitability_summary
)

from src.vision.vision_analysis_service import (
    sanitize_vision_analysis_result
)


class FakeCapture:
    def __init__(
        self,
        frames,
        fps=2.0
    ):
        self.frames = [
            frame.copy()
            for frame in frames
        ]

        self.fps = fps
        self.index = 0
        self.released = False

    def isOpened(self):
        return True

    def read(self):
        if self.index >= len(
            self.frames
        ):
            return False, None

        frame = self.frames[
            self.index
        ]

        self.index += 1

        return True, frame

    def get(
        self,
        property_id
    ):
        if property_id == FakeCV2.CAP_PROP_FPS:
            return self.fps

        if property_id == FakeCV2.CAP_PROP_FRAME_COUNT:
            return len(
                self.frames
            )

        if property_id == FakeCV2.CAP_PROP_FRAME_WIDTH:
            return self.frames[
                0
            ].shape[
                1
            ]

        if property_id == FakeCV2.CAP_PROP_FRAME_HEIGHT:
            return self.frames[
                0
            ].shape[
                0
            ]

        return 0

    def release(self):
        self.released = True


class FakeCV2:
    COLOR_BGR2RGB = 1

    CAP_PROP_FPS = 10
    CAP_PROP_FRAME_COUNT = 11
    CAP_PROP_FRAME_WIDTH = 12
    CAP_PROP_FRAME_HEIGHT = 13

    def __init__(
        self,
        frames,
        fps=2.0
    ):
        self.capture = FakeCapture(
            frames,
            fps=fps
        )

    def VideoCapture(
        self,
        video_path
    ):
        return self.capture

    def cvtColor(
        self,
        frame,
        conversion
    ):
        if conversion != self.COLOR_BGR2RGB:
            raise ValueError(
                "Unexpected color conversion"
            )

        return frame[
            :,
            :,
            ::-1
        ].copy()


class FakePoseAdapter:
    def __init__(
        self,
        responses
    ):
        self.responses = list(
            responses
        )

        self.index = 0
        self.closed = False

    def detect_video_frame_rgb(
        self,
        frame,
        timestamp_seconds
    ):
        if self.index >= len(
            self.responses
        ):
            raise ValueError(
                "Fake pose adapter ran out of responses"
            )

        response = self.responses[
            self.index
        ]

        self.index += 1

        return response

    def close(self):
        self.closed = True


def create_adapter_factory(
    responses
):
    def factory(
        model_path,
        running_mode
    ):
        return FakePoseAdapter(
            responses
        )

    return factory


def make_frame():
    return np.zeros(
        (
            16,
            16,
            3
        ),
        dtype=np.uint8
    )


def temporary_video_placeholder():
    handle = tempfile.NamedTemporaryFile(
        suffix=".mp4",
        delete=False
    )

    path = handle.name

    handle.close()

    return path


def pose_for_knee_angle(
    angle_degrees,
    left_visibility=0.95,
    right_visibility=0.95
):
    angle_radians = math.radians(
        angle_degrees
    )

    return {
        "left_shoulder": {
            "x": 2.0,
            "y": 0.0,
            "visibility": left_visibility
        },
        "left_hip": {
            "x": 1.0,
            "y": 0.0,
            "visibility": left_visibility
        },
        "left_knee": {
            "x": 0.0,
            "y": 0.0,
            "visibility": left_visibility
        },
        "left_ankle": {
            "x": math.cos(
                angle_radians
            ),
            "y": math.sin(
                angle_radians
            ),
            "visibility": left_visibility
        },
        "right_shoulder": {
            "x": 4.0,
            "y": 0.0,
            "visibility": right_visibility
        },
        "right_hip": {
            "x": 3.0,
            "y": 0.0,
            "visibility": right_visibility
        },
        "right_knee": {
            "x": 2.0,
            "y": 0.0,
            "visibility": right_visibility
        },
        "right_ankle": {
            "x": (
                2.0
                + math.cos(
                    angle_radians
                )
            ),
            "y": math.sin(
                angle_radians
            ),
            "visibility": right_visibility
        }
    }


def pose_detection(
    angle,
    left_visibility=0.95,
    right_visibility=0.95
):
    return {
        "status": DETECTION_STATUS_POSE_DETECTED,
        "pose_count": 1,
        "pose_landmarks": pose_for_knee_angle(
            angle,
            left_visibility=left_visibility,
            right_visibility=right_visibility
        )
    }


def no_pose_detection():
    return {
        "status": DETECTION_STATUS_NO_POSE,
        "pose_count": 0,
        "pose_landmarks": None
    }


def complete_rep_angles():
    return [
        170,
        150,
        130,
        110,
        90,
        120,
        145,
        160
    ]


def analyze_fake_video(
    responses
):
    path = temporary_video_placeholder()

    fake_cv2 = FakeCV2(
        [
            make_frame()
            for _ in responses
        ],
        fps=2.0
    )

    try:
        return analyze_squat_video(
            video_path=path,
            model_path="unused.task",
            cv2_module=fake_cv2,
            pose_adapter_factory=create_adapter_factory(
                responses
            )
        )

    finally:
        if os.path.isfile(
            path
        ):
            os.remove(
                path
            )


def test_bilateral_view_summary_classification():
    summary = build_view_suitability_summary(
        {
            "frame_count": 10,
            "bilateral_observable_frame_count": 7,
            "single_side_observable_frame_count": 2,
            "insufficient_landmark_frame_count": 1
        }
    )

    if summary[
        "classification"
    ] != VIEW_BILATERAL_OBSERVABLE:
        raise ValueError(
            "FAIL: Mostly bilateral video was classified incorrectly"
        )

    if summary[
        "bilateral_frame_ratio"
    ] != 0.7:
        raise ValueError(
            "FAIL: Bilateral frame ratio is incorrect"
        )

    print("PASS: Video view summary identifies predominantly bilateral observability")


def test_single_side_view_summary_classification():
    summary = build_view_suitability_summary(
        {
            "frame_count": 10,
            "bilateral_observable_frame_count": 2,
            "single_side_observable_frame_count": 6,
            "insufficient_landmark_frame_count": 2
        }
    )

    if summary[
        "classification"
    ] != VIEW_SINGLE_SIDE_OBSERVABLE:
        raise ValueError(
            "FAIL: Mostly single-side video was classified incorrectly"
        )

    print("PASS: Video view summary degrades to single-side observability")


def test_insufficient_view_summary_classification():
    summary = build_view_suitability_summary(
        {
            "frame_count": 10,
            "bilateral_observable_frame_count": 1,
            "single_side_observable_frame_count": 2,
            "insufficient_landmark_frame_count": 7
        }
    )

    if summary[
        "classification"
    ] != VIEW_INSUFFICIENT:
        raise ValueError(
            "FAIL: Mostly unobservable video was not classified as insufficient"
        )

    print("PASS: Video view summary refuses mostly unobservable landmark data")


def test_real_video_pipeline_adds_rep_confidence():
    responses = [
        pose_detection(
            angle
        )
        for angle in complete_rep_angles()
    ]

    result = analyze_fake_video(
        responses
    )

    if result[
        "rep_count"
    ] != 1:
        raise ValueError(
            "FAIL: Rich video pipeline changed deterministic rep count"
        )

    repetition = result[
        "repetitions"
    ][
        0
    ]

    if repetition[
        "confidence_classification"
    ] != "high":
        raise ValueError(
            "FAIL: High-confidence video repetition was not classified as high"
        )

    if result[
        "rep_confidence_summary"
    ][
        "high_confidence_rep_count"
    ] != 1:
        raise ValueError(
            "FAIL: Video repetition confidence summary is incorrect"
        )

    print("PASS: Real video pipeline includes deterministic per-rep confidence")


def test_real_video_pipeline_adds_bilateral_metrics():
    responses = [
        pose_detection(
            angle
        )
        for angle in complete_rep_angles()
    ]

    result = analyze_fake_video(
        responses
    )

    movement_summary = result[
        "movement_metrics_summary"
    ]

    if movement_summary[
        "frame_count"
    ] != 8:
        raise ValueError(
            "FAIL: Movement metric frame count is incorrect"
        )

    if movement_summary[
        "bilateral_observable_frame_count"
    ] != 8:
        raise ValueError(
            "FAIL: Bilateral observable frame count is incorrect"
        )

    if result[
        "view_suitability_summary"
    ][
        "classification"
    ] != VIEW_BILATERAL_OBSERVABLE:
        raise ValueError(
            "FAIL: Bilateral video view classification is incorrect"
        )

    print("PASS: Real video pipeline summarizes bilateral movement geometry")


def test_single_side_video_remains_observable():
    responses = [
        pose_detection(
            angle,
            left_visibility=0.95,
            right_visibility=0.20
        )
        for angle in complete_rep_angles()
    ]

    result = analyze_fake_video(
        responses
    )

    if result[
        "rep_count"
    ] != 1:
        raise ValueError(
            "FAIL: Single visible side destroyed valid repetition"
        )

    if result[
        "view_suitability_summary"
    ][
        "classification"
    ] != VIEW_SINGLE_SIDE_OBSERVABLE:
        raise ValueError(
            "FAIL: Single-side video view classification is incorrect"
        )

    combined_text = " ".join(
        result[
            "limitations"
        ]
    ).casefold()

    forbidden_claims = {
        "bad form",
        "perfect form",
        "genetic",
        "injury risk"
    }

    for claim in forbidden_claims:
        if claim in combined_text:
            raise ValueError(
                f"FAIL: Video metrics generated unsupported claim: {claim}"
            )

    print("PASS: Single-side video remains measurable without unsupported judgment")


def test_video_result_does_not_expose_raw_movement_frame_metrics():
    responses = [
        no_pose_detection()
        for _ in range(
            4
        )
    ]

    result = analyze_fake_video(
        responses
    )

    if "frame_movement_metrics" in result:
        raise ValueError(
            "FAIL: Video result exposed raw per-frame bilateral metrics"
        )

    if "movement_frame_metrics" in result:
        raise ValueError(
            "FAIL: Video result exposed internal movement frame metrics"
        )

    if result[
        "view_suitability_summary"
    ][
        "classification"
    ] != VIEW_INSUFFICIENT:
        raise ValueError(
            "FAIL: No-pose video did not produce insufficient view summary"
        )

    print("PASS: Real video result keeps raw per-frame movement metrics private")


def test_rich_video_metrics_survive_sanitized_persistence():
    setup_vision_database()

    user_id = create_user()

    responses = [
        pose_detection(
            angle
        )
        for angle in complete_rep_angles()
    ]

    result = analyze_fake_video(
        responses
    )

    sanitized = sanitize_vision_analysis_result(
        result
    )

    try:
        stored = create_vision_analysis(
            user_id=user_id,
            source_filename="rich-squat.mp4",
            file_size_bytes=4096,
            sample_every_n_frames=1,
            analysis_result=sanitized
        )

        saved_result = stored[
            "analysis_result"
        ]

        if "rep_confidence_summary" not in saved_result:
            raise ValueError(
                "FAIL: Rep-confidence summary was lost during persistence"
            )

        if "movement_metrics_summary" not in saved_result:
            raise ValueError(
                "FAIL: Movement metrics summary was lost during persistence"
            )

        if "view_suitability_summary" not in saved_result:
            raise ValueError(
                "FAIL: View suitability summary was lost during persistence"
            )

        if "path" in saved_result[
            "video"
        ]:
            raise ValueError(
                "FAIL: Temporary video path survived sanitized persistence"
            )

        if "frame_movement_metrics" in saved_result:
            raise ValueError(
                "FAIL: Raw movement frames were persisted"
            )

        print("PASS: Rich video summaries persist without raw per-frame landmarks or paths")

    finally:
        delete_user(
            user_id
        )


if __name__ == "__main__":
    test_bilateral_view_summary_classification()
    test_single_side_view_summary_classification()
    test_insufficient_view_summary_classification()
    test_real_video_pipeline_adds_rep_confidence()
    test_real_video_pipeline_adds_bilateral_metrics()
    test_single_side_video_remains_observable()
    test_video_result_does_not_expose_raw_movement_frame_metrics()
    test_rich_video_metrics_survive_sanitized_persistence()