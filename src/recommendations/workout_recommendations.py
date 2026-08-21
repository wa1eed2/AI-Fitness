from src.database.query_user_database import (
    get_user_profile,
    get_user_equipment_access,
    get_user_exercise_preferences,
    get_user_limitations
)

from src.database.query_exercise_database import (
    search_exercises
)
def is_environment_compatible(
    exercise_environment,
    preferred_environment
):
    if preferred_environment == "Both":
        return True

    if exercise_environment == preferred_environment:
        return True

    if exercise_environment == "Both":
        return True

    return False

def is_equipment_compatible(
    exercise_equipment,
    equipment_access
):
    if exercise_equipment == "Bodyweight":
        return True

    for item in equipment_access:
        if (
            item["equipment"] == exercise_equipment
            and item["access_status"] == "Available"
        ):
            return True

    return False

def is_exercise_disliked(
    exercise_id,
    exercise_preferences
):
    for preference in exercise_preferences:
        if (
            preference["exercise_id"] == exercise_id
            and preference["preference"] == "Disliked"
        ):
            return True

    return False

def get_preference_score(
    exercise_id,
    exercise_preferences
):
    for preference in exercise_preferences:
        if (
            preference["exercise_id"] == exercise_id
            and preference["preference"] == "Preferred"
        ):
            return 1

    return 0

def should_exclude_for_limitation(
    limitation_type
):
    hard_exclusions = [
        "Pain",
        "Limited ROM",
        "Medical Restriction"
    ]

    return limitation_type in hard_exclusions

def is_exercise_limited(
    exercise,
    limitations
):
    for limitation in limitations:
        limitation_type = limitation[
            "limitation_type"
        ]

        if not should_exclude_for_limitation(limitation_type):
            continue

        body_area = limitation["body_area"]

        joints = exercise["joints_involved"] or ""
        muscles = exercise["primary_muscle"] or ""

        if (body_area.lower() in joints.lower()
            or body_area.lower() in muscles.lower()):
            return True

    return False

def get_limitation_caution_score(
    exercise,
    limitations
):
    score = 0

    for limitation in limitations:
        if limitation["limitation_type"] != "Injury History":
            continue

        body_area = limitation["body_area"]

        joints = exercise["joints_involved"] or ""
        muscles = exercise["primary_muscle"] or ""

        if (
            body_area.lower() in joints.lower()
            or body_area.lower() in muscles.lower()
        ):
            score += 1

    return score

def is_difficulty_compatible(
    exercise_difficulty,
    user_fitness_level
):
    allowed_difficulties = {
        "Beginner": [
            "Beginner"
        ],
        "Intermediate": [
            "Beginner",
            "Intermediate"
        ],
        "Advanced": [
            "Beginner",
            "Intermediate",
            "Advanced"
        ]
    }

    if user_fitness_level not in allowed_difficulties:
        raise ValueError("Invalid fitness level")

    return exercise_difficulty in allowed_difficulties[
        user_fitness_level
    ]

def get_goal_score(
    exercise,
    primary_goal
):
    score = 0

    category = exercise.get("category")
    exercise_type = exercise.get("exercise_type")

    if primary_goal == "Strength":
        if category == "Strength":
            score += 2

        if exercise_type == "Compound":
            score += 1

    elif primary_goal == "Muscle Gain":
        if category == "Strength":
            score += 2

    elif primary_goal == "Endurance":
        if category == "Cardio":
            score += 2

    elif primary_goal == "Fat Loss":
        if category == "Cardio":
            score += 2

        if category == "Strength":
            score += 1

    elif primary_goal == "General Fitness":
        score += 1

    return score

def get_candidate_exercises_for_user(user_id):
    profile = get_user_profile(user_id)

    if profile is None:
        raise ValueError("User profile not found")

    preferred_environment = profile["preferred_environment"]

    fitness_level = profile["fitness_level"]

    primary_goal = profile["primary_goal"]

    equipment_access = get_user_equipment_access(user_id)

    exercise_preferences = get_user_exercise_preferences(user_id)

    limitations = get_user_limitations(user_id)

    exercises = search_exercises()

    candidate_exercises = []

    for exercise in exercises:
        environment_ok = is_environment_compatible(
            exercise["environment"],
            preferred_environment
        )

        equipment_ok = is_equipment_compatible(
            exercise["equipment"],
            equipment_access
        )

        disliked = is_exercise_disliked(
            exercise["exercise_id"],
            exercise_preferences
        )

        limited = is_exercise_limited(
            exercise,
            limitations
        )

        difficulty_ok = is_difficulty_compatible(
            exercise["difficulty_level"],
            fitness_level
        )

        if (
                environment_ok
                and equipment_ok
                and difficulty_ok
                and not disliked
                and not limited
        ):
            candidate_exercises.append(exercise)

    candidate_exercises.sort(
        key=lambda exercise: (
            get_limitation_caution_score(
                exercise,
                limitations
            ),
            -get_goal_score(
                exercise,
                primary_goal
            ),
            -get_difficulty_fit_score(
                exercise,
                fitness_level
            ),
            -get_preference_score(
                exercise["exercise_id"],
                exercise_preferences
            )
        )
    )
    return candidate_exercises

def select_exercises_with_movement_balance(
    candidates,
    exercise_count,
    max_per_pattern=2
):
    selected_exercises = []

    pattern_counts = {}

    for exercise in candidates:
        movement_pattern = exercise["movement_pattern"]

        current_count = pattern_counts.get(movement_pattern, 0)

        if current_count >= max_per_pattern:
            continue

        selected_exercises.append(exercise)

        pattern_counts[movement_pattern] = (current_count + 1)

        if len(selected_exercises) == exercise_count:
            break

    return selected_exercises

def get_compound_priority_score(
    exercise,
    primary_goal
):
    if primary_goal not in [
        "Strength",
        "Muscle Gain"
    ]:
        return 0

    if (
        exercise.get("category") == "Strength"
        and exercise.get("exercise_type") == "Compound"
    ):
        return 1

    return 0

def select_exercises_with_workout_balance(
    candidates,
    exercise_count,
    max_per_pattern=2,
    max_per_primary_muscle=2
):
    selected_exercises = []

    pattern_counts = {}

    muscle_counts = {}

    for exercise in candidates:
        movement_pattern = exercise[
            "movement_pattern"
        ]

        primary_muscle = exercise.get(
            "primary_muscle"
        )

        pattern_count = pattern_counts.get(
            movement_pattern,
            0
        )

        if pattern_count >= max_per_pattern:
            continue

        if primary_muscle:
            muscle_count = muscle_counts.get(
                primary_muscle,
                0
            )

            if muscle_count >= max_per_primary_muscle:
                continue

        selected_exercises.append(exercise)

        pattern_counts[movement_pattern] = (pattern_count + 1)

        if primary_muscle:
            muscle_counts[primary_muscle] = (
                muscle_counts.get(
                    primary_muscle,
                    0
                ) + 1
            )

        if len(selected_exercises) == exercise_count:
            break

    return selected_exercises

def order_workout_exercises(
    exercises,
    primary_goal
):
    return sorted(exercises, key=lambda exercise: (-get_compound_priority_score(exercise, primary_goal)))

def determine_exercise_count_from_session_duration(
    session_duration_minutes
):
    if (
        isinstance(session_duration_minutes, bool)
        or not isinstance(session_duration_minutes, (int, float))
        or session_duration_minutes <= 0
    ):
        raise ValueError("Session duration must be greater than 0")

    if session_duration_minutes <= 30:
        return 3

    if session_duration_minutes <= 45:
        return 4

    if session_duration_minutes <= 60:
        return 5

    return 6

def get_sets_and_reps_for_goal(
    primary_goal
):
    if primary_goal == "Strength":
        return {"sets": 4, "reps": "4-6"}

    if primary_goal == "Muscle Gain":
        return {"sets": 3, "reps": "8-12"}

    if primary_goal == "Endurance":
        return {"sets": 3, "reps": "15-20"}

    if primary_goal == "Fat Loss":
        return {"sets": 3, "reps": "10-15"}

    return {"sets": 3, "reps": "8-12"}

def get_rest_seconds_for_goal(
    primary_goal
):
    if primary_goal == "Strength":
        return 180

    if primary_goal == "Muscle Gain":
        return 90

    if primary_goal == "Endurance":
        return 45

    if primary_goal == "Fat Loss":
        return 60

    return 60

def get_workout_prescription_for_goal(
    primary_goal
):
    sets_and_reps = get_sets_and_reps_for_goal(primary_goal)

    rest_seconds = get_rest_seconds_for_goal(primary_goal)

    return {
        "sets": sets_and_reps["sets"],
        "reps": sets_and_reps["reps"],
        "rest_seconds": rest_seconds
    }

def estimate_workout_duration_minutes(
    workout_exercises
):
    active_seconds_per_set = 45

    transition_seconds = 60

    total_seconds = 0

    for exercise in workout_exercises:
        duration_minutes = exercise.get(
            "duration_minutes"
        )

        if duration_minutes is not None:
            total_seconds += (
                duration_minutes * 60
            )

            continue

        sets = exercise["sets"]

        rest_seconds = exercise[
            "rest_seconds"
        ]

        active_seconds = (
            sets * active_seconds_per_set
        )

        rest_between_sets = (
            (sets - 1) * rest_seconds
        )

        total_seconds += (
            active_seconds
            + rest_between_sets
        )

    if len(workout_exercises) > 1:
        total_seconds += (
            (len(workout_exercises) - 1)
            * transition_seconds
        )

    return total_seconds / 60

def does_workout_fit_session(
    estimated_duration_minutes,
    session_duration_minutes
):
    return (
        estimated_duration_minutes
        <= session_duration_minutes
    )

def get_warm_up_minutes(
    session_duration_minutes
):
    if session_duration_minutes <= 30:
        return 5

    if session_duration_minutes <= 60:
        return 8

    return 10

def get_cool_down_minutes(
    session_duration_minutes
):
    if session_duration_minutes <= 30:
        return 3

    if session_duration_minutes <= 60:
        return 5

    return 8

def add_exercise_order_numbers(
    exercises
):
    ordered_exercises = []

    for index, exercise in enumerate(
        exercises,
        start=1
    ):
        ordered_exercise = exercise.copy()

        ordered_exercise["order"] = index

        ordered_exercises.append(
            ordered_exercise
        )

    return ordered_exercises

def get_workout_plan_status(
    fits_session
):
    if fits_session:
        return "Fits Session"

    return "Exceeds Session"

def calculate_total_workout_duration(
    workout_exercises,
    warm_up_minutes,
    cool_down_minutes
):
    main_workout_duration = estimate_workout_duration_minutes(
        workout_exercises
    )

    return (
        main_workout_duration
        + warm_up_minutes
        + cool_down_minutes
    )

def trim_workout_to_session_duration(
    workout_exercises,
    session_duration_minutes,
    warm_up_minutes,
    cool_down_minutes
):
    fitted_exercises = list(
        workout_exercises
    )

    while len(fitted_exercises) > 1:
        total_duration = calculate_total_workout_duration(
            fitted_exercises,
            warm_up_minutes,
            cool_down_minutes
        )

        if total_duration <= session_duration_minutes:
            break

        fitted_exercises.pop()

    return fitted_exercises

def get_exercise_prescription(
    exercise,
    primary_goal,
    fitness_level="Intermediate"
):
    category = exercise.get(
        "category"
    )

    if category == "Cardio":
        return {
            "prescription_type": "duration",
            "sets": None,
            "reps": None,
            "rest_seconds": 0,
            "duration_minutes": 10,
            "rir_target": None,
            "rpe_target": None
        }

    if category in [
        "Mobility",
        "Stretching",
        "Yoga"
    ]:
        return {
            "prescription_type": "duration",
            "sets": None,
            "reps": None,
            "rest_seconds": 0,
            "duration_minutes": 5,
            "rir_target": None,
            "rpe_target": None
        }

    sets_and_reps = get_sets_and_reps_for_exercise(
        exercise,
        primary_goal
    )

    rest_seconds = get_rest_seconds_for_goal(
        primary_goal
    )

    rir_target = get_rir_target_for_fitness_level(
        fitness_level
    )

    rpe_target = get_rpe_target_from_rir(
        rir_target
    )

    return {
        "prescription_type": "sets_reps",
        "sets": sets_and_reps["sets"],
        "reps": sets_and_reps["reps"],
        "rest_seconds": rest_seconds,
        "duration_minutes": None,
        "rir_target": rir_target,
        "rpe_target": rpe_target
    }

def get_goal_priority_categories(
    primary_goal
):
    goal_categories = {
        "Strength": [
            "Strength"
        ],
        "Muscle Gain": [
            "Strength"
        ],
        "Endurance": [
            "Cardio"
        ],
        "Fat Loss": [
            "Cardio",
            "Strength"
        ],
        "General Fitness": [
            "Strength",
            "Cardio"
        ]
    }

    return goal_categories.get(
        primary_goal,
        []
    )

def prioritize_candidates_for_goal_composition(
    candidates,
    primary_goal
):
    priority_categories = get_goal_priority_categories(
        primary_goal
    )

    prioritized = []

    prioritized_ids = set()

    for category in priority_categories:
        for exercise in candidates:
            if exercise["exercise_id"] in prioritized_ids:
                continue

            if exercise.get("category") == category:
                prioritized.append(
                    exercise
                )

                prioritized_ids.add(
                    exercise["exercise_id"]
                )

                break

    for exercise in candidates:
        if exercise["exercise_id"] in prioritized_ids:
            continue

        prioritized.append(exercise)

    return prioritized

def get_target_difficulty_score(
    fitness_level
):
    targets = {
        "Beginner": 2,
        "Intermediate": 3,
        "Advanced": 4
    }

    if fitness_level not in targets:
        raise ValueError("Invalid fitness level")

    return targets[fitness_level]

def get_difficulty_fit_score(
    exercise,
    fitness_level
):
    target_score = get_target_difficulty_score(
        fitness_level
    )

    difficulty_score = exercise.get(
        "difficulty_score"
    )

    if difficulty_score is None:
        return 0

    difference = abs(
        difficulty_score
        - target_score
    )

    return max(
        0,
        5 - difference
    )

def adjust_exercise_count_for_fitness_level(
    exercise_count,
    fitness_level
):
    if fitness_level == "Beginner":
        return max(1, exercise_count - 1)

    if fitness_level == "Advanced":
        return exercise_count + 1

    if fitness_level == "Intermediate":
        return exercise_count

    raise ValueError("Invalid fitness level")

def get_rir_target_for_fitness_level(
    fitness_level
):
    targets = {
        "Beginner": 3,
        "Intermediate": 2,
        "Advanced": 1
    }

    if fitness_level not in targets:
        raise ValueError("Invalid fitness level")

    return targets[fitness_level]

def get_rpe_target_from_rir(
    rir_target
):
    if (
        isinstance(rir_target, bool)
        or not isinstance(rir_target, (int, float))
        or rir_target < 0
        or rir_target > 10
    ):
        raise ValueError("RIR target must be between 0 and 10")

    return 10 - rir_target

def get_sets_and_reps_for_exercise(
    exercise,
    primary_goal
):
    prescription = get_sets_and_reps_for_goal(
        primary_goal
    )

    if (
        primary_goal == "Strength"
        and exercise.get("category") == "Strength"
        and exercise.get("exercise_type") == "Isolation"
    ):
        return {
            "sets": 3,
            "reps": "8-12"
        }

    return prescription

def get_weekly_training_day_numbers(
    training_days_per_week
):
    schedules = {
        1: [1],
        2: [1, 4],
        3: [1, 3, 5],
        4: [1, 2, 4, 6],
        5: [1, 2, 3, 5, 6],
        6: [1, 2, 3, 4, 5, 6],
        7: [1, 2, 3, 4, 5, 6, 7]
    }

    if (
        isinstance(training_days_per_week, bool)
        or not isinstance(training_days_per_week, int)
        or training_days_per_week not in schedules
    ):
        raise ValueError("Training days per week must be between 1 and 7")

    return schedules[training_days_per_week]

def get_weekly_focus_categories(
    primary_goal,
    training_days_per_week
):
    get_weekly_training_day_numbers(training_days_per_week)

    focus_patterns = {
        "Strength": [
            "Strength"
        ],
        "Muscle Gain": [
            "Strength"
        ],
        "Endurance": [
            "Cardio",
            "Strength"
        ],
        "Fat Loss": [
            "Cardio",
            "Strength"
        ],
        "General Fitness": [
            "Strength",
            "Cardio",
            "Mobility"
        ]
    }

    pattern = focus_patterns.get(
        primary_goal,
        [
            "Strength",
            "Cardio"
        ]
    )

    focuses = []

    for index in range(training_days_per_week):
        focuses.append(
            pattern[index % len(pattern)]
        )

    return focuses

def prioritize_candidates_for_day_focus(
    candidates,
    focus_category
):
    if focus_category is None:
        return list(candidates)

    focused_candidates = []
    other_candidates = []

    for exercise in candidates:
        if exercise.get("category") == focus_category:
            focused_candidates.append(exercise)
        else:
            other_candidates.append(exercise)

    return focused_candidates + other_candidates

def prioritize_candidates_for_weekly_rotation(
    candidates,
    weekly_used_exercise_ids=None,
    previous_workout_exercise_ids=None,
    previous_primary_muscles=None
):
    weekly_used_exercise_ids = set(weekly_used_exercise_ids or [])
    previous_workout_exercise_ids = set(previous_workout_exercise_ids or [])
    previous_primary_muscles = set(previous_primary_muscles or [])

    def rotation_score(exercise):
        score = 0

        exercise_id = exercise["exercise_id"]
        primary_muscle = exercise.get("primary_muscle")

        if exercise_id in weekly_used_exercise_ids:
            score += 1

        if primary_muscle in previous_primary_muscles:
            score += 2

        if exercise_id in previous_workout_exercise_ids:
            score += 2

        return score

    return sorted(
        candidates,
        key=rotation_score
    )

def build_workout_for_user(
    user_id,
    exercise_count=None,
    focus_category=None,
    weekly_used_exercise_ids=None,
    previous_workout_exercise_ids=None,
    previous_primary_muscles=None
):
    if exercise_count is not None:
        if (
            isinstance(exercise_count, bool)
            or not isinstance(exercise_count, int)
        ):
            raise ValueError("Exercise count must be an integer")

        if exercise_count <= 0:
            raise ValueError("Exercise count must be greater than 0")

    profile = get_user_profile(user_id)

    if profile is None:
        raise ValueError("User profile not found")

    if exercise_count is None:
        exercise_count = determine_exercise_count_from_session_duration(
            profile["session_duration_minutes"]
        )

        exercise_count = adjust_exercise_count_for_fitness_level(
            exercise_count,
            profile.get("fitness_level", "Intermediate")
        )

    candidates = get_candidate_exercises_for_user(user_id)

    candidates = prioritize_candidates_for_goal_composition(
        candidates,
        profile["primary_goal"]
    )

    candidates = prioritize_candidates_for_day_focus(
        candidates,
        focus_category
    )

    candidates = prioritize_candidates_for_weekly_rotation(
        candidates,
        weekly_used_exercise_ids,
        previous_workout_exercise_ids,
        previous_primary_muscles
    )

    selected_exercises = select_exercises_with_workout_balance(
        candidates,
        exercise_count
    )

    selected_exercises = order_workout_exercises(
        selected_exercises,
        profile["primary_goal"]
    )

    workout_exercises = []

    for exercise in selected_exercises:
        workout_exercise = exercise.copy()

        prescription = get_exercise_prescription(
            exercise,
            profile["primary_goal"],
            profile.get("fitness_level", "Intermediate")
        )

        workout_exercise["prescription_type"] = prescription["prescription_type"]
        workout_exercise["sets"] = prescription["sets"]
        workout_exercise["reps"] = prescription["reps"]
        workout_exercise["rest_seconds"] = prescription["rest_seconds"]
        workout_exercise["duration_minutes"] = prescription["duration_minutes"]
        workout_exercise["rir_target"] = prescription["rir_target"]
        workout_exercise["rpe_target"] = prescription["rpe_target"]

        workout_exercises.append(workout_exercise)

    return workout_exercises

def build_workout_plan_for_user(
    user_id,
    exercise_count=None,
    focus_category=None,
    weekly_used_exercise_ids=None,
    previous_workout_exercise_ids=None,
    previous_primary_muscles=None
):
    profile = get_user_profile(user_id)

    if profile is None:
        raise ValueError("User profile not found")

    workout_exercises = build_workout_for_user(
        user_id,
        exercise_count,
        focus_category,
        weekly_used_exercise_ids,
        previous_workout_exercise_ids,
        previous_primary_muscles
    )

    requested_exercise_count = len(workout_exercises)
    session_duration = profile["session_duration_minutes"]

    warm_up_minutes = get_warm_up_minutes(session_duration)
    cool_down_minutes = get_cool_down_minutes(session_duration)

    workout_exercises = trim_workout_to_session_duration(
        workout_exercises,
        session_duration,
        warm_up_minutes,
        cool_down_minutes
    )

    was_shortened = len(workout_exercises) < requested_exercise_count

    workout_exercises = add_exercise_order_numbers(workout_exercises)

    main_workout_duration = estimate_workout_duration_minutes(
        workout_exercises
    )

    total_duration = calculate_total_workout_duration(
        workout_exercises,
        warm_up_minutes,
        cool_down_minutes
    )

    fits_session = does_workout_fit_session(
        total_duration,
        session_duration
    )

    status = get_workout_plan_status(fits_session)

    return {
        "user_id": user_id,
        "primary_goal": profile["primary_goal"],
        "focus_category": focus_category,
        "session_duration_minutes": session_duration,
        "warm_up_minutes": warm_up_minutes,
        "cool_down_minutes": cool_down_minutes,
        "estimated_duration_minutes": main_workout_duration,
        "estimated_total_duration_minutes": total_duration,
        "fits_session": fits_session,
        "status": status,
        "was_shortened": was_shortened,
        "requested_exercise_count": requested_exercise_count,
        "exercise_count": len(workout_exercises),
        "exercises": workout_exercises
    }

def get_weekly_muscle_frequency(
    weekly_plan
):
    muscle_frequency = {}

    for day in weekly_plan:
        if day.get("day_type") != "Training":
            continue

        workout = day.get("workout") or {}
        exercises = workout.get("exercises", [])

        muscles_for_day = {
            exercise["primary_muscle"]
            for exercise in exercises
            if exercise.get("primary_muscle")
        }

        for muscle in muscles_for_day:
            muscle_frequency[muscle] = muscle_frequency.get(muscle, 0) + 1

    return muscle_frequency


def get_weekly_recovery_warnings(
    weekly_plan
):
    warnings = []
    previous_training_day = None

    for day in weekly_plan:
        if day.get("day_type") != "Training":
            continue

        workout = day.get("workout") or {}
        exercises = workout.get("exercises", [])

        current_muscles = {
            exercise["primary_muscle"]
            for exercise in exercises
            if exercise.get("primary_muscle")
        }

        if previous_training_day is not None:
            day_gap = day["day_number"] - previous_training_day["day_number"]

            if day_gap == 1:
                overlap = sorted(
                    current_muscles
                    & previous_training_day["muscles"]
                )

                if overlap:
                    warnings.append(
                        {
                            "previous_day": previous_training_day["day_name"],
                            "current_day": day["day_name"],
                            "overlapping_primary_muscles": overlap
                        }
                    )

        previous_training_day = {
            "day_number": day["day_number"],
            "day_name": day["day_name"],
            "muscles": current_muscles
        }

    return warnings


def validate_weekly_workout_plan(
    weekly_plan_result
):
    if not isinstance(weekly_plan_result, dict):
        raise ValueError("Weekly plan must be a dictionary")

    days = weekly_plan_result.get("weekly_plan")

    if not isinstance(days, list) or len(days) != 7:
        raise ValueError("Weekly plan must contain exactly 7 days")

    expected_training_days = weekly_plan_result.get("training_days_per_week")

    training_days = [
        day
        for day in days
        if day.get("day_type") == "Training"
    ]

    if len(training_days) != expected_training_days:
        raise ValueError("Weekly plan training-day count does not match profile")

    for expected_day_number, day in enumerate(days, start=1):
        if day.get("day_number") != expected_day_number:
            raise ValueError("Weekly plan day numbers must run from 1 to 7")

        if day.get("day_type") == "Rest":
            if day.get("workout") is not None:
                raise ValueError("Rest day must not contain a workout")

            continue

        if day.get("day_type") != "Training":
            raise ValueError("Invalid weekly day type")

        workout = day.get("workout")

        if not isinstance(workout, dict):
            raise ValueError("Training day must contain a workout")

        exercises = workout.get("exercises", [])

        exercise_ids = [
            exercise["exercise_id"]
            for exercise in exercises
        ]

        if len(exercise_ids) != len(set(exercise_ids)):
            raise ValueError("Workout contains duplicate exercises")

        for index, exercise in enumerate(exercises, start=1):
            if exercise.get("order") != index:
                raise ValueError("Workout exercise order is invalid")

    return True

def build_weekly_workout_plan_for_user(
    user_id,
    exercise_count=None
):
    profile = get_user_profile(user_id)

    if profile is None:
        raise ValueError("User profile not found")

    training_days_per_week = profile["training_days_per_week"]

    training_day_numbers = get_weekly_training_day_numbers(
        training_days_per_week
    )

    focus_categories = get_weekly_focus_categories(
        profile["primary_goal"],
        training_days_per_week
    )

    day_names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]

    weekly_plan = []

    weekly_used_exercise_ids = set()
    previous_workout_exercise_ids = set()
    previous_primary_muscles = set()

    focus_index = 0

    for day_number, day_name in enumerate(day_names, start=1):
        if day_number not in training_day_numbers:
            weekly_plan.append(
                {
                    "day_number": day_number,
                    "day_name": day_name,
                    "day_type": "Rest",
                    "focus_category": None,
                    "workout": None
                }
            )

            continue

        focus_category = focus_categories[focus_index]

        workout = build_workout_plan_for_user(
            user_id,
            exercise_count=exercise_count,
            focus_category=focus_category,
            weekly_used_exercise_ids=set(weekly_used_exercise_ids),
            previous_workout_exercise_ids=set(previous_workout_exercise_ids),
            previous_primary_muscles=set(previous_primary_muscles)
        )

        weekly_plan.append(
            {
                "day_number": day_number,
                "day_name": day_name,
                "day_type": "Training",
                "focus_category": focus_category,
                "workout": workout
            }
        )

        workout_exercises = workout.get("exercises", [])

        previous_workout_exercise_ids = {
            exercise["exercise_id"]
            for exercise in workout_exercises
        }

        previous_primary_muscles = {
            exercise["primary_muscle"]
            for exercise in workout_exercises
            if exercise.get("primary_muscle")
        }

        weekly_used_exercise_ids.update(previous_workout_exercise_ids)

        focus_index += 1

    result = {
        "user_id": user_id,
        "training_days_per_week": training_days_per_week,
        "unique_exercise_count": len(weekly_used_exercise_ids),
        "muscle_frequency": get_weekly_muscle_frequency(weekly_plan),
        "recovery_warnings": get_weekly_recovery_warnings(weekly_plan),
        "weekly_plan": weekly_plan
    }

    validate_weekly_workout_plan(result)

    return result