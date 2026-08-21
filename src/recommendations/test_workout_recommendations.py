from unittest.mock import patch

from src.database.query_user_database import (
    create_user,
    create_user_profile,
    add_equipment_access,
    add_exercise_preference,
    add_user_limitation,
    delete_user
)

from src.recommendations.workout_recommendations import (
    is_environment_compatible,
    is_equipment_compatible,
    is_exercise_disliked,
    is_exercise_limited,
    is_difficulty_compatible,
    get_preference_score,
    get_candidate_exercises_for_user,
    get_limitation_caution_score,
    get_goal_score,
    build_workout_for_user,
    select_exercises_with_movement_balance,
    determine_exercise_count_from_session_duration,
    get_sets_and_reps_for_goal,
    get_rest_seconds_for_goal,
    get_workout_prescription_for_goal,
    estimate_workout_duration_minutes,
    does_workout_fit_session,
    build_workout_plan_for_user,
    get_compound_priority_score,
    select_exercises_with_workout_balance,
    order_workout_exercises,
    get_warm_up_minutes,
    get_cool_down_minutes,
    add_exercise_order_numbers,
    get_workout_plan_status,
    calculate_total_workout_duration,
    trim_workout_to_session_duration,
    get_exercise_prescription,
    get_goal_priority_categories,
    prioritize_candidates_for_goal_composition,
    get_target_difficulty_score,
    get_difficulty_fit_score,
    adjust_exercise_count_for_fitness_level,
    get_rir_target_for_fitness_level,
    get_rpe_target_from_rir,
    get_sets_and_reps_for_exercise,
    get_weekly_training_day_numbers,
    get_weekly_focus_categories,
    prioritize_candidates_for_day_focus,
    build_weekly_workout_plan_for_user,
    prioritize_candidates_for_weekly_rotation,
    get_weekly_muscle_frequency,
    get_weekly_recovery_warnings,
    validate_weekly_workout_plan
)

def test_environment_compatibility():
    cases = [
        ("Home", "Home", True),
        ("Both", "Home", True),
        ("Gym", "Home", False),

        ("Gym", "Gym", True),
        ("Both", "Gym", True),
        ("Home", "Gym", False),

        ("Home", "Both", True),
        ("Gym", "Both", True),
        ("Both", "Both", True),
    ]

    for exercise_environment, preferred_environment, expected in cases:
        result = is_environment_compatible(
            exercise_environment,
            preferred_environment
        )

        if result != expected:
            raise ValueError(f"FAIL: {exercise_environment} exercise " f"with {preferred_environment} preference")

    print("PASS: Exercise environment compatibility works correctly")


def test_candidate_exercises_match_user_environment():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "General Fitness",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Home"
        }

        create_user_profile(
            user_id,
            profile
        )

        exercises = get_candidate_exercises_for_user(user_id)

        if not exercises:
            raise ValueError("FAIL: No candidate exercises returned")

        for exercise in exercises:
            if not is_environment_compatible(
                exercise["environment"],
                "Home"
            ):
                raise ValueError(f"FAIL: Incompatible exercise returned: " f"{exercise['name']}")

        print("PASS: Candidate exercises match user environment")

    finally:
        delete_user(user_id)


def test_equipment_compatibility():
    equipment_access = [
        {
            "equipment": "Dumbbell",
            "access_status": "Available"
        },
        {
            "equipment": "Barbell",
            "access_status": "Unavailable"
        }
    ]

    if not is_equipment_compatible(
        "Bodyweight",
        equipment_access
    ):
        raise ValueError("FAIL: Bodyweight should always be compatible")

    if not is_equipment_compatible(
        "Dumbbell",
        equipment_access
    ):
        raise ValueError("FAIL: Available equipment was rejected")

    if is_equipment_compatible(
        "Barbell",
        equipment_access
    ):
        raise ValueError("FAIL: Unavailable equipment was accepted")

    if is_equipment_compatible(
        "Kettlebell",
        equipment_access
    ):
        raise ValueError("FAIL: Unlisted equipment was accepted")

    print("PASS: Exercise equipment compatibility works correctly")


def test_candidate_exercises_match_equipment_access():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "General Fitness",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Both"
        }

        create_user_profile(
            user_id,
            profile
        )

        add_equipment_access(
            user_id,
            "Dumbbell",
            "Available"
        )

        add_equipment_access(
            user_id,
            "Barbell",
            "Unavailable"
        )

        exercises = get_candidate_exercises_for_user(
            user_id
        )

        if not exercises:
            raise ValueError("FAIL: No candidate exercises returned")

        for exercise in exercises:
            if exercise["equipment"] not in [
                "Bodyweight",
                "Dumbbell"
            ]:
                raise ValueError(f"FAIL: Exercise requiring unavailable equipment returned: " f"{exercise['name']}")

        print("PASS: Candidate exercises respect equipment access")

    finally:
        delete_user(user_id)


def test_disliked_exercise_detection():
    preferences = [
        {
            "exercise_id": "E001",
            "preference": "Disliked"
        },
        {
            "exercise_id": "E002",
            "preference": "Preferred"
        }
    ]

    if not is_exercise_disliked(
        "E001",
        preferences
    ):
        raise ValueError("FAIL: Disliked exercise was not detected")

    if is_exercise_disliked(
        "E002",
        preferences
    ):
        raise ValueError("FAIL: Preferred exercise was incorrectly marked as disliked")

    if is_exercise_disliked(
        "E999",
        preferences
    ):
        raise ValueError("FAIL: Exercise with no preference was incorrectly marked as disliked")

    print("PASS: Disliked exercise detection works correctly")


def test_disliked_exercise_excluded_from_candidates():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "General Fitness",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Both"
        }

        create_user_profile(
            user_id,
            profile
        )

        add_exercise_preference(
            user_id,
            "E001",
            "Disliked"
        )

        exercises = get_candidate_exercises_for_user(user_id)

        exercise_ids = [
            exercise["exercise_id"]
            for exercise in exercises
        ]

        if "E001" in exercise_ids:
            raise ValueError("FAIL: Disliked exercise was returned as a candidate")

        print("PASS: Disliked exercise excluded from candidates")

    finally:
        delete_user(user_id)


def test_preferred_exercise_ranks_higher():
    preferences = [
        {
            "exercise_id": "E002",
            "preference": "Preferred"
        }
    ]

    exercises = [
        {
            "exercise_id": "E001",
            "name": "Neutral Exercise"
        },
        {
            "exercise_id": "E002",
            "name": "Preferred Exercise"
        }
    ]

    exercises.sort(
        key=lambda exercise: get_preference_score(
            exercise["exercise_id"],
            preferences
        ),
        reverse=True
    )

    if exercises[0]["exercise_id"] != "E002":
        raise ValueError("FAIL: Preferred exercise did not rank higher")

    print("PASS: Preferred exercise ranked higher")


def test_preferred_exercise_ranks_first_in_candidates():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "General Fitness",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Both"
        }

        create_user_profile(
            user_id,
            profile
        )

        test_exercises = [
            {
                "exercise_id": "TEST001",
                "name": "Neutral Exercise",
                "category": "Strength",
                "exercise_type": "Compound",
                "primary_muscle": "Chest",
                "joints_involved": "Shoulder, Elbow",
                "equipment": "Bodyweight",
                "difficulty_level": "Intermediate",
                "difficulty_score": 3,
                "movement_pattern": "Push",
                "environment": "Both"
            },
            {
                "exercise_id": "TEST002",
                "name": "Preferred Exercise",
                "category": "Strength",
                "exercise_type": "Compound",
                "primary_muscle": "Chest",
                "joints_involved": "Shoulder, Elbow",
                "equipment": "Bodyweight",
                "difficulty_level": "Intermediate",
                "difficulty_score": 3,
                "movement_pattern": "Push",
                "environment": "Both"
            }
        ]

        test_preferences = [
            {
                "exercise_id": "TEST002",
                "preference": "Preferred"
            }
        ]

        with patch(
            "src.recommendations.workout_recommendations.search_exercises",
            return_value=test_exercises
        ), patch(
            "src.recommendations.workout_recommendations.get_user_exercise_preferences",
            return_value=test_preferences
        ):
            exercises = get_candidate_exercises_for_user(
                user_id
            )

        if not exercises:
            raise ValueError("FAIL: No candidate exercises returned")

        if exercises[0]["exercise_id"] != "TEST002":
            raise ValueError("FAIL: Preferred exercise did not rank first " "when higher-priority scores were equal")

        print("PASS: Preferred exercise ranked higher when other scores were equal")

    finally:
        delete_user(user_id)


def test_exercise_limitation_detection():
    exercise = {
        "primary_muscle": "Quadriceps",
        "joints_involved": "Knee, Hip"
    }

    knee_limitations = [
        {
            "body_area": "Knee",
            "limitation_type": "Pain",
            "notes": None
        }
    ]

    shoulder_limitations = [
        {
            "body_area": "Shoulder",
            "limitation_type": "Pain",
            "notes": None
        }
    ]

    if not is_exercise_limited(
        exercise,
        knee_limitations
    ):
        raise ValueError("FAIL: Knee limitation was not detected")

    if is_exercise_limited(
        exercise,
        shoulder_limitations
    ):
        raise ValueError("FAIL: Unrelated shoulder limitation incorrectly blocked exercise")

    print("PASS: Exercise limitation detection works correctly")


def test_user_limitation_excludes_affected_exercises():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "General Fitness",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Both"
        }

        create_user_profile(
            user_id,
            profile
        )

        before_limitation = get_candidate_exercises_for_user(
            user_id
        )

        knee_limitation = {
            "body_area": "Knee",
            "limitation_type": "Pain",
            "notes": None
        }

        knee_related_before = [
            exercise
            for exercise in before_limitation
            if is_exercise_limited(
                exercise,
                [knee_limitation]
            )
        ]

        if not knee_related_before:
            raise ValueError("FAIL: Test setup found no knee-related candidate exercises")

        add_user_limitation(
            user_id,
            "Knee",
            "Pain",
            None
        )

        after_limitation = get_candidate_exercises_for_user(user_id)

        after_ids = {
            exercise["exercise_id"]
            for exercise in after_limitation
        }

        for exercise in knee_related_before:
            if exercise["exercise_id"] in after_ids:
                raise ValueError(f"FAIL: Knee-related exercise was not excluded: " f"{exercise['name']}")

        print("PASS: User limitation excluded affected exercises")

    finally:
        delete_user(user_id)


def test_limitation_type_exclusion_rules():
    exercise = {
        "primary_muscle": "Quadriceps",
        "joints_involved": "Knee, Hip"
    }

    pain_limitation = [
        {
            "body_area": "Knee",
            "limitation_type": "Pain",
            "notes": None
        }
    ]

    injury_history_limitation = [
        {
            "body_area": "Knee",
            "limitation_type": "Injury History",
            "notes": None
        }
    ]

    if not is_exercise_limited(
        exercise,
        pain_limitation
    ):
        raise ValueError("FAIL: Pain limitation should hard-block affected exercise")

    if is_exercise_limited(
        exercise,
        injury_history_limitation
    ):
        raise ValueError("FAIL: Injury History should not hard-block affected exercise")

    print("PASS: Limitation types apply different exclusion rules")


def test_injury_history_lowers_ranking():
    safe_exercise = {
        "exercise_id": "E001",
        "name": "Safe Exercise",
        "primary_muscle": "Chest",
        "joints_involved": "Shoulder, Elbow"
    }

    caution_exercise = {
        "exercise_id": "E002",
        "name": "Knee Exercise",
        "primary_muscle": "Quadriceps",
        "joints_involved": "Knee, Hip"
    }

    exercises = [
        caution_exercise,
        safe_exercise
    ]

    limitations = [
        {
            "body_area": "Knee",
            "limitation_type": "Injury History",
            "notes": None
        }
    ]

    preferences = []

    exercises.sort(
        key=lambda exercise: (
            get_limitation_caution_score(
                exercise,
                limitations
            ),
            -get_preference_score(
                exercise["exercise_id"],
                preferences
            )
        )
    )

    if exercises[0]["exercise_id"] != "E001":
        raise ValueError("FAIL: Safer exercise did not rank above injury-history exercise")

    if exercises[1]["exercise_id"] != "E002":
        raise ValueError("FAIL: Injury-history exercise was not retained")

    print("PASS: Injury history lowered ranking without excluding exercise")


def test_saved_injury_history_lowers_candidate_ranking():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "General Fitness",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Both"
        }

        create_user_profile(
            user_id,
            profile
        )

        before_limitation = get_candidate_exercises_for_user(user_id)

        injury_history = [
            {
                "body_area": "Knee",
                "limitation_type": "Injury History",
                "notes": None
            }
        ]

        knee_exercises = [
            exercise
            for exercise in before_limitation
            if get_limitation_caution_score(
                exercise,
                injury_history
            ) > 0
        ]

        safe_exercises = [
            exercise
            for exercise in before_limitation
            if get_limitation_caution_score(
                exercise,
                injury_history
            ) == 0
        ]

        if not knee_exercises:
            raise ValueError("FAIL: No knee-related candidate found for test")

        if not safe_exercises:
            raise ValueError("FAIL: No safer candidate found for test")

        caution_exercise_id = knee_exercises[0]["exercise_id"]

        safe_exercise_id = safe_exercises[0]["exercise_id"]

        add_user_limitation(
            user_id,
            "Knee",
            "Injury History",
            None
        )

        after_limitation = get_candidate_exercises_for_user(user_id)

        exercise_ids = [
            exercise["exercise_id"]
            for exercise in after_limitation
        ]

        if caution_exercise_id not in exercise_ids:
            raise ValueError("FAIL: Injury-history exercise was incorrectly excluded")

        if safe_exercise_id not in exercise_ids:
            raise ValueError("FAIL: Safer exercise unexpectedly disappeared")

        if (
            exercise_ids.index(safe_exercise_id)
            >= exercise_ids.index(caution_exercise_id)
        ):
            raise ValueError("FAIL: Injury-history exercise was not ranked lower")

        print("PASS: Saved injury history lowered candidate ranking")

    finally:
        delete_user(user_id)

def test_difficulty_compatibility():
    if not is_difficulty_compatible(
        "Beginner",
        "Beginner"
    ):
        raise ValueError("FAIL: Beginner user should allow Beginner exercise")

    if is_difficulty_compatible(
        "Intermediate",
        "Beginner"
    ):
        raise ValueError("FAIL: Beginner user should not allow Intermediate exercise")

    if not is_difficulty_compatible(
        "Beginner",
        "Intermediate"
    ):
        raise ValueError("FAIL: Intermediate user should allow Beginner exercise")

    if not is_difficulty_compatible(
        "Intermediate",
        "Intermediate"
    ):
        raise ValueError("FAIL: Intermediate user should allow Intermediate exercise")

    if is_difficulty_compatible(
        "Advanced",
        "Intermediate"
    ):
        raise ValueError("FAIL: Intermediate user should not allow Advanced exercise")

    if not is_difficulty_compatible(
        "Advanced",
        "Advanced"
    ):
        raise ValueError("FAIL: Advanced user should allow Advanced exercise")

    print("PASS: Exercise difficulty compatibility works correctly")


def test_beginner_user_gets_beginner_exercises_only():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Beginner",
            "primary_goal": "General Fitness",
            "training_days_per_week": 3,
            "session_duration_minutes": 45,
            "preferred_environment": "Both"
        }

        create_user_profile(
            user_id,
            profile
        )

        exercises = get_candidate_exercises_for_user(user_id)

        if not exercises:
            raise ValueError("FAIL: No candidate exercises returned for Beginner user")

        for exercise in exercises:
            if exercise["difficulty_level"] != "Beginner":
                raise ValueError(f"FAIL: Beginner user received " f"{exercise['difficulty_level']} exercise: " f"{exercise['name']}")

        print("PASS: Beginner user received Beginner exercises only")

    finally:
        delete_user(user_id)


def test_intermediate_user_excludes_advanced_exercises():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "General Fitness",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Both"
        }

        create_user_profile(
            user_id,
            profile
        )

        exercises = get_candidate_exercises_for_user(user_id)

        if not exercises:
            raise ValueError("FAIL: No candidate exercises returned for Intermediate user")

        for exercise in exercises:
            if exercise["difficulty_level"] == "Advanced":
                raise ValueError(f"FAIL: Intermediate user received Advanced exercise: " f"{exercise['name']}")

        print("PASS: Intermediate user excluded Advanced exercises")

    finally:
        delete_user(user_id)


def test_strength_goal_ranks_compound_strength_higher():
    strength_exercise = {
        "category": "Strength",
        "exercise_type": "Compound"
    }

    cardio_exercise = {
        "category": "Cardio",
        "exercise_type": None
    }

    strength_score = get_goal_score(
        strength_exercise,
        "Strength"
    )

    cardio_score = get_goal_score(
        cardio_exercise,
        "Strength"
    )

    if strength_score <= cardio_score:
        raise ValueError("FAIL: Compound strength exercise did not rank higher for Strength goal")

    print("PASS: Strength goal ranked compound strength exercise higher")


def test_other_goal_scores():
    strength_exercise = {
        "category": "Strength",
        "exercise_type": "Isolation"
    }

    cardio_exercise = {
        "category": "Cardio",
        "exercise_type": None
    }

    if get_goal_score(
        strength_exercise,
        "Muscle Gain"
    ) <= get_goal_score(
        cardio_exercise,
        "Muscle Gain"
    ):
        raise ValueError("FAIL: Muscle Gain did not favor Strength exercise")

    if get_goal_score(
        cardio_exercise,
        "Endurance"
    ) <= get_goal_score(
        strength_exercise,
        "Endurance"
    ):
        raise ValueError("FAIL: Endurance did not favor Cardio exercise")

    if get_goal_score(
        cardio_exercise,
        "Fat Loss"
    ) <= get_goal_score(
        strength_exercise,
        "Fat Loss"
    ):
        raise ValueError("FAIL: Fat Loss did not rank Cardio higher")

    if get_goal_score(
        strength_exercise,
        "General Fitness"
    ) != get_goal_score(
        cardio_exercise,
        "General Fitness"
    ):
        raise ValueError("FAIL: General Fitness should treat both equally")

    print("PASS: Other primary-goal scoring rules work correctly")


def test_strength_goal_prioritizes_strength_candidates():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Advanced",
            "primary_goal": "Strength",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Both"
        }

        create_user_profile(
            user_id,
            profile
        )

        test_exercises = [
            {
                "exercise_id": "TEST001",
                "name": "Test Compound Strength Exercise",
                "category": "Strength",
                "exercise_type": "Compound",
                "primary_muscle": "Quadriceps",
                "joints_involved": "Knee, Hip",
                "equipment": "Bodyweight",
                "difficulty_level": "Beginner",
                "environment": "Both"
            },
            {
                "exercise_id": "TEST002",
                "name": "Test Cardio Exercise",
                "category": "Cardio",
                "exercise_type": None,
                "primary_muscle": "Quadriceps",
                "joints_involved": "Knee, Hip",
                "equipment": "Bodyweight",
                "difficulty_level": "Beginner",
                "environment": "Both"
            }
        ]

        with patch(
            "src.recommendations.workout_recommendations.search_exercises",
            return_value=test_exercises
        ):
            exercises = get_candidate_exercises_for_user(
                user_id
            )

        if not exercises:
            raise ValueError("FAIL: No candidate exercises returned")

        if exercises[0]["category"] != "Strength":
            raise ValueError("FAIL: Strength goal did not prioritize Strength exercise")

        if exercises[1]["category"] != "Cardio":
            raise ValueError("FAIL: Cardio exercise was unexpectedly removed")

        print("PASS: Strength goal prioritized Strength candidates")

    finally:
        delete_user(user_id)

def test_build_workout_returns_requested_exercise_count():
    test_profile = {
        "primary_goal": "General Fitness",
        "session_duration_minutes": 60
    }

    test_candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Exercise 1",
            "movement_pattern": "Push"
        },
        {
            "exercise_id": "TEST002",
            "name": "Exercise 2",
            "movement_pattern": "Pull"
        },
        {
            "exercise_id": "TEST003",
            "name": "Exercise 3",
            "movement_pattern": "Squat"
        },
        {
            "exercise_id": "TEST004",
            "name": "Exercise 4",
            "movement_pattern": "Hinge"
        },
        {
            "exercise_id": "TEST005",
            "name": "Exercise 5",
            "movement_pattern": "Core"
        }
    ]

    with patch(
        "src.recommendations.workout_recommendations.get_user_profile",
        return_value=test_profile
    ), patch(
        "src.recommendations.workout_recommendations.get_candidate_exercises_for_user",
        return_value=test_candidates
    ):
        workout = build_workout_for_user(
            1,
            exercise_count=3
        )

    if len(workout) != 3:
        raise ValueError("FAIL: Workout did not contain requested exercise count")

    expected_ids = [
        "TEST001",
        "TEST002",
        "TEST003"
    ]

    workout_ids = [exercise["exercise_id"] for exercise in workout]

    if workout_ids != expected_ids:
        raise ValueError("FAIL: Workout did not select highest-ranked candidates")

    print("PASS: Workout returned requested exercise count")

def test_build_workout_rejects_invalid_exercise_count():
    invalid_values = [
        0,
        -1,
        2.5,
        True,
        "3"
    ]

    for value in invalid_values:
        try:
            build_workout_for_user(
                1,
                exercise_count=value
            )

        except ValueError:
            continue

        raise ValueError(f"FAIL: Invalid exercise count was accepted: {value}")

    print("PASS: Workout rejected invalid exercise counts")

def test_build_workout_handles_fewer_candidates_than_requested():
    test_candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Exercise 1",
            "movement_pattern": "Push"
        },
        {
            "exercise_id": "TEST002",
            "name": "Exercise 2",
            "movement_pattern": "Pull"
        },
        {
            "exercise_id": "TEST003",
            "name": "Exercise 3",
            "movement_pattern": "Squat"
        }
    ]

    test_profile = {
        "primary_goal": "General Fitness",
        "session_duration_minutes": 60
    }

    with patch(
            "src.recommendations.workout_recommendations.get_user_profile",
            return_value=test_profile
    ), patch(
        "src.recommendations.workout_recommendations.get_candidate_exercises_for_user",
        return_value=test_candidates
    ):
        workout = build_workout_for_user(
            1,
            exercise_count=5
        )

    if len(workout) != 3:
        raise ValueError("FAIL: Workout did not return all available candidates")

    workout_ids = [
        exercise["exercise_id"]
        for exercise in workout
    ]

    expected_ids = [
        exercise["exercise_id"]
        for exercise in test_candidates
    ]

    if workout_ids != expected_ids:
        raise ValueError("FAIL: Workout candidates changed unexpectedly")

    print("PASS: Workout handled fewer candidates than requested")


def test_movement_balance_limits_same_pattern():
    candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Push Exercise 1",
            "movement_pattern": "Push"
        },
        {
            "exercise_id": "TEST002",
            "name": "Push Exercise 2",
            "movement_pattern": "Push"
        },
        {
            "exercise_id": "TEST003",
            "name": "Push Exercise 3",
            "movement_pattern": "Push"
        },
        {
            "exercise_id": "TEST004",
            "name": "Pull Exercise",
            "movement_pattern": "Pull"
        },
        {
            "exercise_id": "TEST005",
            "name": "Squat Exercise",
            "movement_pattern": "Squat"
        }
    ]

    selected = select_exercises_with_movement_balance(
        candidates,
        exercise_count=4,
        max_per_pattern=2
    )

    if len(selected) != 4:
        raise ValueError("FAIL: Movement balance did not return requested exercise count")

    push_count = 0

    for exercise in selected:
        if exercise["movement_pattern"] == "Push":
            push_count += 1

    if push_count > 2:
        raise ValueError("FAIL: Too many exercises from same movement pattern")

    if selected[2]["exercise_id"] == "TEST003":
        raise ValueError("FAIL: Third Push exercise was not skipped")

    print("PASS: Movement balance limited same movement pattern")

def test_build_workout_applies_movement_balance():
    test_candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Push Exercise 1",
            "movement_pattern": "Push"
        },
        {
            "exercise_id": "TEST002",
            "name": "Push Exercise 2",
            "movement_pattern": "Push"
        },
        {
            "exercise_id": "TEST003",
            "name": "Push Exercise 3",
            "movement_pattern": "Push"
        },
        {
            "exercise_id": "TEST004",
            "name": "Pull Exercise",
            "movement_pattern": "Pull"
        },
        {
            "exercise_id": "TEST005",
            "name": "Squat Exercise",
            "movement_pattern": "Squat"
        }
    ]

    test_profile = {
        "primary_goal": "General Fitness",
        "session_duration_minutes": 60
    }

    with patch(
            "src.recommendations.workout_recommendations.get_user_profile",
            return_value=test_profile
    ), patch(
        "src.recommendations.workout_recommendations.get_candidate_exercises_for_user",
        return_value=test_candidates
    ):
        workout = build_workout_for_user(
            1,
            exercise_count=4
        )

    workout_ids = [
        exercise["exercise_id"]
        for exercise in workout
    ]

    if "TEST003" in workout_ids:
        raise ValueError("FAIL: Workout included too many Push exercises")

    if "TEST004" not in workout_ids:
        raise ValueError("FAIL: Pull exercise was not selected")

    if "TEST005" not in workout_ids:
        raise ValueError("FAIL: Squat exercise was not selected")

    if len(workout) != 4:
        raise ValueError("FAIL: Workout did not contain requested exercise count")

    print("PASS: Workout applied movement-pattern balance")

def test_exercise_count_from_session_duration():
    cases = [
        (20, 3),
        (30, 3),
        (31, 4),
        (45, 4),
        (46, 5),
        (60, 5),
        (61, 6),
        (90, 6)
    ]

    for session_duration, expected_count in cases:
        result = determine_exercise_count_from_session_duration(
            session_duration
        )

        if result != expected_count:
            raise ValueError(f"FAIL: Session duration {session_duration} " f"returned {result} exercises instead of " f"{expected_count}")

    print("PASS: Session duration maps to exercise count correctly")


def test_build_workout_uses_session_duration():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "General Fitness",
            "training_days_per_week": 4,
            "session_duration_minutes": 45,
            "preferred_environment": "Both"
        }

        create_user_profile(
            user_id,
            profile
        )

        test_candidates = [
            {
                "exercise_id": "TEST001",
                "name": "Exercise 1",
                "movement_pattern": "Push"
            },
            {
                "exercise_id": "TEST002",
                "name": "Exercise 2",
                "movement_pattern": "Pull"
            },
            {
                "exercise_id": "TEST003",
                "name": "Exercise 3",
                "movement_pattern": "Squat"
            },
            {
                "exercise_id": "TEST004",
                "name": "Exercise 4",
                "movement_pattern": "Hinge"
            },
            {
                "exercise_id": "TEST005",
                "name": "Exercise 5",
                "movement_pattern": "Core"
            }
        ]

        with patch(
            "src.recommendations.workout_recommendations.get_candidate_exercises_for_user",
            return_value=test_candidates
        ):
            workout = build_workout_for_user(user_id)

        if len(workout) != 4:
            raise ValueError("FAIL: 45-minute session did not create 4-exercise workout")

        print("PASS: Workout used session duration automatically")

    finally:
        delete_user(user_id)

def test_sets_and_reps_for_goal():
    cases = [
        (
            "Strength",
            {
                "sets": 4,
                "reps": "4-6"
            }
        ),
        (
            "Muscle Gain",
            {
                "sets": 3,
                "reps": "8-12"
            }
        ),
        (
            "Endurance",
            {
                "sets": 3,
                "reps": "15-20"
            }
        ),
        (
            "Fat Loss",
            {
                "sets": 3,
                "reps": "10-15"
            }
        ),
        (
            "General Fitness",
            {
                "sets": 3,
                "reps": "8-12"
            }
        )
    ]

    for primary_goal, expected in cases:
        result = get_sets_and_reps_for_goal(primary_goal)

        if result != expected:
            raise ValueError(f"FAIL: {primary_goal} returned " f"{result} instead of {expected}")

    print("PASS: Goal-based sets and reps work correctly")

def test_build_workout_adds_strength_sets_and_reps():
    test_profile = {
        "primary_goal": "Strength",
        "session_duration_minutes": 60
    }

    test_candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Strength Exercise 1",
            "movement_pattern": "Squat"
        },
        {
            "exercise_id": "TEST002",
            "name": "Strength Exercise 2",
            "movement_pattern": "Push"
        },
        {
            "exercise_id": "TEST003",
            "name": "Strength Exercise 3",
            "movement_pattern": "Pull"
        }
    ]

    with patch(
        "src.recommendations.workout_recommendations.get_user_profile",
        return_value=test_profile
    ), patch(
        "src.recommendations.workout_recommendations.get_candidate_exercises_for_user",
        return_value=test_candidates
    ):
        workout = build_workout_for_user(
            1,
            exercise_count=3
        )

    for exercise in workout:
        if exercise["sets"] != 4:
            raise ValueError("FAIL: Strength workout did not use 4 sets")

        if exercise["reps"] != "4-6":
            raise ValueError("FAIL: Strength workout did not use 4-6 reps")

    print("PASS: Strength workout added correct sets and reps")

def test_rest_seconds_for_goal():
    cases = [
        ("Strength", 180),
        ("Muscle Gain", 90),
        ("Endurance", 45),
        ("Fat Loss", 60),
        ("General Fitness", 60)
    ]

    for primary_goal, expected_rest in cases:
        result = get_rest_seconds_for_goal(primary_goal)

        if result != expected_rest:
            raise ValueError(f"FAIL: {primary_goal} returned " f"{result} seconds instead of " f"{expected_rest}")

    print("PASS: Goal-based rest times work correctly")

def test_build_workout_adds_strength_rest_seconds():
    test_profile = {
        "primary_goal": "Strength",
        "session_duration_minutes": 60
    }

    test_candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Strength Exercise 1",
            "movement_pattern": "Squat"
        },
        {
            "exercise_id": "TEST002",
            "name": "Strength Exercise 2",
            "movement_pattern": "Push"
        }
    ]

    with patch(
        "src.recommendations.workout_recommendations.get_user_profile",
        return_value=test_profile
    ), patch(
        "src.recommendations.workout_recommendations.get_candidate_exercises_for_user",
        return_value=test_candidates
    ):
        workout = build_workout_for_user(
            1,
            exercise_count=2
        )

    for exercise in workout:
        if exercise["rest_seconds"] != 180:
            raise ValueError("FAIL: Strength workout did not use 180 seconds rest")

    print("PASS: Strength workout added correct rest time")

def test_workout_prescription_for_goal():
    cases = [
        (
            "Strength",
            {
                "sets": 4,
                "reps": "4-6",
                "rest_seconds": 180
            }
        ),
        (
            "Muscle Gain",
            {
                "sets": 3,
                "reps": "8-12",
                "rest_seconds": 90
            }
        ),
        (
            "Endurance",
            {
                "sets": 3,
                "reps": "15-20",
                "rest_seconds": 45
            }
        ),
        (
            "Fat Loss",
            {
                "sets": 3,
                "reps": "10-15",
                "rest_seconds": 60
            }
        ),
        (
            "General Fitness",
            {
                "sets": 3,
                "reps": "8-12",
                "rest_seconds": 60
            }
        )
    ]

    for primary_goal, expected in cases:
        result = get_workout_prescription_for_goal(primary_goal)

        if result != expected:
            raise ValueError(f"FAIL: {primary_goal} returned " f"{result} instead of {expected}")

    print("PASS: Combined workout prescription works correctly")

def test_estimate_workout_duration_minutes():
    workout = [
        {
            "sets": 3,
            "rest_seconds": 60
        },
        {
            "sets": 3,
            "rest_seconds": 60
        }
    ]

    result = estimate_workout_duration_minutes(workout)

    expected_minutes = 9.5

    if result != expected_minutes:
        raise ValueError(f"FAIL: Estimated workout duration was " f"{result} instead of {expected_minutes}")

    print("PASS: Workout duration estimation works correctly")

def test_workout_fit_session():
    if not does_workout_fit_session(
        45,
        60
    ):
        raise ValueError("FAIL: 45-minute workout should fit 60-minute session")

    if not does_workout_fit_session(
        60,
        60
    ):
        raise ValueError("FAIL: Equal workout and session duration should fit")

    if does_workout_fit_session(
        75,
        60
    ):
        raise ValueError("FAIL: 75-minute workout should not fit 60-minute session")

    print("PASS: Workout session-fit checking works correctly")

def test_build_workout_plan_for_user():
    test_profile = {
        "primary_goal": "Strength",
        "session_duration_minutes": 60
    }

    test_candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Exercise 1",
            "movement_pattern": "Squat"
        },
        {
            "exercise_id": "TEST002",
            "name": "Exercise 2",
            "movement_pattern": "Push"
        },
        {
            "exercise_id": "TEST003",
            "name": "Exercise 3",
            "movement_pattern": "Pull"
        }
    ]

    with patch(
        "src.recommendations.workout_recommendations.get_user_profile",
        return_value=test_profile
    ), patch(
        "src.recommendations.workout_recommendations.get_candidate_exercises_for_user",
        return_value=test_candidates
    ):
        workout_plan = build_workout_plan_for_user(
            1,
            exercise_count=3
        )

    if workout_plan["primary_goal"] != "Strength":
        raise ValueError("FAIL: Workout plan did not include primary goal")

    if workout_plan["session_duration_minutes"] != 60:
        raise ValueError("FAIL: Workout plan did not include session duration")

    if workout_plan["exercise_count"] != 3:
        raise ValueError("FAIL: Workout plan exercise count was incorrect")

    if len(workout_plan["exercises"]) != 3:
        raise ValueError("FAIL: Workout plan did not contain 3 exercises")

    if workout_plan["estimated_duration_minutes"] <= 0:
        raise ValueError("FAIL: Workout plan duration was not calculated")

    if not isinstance(
        workout_plan["fits_session"],
        bool
    ):
        raise ValueError("FAIL: Workout plan session-fit value is not boolean")

    for exercise in workout_plan["exercises"]:
        if exercise["sets"] != 4:
            raise ValueError("FAIL: Strength workout plan did not use 4 sets")

        if exercise["reps"] != "4-6":
            raise ValueError("FAIL: Strength workout plan did not use 4-6 reps")

        if exercise["rest_seconds"] != 180:
            raise ValueError("FAIL: Strength workout plan did not use 180 seconds rest")

    print("PASS: Complete workout plan generated correctly")

def test_workout_balance_limits_same_primary_muscle():
    candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Chest Exercise 1",
            "movement_pattern": "Push 1",
            "primary_muscle": "Chest"
        },
        {
            "exercise_id": "TEST002",
            "name": "Chest Exercise 2",
            "movement_pattern": "Push 2",
            "primary_muscle": "Chest"
        },
        {
            "exercise_id": "TEST003",
            "name": "Chest Exercise 3",
            "movement_pattern": "Push 3",
            "primary_muscle": "Chest"
        },
        {
            "exercise_id": "TEST004",
            "name": "Back Exercise",
            "movement_pattern": "Pull",
            "primary_muscle": "Back"
        },
        {
            "exercise_id": "TEST005",
            "name": "Leg Exercise",
            "movement_pattern": "Squat",
            "primary_muscle": "Quadriceps"
        }
    ]

    selected = select_exercises_with_workout_balance(
        candidates,
        exercise_count=4,
        max_per_pattern=2,
        max_per_primary_muscle=2
    )

    chest_count = 0

    for exercise in selected:
        if exercise["primary_muscle"] == "Chest":
            chest_count += 1

    if chest_count > 2:
        raise ValueError("FAIL: Too many exercises for same primary muscle")

    selected_ids = [
        exercise["exercise_id"]
        for exercise in selected
    ]

    if "TEST003" in selected_ids:
        raise ValueError("FAIL: Third Chest exercise was not skipped")

    if len(selected) != 4:
        raise ValueError("FAIL: Workout balance did not return requested count")

    print("PASS: Workout balance limited same primary muscle")

def test_compound_priority_score():
    compound_exercise = {
        "category": "Strength",
        "exercise_type": "Compound"
    }

    isolation_exercise = {
        "category": "Strength",
        "exercise_type": "Isolation"
    }

    cardio_exercise = {
        "category": "Cardio",
        "exercise_type": None
    }

    if get_compound_priority_score(
        compound_exercise,
        "Strength"
    ) != 1:
        raise ValueError("FAIL: Strength goal did not prioritize Compound exercise")

    if get_compound_priority_score(
        compound_exercise,
        "Muscle Gain"
    ) != 1:
        raise ValueError("FAIL: Muscle Gain did not prioritize Compound exercise")

    if get_compound_priority_score(
        isolation_exercise,
        "Strength"
    ) != 0:
        raise ValueError("FAIL: Isolation exercise received Compound priority")

    if get_compound_priority_score(
        cardio_exercise,
        "Strength"
    ) != 0:
        raise ValueError("FAIL: Cardio exercise received Compound priority")

    if get_compound_priority_score(
        compound_exercise,
        "General Fitness"
    ) != 0:
        raise ValueError("FAIL: General Fitness incorrectly used Compound priority")

    print("PASS: Compound exercise priority works correctly")


def test_workout_order_prioritizes_compound_exercises():
    exercises = [
        {
            "exercise_id": "TEST001",
            "name": "Isolation Exercise",
            "category": "Strength",
            "exercise_type": "Isolation"
        },
        {
            "exercise_id": "TEST002",
            "name": "Cardio Exercise",
            "category": "Cardio",
            "exercise_type": None
        },
        {
            "exercise_id": "TEST003",
            "name": "Compound Exercise",
            "category": "Strength",
            "exercise_type": "Compound"
        }
    ]

    ordered = order_workout_exercises(
        exercises,
        "Strength"
    )

    if ordered[0]["exercise_id"] != "TEST003":
        raise ValueError("FAIL: Compound exercise was not ordered first")

    print("PASS: Workout ordering prioritized Compound exercise")

def test_build_workout_applies_primary_muscle_balance():
    test_profile = {
        "primary_goal": "General Fitness",
        "session_duration_minutes": 60
    }

    test_candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Chest Exercise 1",
            "movement_pattern": "Push 1",
            "primary_muscle": "Chest"
        },
        {
            "exercise_id": "TEST002",
            "name": "Chest Exercise 2",
            "movement_pattern": "Push 2",
            "primary_muscle": "Chest"
        },
        {
            "exercise_id": "TEST003",
            "name": "Chest Exercise 3",
            "movement_pattern": "Push 3",
            "primary_muscle": "Chest"
        },
        {
            "exercise_id": "TEST004",
            "name": "Back Exercise",
            "movement_pattern": "Pull",
            "primary_muscle": "Back"
        },
        {
            "exercise_id": "TEST005",
            "name": "Leg Exercise",
            "movement_pattern": "Squat",
            "primary_muscle": "Quadriceps"
        }
    ]

    with patch(
        "src.recommendations.workout_recommendations.get_user_profile",
        return_value=test_profile
    ), patch(
        "src.recommendations.workout_recommendations.get_candidate_exercises_for_user",
        return_value=test_candidates
    ):
        workout = build_workout_for_user(
            1,
            exercise_count=4
        )

    workout_ids = [
        exercise["exercise_id"]
        for exercise in workout
    ]

    if "TEST003" in workout_ids:
        raise ValueError("FAIL: Workout included too many Chest exercises")

    if "TEST004" not in workout_ids:
        raise ValueError("FAIL: Back exercise was not selected")

    if "TEST005" not in workout_ids:
        raise ValueError("FAIL: Leg exercise was not selected")

    if len(workout) != 4:
        raise ValueError("FAIL: Balanced workout did not contain requested count")

    print("PASS: Workout builder applied primary-muscle balance")

def test_warm_up_and_cool_down_minutes():
    cases = [
        (30, 5, 3),
        (45, 8, 5),
        (60, 8, 5),
        (75, 10, 8)
    ]

    for (
        session_duration,
        expected_warm_up,
        expected_cool_down
    ) in cases:
        warm_up = get_warm_up_minutes(
            session_duration
        )

        cool_down = get_cool_down_minutes(
            session_duration
        )

        if warm_up != expected_warm_up:
            raise ValueError(f"FAIL: {session_duration}-minute session " f"returned incorrect warm-up duration")

        if cool_down != expected_cool_down:
            raise ValueError(f"FAIL: {session_duration}-minute session " f"returned incorrect cool-down duration")

    print("PASS: Warm-up and cool-down durations work correctly")


def test_add_exercise_order_numbers():
    exercises = [
        {
            "exercise_id": "TEST001",
            "name": "Exercise 1"
        },
        {
            "exercise_id": "TEST002",
            "name": "Exercise 2"
        },
        {
            "exercise_id": "TEST003",
            "name": "Exercise 3"
        }
    ]

    ordered = add_exercise_order_numbers(
        exercises
    )

    if ordered[0]["order"] != 1:
        raise ValueError("FAIL: First exercise did not receive order 1")

    if ordered[1]["order"] != 2:
        raise ValueError("FAIL: Second exercise did not receive order 2")

    if ordered[2]["order"] != 3:
        raise ValueError("FAIL: Third exercise did not receive order 3")

    if "order" in exercises[0]:
        raise ValueError("FAIL: Original exercise data was modified")

    print("PASS: Exercise order numbers added correctly")


def test_workout_plan_status():
    if get_workout_plan_status(
        True
    ) != "Fits Session":
        raise ValueError("FAIL: Fitting workout returned incorrect status")

    if get_workout_plan_status(
        False
    ) != "Exceeds Session":
        raise ValueError("FAIL: Long workout returned incorrect status")

    print("PASS: Workout plan status works correctly")


def test_workout_plan_includes_structure_metadata():
    test_profile = {
        "primary_goal": "Strength",
        "session_duration_minutes": 60
    }

    test_candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Exercise 1",
            "movement_pattern": "Squat",
            "primary_muscle": "Quadriceps",
            "category": "Strength",
            "exercise_type": "Compound"
        },
        {
            "exercise_id": "TEST002",
            "name": "Exercise 2",
            "movement_pattern": "Push",
            "primary_muscle": "Chest",
            "category": "Strength",
            "exercise_type": "Compound"
        },
        {
            "exercise_id": "TEST003",
            "name": "Exercise 3",
            "movement_pattern": "Pull",
            "primary_muscle": "Back",
            "category": "Strength",
            "exercise_type": "Compound"
        }
    ]

    with patch(
        "src.recommendations.workout_recommendations.get_user_profile",
        return_value=test_profile
    ), patch(
        "src.recommendations.workout_recommendations.get_candidate_exercises_for_user",
        return_value=test_candidates
    ):
        workout_plan = build_workout_plan_for_user(
            1,
            exercise_count=3
        )

    if workout_plan["warm_up_minutes"] != 8:
        raise ValueError("FAIL: Workout plan warm-up duration was incorrect")

    if workout_plan["cool_down_minutes"] != 5:
        raise ValueError("FAIL: Workout plan cool-down duration was incorrect")

    expected_total = (
        workout_plan["estimated_duration_minutes"]
        + 8
        + 5
    )

    if (
        workout_plan["estimated_total_duration_minutes"]
        != expected_total
    ):
        raise ValueError("FAIL: Total workout duration was incorrect")

    for index, exercise in enumerate(
        workout_plan["exercises"],
        start=1
    ):
        if exercise["order"] != index:
            raise ValueError("FAIL: Exercise order number was incorrect")

    if workout_plan["status"] != "Fits Session":
        raise ValueError("FAIL: 60-minute workout plan should fit session")

    print("PASS: Workout plan includes structure metadata")



def test_calculate_total_workout_duration():
    workout = [
        {
            "sets": 3,
            "rest_seconds": 60
        },
        {
            "sets": 3,
            "rest_seconds": 60
        }
    ]

    result = calculate_total_workout_duration(
        workout,
        warm_up_minutes=5,
        cool_down_minutes=5
    )

    expected = 19.5

    if result != expected:
        raise ValueError(f"FAIL: Total workout duration was " f"{result} instead of {expected}")

    print("PASS: Total workout duration calculated correctly")


def test_trim_workout_to_session_duration():
    workout = [
        {
            "exercise_id": "TEST001",
            "sets": 4,
            "rest_seconds": 180
        },
        {
            "exercise_id": "TEST002",
            "sets": 4,
            "rest_seconds": 180
        },
        {
            "exercise_id": "TEST003",
            "sets": 4,
            "rest_seconds": 180
        }
    ]

    fitted = trim_workout_to_session_duration(
        workout,
        session_duration_minutes=30,
        warm_up_minutes=5,
        cool_down_minutes=3
    )

    if len(fitted) != 1:
        raise ValueError("FAIL: Workout was not shortened enough to fit")

    if fitted[0]["exercise_id"] != "TEST001":
        raise ValueError("FAIL: Highest-priority exercise was not preserved")

    total_duration = calculate_total_workout_duration(
        fitted,
        5,
        3
    )

    if total_duration > 30:
        raise ValueError("FAIL: Trimmed workout still exceeds session")

    print("PASS: Workout shortened to fit session")

def test_trim_workout_keeps_at_least_one_exercise():
    workout = [
        {
            "exercise_id": "TEST001",
            "sets": 10,
            "rest_seconds": 300
        },
        {
            "exercise_id": "TEST002",
            "sets": 10,
            "rest_seconds": 300
        }
    ]

    fitted = trim_workout_to_session_duration(
        workout,
        session_duration_minutes=10,
        warm_up_minutes=5,
        cool_down_minutes=3
    )

    if len(fitted) != 1:
        raise ValueError("FAIL: Workout should retain at least one exercise")

    print("PASS: Workout trimming retained at least one exercise")

def test_workout_plan_automatically_shortens_to_fit():
    test_profile = {
        "primary_goal": "Strength",
        "session_duration_minutes": 30
    }

    test_candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Exercise 1",
            "movement_pattern": "Squat",
            "primary_muscle": "Quadriceps",
            "category": "Strength",
            "exercise_type": "Compound"
        },
        {
            "exercise_id": "TEST002",
            "name": "Exercise 2",
            "movement_pattern": "Push",
            "primary_muscle": "Chest",
            "category": "Strength",
            "exercise_type": "Compound"
        },
        {
            "exercise_id": "TEST003",
            "name": "Exercise 3",
            "movement_pattern": "Pull",
            "primary_muscle": "Back",
            "category": "Strength",
            "exercise_type": "Compound"
        }
    ]

    with patch(
        "src.recommendations.workout_recommendations.get_user_profile",
        return_value=test_profile
    ), patch(
        "src.recommendations.workout_recommendations.get_candidate_exercises_for_user",
        return_value=test_candidates
    ):
        workout_plan = build_workout_plan_for_user(
            1,
            exercise_count=3
        )

    if not workout_plan["was_shortened"]:
        raise ValueError("FAIL: Oversized workout was not shortened")

    if workout_plan["requested_exercise_count"] != 3:
        raise ValueError("FAIL: Requested exercise count was incorrect")

    if workout_plan["exercise_count"] >= 3:
        raise ValueError("FAIL: Exercise count was not reduced")

    if not workout_plan["fits_session"]:
        raise ValueError("FAIL: Automatically shortened workout still does not fit")

    if (
        workout_plan["estimated_total_duration_minutes"]
        > 30
    ):
        raise ValueError("FAIL: Workout duration still exceeds session")

    if (
        workout_plan["exercises"][0]["exercise_id"]
        != "TEST001"
    ):
        raise ValueError("FAIL: Highest-priority exercise was not preserved")

    print("PASS: Workout plan automatically shortened to fit session")

def test_exercise_prescription_by_category():
    strength_exercise = {
        "category": "Strength"
    }

    cardio_exercise = {
        "category": "Cardio"
    }

    mobility_exercise = {
        "category": "Mobility"
    }

    strength = get_exercise_prescription(
        strength_exercise,
        "Strength"
    )

    cardio = get_exercise_prescription(
        cardio_exercise,
        "Endurance"
    )

    mobility = get_exercise_prescription(
        mobility_exercise,
        "General Fitness"
    )

    if strength["prescription_type"] != "sets_reps":
        raise ValueError("FAIL: Strength exercise did not use sets and reps")

    if strength["sets"] != 4:
        raise ValueError("FAIL: Strength exercise did not use 4 sets")

    if strength["reps"] != "4-6":
        raise ValueError("FAIL: Strength exercise did not use 4-6 reps")

    if strength["rest_seconds"] != 180:
        raise ValueError("FAIL: Strength exercise did not use 180 seconds rest")

    if cardio["prescription_type"] != "duration":
        raise ValueError("FAIL: Cardio exercise did not use duration")

    if cardio["duration_minutes"] != 10:
        raise ValueError("FAIL: Cardio exercise did not use 10 minutes")

    if cardio["sets"] is not None:
        raise ValueError("FAIL: Cardio exercise incorrectly received sets")

    if mobility["prescription_type"] != "duration":
        raise ValueError("FAIL: Mobility exercise did not use duration")

    if mobility["duration_minutes"] != 5:
        raise ValueError("FAIL: Mobility exercise did not use 5 minutes")

    print("PASS: Exercise prescriptions match exercise category")

def test_estimate_mixed_workout_duration():
    workout = [
        {
            "sets": 3,
            "rest_seconds": 60,
            "duration_minutes": None
        },
        {
            "sets": None,
            "rest_seconds": 0,
            "duration_minutes": 10
        }
    ]

    result = estimate_workout_duration_minutes(workout)

    expected = 15.25

    if result != expected:
        raise ValueError(f"FAIL: Mixed workout duration was " f"{result} instead of {expected}")

    print("PASS: Mixed workout duration calculated correctly")

def test_build_workout_uses_mixed_prescriptions():
    test_profile = {
        "primary_goal": "General Fitness",
        "session_duration_minutes": 60
    }

    test_candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Strength Exercise",
            "category": "Strength",
            "exercise_type": "Compound",
            "movement_pattern": "Squat",
            "primary_muscle": "Quadriceps"
        },
        {
            "exercise_id": "TEST002",
            "name": "Cardio Exercise",
            "category": "Cardio",
            "exercise_type": None,
            "movement_pattern": "Locomotion",
            "primary_muscle": "Quadriceps"
        },
        {
            "exercise_id": "TEST003",
            "name": "Mobility Exercise",
            "category": "Mobility",
            "exercise_type": None,
            "movement_pattern": "Mobility",
            "primary_muscle": "Hip Flexors"
        }
    ]

    with patch(
        "src.recommendations.workout_recommendations.get_user_profile",
        return_value=test_profile
    ), patch(
        "src.recommendations.workout_recommendations.get_candidate_exercises_for_user",
        return_value=test_candidates
    ):
        workout = build_workout_for_user(
            1,
            exercise_count=3
        )

    strength = next(
        exercise
        for exercise in workout
        if exercise["category"] == "Strength"
    )

    cardio = next(
        exercise
        for exercise in workout
        if exercise["category"] == "Cardio"
    )

    mobility = next(
        exercise
        for exercise in workout
        if exercise["category"] == "Mobility"
    )

    if strength["prescription_type"] != "sets_reps":
        raise ValueError("FAIL: Strength workout exercise used wrong prescription")

    if cardio["prescription_type"] != "duration":
        raise ValueError("FAIL: Cardio workout exercise used wrong prescription")

    if cardio["duration_minutes"] != 10:
        raise ValueError("FAIL: Cardio duration was incorrect")

    if mobility["duration_minutes"] != 5:
        raise ValueError("FAIL: Mobility duration was incorrect")

    print("PASS: Workout builder used mixed exercise prescriptions")

def test_goal_priority_categories():
    cases = [
        (
            "Strength",
            ["Strength"]
        ),
        (
            "Muscle Gain",
            ["Strength"]
        ),
        (
            "Endurance",
            ["Cardio"]
        ),
        (
            "Fat Loss",
            [
                "Cardio",
                "Strength"
            ]
        ),
        (
            "General Fitness",
            [
                "Strength",
                "Cardio"
            ]
        )
    ]

    for primary_goal, expected in cases:
        result = get_goal_priority_categories(
            primary_goal
        )

        if result != expected:
            raise ValueError(f"FAIL: {primary_goal} returned " f"{result} instead of {expected}")

    print("PASS: Goal priority categories work correctly")


def test_endurance_prioritizes_cardio_candidate():
    candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Strength Exercise",
            "category": "Strength"
        },
        {
            "exercise_id": "TEST002",
            "name": "Mobility Exercise",
            "category": "Mobility"
        },
        {
            "exercise_id": "TEST003",
            "name": "Cardio Exercise",
            "category": "Cardio"
        }
    ]

    prioritized = prioritize_candidates_for_goal_composition(
        candidates,
        "Endurance"
    )

    if prioritized[0]["exercise_id"] != "TEST003":
        raise ValueError("FAIL: Endurance did not prioritize Cardio exercise")

    print("PASS: Endurance prioritized Cardio candidate")


def test_general_fitness_prioritizes_mixed_categories():
    candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Mobility Exercise",
            "category": "Mobility"
        },
        {
            "exercise_id": "TEST002",
            "name": "Cardio Exercise",
            "category": "Cardio"
        },
        {
            "exercise_id": "TEST003",
            "name": "Strength Exercise",
            "category": "Strength"
        },
        {
            "exercise_id": "TEST004",
            "name": "Stretching Exercise",
            "category": "Stretching"
        }
    ]

    prioritized = prioritize_candidates_for_goal_composition(
        candidates,
        "General Fitness"
    )

    first_two_categories = [
        prioritized[0]["category"],
        prioritized[1]["category"]
    ]

    if first_two_categories != [
        "Strength",
        "Cardio"
    ]:
        raise ValueError("FAIL: General Fitness did not prioritize " "Strength and Cardio")

    print("PASS: General Fitness prioritized mixed categories")


def test_goal_composition_handles_missing_category():
    candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Strength Exercise",
            "category": "Strength"
        },
        {
            "exercise_id": "TEST002",
            "name": "Mobility Exercise",
            "category": "Mobility"
        }
    ]

    prioritized = prioritize_candidates_for_goal_composition(
        candidates,
        "Endurance"
    )

    if len(prioritized) != 2:
        raise ValueError("FAIL: Missing priority category removed candidates")

    if prioritized[0]["exercise_id"] != "TEST001":
        raise ValueError("FAIL: Existing candidate order changed unexpectedly")

    print("PASS: Goal composition handles missing category")

def test_general_fitness_builds_mixed_workout():
    test_profile = {
        "primary_goal": "General Fitness",
        "session_duration_minutes": 60
    }

    test_candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Mobility Exercise",
            "category": "Mobility",
            "exercise_type": None,
            "movement_pattern": "Mobility",
            "primary_muscle": "Hip Flexors"
        },
        {
            "exercise_id": "TEST002",
            "name": "Cardio Exercise",
            "category": "Cardio",
            "exercise_type": None,
            "movement_pattern": "Locomotion",
            "primary_muscle": "Quadriceps"
        },
        {
            "exercise_id": "TEST003",
            "name": "Strength Exercise",
            "category": "Strength",
            "exercise_type": "Compound",
            "movement_pattern": "Push",
            "primary_muscle": "Chest"
        },
        {
            "exercise_id": "TEST004",
            "name": "Stretching Exercise",
            "category": "Stretching",
            "exercise_type": None,
            "movement_pattern": "Stretch",
            "primary_muscle": "Hamstrings"
        }
    ]

    with patch(
        "src.recommendations.workout_recommendations.get_user_profile",
        return_value=test_profile
    ), patch(
        "src.recommendations.workout_recommendations.get_candidate_exercises_for_user",
        return_value=test_candidates
    ):
        workout = build_workout_for_user(
            1,
            exercise_count=3
        )

    categories = [
        exercise["category"]
        for exercise in workout
    ]

    if "Strength" not in categories:
        raise ValueError("FAIL: General Fitness workout did not include Strength")

    if "Cardio" not in categories:
        raise ValueError("FAIL: General Fitness workout did not include Cardio")

    print("PASS: General Fitness built mixed workout")

def test_target_difficulty_score():
    cases = [
        ("Beginner", 2),
        ("Intermediate", 3),
        ("Advanced", 4)
    ]

    for fitness_level, expected in cases:
        result = get_target_difficulty_score(
            fitness_level
        )

        if result != expected:
            raise ValueError(f"FAIL: {fitness_level} returned " f"difficulty target {result} instead of " f"{expected}")

    print("PASS: Fitness levels map to difficulty targets correctly")


def test_difficulty_fit_score():
    ideal_exercise = {
        "difficulty_score": 3
    }

    easier_exercise = {
        "difficulty_score": 1
    }

    ideal_score = get_difficulty_fit_score(
        ideal_exercise,
        "Intermediate"
    )

    easier_score = get_difficulty_fit_score(
        easier_exercise,
        "Intermediate"
    )

    if ideal_score <= easier_score:
        raise ValueError("FAIL: Better difficulty match did not score higher")

    print("PASS: Difficulty-fit scoring works correctly")


def test_exercise_count_adjusts_for_fitness_level():
    if adjust_exercise_count_for_fitness_level(
        4,
        "Beginner"
    ) != 3:
        raise ValueError("FAIL: Beginner exercise count was not reduced")

    if adjust_exercise_count_for_fitness_level(
        4,
        "Intermediate"
    ) != 4:
        raise ValueError("FAIL: Intermediate exercise count changed unexpectedly")

    if adjust_exercise_count_for_fitness_level(
        4,
        "Advanced"
    ) != 5:
        raise ValueError("FAIL: Advanced exercise count was not increased")

    if adjust_exercise_count_for_fitness_level(
        1,
        "Beginner"
    ) != 1:
        raise ValueError("FAIL: Beginner adjustment dropped below one exercise")

    print("PASS: Exercise count adjusts for fitness level")

def test_intermediate_user_prioritizes_matching_difficulty():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "Strength",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Both"
        }

        create_user_profile(
            user_id,
            profile
        )

        test_exercises = [
            {
                "exercise_id": "TEST001",
                "name": "Easy Strength Exercise",
                "category": "Strength",
                "exercise_type": "Compound",
                "primary_muscle": "Quadriceps",
                "joints_involved": "Knee, Hip",
                "equipment": "Bodyweight",
                "difficulty_level": "Beginner",
                "difficulty_score": 1,
                "movement_pattern": "Squat",
                "environment": "Both"
            },
            {
                "exercise_id": "TEST002",
                "name": "Matching Strength Exercise",
                "category": "Strength",
                "exercise_type": "Compound",
                "primary_muscle": "Chest",
                "joints_involved": "Shoulder, Elbow",
                "equipment": "Bodyweight",
                "difficulty_level": "Intermediate",
                "difficulty_score": 3,
                "movement_pattern": "Push",
                "environment": "Both"
            }
        ]

        with patch(
            "src.recommendations.workout_recommendations.search_exercises",
            return_value=test_exercises
        ):
            candidates = get_candidate_exercises_for_user(
                user_id
            )

        if candidates[0]["exercise_id"] != "TEST002":
            raise ValueError("FAIL: Intermediate user did not prioritize matching difficulty")

        print("PASS: Candidate ranking considers difficulty fit")

    finally:
        delete_user(user_id)

def test_beginner_workout_uses_reduced_automatic_volume():
    test_profile = {
        "primary_goal": "General Fitness",
        "fitness_level": "Beginner",
        "session_duration_minutes": 45
    }

    test_candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Exercise 1",
            "category": "Strength",
            "movement_pattern": "Push",
            "primary_muscle": "Chest"
        },
        {
            "exercise_id": "TEST002",
            "name": "Exercise 2",
            "category": "Strength",
            "movement_pattern": "Pull",
            "primary_muscle": "Back"
        },
        {
            "exercise_id": "TEST003",
            "name": "Exercise 3",
            "category": "Strength",
            "movement_pattern": "Squat",
            "primary_muscle": "Quadriceps"
        },
        {
            "exercise_id": "TEST004",
            "name": "Exercise 4",
            "category": "Strength",
            "movement_pattern": "Hinge",
            "primary_muscle": "Hamstrings"
        },
        {
            "exercise_id": "TEST005",
            "name": "Exercise 5",
            "category": "Strength",
            "movement_pattern": "Core",
            "primary_muscle": "Abdominals"
        }
    ]

    with patch(
        "src.recommendations.workout_recommendations.get_user_profile",
        return_value=test_profile
    ), patch(
        "src.recommendations.workout_recommendations.get_candidate_exercises_for_user",
        return_value=test_candidates
    ):
        workout = build_workout_for_user(
            1
        )

    if len(workout) != 3:
        raise ValueError("FAIL: Beginner 45-minute workout " "did not use reduced volume")

    print("PASS: Beginner workout used reduced automatic volume")

def test_rir_targets_for_fitness_level():
    cases = [
        ("Beginner", 3),
        ("Intermediate", 2),
        ("Advanced", 1)
    ]

    for fitness_level, expected in cases:
        result = get_rir_target_for_fitness_level(
            fitness_level
        )

        if result != expected:
            raise ValueError(f"FAIL: {fitness_level} returned " f"{result} RIR instead of {expected}")

    print("PASS: Fitness levels map to RIR targets correctly")


def test_rpe_target_from_rir():
    cases = [
        (3, 7),
        (2, 8),
        (1, 9)
    ]

    for rir_target, expected_rpe in cases:
        result = get_rpe_target_from_rir(
            rir_target
        )

        if result != expected_rpe:
            raise ValueError(f"FAIL: {rir_target} RIR returned " f"RPE {result} instead of {expected_rpe}")

    print("PASS: RIR converts to RPE target correctly")

def test_strength_isolation_uses_higher_rep_range():
    compound_exercise = {
        "category": "Strength",
        "exercise_type": "Compound"
    }

    isolation_exercise = {
        "category": "Strength",
        "exercise_type": "Isolation"
    }

    compound = get_sets_and_reps_for_exercise(
        compound_exercise,
        "Strength"
    )

    isolation = get_sets_and_reps_for_exercise(
        isolation_exercise,
        "Strength"
    )

    if compound["sets"] != 4:
        raise ValueError("FAIL: Compound Strength exercise did not use 4 sets")

    if compound["reps"] != "4-6":
        raise ValueError("FAIL: Compound Strength exercise did not use 4-6 reps")

    if isolation["sets"] != 3:
        raise ValueError("FAIL: Isolation Strength exercise did not use 3 sets")

    if isolation["reps"] != "8-12":
        raise ValueError("FAIL: Isolation Strength exercise did not use 8-12 reps")

    print("PASS: Strength prescriptions consider exercise type")


def test_strength_prescription_includes_intensity_targets():
    exercise = {
        "category": "Strength",
        "exercise_type": "Compound"
    }

    beginner = get_exercise_prescription(
        exercise,
        "Strength",
        "Beginner"
    )

    intermediate = get_exercise_prescription(
        exercise,
        "Strength",
        "Intermediate"
    )

    advanced = get_exercise_prescription(
        exercise,
        "Strength",
        "Advanced"
    )

    if beginner["rir_target"] != 3:
        raise ValueError("FAIL: Beginner did not receive 3 RIR target")

    if beginner["rpe_target"] != 7:
        raise ValueError("FAIL: Beginner did not receive RPE 7 target")

    if intermediate["rir_target"] != 2:
        raise ValueError("FAIL: Intermediate did not receive 2 RIR target")

    if advanced["rir_target"] != 1:
        raise ValueError("FAIL: Advanced did not receive 1 RIR target")

    print("PASS: Strength prescriptions include intensity targets")

def test_beginner_workout_uses_beginner_intensity():
    test_profile = {
        "primary_goal": "Strength",
        "fitness_level": "Beginner",
        "session_duration_minutes": 45
    }

    test_candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Compound Exercise",
            "category": "Strength",
            "exercise_type": "Compound",
            "movement_pattern": "Squat",
            "primary_muscle": "Quadriceps"
        },
        {
            "exercise_id": "TEST002",
            "name": "Isolation Exercise",
            "category": "Strength",
            "exercise_type": "Isolation",
            "movement_pattern": "Knee Extension",
            "primary_muscle": "Quadriceps"
        }
    ]

    with patch(
        "src.recommendations.workout_recommendations.get_user_profile",
        return_value=test_profile
    ), patch(
        "src.recommendations.workout_recommendations.get_candidate_exercises_for_user",
        return_value=test_candidates
    ):
        workout = build_workout_for_user(
            1,
            exercise_count=2
        )

    for exercise in workout:
        if exercise["rir_target"] != 3:
            raise ValueError("FAIL: Beginner workout did not use 3 RIR")

        if exercise["rpe_target"] != 7:
            raise ValueError("FAIL: Beginner workout did not use RPE 7")

    print("PASS: Beginner workout used beginner intensity targets")

def test_weekly_training_day_numbers():
    cases = [
        (
            1,
            [1]
        ),
        (
            2,
            [1, 4]
        ),
        (
            3,
            [1, 3, 5]
        ),
        (
            4,
            [1, 2, 4, 6]
        ),
        (
            5,
            [1, 2, 3, 5, 6]
        ),
        (
            6,
            [1, 2, 3, 4, 5, 6]
        ),
        (
            7,
            [1, 2, 3, 4, 5, 6, 7]
        )
    ]

    for training_days, expected in cases:
        result = get_weekly_training_day_numbers(
            training_days
        )

        if result != expected:
            raise ValueError(f"FAIL: {training_days} training days returned {result} instead of {expected}")

    print("PASS: Weekly training days distributed correctly")


def test_weekly_focus_categories():
    result = get_weekly_focus_categories(
        "General Fitness",
        5
    )

    expected = [
        "Strength",
        "Cardio",
        "Mobility",
        "Strength",
        "Cardio"
    ]

    if result != expected:
        raise ValueError(f"FAIL: General Fitness weekly focuses were {result} instead of {expected}")

    strength_result = get_weekly_focus_categories(
        "Strength",
        3
    )

    if strength_result != [
        "Strength",
        "Strength",
        "Strength"
    ]:
        raise ValueError("FAIL: Strength weekly focuses were incorrect")

    print("PASS: Weekly focus categories work correctly")


def test_day_focus_prioritizes_matching_category():
    candidates = [
        {
            "exercise_id": "TEST001",
            "category": "Strength"
        },
        {
            "exercise_id": "TEST002",
            "category": "Mobility"
        },
        {
            "exercise_id": "TEST003",
            "category": "Cardio"
        }
    ]

    prioritized = prioritize_candidates_for_day_focus(
        candidates,
        "Cardio"
    )

    if prioritized[0]["exercise_id"] != "TEST003":
        raise ValueError("FAIL: Cardio day did not prioritize Cardio exercise")

    if len(prioritized) != 3:
        raise ValueError("FAIL: Day focus removed valid candidates")

    print("PASS: Day focus prioritizes matching category")


def test_invalid_weekly_training_days_rejected():
    invalid_values = [
        0,
        8,
        -1,
        True,
        3.5
    ]

    for value in invalid_values:
        try:
            get_weekly_training_day_numbers(
                value
            )

        except ValueError:
            continue

        raise ValueError(f"FAIL: Invalid training days accepted: {value}")

    print("PASS: Invalid weekly training days rejected")


def test_build_weekly_workout_plan():
    test_profile = {
        "primary_goal": "General Fitness",
        "fitness_level": "Intermediate",
        "training_days_per_week": 3,
        "session_duration_minutes": 45
    }

    fake_workout = {
        "exercise_count": 3,
        "fits_session": True
    }

    with patch(
        "src.recommendations.workout_recommendations.get_user_profile",
        return_value=test_profile
    ), patch(
        "src.recommendations.workout_recommendations.build_workout_plan_for_user",
        return_value=fake_workout
    ) as mock_builder:
        weekly_plan = build_weekly_workout_plan_for_user(
            1
        )

    days = weekly_plan[
        "weekly_plan"
    ]

    if len(days) != 7:
        raise ValueError("FAIL: Weekly plan did not contain 7 days")

    training_days = [
        day
        for day in days
        if day["day_type"] == "Training"
    ]

    rest_days = [
        day
        for day in days
        if day["day_type"] == "Rest"
    ]

    if len(training_days) != 3:
        raise ValueError("FAIL: Weekly plan did not contain 3 training days")

    if len(rest_days) != 4:
        raise ValueError("FAIL: Weekly plan did not contain 4 rest days")

    training_day_numbers = [
        day["day_number"]
        for day in training_days
    ]

    if training_day_numbers != [
        1,
        3,
        5
    ]:
        raise ValueError("FAIL: Training days were distributed incorrectly")

    focuses = [
        day["focus_category"]
        for day in training_days
    ]

    if focuses != [
        "Strength",
        "Cardio",
        "Mobility"
    ]:
        raise ValueError("FAIL: Weekly workout focuses were incorrect")

    if mock_builder.call_count != 3:
        raise ValueError("FAIL: Workout builder was not called once per training day")

    print("PASS: Weekly workout plan generated correctly")

def test_weekly_rotation_prioritizes_fresh_exercises():
    candidates = [
        {
            "exercise_id": "TEST001",
            "name": "Chest Exercise",
            "primary_muscle": "Chest"
        },
        {
            "exercise_id": "TEST002",
            "name": "Back Exercise",
            "primary_muscle": "Back"
        },
        {
            "exercise_id": "TEST003",
            "name": "Leg Exercise",
            "primary_muscle": "Quadriceps"
        },
        {
            "exercise_id": "TEST004",
            "name": "Shoulder Exercise",
            "primary_muscle": "Shoulders"
        }
    ]

    prioritized = prioritize_candidates_for_weekly_rotation(
        candidates,
        weekly_used_exercise_ids={
            "TEST001",
            "TEST002"
        },
        previous_workout_exercise_ids={
            "TEST002"
        },
        previous_primary_muscles={
            "Back"
        }
    )

    exercise_ids = [
        exercise["exercise_id"]
        for exercise in prioritized
    ]

    if exercise_ids[0] != "TEST003":
        raise ValueError("FAIL: Fresh exercise was not prioritized")

    if exercise_ids[1] != "TEST004":
        raise ValueError("FAIL: Second fresh exercise was not prioritized")

    if exercise_ids[-1] != "TEST002":
        raise ValueError("FAIL: Previous workout exercise was not deprioritized")

    print("PASS: Weekly rotation prioritized fresh exercises")

def test_weekly_plan_passes_rotation_history():
    test_profile = {
        "primary_goal": "General Fitness",
        "fitness_level": "Intermediate",
        "training_days_per_week": 3,
        "session_duration_minutes": 45
    }

    fake_workouts = [
        {
            "exercise_count": 1,
            "fits_session": True,
            "exercises": [
                {
                    "exercise_id": "TEST001",
                    "primary_muscle": "Chest",
                    "order": 1
                }
            ]
        },
        {
            "exercise_count": 1,
            "fits_session": True,
            "exercises": [
                {
                    "exercise_id": "TEST002",
                    "primary_muscle": "Back",
                    "order": 1
                }
            ]
        },
        {
            "exercise_count": 1,
            "fits_session": True,
            "exercises": [
                {
                    "exercise_id": "TEST003",
                    "primary_muscle": "Quadriceps",
                    "order": 1
                }
            ]
        }
    ]

    with patch(
        "src.recommendations.workout_recommendations.get_user_profile",
        return_value=test_profile
    ), patch(
        "src.recommendations.workout_recommendations.build_workout_plan_for_user",
        side_effect=fake_workouts
    ) as mock_builder:
        weekly_plan = build_weekly_workout_plan_for_user(
            1
        )

    second_call = mock_builder.call_args_list[
        1
    ]

    second_weekly_used = second_call.kwargs[
        "weekly_used_exercise_ids"
    ]

    second_previous = second_call.kwargs[
        "previous_workout_exercise_ids"
    ]

    second_muscles = second_call.kwargs[
        "previous_primary_muscles"
    ]

    if second_weekly_used != {"TEST001"}:
        raise ValueError("FAIL: Second workout did not receive weekly exercise history")

    if second_previous != {"TEST001"}:
        raise ValueError("FAIL: Second workout did not receive previous exercise history")

    if second_muscles != {"Chest"}:
        raise ValueError("FAIL: Second workout did not receive previous muscle history")

    third_call = mock_builder.call_args_list[
        2
    ]

    third_weekly_used = third_call.kwargs[
        "weekly_used_exercise_ids"
    ]

    third_previous = third_call.kwargs[
        "previous_workout_exercise_ids"
    ]

    third_muscles = third_call.kwargs[
        "previous_primary_muscles"
    ]

    if third_weekly_used != {"TEST001", "TEST002"}:
        raise ValueError("FAIL: Third workout did not receive full weekly exercise history")

    if third_previous != {"TEST002"}:
        raise ValueError("FAIL: Third workout received incorrect previous workout history")

    if third_muscles != {"Back"}:
        raise ValueError("FAIL: Third workout received incorrect previous muscle history")

    if weekly_plan["unique_exercise_count"] != 3:
        raise ValueError("FAIL: Weekly unique exercise count was incorrect")

    print("PASS: Weekly plan tracks exercise and recovery history")



def test_invalid_fitness_level_rejected():
    functions = [
        lambda: is_difficulty_compatible("Beginner", "Unknown"),
        lambda: get_target_difficulty_score("Unknown"),
        lambda: adjust_exercise_count_for_fitness_level(4, "Unknown"),
        lambda: get_rir_target_for_fitness_level("Unknown")
    ]

    for function in functions:
        try:
            function()

        except ValueError:
            continue

        raise ValueError("FAIL: Invalid fitness level was accepted")

    print("PASS: Invalid fitness levels are rejected")


def test_invalid_session_duration_rejected():
    invalid_values = [
        0,
        -1,
        True,
        "45"
    ]

    for value in invalid_values:
        try:
            determine_exercise_count_from_session_duration(
                value
            )

        except ValueError:
            continue

        raise ValueError(f"FAIL: Invalid session duration was accepted: {value}")

    print("PASS: Invalid session durations are rejected")


def test_invalid_rir_rejected():
    invalid_values = [
        -1,
        11,
        True,
        "2"
    ]

    for value in invalid_values:
        try:
            get_rpe_target_from_rir(
                value
            )

        except ValueError:
            continue

        raise ValueError(f"FAIL: Invalid RIR was accepted: {value}")

    print("PASS: Invalid RIR values are rejected")


def make_valid_weekly_plan():
    return {
        "user_id": 1,
        "training_days_per_week": 3,
        "weekly_plan": [
            {
                "day_number": 1,
                "day_name": "Monday",
                "day_type": "Training",
                "focus_category": "Strength",
                "workout": {
                    "exercises": [
                        {
                            "exercise_id": "A",
                            "primary_muscle": "Chest",
                            "order": 1
                        },
                        {
                            "exercise_id": "B",
                            "primary_muscle": "Back",
                            "order": 2
                        }
                    ]
                }
            },
            {
                "day_number": 2,
                "day_name": "Tuesday",
                "day_type": "Rest",
                "focus_category": None,
                "workout": None
            },
            {
                "day_number": 3,
                "day_name": "Wednesday",
                "day_type": "Training",
                "focus_category": "Cardio",
                "workout": {
                    "exercises": [
                        {
                            "exercise_id": "C",
                            "primary_muscle": "Quadriceps",
                            "order": 1
                        }
                    ]
                }
            },
            {
                "day_number": 4,
                "day_name": "Thursday",
                "day_type": "Rest",
                "focus_category": None,
                "workout": None
            },
            {
                "day_number": 5,
                "day_name": "Friday",
                "day_type": "Training",
                "focus_category": "Mobility",
                "workout": {
                    "exercises": [
                        {
                            "exercise_id": "D",
                            "primary_muscle": "Chest",
                            "order": 1
                        }
                    ]
                }
            },
            {
                "day_number": 6,
                "day_name": "Saturday",
                "day_type": "Rest",
                "focus_category": None,
                "workout": None
            },
            {
                "day_number": 7,
                "day_name": "Sunday",
                "day_type": "Rest",
                "focus_category": None,
                "workout": None
            }
        ]
    }


def test_weekly_muscle_frequency():
    plan = make_valid_weekly_plan()

    frequency = get_weekly_muscle_frequency(
        plan["weekly_plan"]
    )

    if frequency["Chest"] != 2:
        raise ValueError("FAIL: Chest weekly frequency should be 2")

    if frequency["Back"] != 1:
        raise ValueError("FAIL: Back weekly frequency should be 1")

    if frequency["Quadriceps"] != 1:
        raise ValueError("FAIL: Quadriceps weekly frequency should be 1")

    print("PASS: Weekly muscle-frequency tracking works correctly")


def test_weekly_recovery_warnings():
    weekly_plan = [
        {
            "day_number": 1,
            "day_name": "Monday",
            "day_type": "Training",
            "workout": {
                "exercises": [
                    {
                        "exercise_id": "A",
                        "primary_muscle": "Chest"
                    }
                ]
            }
        },
        {
            "day_number": 2,
            "day_name": "Tuesday",
            "day_type": "Training",
            "workout": {
                "exercises": [
                    {
                        "exercise_id": "B",
                        "primary_muscle": "Chest"
                    }
                ]
            }
        },
        {
            "day_number": 3,
            "day_name": "Wednesday",
            "day_type": "Rest",
            "workout": None
        }
    ]

    warnings = get_weekly_recovery_warnings(
        weekly_plan
    )

    if len(warnings) != 1:
        raise ValueError("FAIL: Consecutive overlapping muscle days should create one recovery warning")

    if warnings[0]["overlapping_primary_muscles"] != ["Chest"]:
        raise ValueError("FAIL: Recovery warning contained wrong muscle")

    print("PASS: Weekly recovery warnings work correctly")


def test_weekly_plan_validation():
    valid_plan = make_valid_weekly_plan()

    if not validate_weekly_workout_plan(
        valid_plan
    ):
        raise ValueError("FAIL: Valid weekly plan did not pass validation")

    invalid_plan = make_valid_weekly_plan()

    invalid_plan["weekly_plan"][1]["workout"] = {
        "exercises": []
    }

    try:
        validate_weekly_workout_plan(
            invalid_plan
        )

    except ValueError:
        pass

    else:
        raise ValueError("FAIL: Rest day with workout was accepted")

    duplicate_plan = make_valid_weekly_plan()

    duplicate_plan[
        "weekly_plan"
    ][0][
        "workout"
    ][
        "exercises"
    ][1][
        "exercise_id"
    ] = "A"

    try:
        validate_weekly_workout_plan(
            duplicate_plan
        )

    except ValueError:
        pass

    else:
        raise ValueError("FAIL: Duplicate exercise IDs were accepted")

    print("PASS: Weekly workout-plan validation works correctly")


def test_build_weekly_workout_plan_includes_analytics():
    test_profile = {
        "primary_goal": "General Fitness",
        "fitness_level": "Intermediate",
        "training_days_per_week": 3,
        "session_duration_minutes": 45
    }

    fake_workouts = [
        {
            "exercises": [
                {
                    "exercise_id": "TEST001",
                    "primary_muscle": "Chest",
                    "order": 1
                }
            ]
        },
        {
            "exercises": [
                {
                    "exercise_id": "TEST002",
                    "primary_muscle": "Back",
                    "order": 1
                }
            ]
        },
        {
            "exercises": [
                {
                    "exercise_id": "TEST003",
                    "primary_muscle": "Chest",
                    "order": 1
                }
            ]
        }
    ]

    with patch(
        "src.recommendations.workout_recommendations.get_user_profile",
        return_value=test_profile
    ), patch(
        "src.recommendations.workout_recommendations.build_workout_plan_for_user",
        side_effect=fake_workouts
    ):
        result = build_weekly_workout_plan_for_user(
            1
        )

    if result["unique_exercise_count"] != 3:
        raise ValueError("FAIL: Weekly unique exercise count was incorrect")

    if result["muscle_frequency"]["Chest"] != 2:
        raise ValueError("FAIL: Weekly plan did not calculate Chest frequency correctly")

    if result["muscle_frequency"]["Back"] != 1:
        raise ValueError("FAIL: Weekly plan did not calculate Back frequency correctly")

    if result["recovery_warnings"] != []:
        raise ValueError("FAIL: Non-consecutive training days produced recovery warnings")

    print("PASS: Weekly workout plan includes analytics and validation")


if __name__ == "__main__":
    test_environment_compatibility()
    test_candidate_exercises_match_user_environment()
    test_equipment_compatibility()
    test_candidate_exercises_match_equipment_access()
    test_disliked_exercise_detection()
    test_disliked_exercise_excluded_from_candidates()
    test_preferred_exercise_ranks_higher()
    test_preferred_exercise_ranks_first_in_candidates()
    test_exercise_limitation_detection()
    test_user_limitation_excludes_affected_exercises()
    test_limitation_type_exclusion_rules()
    test_injury_history_lowers_ranking()
    test_saved_injury_history_lowers_candidate_ranking()
    test_difficulty_compatibility()
    test_beginner_user_gets_beginner_exercises_only()
    test_intermediate_user_excludes_advanced_exercises()
    test_strength_goal_ranks_compound_strength_higher()
    test_other_goal_scores()
    test_strength_goal_prioritizes_strength_candidates()
    test_build_workout_returns_requested_exercise_count()
    test_build_workout_rejects_invalid_exercise_count()
    test_build_workout_handles_fewer_candidates_than_requested()
    test_movement_balance_limits_same_pattern()
    test_build_workout_applies_movement_balance()
    test_exercise_count_from_session_duration()
    test_build_workout_uses_session_duration()
    test_sets_and_reps_for_goal()
    test_build_workout_adds_strength_sets_and_reps()
    test_rest_seconds_for_goal()
    test_build_workout_adds_strength_rest_seconds()
    test_workout_prescription_for_goal()
    test_estimate_workout_duration_minutes()
    test_workout_fit_session()
    test_build_workout_plan_for_user()
    test_workout_balance_limits_same_primary_muscle()
    test_compound_priority_score()
    test_workout_order_prioritizes_compound_exercises()
    test_build_workout_applies_primary_muscle_balance()
    test_warm_up_and_cool_down_minutes()
    test_add_exercise_order_numbers()
    test_workout_plan_status()
    test_workout_plan_includes_structure_metadata()
    test_calculate_total_workout_duration()
    test_trim_workout_to_session_duration()
    test_trim_workout_keeps_at_least_one_exercise()
    test_workout_plan_automatically_shortens_to_fit()
    test_exercise_prescription_by_category()
    test_estimate_mixed_workout_duration()
    test_build_workout_uses_mixed_prescriptions()
    test_goal_priority_categories()
    test_endurance_prioritizes_cardio_candidate()
    test_general_fitness_prioritizes_mixed_categories()
    test_goal_composition_handles_missing_category()
    test_general_fitness_builds_mixed_workout()
    test_target_difficulty_score()
    test_difficulty_fit_score()
    test_exercise_count_adjusts_for_fitness_level()
    test_intermediate_user_prioritizes_matching_difficulty()
    test_beginner_workout_uses_reduced_automatic_volume()
    test_rir_targets_for_fitness_level()
    test_rpe_target_from_rir()
    test_strength_isolation_uses_higher_rep_range()
    test_strength_prescription_includes_intensity_targets()
    test_beginner_workout_uses_beginner_intensity()
    test_weekly_training_day_numbers()
    test_weekly_focus_categories()
    test_day_focus_prioritizes_matching_category()
    test_invalid_weekly_training_days_rejected()
    test_build_weekly_workout_plan()
    test_weekly_rotation_prioritizes_fresh_exercises()
    test_weekly_plan_passes_rotation_history()
    test_invalid_fitness_level_rejected()
    test_invalid_session_duration_rejected()
    test_invalid_rir_rejected()
    test_weekly_muscle_frequency()
    test_weekly_recovery_warnings()
    test_weekly_plan_validation()
    test_build_weekly_workout_plan_includes_analytics()