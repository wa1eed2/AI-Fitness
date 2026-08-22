import argparse
import json
from pathlib import Path

from src.vision.real_world_validation import (
    build_validation_expectation,
    run_real_world_validation_case
)

from src.vision.squat_movement_metrics import (
    VIEW_BILATERAL_OBSERVABLE,
    VIEW_SINGLE_SIDE_OBSERVABLE
)


DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "models"
    / "pose_landmarker_lite.task"
)


def build_argument_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Run local real-world squat-video validation "
            "without uploading or persisting the video."
        )
    )

    parser.add_argument(
        "--video",
        required=True
    )

    parser.add_argument(
        "--model",
        default=str(
            DEFAULT_MODEL_PATH
        )
    )

    parser.add_argument(
        "--min-reps",
        required=True,
        type=int
    )

    parser.add_argument(
        "--max-reps",
        required=True,
        type=int
    )

    parser.add_argument(
        "--min-detection-ratio",
        type=float,
        default=0.70
    )

    parser.add_argument(
        "--min-observable-ratio",
        type=float,
        default=0.70
    )

    parser.add_argument(
        "--min-rep-confidence",
        type=float,
        default=None
    )

    parser.add_argument(
        "--sample-every",
        type=int,
        default=1
    )

    parser.add_argument(
        "--max-analyzed-frames",
        type=int,
        default=None
    )

    parser.add_argument(
        "--bilateral-only",
        action="store_true"
    )

    return parser


def main():
    parser = build_argument_parser()

    arguments = parser.parse_args()

    allowed_views = [
        VIEW_BILATERAL_OBSERVABLE
    ]

    if not arguments.bilateral_only:
        allowed_views.append(
            VIEW_SINGLE_SIDE_OBSERVABLE
        )

    expectation = build_validation_expectation(
        minimum_reps=arguments.min_reps,
        maximum_reps=arguments.max_reps,
        minimum_pose_detection_ratio=arguments.min_detection_ratio,
        minimum_observable_frame_ratio=arguments.min_observable_ratio,
        minimum_average_rep_confidence=arguments.min_rep_confidence,
        allowed_views=allowed_views
    )

    report = run_real_world_validation_case(
        video_path=arguments.video,
        model_path=arguments.model,
        expectation=expectation,
        sample_every_n_frames=arguments.sample_every,
        max_analyzed_frames=arguments.max_analyzed_frames
    )

    print(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()