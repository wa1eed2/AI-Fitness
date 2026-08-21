from src.database.query_workout_log_database import (
    start_workout_from_plan,
    finish_workout_session,
    cancel_workout_session,
    get_workout_session_details,
    get_workout_session_exercises,
    get_workout_set_logs,
    log_workout_set,
    mark_session_exercise_complete,
    get_workout_progress
)

from src.workouts.workout_timer import (
    WorkoutTimer,
    RestTimer
)

def seconds_to_minutes(
    seconds
):
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
        raise ValueError("Seconds must be a number")

    if seconds < 0:
        raise ValueError("Seconds cannot be negative")

    return round(
        seconds / 60,
        2
    )

def get_next_set_number(
    session_exercise_id
):
    set_logs = get_workout_set_logs(
        session_exercise_id
    )

    if not set_logs:
        return 1

    existing_set_numbers = [
        set_log["set_number"]
        for set_log in set_logs
    ]

    return max(
        existing_set_numbers
    ) + 1

class WorkoutSessionTracker:
    def __init__(
        self,
        user_id,
        workout_plan,
        time_function=None
    ):
        self.user_id = user_id

        self.workout_plan = workout_plan

        self.workout_session_id = None

        self.workout_timer = WorkoutTimer(
            time_function=time_function
        )

        self.rest_timer = RestTimer(
            time_function=time_function
        )

        self.status = "Not Started"

    def start(self):
        if self.status != "Not Started":
            raise ValueError("Workout session tracker has already started")

        self.workout_session_id = start_workout_from_plan(
            self.user_id,
            self.workout_plan
        )

        self.workout_timer.start()

        self.status = "In Progress"

        return self.workout_session_id

    def pause(self):
        if self.status != "In Progress":
            raise ValueError("Workout session is not in progress")

        self.workout_timer.pause()

        if self.rest_timer.status == "Running":
            self.rest_timer.pause()

        self.status = "Paused"

    def resume(self):
        if self.status != "Paused":
            raise ValueError("Workout session is not paused")

        self.workout_timer.resume()

        if self.rest_timer.status == "Paused":
            self.rest_timer.resume()

        self.status = "In Progress"

    def start_rest(
        self,
        duration_seconds
    ):
        if self.status != "In Progress":
            raise ValueError("Workout session is not in progress")

        if self.rest_timer.status in {
            "Running",
            "Paused"
        }:
            raise ValueError("Rest timer is already active")

        if self.rest_timer.status == "Finished":
            self.rest_timer.reset()

        self.rest_timer.start(
            duration_seconds
        )

    def reset_rest(self):
        self.rest_timer.reset()

    def log_set(
        self,
        session_exercise_id,
        reps_completed=None,
        weight_kg=None,
        duration_seconds=None,
        rir_actual=None,
        rpe_actual=None,
        start_planned_rest=False
    ):
        if self.status != "In Progress":
            raise ValueError("Workout session is not in progress")

        set_number = get_next_set_number(
            session_exercise_id
        )

        set_log_id = log_workout_set(
            session_exercise_id,
            set_number,
            reps_completed=reps_completed,
            weight_kg=weight_kg,
            duration_seconds=duration_seconds,
            rir_actual=rir_actual,
            rpe_actual=rpe_actual
        )

        if start_planned_rest:
            planned_rest_seconds = self.get_planned_rest_seconds(
                session_exercise_id
            )

            if planned_rest_seconds > 0:
                self.start_rest(
                    planned_rest_seconds
                )

        return set_log_id

    def get_planned_rest_seconds(
        self,
        session_exercise_id
    ):
        if self.workout_session_id is None:
            raise ValueError("Workout session has not started")

        exercises = get_workout_session_exercises(
            self.workout_session_id
        )

        for exercise in exercises:
            if exercise["session_exercise_id"] == session_exercise_id:
                planned_rest_seconds = exercise[
                    "planned_rest_seconds"
                ]

                if planned_rest_seconds is None:
                    return 0

                return planned_rest_seconds

        raise ValueError("Session exercise not found")

    def complete_exercise(
        self,
        session_exercise_id
    ):
        if self.status != "In Progress":
            raise ValueError("Workout session is not in progress")

        mark_session_exercise_complete(
            session_exercise_id
        )

    def get_adherence_summary(self):
        if self.workout_session_id is None:
            raise ValueError("Workout session has not started")

        exercises = get_workout_session_exercises(
            self.workout_session_id
        )

        progress = get_workout_progress(
            self.workout_session_id
        )

        total_planned_sets = 0

        total_logged_sets = 0

        for exercise in exercises:
            planned_sets = exercise[
                "planned_sets"
            ]

            if planned_sets is None:
                continue

            total_planned_sets += planned_sets

            set_logs = get_workout_set_logs(
                exercise["session_exercise_id"]
            )

            total_logged_sets += min(
                len(set_logs),
                planned_sets
            )

        if total_planned_sets == 0:
            set_adherence_percentage = 0.0

        else:
            set_adherence_percentage = round(
                (
                    total_logged_sets
                    / total_planned_sets
                ) * 100,
                2
            )

        return {
            "total_exercises": progress["total_exercises"],
            "completed_exercises": progress["completed_exercises"],
            "exercise_completion_percentage": progress["completion_percentage"],
            "total_planned_sets": total_planned_sets,
            "total_logged_sets": total_logged_sets,
            "set_adherence_percentage": set_adherence_percentage
        }

    def finish(
        self,
        notes=None
    ):
        if self.status not in {
            "In Progress",
            "Paused"
        }:
            raise ValueError("Workout session cannot be finished")

        elapsed_seconds = self.workout_timer.stop()

        actual_duration_minutes = seconds_to_minutes(
            elapsed_seconds
        )

        finish_workout_session(
            self.workout_session_id,
            actual_duration_minutes=actual_duration_minutes,
            notes=notes
        )

        self.rest_timer.reset()

        self.status = "Completed"

        return actual_duration_minutes

    def cancel(
        self,
        notes=None
    ):
        if self.status not in {
            "In Progress",
            "Paused"
        }:
            raise ValueError("Workout session cannot be cancelled")

        if self.workout_timer.status in {
            "Running",
            "Paused"
        }:
            self.workout_timer.stop()

        self.rest_timer.reset()

        cancel_workout_session(
            self.workout_session_id,
            notes=notes
        )

        self.status = "Cancelled"

    def get_details(self):
        if self.workout_session_id is None:
            raise ValueError("Workout session has not started")

        return get_workout_session_details(
            self.workout_session_id
        )