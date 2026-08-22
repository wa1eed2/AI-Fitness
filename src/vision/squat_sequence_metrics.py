from src.vision.squat_movement_metrics import (
    analyze_bilateral_squat_frame,
    enrich_repetitions_with_confidence,
    summarize_bilateral_frame_metrics
)

from src.vision.squat_repetition_analysis import (
    analyze_squat_pose_sequence
)


def validate_pose_sequence(
    frames
):
    if not isinstance(frames, list):
        raise ValueError(
            "frames must be a list"
        )

    if not frames:
        raise ValueError(
            "frames cannot be empty"
        )

    for frame in frames:
        if not isinstance(frame, dict):
            raise ValueError(
                "Each frame must be a dictionary"
            )

        if "timestamp_seconds" not in frame:
            raise ValueError(
                "Each frame requires timestamp_seconds"
            )

        if not isinstance(
            frame.get(
                "pose_landmarks"
            ),
            dict
        ):
            raise ValueError(
                "Each frame requires pose_landmarks dictionary"
            )

    return frames


def analyze_squat_pose_sequence_with_metrics(
    frames,
    include_frame_metrics=False,
    **sequence_options
):
    validate_pose_sequence(
        frames
    )

    if not isinstance(
        include_frame_metrics,
        bool
    ):
        raise ValueError(
            "include_frame_metrics must be a boolean"
        )

    sequence_result = analyze_squat_pose_sequence(
        frames,
        **sequence_options
    )

    enriched_sequence = enrich_repetitions_with_confidence(
        sequence_result
    )

    frame_metrics = [
        analyze_bilateral_squat_frame(
            frame[
                "pose_landmarks"
            ],
            minimum_visibility=sequence_options.get(
                "minimum_visibility",
                0.60
            )
        )
        for frame in frames
    ]

    enriched_sequence[
        "movement_metrics_summary"
    ] = summarize_bilateral_frame_metrics(
        frame_metrics
    )

    if include_frame_metrics:
        enriched_sequence[
            "frame_movement_metrics"
        ] = frame_metrics

    return enriched_sequence