import math
import statistics

from src.vision.squat_analysis import (
    ANALYSIS_STATUS_ANALYZABLE,
    MIN_REQUIRED_VISIBILITY,
    SIDE_LEFT,
    SIDE_RIGHT,
    analyze_squat_frame
)


SEQUENCE_STATUS_ANALYZED = "analyzed"
SEQUENCE_STATUS_INSUFFICIENT_DATA = "insufficient_data"


PHASE_WAITING = "waiting"
PHASE_STANDING = "standing"
PHASE_DESCENDING = "descending"
PHASE_BOTTOM = "bottom"
PHASE_ASCENDING = "ascending"


STANDING_ANGLE_MIN = 155.0
BOTTOM_ANGLE_MAX = 115.0

MIN_FRAME_CONFIDENCE = 0.60

MIN_REP_DURATION_SECONDS = 0.50
MAX_REP_DURATION_SECONDS = 10.0

MIN_REP_RANGE_OF_MOTION_DEGREES = 30.0

MAX_ACTIVE_FRAME_GAP_SECONDS = 1.0

ANGLE_DIRECTION_EPSILON_DEGREES = 1.0


def validate_numeric(value, field_name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric")

    value = float(value)

    if not math.isfinite(value):
        raise ValueError(f"{field_name} must be finite")

    return value


def validate_probability(value, field_name):
    value = validate_numeric(value, field_name)

    if value < 0 or value > 1:
        raise ValueError(f"{field_name} must be between 0 and 1")

    return value


def validate_positive_seconds(value, field_name):
    value = validate_numeric(value, field_name)

    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0")

    return value


def validate_thresholds(
    standing_angle_min,
    bottom_angle_max,
    minimum_frame_confidence,
    min_rep_duration_seconds,
    max_rep_duration_seconds,
    minimum_rep_range_of_motion_degrees,
    max_active_frame_gap_seconds
):
    standing_angle_min = validate_numeric(
        standing_angle_min,
        "standing_angle_min"
    )

    bottom_angle_max = validate_numeric(
        bottom_angle_max,
        "bottom_angle_max"
    )

    if standing_angle_min < 0 or standing_angle_min > 180:
        raise ValueError("standing_angle_min must be between 0 and 180")

    if bottom_angle_max < 0 or bottom_angle_max > 180:
        raise ValueError("bottom_angle_max must be between 0 and 180")

    if bottom_angle_max >= standing_angle_min:
        raise ValueError("bottom_angle_max must be lower than standing_angle_min")

    validate_probability(
        minimum_frame_confidence,
        "minimum_frame_confidence"
    )

    min_rep_duration_seconds = validate_positive_seconds(
        min_rep_duration_seconds,
        "min_rep_duration_seconds"
    )

    max_rep_duration_seconds = validate_positive_seconds(
        max_rep_duration_seconds,
        "max_rep_duration_seconds"
    )

    if min_rep_duration_seconds >= max_rep_duration_seconds:
        raise ValueError("min_rep_duration_seconds must be lower than max_rep_duration_seconds")

    minimum_rep_range_of_motion_degrees = validate_numeric(
        minimum_rep_range_of_motion_degrees,
        "minimum_rep_range_of_motion_degrees"
    )

    if minimum_rep_range_of_motion_degrees <= 0 or minimum_rep_range_of_motion_degrees > 180:
        raise ValueError("minimum_rep_range_of_motion_degrees must be between 0 and 180")

    validate_positive_seconds(
        max_active_frame_gap_seconds,
        "max_active_frame_gap_seconds"
    )


def validate_selected_side(side):
    if side is None:
        return None

    if side not in {
        SIDE_LEFT,
        SIDE_RIGHT
    }:
        raise ValueError("selected_side must be left, right, or None")

    return side


def normalize_angle_frame(
    frame,
    previous_timestamp=None
):
    if not isinstance(frame, dict):
        raise ValueError("Each frame observation must be a dictionary")

    if "timestamp_seconds" not in frame:
        raise ValueError("Frame observation requires timestamp_seconds")

    timestamp = validate_numeric(
        frame[
            "timestamp_seconds"
        ],
        "timestamp_seconds"
    )

    if timestamp < 0:
        raise ValueError("timestamp_seconds cannot be negative")

    if previous_timestamp is not None and timestamp <= previous_timestamp:
        raise ValueError("Frame timestamps must be strictly increasing")

    analyzable = frame.get(
        "analyzable",
        True
    )

    if not isinstance(analyzable, bool):
        raise ValueError("analyzable must be a boolean")

    selected_side = validate_selected_side(
        frame.get(
            "selected_side"
        )
    )

    if not analyzable:
        return {
            "timestamp_seconds": timestamp,
            "analyzable": False,
            "knee_angle_degrees": None,
            "confidence": None,
            "selected_side": selected_side
        }

    if "knee_angle_degrees" not in frame:
        raise ValueError("Analyzable frame requires knee_angle_degrees")

    angle = validate_numeric(
        frame[
            "knee_angle_degrees"
        ],
        "knee_angle_degrees"
    )

    if angle < 0 or angle > 180:
        raise ValueError("knee_angle_degrees must be between 0 and 180")

    confidence = validate_probability(
        frame.get(
            "confidence",
            1.0
        ),
        "confidence"
    )

    return {
        "timestamp_seconds": timestamp,
        "analyzable": True,
        "knee_angle_degrees": angle,
        "confidence": confidence,
        "selected_side": selected_side
    }


def normalize_angle_frames(frames):
    if not isinstance(frames, list):
        raise ValueError("frames must be a list")

    if not frames:
        raise ValueError("frames cannot be empty")

    normalized = []
    previous_timestamp = None

    for frame in frames:
        normalized_frame = normalize_angle_frame(
            frame,
            previous_timestamp=previous_timestamp
        )

        normalized.append(
            normalized_frame
        )

        previous_timestamp = normalized_frame[
            "timestamp_seconds"
        ]

    return normalized


def calculate_average(values):
    if not values:
        return None

    return round(
        sum(values)
        / len(values),
        3
    )


def calculate_population_standard_deviation(values):
    if not values:
        return None

    if len(values) == 1:
        return 0.0

    return round(
        statistics.pstdev(
            values
        ),
        3
    )


def calculate_coefficient_of_variation(
    standard_deviation,
    average
):
    if standard_deviation is None or average is None or average == 0:
        return None

    return round(
        standard_deviation
        / average,
        4
    )


def classify_rep_variability(
    rep_count,
    duration_coefficient_of_variation,
    range_of_motion_standard_deviation
):
    if rep_count < 2:
        return "insufficient_repetitions"

    if (
        duration_coefficient_of_variation is not None
        and duration_coefficient_of_variation <= 0.10
        and range_of_motion_standard_deviation is not None
        and range_of_motion_standard_deviation <= 5.0
    ):
        return "low_variability"

    if (
        duration_coefficient_of_variation is not None
        and duration_coefficient_of_variation <= 0.20
        and range_of_motion_standard_deviation is not None
        and range_of_motion_standard_deviation <= 10.0
    ):
        return "moderate_variability"

    return "high_variability"


def build_sequence_summary(repetitions):
    if not repetitions:
        return {
            "average_rep_duration_seconds": None,
            "average_descent_duration_seconds": None,
            "average_ascent_duration_seconds": None,
            "average_range_of_motion_degrees": None,
            "rep_duration_standard_deviation_seconds": None,
            "range_of_motion_standard_deviation_degrees": None,
            "rep_duration_coefficient_of_variation": None,
            "variability_classification": "insufficient_repetitions"
        }

    durations = [
        repetition[
            "duration_seconds"
        ]
        for repetition in repetitions
    ]

    descent_durations = [
        repetition[
            "descent_duration_seconds"
        ]
        for repetition in repetitions
    ]

    ascent_durations = [
        repetition[
            "ascent_duration_seconds"
        ]
        for repetition in repetitions
    ]

    ranges_of_motion = [
        repetition[
            "knee_range_of_motion_degrees"
        ]
        for repetition in repetitions
    ]

    average_duration = calculate_average(
        durations
    )

    duration_standard_deviation = calculate_population_standard_deviation(
        durations
    )

    range_of_motion_standard_deviation = calculate_population_standard_deviation(
        ranges_of_motion
    )

    duration_coefficient_of_variation = calculate_coefficient_of_variation(
        duration_standard_deviation,
        average_duration
    )

    return {
        "average_rep_duration_seconds": average_duration,
        "average_descent_duration_seconds": calculate_average(
            descent_durations
        ),
        "average_ascent_duration_seconds": calculate_average(
            ascent_durations
        ),
        "average_range_of_motion_degrees": calculate_average(
            ranges_of_motion
        ),
        "rep_duration_standard_deviation_seconds": duration_standard_deviation,
        "range_of_motion_standard_deviation_degrees": range_of_motion_standard_deviation,
        "rep_duration_coefficient_of_variation": duration_coefficient_of_variation,
        "variability_classification": classify_rep_variability(
            len(
                repetitions
            ),
            duration_coefficient_of_variation,
            range_of_motion_standard_deviation
        )
    }


def create_active_attempt(
    standing_frame,
    current_frame
):
    frames = [
        standing_frame,
        current_frame
    ]

    return {
        "frames": frames,
        "start_timestamp_seconds": standing_frame[
            "timestamp_seconds"
        ],
        "minimum_angle_degrees": min(
            standing_frame[
                "knee_angle_degrees"
            ],
            current_frame[
                "knee_angle_degrees"
            ]
        ),
        "minimum_angle_timestamp_seconds": (
            current_frame[
                "timestamp_seconds"
            ]
            if current_frame[
                "knee_angle_degrees"
            ]
            <= standing_frame[
                "knee_angle_degrees"
            ]
            else standing_frame[
                "timestamp_seconds"
            ]
        ),
        "maximum_angle_degrees": max(
            standing_frame[
                "knee_angle_degrees"
            ],
            current_frame[
                "knee_angle_degrees"
            ]
        ),
        "bottom_reached": False,
        "selected_side": (
            current_frame[
                "selected_side"
            ]
            or standing_frame[
                "selected_side"
            ]
        ),
        "last_angle_degrees": current_frame[
            "knee_angle_degrees"
        ]
    }


def append_active_frame(
    active_attempt,
    frame
):
    active_attempt[
        "frames"
    ].append(
        frame
    )

    angle = frame[
        "knee_angle_degrees"
    ]

    if angle < active_attempt[
        "minimum_angle_degrees"
    ]:
        active_attempt[
            "minimum_angle_degrees"
        ] = angle

        active_attempt[
            "minimum_angle_timestamp_seconds"
        ] = frame[
            "timestamp_seconds"
        ]

    if angle > active_attempt[
        "maximum_angle_degrees"
    ]:
        active_attempt[
            "maximum_angle_degrees"
        ] = angle


def finalize_repetition(
    active_attempt,
    end_frame,
    repetition_number,
    min_rep_duration_seconds,
    max_rep_duration_seconds,
    minimum_rep_range_of_motion_degrees
):
    start_timestamp = active_attempt[
        "start_timestamp_seconds"
    ]

    bottom_timestamp = active_attempt[
        "minimum_angle_timestamp_seconds"
    ]

    end_timestamp = end_frame[
        "timestamp_seconds"
    ]

    duration = (
        end_timestamp
        - start_timestamp
    )

    descent_duration = (
        bottom_timestamp
        - start_timestamp
    )

    ascent_duration = (
        end_timestamp
        - bottom_timestamp
    )

    range_of_motion = (
        active_attempt[
            "maximum_angle_degrees"
        ]
        - active_attempt[
            "minimum_angle_degrees"
        ]
    )

    if duration < min_rep_duration_seconds:
        return None

    if duration > max_rep_duration_seconds:
        return None

    if range_of_motion < minimum_rep_range_of_motion_degrees:
        return None

    confidence_values = [
        frame[
            "confidence"
        ]
        for frame in active_attempt[
            "frames"
        ]
        if frame[
            "confidence"
        ] is not None
    ]

    return {
        "repetition_number": repetition_number,
        "start_timestamp_seconds": round(
            start_timestamp,
            3
        ),
        "bottom_timestamp_seconds": round(
            bottom_timestamp,
            3
        ),
        "end_timestamp_seconds": round(
            end_timestamp,
            3
        ),
        "duration_seconds": round(
            duration,
            3
        ),
        "descent_duration_seconds": round(
            descent_duration,
            3
        ),
        "ascent_duration_seconds": round(
            ascent_duration,
            3
        ),
        "minimum_knee_angle_degrees": round(
            active_attempt[
                "minimum_angle_degrees"
            ],
            2
        ),
        "maximum_knee_angle_degrees": round(
            active_attempt[
                "maximum_angle_degrees"
            ],
            2
        ),
        "knee_range_of_motion_degrees": round(
            range_of_motion,
            2
        ),
        "frame_count": len(
            active_attempt[
                "frames"
            ]
        ),
        "mean_confidence": calculate_average(
            confidence_values
        ),
        "selected_side": active_attempt[
            "selected_side"
        ]
    }


def record_phase_transition(
    phase_transitions,
    phase,
    timestamp_seconds
):
    if (
        phase_transitions
        and phase_transitions[
            -1
        ][
            "phase"
        ] == phase
    ):
        return

    phase_transitions.append(
        {
            "phase": phase,
            "timestamp_seconds": round(
                timestamp_seconds,
                3
            )
        }
    )


def analyze_squat_angle_sequence(
    frames,
    standing_angle_min=STANDING_ANGLE_MIN,
    bottom_angle_max=BOTTOM_ANGLE_MAX,
    minimum_frame_confidence=MIN_FRAME_CONFIDENCE,
    min_rep_duration_seconds=MIN_REP_DURATION_SECONDS,
    max_rep_duration_seconds=MAX_REP_DURATION_SECONDS,
    minimum_rep_range_of_motion_degrees=MIN_REP_RANGE_OF_MOTION_DEGREES,
    max_active_frame_gap_seconds=MAX_ACTIVE_FRAME_GAP_SECONDS
):
    validate_thresholds(
        standing_angle_min=standing_angle_min,
        bottom_angle_max=bottom_angle_max,
        minimum_frame_confidence=minimum_frame_confidence,
        min_rep_duration_seconds=min_rep_duration_seconds,
        max_rep_duration_seconds=max_rep_duration_seconds,
        minimum_rep_range_of_motion_degrees=minimum_rep_range_of_motion_degrees,
        max_active_frame_gap_seconds=max_active_frame_gap_seconds
    )

    normalized_frames = normalize_angle_frames(
        frames
    )

    phase = PHASE_WAITING

    repetitions = []
    phase_transitions = []

    active_attempt = None
    last_standing_frame = None
    last_analyzable_timestamp = None

    analyzable_frame_count = 0
    insufficient_frame_count = 0
    low_confidence_frame_count = 0
    incomplete_attempt_count = 0
    side_switch_count = 0

    for frame in normalized_frames:
        if not frame[
            "analyzable"
        ]:
            insufficient_frame_count += 1
            continue

        if frame[
            "confidence"
        ] < minimum_frame_confidence:
            low_confidence_frame_count += 1
            continue

        analyzable_frame_count += 1

        timestamp = frame[
            "timestamp_seconds"
        ]

        angle = frame[
            "knee_angle_degrees"
        ]

        if (
            active_attempt is not None
            and last_analyzable_timestamp is not None
            and timestamp - last_analyzable_timestamp
            > max_active_frame_gap_seconds
        ):
            incomplete_attempt_count += 1
            active_attempt = None
            last_standing_frame = None
            phase = PHASE_WAITING

        if active_attempt is not None:
            active_side = active_attempt[
                "selected_side"
            ]

            current_side = frame[
                "selected_side"
            ]

            if (
                active_side is not None
                and current_side is not None
                and active_side != current_side
            ):
                side_switch_count += 1
                incomplete_attempt_count += 1
                active_attempt = None
                last_standing_frame = None
                phase = PHASE_WAITING

        last_analyzable_timestamp = timestamp

        if active_attempt is None:
            if angle >= standing_angle_min:
                phase = PHASE_STANDING
                last_standing_frame = frame

                record_phase_transition(
                    phase_transitions,
                    PHASE_STANDING,
                    timestamp
                )

                continue

            if phase == PHASE_STANDING and last_standing_frame is not None:
                active_attempt = create_active_attempt(
                    last_standing_frame,
                    frame
                )

                phase = PHASE_DESCENDING

                record_phase_transition(
                    phase_transitions,
                    PHASE_DESCENDING,
                    timestamp
                )

                if angle <= bottom_angle_max:
                    active_attempt[
                        "bottom_reached"
                    ] = True

                    phase = PHASE_BOTTOM

                    record_phase_transition(
                        phase_transitions,
                        PHASE_BOTTOM,
                        timestamp
                    )

                continue

            phase = PHASE_WAITING
            continue

        previous_angle = active_attempt[
            "last_angle_degrees"
        ]

        append_active_frame(
            active_attempt,
            frame
        )

        if not active_attempt[
            "bottom_reached"
        ]:
            if angle <= bottom_angle_max:
                active_attempt[
                    "bottom_reached"
                ] = True

                phase = PHASE_BOTTOM

                record_phase_transition(
                    phase_transitions,
                    PHASE_BOTTOM,
                    timestamp
                )

            elif angle >= standing_angle_min:
                incomplete_attempt_count += 1
                active_attempt = None
                phase = PHASE_STANDING
                last_standing_frame = frame

                record_phase_transition(
                    phase_transitions,
                    PHASE_STANDING,
                    timestamp
                )

            else:
                phase = PHASE_DESCENDING

        else:
            if angle >= standing_angle_min:
                repetition = finalize_repetition(
                    active_attempt=active_attempt,
                    end_frame=frame,
                    repetition_number=len(
                        repetitions
                    ) + 1,
                    min_rep_duration_seconds=min_rep_duration_seconds,
                    max_rep_duration_seconds=max_rep_duration_seconds,
                    minimum_rep_range_of_motion_degrees=minimum_rep_range_of_motion_degrees
                )

                if repetition is None:
                    incomplete_attempt_count += 1

                else:
                    repetitions.append(
                        repetition
                    )

                active_attempt = None
                phase = PHASE_STANDING
                last_standing_frame = frame

                record_phase_transition(
                    phase_transitions,
                    PHASE_STANDING,
                    timestamp
                )

            elif angle > (
                previous_angle
                + ANGLE_DIRECTION_EPSILON_DEGREES
            ):
                phase = PHASE_ASCENDING

                record_phase_transition(
                    phase_transitions,
                    PHASE_ASCENDING,
                    timestamp
                )

            elif angle <= bottom_angle_max:
                phase = PHASE_BOTTOM

                record_phase_transition(
                    phase_transitions,
                    PHASE_BOTTOM,
                    timestamp
                )

            else:
                phase = PHASE_DESCENDING

                record_phase_transition(
                    phase_transitions,
                    PHASE_DESCENDING,
                    timestamp
                )

        if active_attempt is not None:
            active_attempt[
                "last_angle_degrees"
            ] = angle

    if active_attempt is not None:
        incomplete_attempt_count += 1

    if analyzable_frame_count == 0:
        status = SEQUENCE_STATUS_INSUFFICIENT_DATA

    else:
        status = SEQUENCE_STATUS_ANALYZED

    return {
        "status": status,
        "exercise": "squat",
        "source": "knee_angle_sequence",
        "frame_count": len(
            normalized_frames
        ),
        "analyzable_frame_count": analyzable_frame_count,
        "insufficient_frame_count": insufficient_frame_count,
        "low_confidence_frame_count": low_confidence_frame_count,
        "side_switch_count": side_switch_count,
        "rep_count": len(
            repetitions
        ),
        "incomplete_attempt_count": incomplete_attempt_count,
        "repetitions": repetitions,
        "phase_transitions": phase_transitions,
        "summary": build_sequence_summary(
            repetitions
        ),
        "limitations": [
            (
                "Repetitions are counted from deterministic 2D knee-angle threshold "
                "crossings and should not be interpreted as a medical or injury assessment."
            ),
            (
                "The variability metrics describe observed repetition geometry and "
                "timing; they do not determine whether technique is safe or appropriate."
            ),
            (
                "Camera position, landmark-estimation error, body proportions, "
                "exercise variation, occlusion, and missing frames can affect results."
            )
        ]
    }


def normalize_pose_sequence_frame(
    frame,
    previous_timestamp=None
):
    if not isinstance(frame, dict):
        raise ValueError("Each pose frame must be a dictionary")

    if "timestamp_seconds" not in frame:
        raise ValueError("Pose frame requires timestamp_seconds")

    timestamp = validate_numeric(
        frame[
            "timestamp_seconds"
        ],
        "timestamp_seconds"
    )

    if timestamp < 0:
        raise ValueError("timestamp_seconds cannot be negative")

    if previous_timestamp is not None and timestamp <= previous_timestamp:
        raise ValueError("Pose frame timestamps must be strictly increasing")

    pose_landmarks = frame.get(
        "pose_landmarks"
    )

    if not isinstance(pose_landmarks, dict):
        raise ValueError("Pose frame requires pose_landmarks dictionary")

    return {
        "timestamp_seconds": timestamp,
        "pose_landmarks": pose_landmarks
    }


def analyze_squat_pose_sequence(
    frames,
    minimum_visibility=MIN_REQUIRED_VISIBILITY,
    standing_angle_min=STANDING_ANGLE_MIN,
    bottom_angle_max=BOTTOM_ANGLE_MAX,
    minimum_frame_confidence=MIN_FRAME_CONFIDENCE,
    min_rep_duration_seconds=MIN_REP_DURATION_SECONDS,
    max_rep_duration_seconds=MAX_REP_DURATION_SECONDS,
    minimum_rep_range_of_motion_degrees=MIN_REP_RANGE_OF_MOTION_DEGREES,
    max_active_frame_gap_seconds=MAX_ACTIVE_FRAME_GAP_SECONDS
):
    if not isinstance(frames, list):
        raise ValueError("frames must be a list")

    if not frames:
        raise ValueError("frames cannot be empty")

    normalized_pose_frames = []
    previous_timestamp = None

    for frame in frames:
        normalized = normalize_pose_sequence_frame(
            frame,
            previous_timestamp=previous_timestamp
        )

        normalized_pose_frames.append(
            normalized
        )

        previous_timestamp = normalized[
            "timestamp_seconds"
        ]

    angle_frames = []
    frame_analyses = []

    for frame in normalized_pose_frames:
        frame_analysis = analyze_squat_frame(
            frame[
                "pose_landmarks"
            ],
            minimum_visibility=minimum_visibility
        )

        frame_analyses.append(
            {
                "timestamp_seconds": frame[
                    "timestamp_seconds"
                ],
                "analysis": frame_analysis
            }
        )

        if frame_analysis[
            "status"
        ] != ANALYSIS_STATUS_ANALYZABLE:
            angle_frames.append(
                {
                    "timestamp_seconds": frame[
                        "timestamp_seconds"
                    ],
                    "analyzable": False,
                    "selected_side": None
                }
            )

            continue

        angle_frames.append(
            {
                "timestamp_seconds": frame[
                    "timestamp_seconds"
                ],
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
                ]
            }
        )

    result = analyze_squat_angle_sequence(
        frames=angle_frames,
        standing_angle_min=standing_angle_min,
        bottom_angle_max=bottom_angle_max,
        minimum_frame_confidence=minimum_frame_confidence,
        min_rep_duration_seconds=min_rep_duration_seconds,
        max_rep_duration_seconds=max_rep_duration_seconds,
        minimum_rep_range_of_motion_degrees=minimum_rep_range_of_motion_degrees,
        max_active_frame_gap_seconds=max_active_frame_gap_seconds
    )

    result[
        "source"
    ] = "pose_landmarks"

    result[
        "frame_analyses"
    ] = frame_analyses

    return result