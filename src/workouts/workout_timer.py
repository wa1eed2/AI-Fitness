import time


class WorkoutTimer:
    def __init__(
        self,
        time_function=None
    ):
        self.time_function = (
            time_function
            or time.monotonic
        )

        self.started_at = None

        self.elapsed_before_start = 0.0

        self.status = "Not Started"


    def start(self):
        if self.status == "Running":
            raise ValueError("Workout timer is already running")

        if self.status == "Paused":
            raise ValueError("Paused workout timer must be resumed")

        self.started_at = self.time_function()

        self.elapsed_before_start = 0.0

        self.status = "Running"


    def elapsed_seconds(self):
        if self.status == "Running":
            current_time = self.time_function()

            elapsed = (
                self.elapsed_before_start
                + (
                    current_time
                    - self.started_at
                )
            )

            return round(
                elapsed,
                2
            )

        return round(
            self.elapsed_before_start,
            2
        )


    def pause(self):
        if self.status != "Running":
            raise ValueError("Workout timer is not running")

        self.elapsed_before_start = self.elapsed_seconds()

        self.started_at = None

        self.status = "Paused"


    def resume(self):
        if self.status != "Paused":
            raise ValueError("Workout timer is not paused")

        self.started_at = self.time_function()

        self.status = "Running"


    def stop(self):
        if self.status not in {
            "Running",
            "Paused"
        }:
            raise ValueError("Workout timer cannot be stopped")

        if self.status == "Running":
            self.elapsed_before_start = self.elapsed_seconds()

        self.started_at = None

        self.status = "Stopped"

        return self.elapsed_before_start

class RestTimer:
    def __init__(
        self,
        time_function=None
    ):
        self.time_function = (
            time_function
            or time.monotonic
        )

        self.duration_seconds = 0.0

        self.started_at = None

        self.remaining_before_resume = 0.0

        self.status = "Not Started"


    def start(
        self,
        duration_seconds
    ):
        if isinstance(duration_seconds, bool) or not isinstance(duration_seconds, (int, float)):
            raise ValueError("Rest duration must be a number")

        if duration_seconds <= 0:
            raise ValueError("Rest duration must be greater than 0")

        if self.status == "Running":
            raise ValueError("Rest timer is already running")

        if self.status == "Paused":
            raise ValueError("Paused rest timer must be resumed")

        self.duration_seconds = float(
            duration_seconds
        )

        self.remaining_before_resume = self.duration_seconds

        self.started_at = self.time_function()

        self.status = "Running"


    def remaining_seconds(self):
        if self.status == "Not Started":
            return 0.0

        if self.status == "Finished":
            return 0.0

        if self.status == "Paused":
            return round(
                self.remaining_before_resume,
                2
            )

        elapsed = (
            self.time_function()
            - self.started_at
        )

        remaining = (
            self.remaining_before_resume
            - elapsed
        )

        if remaining <= 0:
            self.remaining_before_resume = 0.0

            self.started_at = None

            self.status = "Finished"

            return 0.0

        return round(
            remaining,
            2
        )


    def pause(self):
        if self.status != "Running":
            raise ValueError("Rest timer is not running")

        self.remaining_before_resume = self.remaining_seconds()

        if self.status == "Finished":
            raise ValueError("Finished rest timer cannot be paused")

        self.started_at = None

        self.status = "Paused"


    def resume(self):
        if self.status != "Paused":
            raise ValueError("Rest timer is not paused")

        self.started_at = self.time_function()

        self.status = "Running"


    def is_finished(self):
        self.remaining_seconds()

        return self.status == "Finished"


    def reset(self):
        self.duration_seconds = 0.0

        self.started_at = None

        self.remaining_before_resume = 0.0

        self.status = "Not Started"

class Stopwatch:
    def __init__(
        self,
        time_function=None
    ):
        self.time_function = (
            time_function
            or time.monotonic
        )

        self.started_at = None

        self.elapsed_before_start = 0.0

        self.status = "Not Started"


    def start(self):
        if self.status == "Running":
            raise ValueError("Stopwatch is already running")

        if self.status == "Paused":
            raise ValueError("Paused stopwatch must be resumed")

        self.started_at = self.time_function()

        self.elapsed_before_start = 0.0

        self.status = "Running"


    def elapsed_seconds(self):
        if self.status == "Running":
            elapsed = (
                self.elapsed_before_start
                + (
                    self.time_function()
                    - self.started_at
                )
            )

            return round(
                elapsed,
                2
            )

        return round(
            self.elapsed_before_start,
            2
        )


    def pause(self):
        if self.status != "Running":
            raise ValueError("Stopwatch is not running")

        self.elapsed_before_start = self.elapsed_seconds()

        self.started_at = None

        self.status = "Paused"


    def resume(self):
        if self.status != "Paused":
            raise ValueError("Stopwatch is not paused")

        self.started_at = self.time_function()

        self.status = "Running"


    def stop(self):
        if self.status not in {
            "Running",
            "Paused"
        }:
            raise ValueError("Stopwatch cannot be stopped")

        if self.status == "Running":
            self.elapsed_before_start = self.elapsed_seconds()

        self.started_at = None

        self.status = "Stopped"

        return self.elapsed_before_start


    def reset(self):
        self.started_at = None

        self.elapsed_before_start = 0.0

        self.status = "Not Started"