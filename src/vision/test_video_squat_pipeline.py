import math
import os
import tempfile

import numpy as np

from src.vision.mediapipe_pose_adapter import (
    DETECTION_STATUS_NO_POSE,
    DETECTION_STATUS_POSE_DETECTED,
    RUNNING_MODE_VIDEO
)

from src.vision.video_squat_pipeline import (
    VideoMetadataError,
    VideoOpenError,
    analyze_squat_video,
    build_frame_timestamp,
    validate_video_path
)


class FakeCapture:
    def __init__(
        self,
        frames,
        fps=2.0,
        opened=True
    ):
        self.frames = [
            frame.copy()
            for frame in frames
        ]

        self.fps = fps
        self.opened = opened
        self.index = 0
        self.released = False

    def isOpened(self):
        return self.opened

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
            if not self.frames:
                return 0

            return self.frames[
                0
            ].shape[
                1
            ]

        if property_id == FakeCV2.CAP_PROP_FRAME_HEIGHT:
            if not self.frames:
                return 0

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
        fps=2.0,
        opened=True
    ):
        self.capture = FakeCapture(
            frames,
            fps=fps,
            opened=opened
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
                "Unexpected fake color conversion"
            )

        return frame[
            :,
            :,
            ::-1
        ].copy()


class FakePoseAdapter:
    def __init__(
        self,
        responses,
        recording
    ):
        self.responses = list(
            responses
        )

        self.recording = recording
        self.index = 0
        self.closed = False

    def detect_video_frame_rgb(
        self,
        frame,
        timestamp_seconds
    ):
        self.recording[
            "frames"
        ].append(
            frame.copy()
        )

        self.recording[
            "timestamps"
        ].append(
            timestamp_seconds
        )

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
        self.recording[
            "closed"
        ] = True


def create_fake_adapter_factory(
    responses,
    recording
):
    def factory(
        model_path,
        running_mode
    ):
        recording[
            "model_path"
        ] = model_path

        recording[
            "running_mode"
        ] = running_mode

        adapter = FakePoseAdapter(
            responses,
            recording
        )

        recording[
            "adapter"
        ] = adapter

        return adapter

    return factory


def make_frame(
    b=10,
    g=20,
    r=30
):
    frame = np.zeros(
        (
            8,
            8,
            3
        ),
        dtype=np.uint8
    )

    frame[
        :,
        :
    ] = [
        b,
        g,
        r
    ]

    return frame


def pose_for_knee_angle(
    angle_degrees,
    visibility=0.95
):
    angle_radians = math.radians(
        angle_degrees
    )

    return {
        "left_shoulder": {
            "x": 2.0,
            "y": 0.0,
            "visibility": visibility
        },
        "left_hip": {
            "x": 1.0,
            "y": 0.0,
            "visibility": visibility
        },
        "left_knee": {
            "x": 0.0,
            "y": 0.0,
            "visibility": visibility
        },
        "left_ankle": {
            "x": math.cos(
                angle_radians
            ),
            "y": math.sin(
                angle_radians
            ),
            "visibility": visibility
        }
    }


def pose_detection(
    angle
):
    return {
        "status": DETECTION_STATUS_POSE_DETECTED,
        "pose_count": 1,
        "pose_landmarks": pose_for_knee_angle(
            angle
        )
    }


def no_pose_detection():
    return {
        "status": DETECTION_STATUS_NO_POSE,
        "pose_count": 0,
        "pose_landmarks": None
    }


def temporary_video_placeholder():
    handle = tempfile.NamedTemporaryFile(
        suffix=".mp4",
        delete=False
    )

    path = handle.name

    handle.close()

    return path


def test_missing_video_file_is_rejected():
    try:
        validate_video_path(
            "video-that-does-not-exist.mp4"
        )

    except VideoOpenError:
        print("PASS: Video pipeline rejects missing input files")
        return

    raise ValueError(
        "FAIL: Missing video path was accepted"
    )


def test_capture_that_cannot_open_is_rejected():
    path = temporary_video_placeholder()

    fake_cv2 = FakeCV2(
        [],
        opened=False
    )

    try:
        try:
            analyze_squat_video(
                video_path=path,
                model_path="unused.task",
                cv2_module=fake_cv2,
                pose_adapter_factory=create_fake_adapter_factory(
                    [],
                    {
                        "frames": [],
                        "timestamps": []
                    }
                )
            )

        except VideoOpenError:
            if not fake_cv2.capture.released:
                raise ValueError(
                    "FAIL: Failed video capture was not released"
                )

            print("PASS: Video pipeline rejects files OpenCV cannot open")
            return

        raise ValueError(
            "FAIL: Closed OpenCV capture was accepted"
        )

    finally:
        os.unlink(
            path
        )


def test_invalid_video_fps_is_rejected():
    path = temporary_video_placeholder()

    fake_cv2 = FakeCV2(
        [
            make_frame()
        ],
        fps=0.0
    )

    try:
        try:
            analyze_squat_video(
                video_path=path,
                model_path="unused.task",
                cv2_module=fake_cv2,
                pose_adapter_factory=create_fake_adapter_factory(
                    [],
                    {
                        "frames": [],
                        "timestamps": []
                    }
                )
            )

        except VideoMetadataError:
            print("PASS: Video pipeline rejects invalid FPS metadata")
            return

        raise ValueError(
            "FAIL: Zero-FPS video metadata was accepted"
        )

    finally:
        os.unlink(
            path
        )


def test_video_frames_are_converted_from_bgr_to_rgb():
    path = temporary_video_placeholder()

    recording = {
        "frames": [],
        "timestamps": []
    }

    fake_cv2 = FakeCV2(
        [
            make_frame(
                b=10,
                g=20,
                r=30
            )
        ],
        fps=30.0
    )

    factory = create_fake_adapter_factory(
        [
            no_pose_detection()
        ],
        recording
    )

    try:
        analyze_squat_video(
            video_path=path,
            model_path="unused.task",
            cv2_module=fake_cv2,
            pose_adapter_factory=factory
        )

        first_pixel = recording[
            "frames"
        ][
            0
        ][
            0,
            0
        ].tolist()

        if first_pixel != [
            30,
            20,
            10
        ]:
            raise ValueError(
                f"FAIL: Expected RGB [30, 20, 10], got {first_pixel}"
            )

        if recording["running_mode"] != RUNNING_MODE_VIDEO:
            raise ValueError(
                "FAIL: Video pipeline did not initialize pose adapter in VIDEO mode"
            )

        print("PASS: OpenCV BGR frames are converted to RGB before pose inference")

    finally:
        os.unlink(
            path
        )


def test_complete_video_sequence_counts_one_rep():
    path = temporary_video_placeholder()

    angles = [
        170,
        150,
        130,
        110,
        90,
        120,
        145,
        160
    ]

    responses = [
        pose_detection(
            angle
        )
        for angle in angles
    ]

    frames = [
        make_frame()
        for _ in angles
    ]

    recording = {
        "frames": [],
        "timestamps": []
    }

    fake_cv2 = FakeCV2(
        frames,
        fps=2.0
    )

    try:
        result = analyze_squat_video(
            video_path=path,
            model_path="unused.task",
            cv2_module=fake_cv2,
            pose_adapter_factory=create_fake_adapter_factory(
                responses,
                recording
            )
        )

        if result["source"] != "video":
            raise ValueError(
                "FAIL: Video analysis source metadata is incorrect"
            )

        if result["rep_count"] != 1:
            raise ValueError(
                f"FAIL: Expected 1 video repetition, got {result['rep_count']}"
            )

        repetition = result[
            "repetitions"
        ][
            0
        ]

        if repetition["duration_seconds"] != 3.5:
            raise ValueError(
                "FAIL: Video repetition timing was not preserved"
            )

        if repetition["knee_range_of_motion_degrees"] != 80:
            raise ValueError(
                "FAIL: Video repetition knee range of motion is incorrect"
            )

        print("PASS: Decoded video frames feed deterministic squat repetition analysis")

    finally:
        os.unlink(
            path
        )


def test_no_pose_video_is_reported_without_inventing_repetitions():
    path = temporary_video_placeholder()

    frames = [
        make_frame()
        for _ in range(
            4
        )
    ]

    responses = [
        no_pose_detection()
        for _ in frames
    ]

    recording = {
        "frames": [],
        "timestamps": []
    }

    fake_cv2 = FakeCV2(
        frames,
        fps=2.0
    )

    try:
        result = analyze_squat_video(
            video_path=path,
            model_path="unused.task",
            cv2_module=fake_cv2,
            pose_adapter_factory=create_fake_adapter_factory(
                responses,
                recording
            )
        )

        if result["rep_count"] != 0:
            raise ValueError(
                "FAIL: No-pose video produced fabricated repetitions"
            )

        if result[
            "detection_summary"
        ][
            "no_pose_frame_count"
        ] != 4:
            raise ValueError(
                "FAIL: No-pose frames were not tracked"
            )

        if result["status"] != "insufficient_data":
            raise ValueError(
                "FAIL: No-pose video did not return insufficient-data status"
            )

        print("PASS: Video pipeline handles clips without a detected person conservatively")

    finally:
        os.unlink(
            path
        )


def test_frame_sampling_preserves_video_time():
    path = temporary_video_placeholder()

    frames = [
        make_frame()
        for _ in range(
            5
        )
    ]

    responses = [
        no_pose_detection(),
        no_pose_detection(),
        no_pose_detection()
    ]

    recording = {
        "frames": [],
        "timestamps": []
    }

    fake_cv2 = FakeCV2(
        frames,
        fps=2.0
    )

    try:
        result = analyze_squat_video(
            video_path=path,
            model_path="unused.task",
            sample_every_n_frames=2,
            cv2_module=fake_cv2,
            pose_adapter_factory=create_fake_adapter_factory(
                responses,
                recording
            )
        )

        expected_timestamps = [
            0.0,
            1.0,
            2.0
        ]

        if recording["timestamps"] != expected_timestamps:
            raise ValueError(
                f"FAIL: Expected timestamps {expected_timestamps}, "
                f"got {recording['timestamps']}"
            )

        if result[
            "video"
        ][
            "sampled_frame_count"
        ] != 3:
            raise ValueError(
                "FAIL: Video frame sampling count is incorrect"
            )

        print("PASS: Frame sampling preserves original video timeline")

    finally:
        os.unlink(
            path
        )


def test_max_analyzed_frames_limits_pose_inference():
    path = temporary_video_placeholder()

    frames = [
        make_frame()
        for _ in range(
            10
        )
    ]

    responses = [
        no_pose_detection(),
        no_pose_detection(),
        no_pose_detection()
    ]

    recording = {
        "frames": [],
        "timestamps": []
    }

    fake_cv2 = FakeCV2(
        frames,
        fps=30.0
    )

    try:
        result = analyze_squat_video(
            video_path=path,
            model_path="unused.task",
            max_analyzed_frames=3,
            cv2_module=fake_cv2,
            pose_adapter_factory=create_fake_adapter_factory(
                responses,
                recording
            )
        )

        if len(
            recording[
                "frames"
            ]
        ) != 3:
            raise ValueError(
                "FAIL: max_analyzed_frames did not limit pose inference"
            )

        if result[
            "video"
        ][
            "sampled_frame_count"
        ] != 3:
            raise ValueError(
                "FAIL: Result metadata ignored max_analyzed_frames"
            )

        print("PASS: Video pipeline supports bounded frame analysis")

    finally:
        os.unlink(
            path
        )


def test_video_resources_are_closed_after_success():
    path = temporary_video_placeholder()

    recording = {
        "frames": [],
        "timestamps": [],
        "closed": False
    }

    fake_cv2 = FakeCV2(
        [
            make_frame()
        ],
        fps=30.0
    )

    try:
        analyze_squat_video(
            video_path=path,
            model_path="unused.task",
            cv2_module=fake_cv2,
            pose_adapter_factory=create_fake_adapter_factory(
                [
                    no_pose_detection()
                ],
                recording
            )
        )

        if not fake_cv2.capture.released:
            raise ValueError(
                "FAIL: OpenCV VideoCapture was not released"
            )

        if recording["closed"] is not True:
            raise ValueError(
                "FAIL: Pose adapter was not closed"
            )

        print("PASS: Video decoder and pose estimator resources close deterministically")

    finally:
        os.unlink(
            path
        )


def test_unknown_pose_status_fails_without_leaking_resources():
    path = temporary_video_placeholder()

    recording = {
        "frames": [],
        "timestamps": [],
        "closed": False
    }

    fake_cv2 = FakeCV2(
        [
            make_frame()
        ],
        fps=30.0
    )

    try:
        try:
            analyze_squat_video(
                video_path=path,
                model_path="unused.task",
                cv2_module=fake_cv2,
                pose_adapter_factory=create_fake_adapter_factory(
                    [
                        {
                            "status": "mystery_status"
                        }
                    ],
                    recording
                )
            )

        except ValueError:
            if not fake_cv2.capture.released:
                raise ValueError(
                    "FAIL: Video capture leaked after analysis error"
                )

            if recording["closed"] is not True:
                raise ValueError(
                    "FAIL: Pose adapter leaked after analysis error"
                )

            print("PASS: Unexpected pose results fail safely without leaking resources")
            return

        raise ValueError(
            "FAIL: Unknown pose detection status was accepted"
        )

    finally:
        os.unlink(
            path
        )


if __name__ == "__main__":
    test_missing_video_file_is_rejected()
    test_capture_that_cannot_open_is_rejected()
    test_invalid_video_fps_is_rejected()
    test_video_frames_are_converted_from_bgr_to_rgb()
    test_complete_video_sequence_counts_one_rep()
    test_no_pose_video_is_reported_without_inventing_repetitions()
    test_frame_sampling_preserves_video_time()
    test_max_analyzed_frames_limits_pose_inference()
    test_video_resources_are_closed_after_success()
    test_unknown_pose_status_fails_without_leaking_resources()