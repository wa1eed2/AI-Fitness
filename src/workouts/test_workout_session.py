from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.workouts.workout_session import (
    seconds_to_minutes,
    get_next_set_number,
    WorkoutSessionTracker
)

from src.database.query_workout_log_database import (
    get_workout_session_exercises,
    get_workout_set_logs
)


class FakeClock:
    def __init__(self):
        self.current_time = 0.0

    def time(self):
        return self.current_time

    def advance(
        self,
        seconds
    ):
        self.current_time += seconds


def test_seconds_to_minutes():
    cases = [
        (0, 0.0),
        (30, 0.5),
        (60, 1.0),
        (90, 1.5),
        (3600, 60.0)
    ]

    for seconds, expected in cases:
        result = seconds_to_minutes(
            seconds
        )

        if result != expected:
            raise ValueError(f"FAIL: {seconds} seconds converted to {result} instead of {expected}")

    print("PASS: Seconds convert to minutes correctly")


def test_workout_session_tracker_starts():
    user_id = create_user()

    try:
        clock = FakeClock()

        plan = {
            "primary_goal": "General Fitness",
            "session_duration_minutes": 60,
            "exercises": [
                {
                    "exercise_id": "E001",
                    "sets": 3,
                    "reps": "8-12",
                    "rest_seconds": 60
                }
            ]
        }

        tracker = WorkoutSessionTracker(
            user_id,
            plan,
            time_function=clock.time
        )

        workout_session_id = tracker.start()

        if not isinstance(workout_session_id, int):
            raise ValueError("FAIL: Workout tracker did not return session ID")

        if tracker.status != "In Progress":
            raise ValueError("FAIL: Workout tracker did not enter In Progress status")

        if tracker.workout_timer.status != "Running":
            raise ValueError("FAIL: Workout timer did not start with session")

        print("PASS: Workout session tracker starts database session and timer")

    finally:
        delete_user(user_id)


def test_workout_session_tracker_saves_timer_duration():
    user_id = create_user()

    try:
        clock = FakeClock()

        plan = {
            "primary_goal": "Strength",
            "session_duration_minutes": 60,
            "exercises": [
                {
                    "exercise_id": "E001",
                    "sets": 4,
                    "reps": "4-6",
                    "rest_seconds": 180
                }
            ]
        }

        tracker = WorkoutSessionTracker(
            user_id,
            plan,
            time_function=clock.time
        )

        tracker.start()

        clock.advance(
            2700
        )

        actual_duration = tracker.finish(
            notes="Completed test workout"
        )

        if actual_duration != 45.0:
            raise ValueError("FAIL: Workout timer did not produce 45-minute duration")

        details = tracker.get_details()

        if details["status"] != "Completed":
            raise ValueError("FAIL: Finished tracker did not complete database workout")

        if details["actual_duration_minutes"] != 45.0:
            raise ValueError("FAIL: Timer duration was not saved to workout database")

        if details["notes"] != "Completed test workout":
            raise ValueError("FAIL: Workout completion notes were not saved")

        if tracker.status != "Completed":
            raise ValueError("FAIL: Tracker did not enter Completed status")

        if tracker.workout_timer.status != "Stopped":
            raise ValueError("FAIL: Workout timer did not stop after workout completion")

        print("PASS: Workout timer duration saves to workout database")

    finally:
        delete_user(user_id)


def test_workout_session_pause_excludes_paused_time():
    user_id = create_user()

    try:
        clock = FakeClock()

        plan = {
            "primary_goal": "General Fitness",
            "session_duration_minutes": 60,
            "exercises": []
        }

        tracker = WorkoutSessionTracker(
            user_id,
            plan,
            time_function=clock.time
        )

        tracker.start()

        clock.advance(
            20 * 60
        )

        tracker.pause()

        if tracker.status != "Paused":
            raise ValueError("FAIL: Workout tracker did not enter Paused status")

        if tracker.workout_timer.status != "Paused":
            raise ValueError("FAIL: Workout timer did not pause")

        clock.advance(
            60 * 60
        )

        tracker.resume()

        if tracker.status != "In Progress":
            raise ValueError("FAIL: Workout tracker did not resume")

        if tracker.workout_timer.status != "Running":
            raise ValueError("FAIL: Workout timer did not resume")

        clock.advance(
            10 * 60
        )

        actual_duration = tracker.finish()

        if actual_duration != 30.0:
            raise ValueError("FAIL: Paused time was incorrectly included in workout duration")

        details = tracker.get_details()

        if details["actual_duration_minutes"] != 30.0:
            raise ValueError("FAIL: Correct active workout duration was not saved")

        print("PASS: Workout session excludes paused time from duration")

    finally:
        delete_user(user_id)


def test_workout_session_controls_rest_timer():
    user_id = create_user()

    try:
        clock = FakeClock()

        plan = {
            "primary_goal": "Strength",
            "session_duration_minutes": 60,
            "exercises": []
        }

        tracker = WorkoutSessionTracker(
            user_id,
            plan,
            time_function=clock.time
        )

        tracker.start()

        tracker.start_rest(
            90
        )

        if tracker.rest_timer.status != "Running":
            raise ValueError("FAIL: Workout rest timer did not start")

        clock.advance(
            30
        )

        if tracker.rest_timer.remaining_seconds() != 60.0:
            raise ValueError("FAIL: Workout rest timer returned incorrect remaining time")

        tracker.pause()

        if tracker.rest_timer.status != "Paused":
            raise ValueError("FAIL: Workout pause did not pause rest timer")

        clock.advance(
            100
        )

        if tracker.rest_timer.remaining_seconds() != 60.0:
            raise ValueError("FAIL: Workout pause did not preserve rest time")

        tracker.resume()

        if tracker.rest_timer.status != "Running":
            raise ValueError("FAIL: Workout resume did not resume rest timer")

        clock.advance(
            60
        )

        if not tracker.rest_timer.is_finished():
            raise ValueError("FAIL: Rest timer did not finish after resume")

        if tracker.rest_timer.remaining_seconds() != 0.0:
            raise ValueError("FAIL: Finished rest timer did not return zero")

        print("PASS: Workout session controls rest timer correctly")

    finally:
        delete_user(user_id)


def test_workout_session_tracker_cancels():
    user_id = create_user()

    try:
        clock = FakeClock()

        plan = {
            "primary_goal": "General Fitness",
            "session_duration_minutes": 45,
            "exercises": []
        }

        tracker = WorkoutSessionTracker(
            user_id,
            plan,
            time_function=clock.time
        )

        tracker.start()

        clock.advance(
            300
        )

        tracker.cancel(
            notes="Stopped early"
        )

        details = tracker.get_details()

        if tracker.status != "Cancelled":
            raise ValueError("FAIL: Tracker did not enter Cancelled status")

        if tracker.workout_timer.status != "Stopped":
            raise ValueError("FAIL: Workout timer did not stop after cancellation")

        if tracker.rest_timer.status != "Not Started":
            raise ValueError("FAIL: Rest timer did not reset after cancellation")

        if details["status"] != "Cancelled":
            raise ValueError("FAIL: Database workout did not become Cancelled")

        if details["completed_at"] is None:
            raise ValueError("FAIL: Cancelled workout did not receive completion timestamp")

        if details["notes"] != "Stopped early":
            raise ValueError("FAIL: Cancellation notes were not saved")

        print("PASS: Workout session tracker cancels correctly")

    finally:
        delete_user(user_id)

def test_next_set_number():
    user_id = create_user()

    try:
        clock = FakeClock()

        plan = {
            "primary_goal": "Strength",
            "session_duration_minutes": 60,
            "exercises": [
                {
                    "exercise_id": "E001",
                    "sets": 4,
                    "reps": "4-6",
                    "rest_seconds": 180
                }
            ]
        }

        tracker = WorkoutSessionTracker(
            user_id,
            plan,
            time_function=clock.time
        )

        tracker.start()

        exercises = get_workout_session_exercises(
            tracker.workout_session_id
        )

        session_exercise_id = exercises[0][
            "session_exercise_id"
        ]

        if get_next_set_number(session_exercise_id) != 1:
            raise ValueError("FAIL: Empty exercise did not return set number 1")

        tracker.log_set(
            session_exercise_id,
            reps_completed=5,
            weight_kg=100
        )

        if get_next_set_number(session_exercise_id) != 2:
            raise ValueError("FAIL: Next set number did not become 2")

        print("PASS: Next set number calculated automatically")

    finally:
        delete_user(user_id)

def test_tracker_logs_sets_sequentially():
    user_id = create_user()

    try:
        clock = FakeClock()

        plan = {
            "primary_goal": "Strength",
            "session_duration_minutes": 60,
            "exercises": [
                {
                    "exercise_id": "E001",
                    "sets": 3,
                    "reps": "4-6",
                    "rest_seconds": 180
                }
            ]
        }

        tracker = WorkoutSessionTracker(
            user_id,
            plan,
            time_function=clock.time
        )

        tracker.start()

        exercises = get_workout_session_exercises(
            tracker.workout_session_id
        )

        session_exercise_id = exercises[0][
            "session_exercise_id"
        ]

        tracker.log_set(
            session_exercise_id,
            reps_completed=6,
            weight_kg=80
        )

        tracker.log_set(
            session_exercise_id,
            reps_completed=5,
            weight_kg=85
        )

        tracker.log_set(
            session_exercise_id,
            reps_completed=4,
            weight_kg=90
        )

        logs = get_workout_set_logs(
            session_exercise_id
        )

        set_numbers = [
            log["set_number"]
            for log in logs
        ]

        if set_numbers != [1, 2, 3]:
            raise ValueError("FAIL: Tracker did not log sequential set numbers")

        print("PASS: Workout tracker logs sets sequentially")

    finally:
        delete_user(user_id)

def test_tracker_gets_planned_rest():
    user_id = create_user()

    try:
        clock = FakeClock()

        plan = {
            "primary_goal": "Strength",
            "session_duration_minutes": 60,
            "exercises": [
                {
                    "exercise_id": "E001",
                    "sets": 4,
                    "reps": "4-6",
                    "rest_seconds": 180
                }
            ]
        }

        tracker = WorkoutSessionTracker(
            user_id,
            plan,
            time_function=clock.time
        )

        tracker.start()

        exercises = get_workout_session_exercises(
            tracker.workout_session_id
        )

        session_exercise_id = exercises[0][
            "session_exercise_id"
        ]

        rest_seconds = tracker.get_planned_rest_seconds(
            session_exercise_id
        )

        if rest_seconds != 180:
            raise ValueError("FAIL: Tracker did not return planned rest duration")

        print("PASS: Workout tracker retrieves planned rest duration")

    finally:
        delete_user(user_id)

def test_logged_set_can_start_planned_rest():
    user_id = create_user()

    try:
        clock = FakeClock()

        plan = {
            "primary_goal": "Strength",
            "session_duration_minutes": 60,
            "exercises": [
                {
                    "exercise_id": "E001",
                    "sets": 4,
                    "reps": "4-6",
                    "rest_seconds": 180
                }
            ]
        }

        tracker = WorkoutSessionTracker(
            user_id,
            plan,
            time_function=clock.time
        )

        tracker.start()

        exercises = get_workout_session_exercises(
            tracker.workout_session_id
        )

        session_exercise_id = exercises[0][
            "session_exercise_id"
        ]

        tracker.log_set(
            session_exercise_id,
            reps_completed=5,
            weight_kg=100,
            start_planned_rest=True
        )

        if tracker.rest_timer.status != "Running":
            raise ValueError("FAIL: Logging set did not start planned rest timer")

        if tracker.rest_timer.remaining_seconds() != 180.0:
            raise ValueError("FAIL: Rest timer did not use planned rest duration")

        print("PASS: Logged set can automatically start planned rest")

    finally:
        delete_user(user_id)

def test_tracker_completes_exercise():
    user_id = create_user()

    try:
        clock = FakeClock()

        plan = {
            "primary_goal": "Strength",
            "session_duration_minutes": 60,
            "exercises": [
                {
                    "exercise_id": "E001",
                    "sets": 3,
                    "reps": "8-12",
                    "rest_seconds": 90
                }
            ]
        }

        tracker = WorkoutSessionTracker(
            user_id,
            plan,
            time_function=clock.time
        )

        tracker.start()

        exercises = get_workout_session_exercises(
            tracker.workout_session_id
        )

        session_exercise_id = exercises[0][
            "session_exercise_id"
        ]

        tracker.complete_exercise(
            session_exercise_id
        )

        exercises = get_workout_session_exercises(
            tracker.workout_session_id
        )

        if exercises[0]["completed"] != 1:
            raise ValueError("FAIL: Tracker did not complete session exercise")

        print("PASS: Workout tracker completes exercises")

    finally:
        delete_user(user_id)

def test_workout_adherence_summary():
    user_id = create_user()

    try:
        clock = FakeClock()

        plan = {
            "primary_goal": "Strength",
            "session_duration_minutes": 60,
            "exercises": [
                {
                    "exercise_id": "E001",
                    "sets": 4,
                    "reps": "4-6",
                    "rest_seconds": 180
                },
                {
                    "exercise_id": "E006",
                    "duration_minutes": 10
                }
            ]
        }

        tracker = WorkoutSessionTracker(
            user_id,
            plan,
            time_function=clock.time
        )

        tracker.start()

        exercises = get_workout_session_exercises(
            tracker.workout_session_id
        )

        strength_exercise_id = exercises[0][
            "session_exercise_id"
        ]

        tracker.log_set(
            strength_exercise_id,
            reps_completed=6
        )

        tracker.log_set(
            strength_exercise_id,
            reps_completed=6
        )

        tracker.complete_exercise(
            strength_exercise_id
        )

        summary = tracker.get_adherence_summary()

        if summary["total_exercises"] != 2:
            raise ValueError("FAIL: Adherence summary returned incorrect exercise count")

        if summary["completed_exercises"] != 1:
            raise ValueError("FAIL: Adherence summary returned incorrect completed count")

        if summary["exercise_completion_percentage"] != 50.0:
            raise ValueError("FAIL: Exercise completion percentage was incorrect")

        if summary["total_planned_sets"] != 4:
            raise ValueError("FAIL: Planned set count was incorrect")

        if summary["total_logged_sets"] != 2:
            raise ValueError("FAIL: Logged set count was incorrect")

        if summary["set_adherence_percentage"] != 50.0:
            raise ValueError("FAIL: Set adherence percentage was incorrect")

        print("PASS: Workout adherence summary calculated correctly")

    finally:
        delete_user(user_id)

def test_tracker_rejects_actions_before_start():
    user_id = create_user()

    try:
        clock = FakeClock()

        tracker = WorkoutSessionTracker(
            user_id,
            {
                "primary_goal": "General Fitness",
                "session_duration_minutes": 60,
                "exercises": []
            },
            time_function=clock.time
        )

        actions = [
            tracker.pause,
            tracker.resume,
            tracker.finish,
            tracker.cancel
        ]

        for action in actions:
            try:
                action()

            except ValueError:
                continue

            raise ValueError("FAIL: Tracker allowed action before workout start")

        print("PASS: Tracker rejects actions before workout start")

    finally:
        delete_user(user_id)

def test_tracker_rejects_duplicate_start():
    user_id = create_user()

    try:
        clock = FakeClock()

        tracker = WorkoutSessionTracker(
            user_id,
            {
                "primary_goal": "General Fitness",
                "session_duration_minutes": 60,
                "exercises": []
            },
            time_function=clock.time
        )

        tracker.start()

        try:
            tracker.start()

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Tracker allowed duplicate workout start")

        print("PASS: Tracker rejects duplicate workout start")

    finally:
        delete_user(user_id)

def test_tracker_rejects_set_logging_while_paused():
    user_id = create_user()

    try:
        clock = FakeClock()

        tracker = WorkoutSessionTracker(
            user_id,
            {
                "primary_goal": "Strength",
                "session_duration_minutes": 60,
                "exercises": [
                    {
                        "exercise_id": "E001",
                        "sets": 3,
                        "reps": "4-6",
                        "rest_seconds": 180
                    }
                ]
            },
            time_function=clock.time
        )

        tracker.start()

        exercises = get_workout_session_exercises(
            tracker.workout_session_id
        )

        session_exercise_id = exercises[0][
            "session_exercise_id"
        ]

        tracker.pause()

        try:
            tracker.log_set(
                session_exercise_id,
                reps_completed=5
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Tracker allowed set logging while paused")

        print("PASS: Tracker rejects set logging while paused")

    finally:
        delete_user(user_id)

def test_tracker_handles_exercise_without_planned_rest():
    user_id = create_user()

    try:
        clock = FakeClock()

        tracker = WorkoutSessionTracker(
            user_id,
            {
                "primary_goal": "Endurance",
                "session_duration_minutes": 45,
                "exercises": [
                    {
                        "exercise_id": "E006",
                        "duration_minutes": 10
                    }
                ]
            },
            time_function=clock.time
        )

        tracker.start()

        exercises = get_workout_session_exercises(
            tracker.workout_session_id
        )

        session_exercise_id = exercises[0][
            "session_exercise_id"
        ]

        rest_seconds = tracker.get_planned_rest_seconds(
            session_exercise_id
        )

        if rest_seconds != 0:
            raise ValueError("FAIL: Exercise without planned rest did not return zero")

        tracker.log_set(
            session_exercise_id,
            duration_seconds=600,
            start_planned_rest=True
        )

        if tracker.rest_timer.status != "Not Started":
            raise ValueError("FAIL: Exercise without rest incorrectly started rest timer")

        print("PASS: Tracker handles exercise without planned rest")

    finally:
        delete_user(user_id)

def test_adherence_summary_handles_no_planned_sets():
    user_id = create_user()

    try:
        clock = FakeClock()

        tracker = WorkoutSessionTracker(
            user_id,
            {
                "primary_goal": "Endurance",
                "session_duration_minutes": 45,
                "exercises": [
                    {
                        "exercise_id": "E006",
                        "duration_minutes": 10
                    }
                ]
            },
            time_function=clock.time
        )

        tracker.start()

        summary = tracker.get_adherence_summary()

        if summary["total_planned_sets"] != 0:
            raise ValueError("FAIL: Duration exercise incorrectly counted planned sets")

        if summary["total_logged_sets"] != 0:
            raise ValueError("FAIL: Empty duration exercise incorrectly counted logged sets")

        if summary["set_adherence_percentage"] != 0.0:
            raise ValueError("FAIL: No-set workout returned incorrect set adherence")

        print("PASS: Adherence summary handles workouts without planned sets")

    finally:
        delete_user(user_id)

def test_set_adherence_does_not_exceed_100_percent():
    user_id = create_user()

    try:
        clock = FakeClock()

        tracker = WorkoutSessionTracker(
            user_id,
            {
                "primary_goal": "Strength",
                "session_duration_minutes": 60,
                "exercises": [
                    {
                        "exercise_id": "E001",
                        "sets": 2,
                        "reps": "4-6",
                        "rest_seconds": 180
                    }
                ]
            },
            time_function=clock.time
        )

        tracker.start()

        exercises = get_workout_session_exercises(
            tracker.workout_session_id
        )

        session_exercise_id = exercises[0][
            "session_exercise_id"
        ]

        tracker.log_set(
            session_exercise_id,
            reps_completed=6
        )

        tracker.log_set(
            session_exercise_id,
            reps_completed=6
        )

        tracker.log_set(
            session_exercise_id,
            reps_completed=5
        )

        summary = tracker.get_adherence_summary()

        if summary["total_logged_sets"] != 2:
            raise ValueError("FAIL: Adherence counted extra sets above planned volume")

        if summary["set_adherence_percentage"] != 100.0:
            raise ValueError("FAIL: Set adherence exceeded or failed to reach 100 percent")

        print("PASS: Set adherence does not exceed 100 percent")

    finally:
        delete_user(user_id)

def test_complete_simulated_workout_flow():
    user_id = create_user()

    try:
        clock = FakeClock()

        tracker = WorkoutSessionTracker(
            user_id,
            {
                "primary_goal": "General Fitness",
                "session_duration_minutes": 60,
                "exercises": [
                    {
                        "exercise_id": "E001",
                        "sets": 2,
                        "reps": "8-12",
                        "rest_seconds": 60
                    },
                    {
                        "exercise_id": "E006",
                        "duration_minutes": 10
                    }
                ]
            },
            time_function=clock.time
        )

        tracker.start()

        exercises = get_workout_session_exercises(
            tracker.workout_session_id
        )

        strength_exercise_id = exercises[0][
            "session_exercise_id"
        ]

        cardio_exercise_id = exercises[1][
            "session_exercise_id"
        ]

        clock.advance(
            300
        )

        tracker.log_set(
            strength_exercise_id,
            reps_completed=10,
            weight_kg=40,
            rir_actual=2,
            rpe_actual=8,
            start_planned_rest=True
        )

        clock.advance(
            60
        )

        if not tracker.rest_timer.is_finished():
            raise ValueError("FAIL: Simulated workout rest timer did not finish")

        tracker.log_set(
            strength_exercise_id,
            reps_completed=9,
            weight_kg=40,
            rir_actual=1,
            rpe_actual=9
        )

        tracker.complete_exercise(
            strength_exercise_id
        )

        clock.advance(
            600
        )

        tracker.log_set(
            cardio_exercise_id,
            duration_seconds=600
        )

        tracker.complete_exercise(
            cardio_exercise_id
        )

        summary = tracker.get_adherence_summary()

        if summary["exercise_completion_percentage"] != 100.0:
            raise ValueError("FAIL: Simulated workout did not reach full exercise completion")

        if summary["set_adherence_percentage"] != 100.0:
            raise ValueError("FAIL: Simulated workout did not reach full set adherence")

        clock.advance(
            240
        )

        actual_duration = tracker.finish(
            notes="Full simulated workout"
        )

        if actual_duration != 20.0:
            raise ValueError("FAIL: Simulated workout returned incorrect total active duration")

        details = tracker.get_details()

        if details["status"] != "Completed":
            raise ValueError("FAIL: Simulated workout did not finish")

        if len(details["exercises"]) != 2:
            raise ValueError("FAIL: Simulated workout did not retain both exercises")

        if len(details["exercises"][0]["sets"]) != 2:
            raise ValueError("FAIL: Strength exercise did not retain two set logs")

        if len(details["exercises"][1]["sets"]) != 1:
            raise ValueError("FAIL: Cardio exercise did not retain duration log")

        print("PASS: Complete simulated workout flow works correctly")

    finally:
        delete_user(user_id)


if __name__ == "__main__":
    test_seconds_to_minutes()
    test_workout_session_tracker_starts()
    test_workout_session_tracker_saves_timer_duration()
    test_workout_session_pause_excludes_paused_time()
    test_workout_session_controls_rest_timer()
    test_workout_session_tracker_cancels()
    test_next_set_number()
    test_tracker_logs_sets_sequentially()
    test_tracker_gets_planned_rest()
    test_logged_set_can_start_planned_rest()
    test_tracker_completes_exercise()
    test_workout_adherence_summary()
    test_tracker_rejects_actions_before_start()
    test_tracker_rejects_duplicate_start()
    test_tracker_rejects_set_logging_while_paused()
    test_tracker_handles_exercise_without_planned_rest()
    test_adherence_summary_handles_no_planned_sets()
    test_set_adherence_does_not_exceed_100_percent()
    test_complete_simulated_workout_flow()