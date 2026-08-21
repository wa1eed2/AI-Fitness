from src.workouts.workout_timer import (
    WorkoutTimer,
    RestTimer,
    Stopwatch
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

def test_workout_timer_starts():
    clock = FakeClock()

    timer = WorkoutTimer(
        time_function=clock.time
    )

    timer.start()

    if timer.status != "Running":
        raise ValueError("FAIL: Workout timer did not start")

    if timer.elapsed_seconds() != 0.0:
        raise ValueError("FAIL: New workout timer did not start at zero")

    print("PASS: Workout timer starts correctly")

def test_workout_timer_tracks_elapsed_time():
    clock = FakeClock()

    timer = WorkoutTimer(
        time_function=clock.time
    )

    timer.start()

    clock.advance(
        15
    )

    if timer.elapsed_seconds() != 15.0:
        raise ValueError("FAIL: Workout timer did not track elapsed time")

    clock.advance(
        10
    )

    if timer.elapsed_seconds() != 25.0:
        raise ValueError("FAIL: Workout timer did not continue tracking time")

    print("PASS: Workout timer tracks elapsed time correctly")

def test_workout_timer_pauses():
    clock = FakeClock()

    timer = WorkoutTimer(
        time_function=clock.time
    )

    timer.start()

    clock.advance(
        20
    )

    timer.pause()

    clock.advance(
        30
    )

    if timer.elapsed_seconds() != 20.0:
        raise ValueError("FAIL: Paused workout timer continued counting")

    if timer.status != "Paused":
        raise ValueError("FAIL: Workout timer did not enter Paused status")

    print("PASS: Workout timer pauses correctly")

def test_workout_timer_resumes():
    clock = FakeClock()

    timer = WorkoutTimer(
        time_function=clock.time
    )

    timer.start()

    clock.advance(
        20
    )

    timer.pause()

    clock.advance(
        100
    )

    timer.resume()

    clock.advance(
        15
    )

    if timer.elapsed_seconds() != 35.0:
        raise ValueError("FAIL: Resumed workout timer calculated incorrect elapsed time")

    print("PASS: Workout timer resumes correctly")

def test_workout_timer_stops():
    clock = FakeClock()

    timer = WorkoutTimer(
        time_function=clock.time
    )

    timer.start()

    clock.advance(
        45
    )

    elapsed = timer.stop()

    clock.advance(
        100
    )

    if elapsed != 45.0:
        raise ValueError("FAIL: Stopped workout timer returned incorrect duration")

    if timer.elapsed_seconds() != 45.0:
        raise ValueError("FAIL: Stopped workout timer continued counting")

    if timer.status != "Stopped":
        raise ValueError("FAIL: Workout timer did not enter Stopped status")

    print("PASS: Workout timer stops correctly")

def test_workout_timer_rejects_invalid_actions():
    clock = FakeClock()

    timer = WorkoutTimer(
        time_function=clock.time
    )

    try:
        timer.pause()

    except ValueError:
        pass

    else:
        raise ValueError("FAIL: Workout timer allowed pause before start")

    timer.start()

    try:
        timer.start()

    except ValueError:
        pass

    else:
        raise ValueError("FAIL: Workout timer allowed duplicate start")

    try:
        timer.resume()

    except ValueError:
        pass

    else:
        raise ValueError("FAIL: Running workout timer allowed resume")

    timer.stop()

    try:
        timer.stop()

    except ValueError:
        pass

    else:
        raise ValueError("FAIL: Workout timer allowed duplicate stop")

    print("PASS: Workout timer rejects invalid state changes")

def test_workout_timer_handles_multiple_pause_resume_cycles():
    clock = FakeClock()

    timer = WorkoutTimer(
        time_function=clock.time
    )

    timer.start()

    clock.advance(
        10
    )

    timer.pause()

    clock.advance(
        100
    )

    timer.resume()

    clock.advance(
        20
    )

    timer.pause()

    clock.advance(
        200
    )

    timer.resume()

    clock.advance(
        30
    )

    if timer.elapsed_seconds() != 60.0:
        raise ValueError("FAIL: Multiple pause/resume cycles produced incorrect workout time")

    print("PASS: Workout timer handles multiple pause/resume cycles")


def test_workout_timer_stops_while_paused():
    clock = FakeClock()

    timer = WorkoutTimer(
        time_function=clock.time
    )

    timer.start()

    clock.advance(
        25
    )

    timer.pause()

    clock.advance(
        500
    )

    elapsed = timer.stop()

    if elapsed != 25.0:
        raise ValueError("FAIL: Stopping paused workout timer included paused time")

    if timer.status != "Stopped":
        raise ValueError("FAIL: Paused workout timer did not enter Stopped status")

    print("PASS: Workout timer stops correctly while paused")


def test_workout_timer_rounds_elapsed_time():
    clock = FakeClock()

    timer = WorkoutTimer(
        time_function=clock.time
    )

    timer.start()

    clock.advance(
        1.2345
    )

    if timer.elapsed_seconds() != 1.23:
        raise ValueError("FAIL: Workout timer did not round elapsed time to two decimals")

    print("PASS: Workout timer rounds elapsed time correctly")

def test_rest_timer_starts():
    clock = FakeClock()

    timer = RestTimer(
        time_function=clock.time
    )

    timer.start(
        60
    )

    if timer.status != "Running":
        raise ValueError("FAIL: Rest timer did not start")

    if timer.remaining_seconds() != 60.0:
        raise ValueError("FAIL: Rest timer did not start with correct duration")

    print("PASS: Rest timer starts correctly")

def test_rest_timer_counts_down():
    clock = FakeClock()

    timer = RestTimer(
        time_function=clock.time
    )

    timer.start(
        60
    )

    clock.advance(
        15
    )

    if timer.remaining_seconds() != 45.0:
        raise ValueError("FAIL: Rest timer calculated incorrect remaining time")

    clock.advance(
        20
    )

    if timer.remaining_seconds() != 25.0:
        raise ValueError("FAIL: Rest timer did not continue counting down")

    print("PASS: Rest timer counts down correctly")

def test_rest_timer_finishes():
    clock = FakeClock()

    timer = RestTimer(
        time_function=clock.time
    )

    timer.start(
        30
    )

    clock.advance(
        30
    )

    if timer.remaining_seconds() != 0.0:
        raise ValueError("FAIL: Finished rest timer did not return zero")

    if not timer.is_finished():
        raise ValueError("FAIL: Rest timer did not enter Finished state")

    if timer.status != "Finished":
        raise ValueError("FAIL: Rest timer status was not Finished")

    print("PASS: Rest timer finishes correctly")

def test_rest_timer_does_not_go_negative():
    clock = FakeClock()

    timer = RestTimer(
        time_function=clock.time
    )

    timer.start(
        10
    )

    clock.advance(
        100
    )

    if timer.remaining_seconds() != 0.0:
        raise ValueError("FAIL: Rest timer returned negative remaining time")

    print("PASS: Rest timer does not go below zero")

def test_rest_timer_resets():
    clock = FakeClock()

    timer = RestTimer(
        time_function=clock.time
    )

    timer.start(
        60
    )

    clock.advance(
        20
    )

    timer.reset()

    if timer.status != "Not Started":
        raise ValueError("FAIL: Rest timer did not reset status")

    if timer.remaining_seconds() != 0.0:
        raise ValueError("FAIL: Reset rest timer did not return zero")

    if timer.duration_seconds != 0.0:
        raise ValueError("FAIL: Reset rest timer retained old duration")

    print("PASS: Rest timer resets correctly")

def test_rest_timer_can_restart_after_reset():
    clock = FakeClock()

    timer = RestTimer(
        time_function=clock.time
    )

    timer.start(
        60
    )

    clock.advance(
        10
    )

    timer.reset()

    timer.start(
        90
    )

    if timer.remaining_seconds() != 90.0:
        raise ValueError("FAIL: Rest timer did not restart with new duration")

    print("PASS: Rest timer restarts after reset")

def test_rest_timer_rejects_invalid_duration():
    invalid_values = [
        0,
        -1,
        True,
        "60"
    ]

    for value in invalid_values:
        clock = FakeClock()

        timer = RestTimer(
            time_function=clock.time
        )

        try:
            timer.start(
                value
            )

        except ValueError:
            continue

        raise ValueError(f"FAIL: Invalid rest duration was accepted: {value}")

    print("PASS: Rest timer rejects invalid durations")

def test_rest_timer_rejects_duplicate_start():
    clock = FakeClock()

    timer = RestTimer(
        time_function=clock.time
    )

    timer.start(
        60
    )

    try:
        timer.start(
            90
        )

    except ValueError:
        pass

    else:
        raise ValueError("FAIL: Running rest timer allowed duplicate start")

    print("PASS: Rest timer rejects duplicate start")

def test_rest_timer_pauses():
    clock = FakeClock()

    timer = RestTimer(
        time_function=clock.time
    )

    timer.start(
        60
    )

    clock.advance(
        20
    )

    timer.pause()

    clock.advance(
        100
    )

    if timer.remaining_seconds() != 40.0:
        raise ValueError("FAIL: Paused rest timer continued counting down")

    if timer.status != "Paused":
        raise ValueError("FAIL: Rest timer did not enter Paused status")

    print("PASS: Rest timer pauses correctly")

def test_rest_timer_resumes():
    clock = FakeClock()

    timer = RestTimer(
        time_function=clock.time
    )

    timer.start(
        60
    )

    clock.advance(
        20
    )

    timer.pause()

    clock.advance(
        100
    )

    timer.resume()

    clock.advance(
        15
    )

    if timer.remaining_seconds() != 25.0:
        raise ValueError("FAIL: Resumed rest timer returned incorrect remaining time")

    if timer.status != "Running":
        raise ValueError("FAIL: Rest timer did not return to Running status")

    print("PASS: Rest timer resumes correctly")

def test_rest_timer_rejects_invalid_pause_resume():
    clock = FakeClock()

    timer = RestTimer(
        time_function=clock.time
    )

    try:
        timer.pause()

    except ValueError:
        pass

    else:
        raise ValueError("FAIL: Rest timer allowed pause before start")

    timer.start(
        30
    )

    try:
        timer.resume()

    except ValueError:
        pass

    else:
        raise ValueError("FAIL: Running rest timer allowed resume")

    timer.pause()

    try:
        timer.pause()

    except ValueError:
        pass

    else:
        raise ValueError("FAIL: Paused rest timer allowed duplicate pause")

    print("PASS: Rest timer rejects invalid pause and resume actions")

def test_rest_timer_not_finished_before_boundary():
    clock = FakeClock()

    timer = RestTimer(
        time_function=clock.time
    )

    timer.start(
        60
    )

    clock.advance(
        59.99
    )

    if timer.is_finished():
        raise ValueError("FAIL: Rest timer finished before duration elapsed")

    if timer.remaining_seconds() != 0.01:
        raise ValueError("FAIL: Rest timer boundary remaining time was incorrect")

    print("PASS: Rest timer remains active before finish boundary")


def test_rest_timer_finishes_exactly_at_boundary():
    clock = FakeClock()

    timer = RestTimer(
        time_function=clock.time
    )

    timer.start(
        60
    )

    clock.advance(
        60
    )

    if not timer.is_finished():
        raise ValueError("FAIL: Rest timer did not finish exactly at duration boundary")

    if timer.remaining_seconds() != 0.0:
        raise ValueError("FAIL: Finished rest timer did not return zero")

    print("PASS: Rest timer finishes exactly at duration boundary")


def test_rest_timer_can_restart_after_finishing():
    clock = FakeClock()

    timer = RestTimer(
        time_function=clock.time
    )

    timer.start(
        30
    )

    clock.advance(
        30
    )

    if not timer.is_finished():
        raise ValueError("FAIL: First rest timer did not finish")

    timer.start(
        60
    )

    if timer.status != "Running":
        raise ValueError("FAIL: Finished rest timer could not restart")

    if timer.remaining_seconds() != 60.0:
        raise ValueError("FAIL: Restarted rest timer used incorrect duration")

    print("PASS: Rest timer can restart after finishing")

def test_stopwatch_starts_and_tracks_time():
    clock = FakeClock()

    stopwatch = Stopwatch(
        time_function=clock.time
    )

    stopwatch.start()

    clock.advance(
        12
    )

    if stopwatch.elapsed_seconds() != 12.0:
        raise ValueError("FAIL: Stopwatch did not track elapsed time")

    if stopwatch.status != "Running":
        raise ValueError("FAIL: Stopwatch did not enter Running status")

    print("PASS: Stopwatch starts and tracks time correctly")

def test_stopwatch_pauses():
    clock = FakeClock()

    stopwatch = Stopwatch(
        time_function=clock.time
    )

    stopwatch.start()

    clock.advance(
        20
    )

    stopwatch.pause()

    clock.advance(
        100
    )

    if stopwatch.elapsed_seconds() != 20.0:
        raise ValueError("FAIL: Paused stopwatch continued counting")

    print("PASS: Stopwatch pauses correctly")

def test_stopwatch_resumes():
    clock = FakeClock()

    stopwatch = Stopwatch(
        time_function=clock.time
    )

    stopwatch.start()

    clock.advance(
        10
    )

    stopwatch.pause()

    clock.advance(
        50
    )

    stopwatch.resume()

    clock.advance(
        5
    )

    if stopwatch.elapsed_seconds() != 15.0:
        raise ValueError("FAIL: Resumed stopwatch returned incorrect elapsed time")

    print("PASS: Stopwatch resumes correctly")

def test_stopwatch_stops():
    clock = FakeClock()

    stopwatch = Stopwatch(
        time_function=clock.time
    )

    stopwatch.start()

    clock.advance(
        25
    )

    elapsed = stopwatch.stop()

    clock.advance(
        100
    )

    if elapsed != 25.0:
        raise ValueError("FAIL: Stopwatch returned incorrect stopped duration")

    if stopwatch.elapsed_seconds() != 25.0:
        raise ValueError("FAIL: Stopped stopwatch continued counting")

    if stopwatch.status != "Stopped":
        raise ValueError("FAIL: Stopwatch did not enter Stopped status")

    print("PASS: Stopwatch stops correctly")

def test_stopwatch_resets():
    clock = FakeClock()

    stopwatch = Stopwatch(
        time_function=clock.time
    )

    stopwatch.start()

    clock.advance(
        30
    )

    stopwatch.stop()

    stopwatch.reset()

    if stopwatch.elapsed_seconds() != 0.0:
        raise ValueError("FAIL: Stopwatch reset did not clear elapsed time")

    if stopwatch.status != "Not Started":
        raise ValueError("FAIL: Stopwatch reset did not restore initial status")

    print("PASS: Stopwatch resets correctly")

def test_stopwatch_rejects_invalid_actions():
    clock = FakeClock()

    stopwatch = Stopwatch(
        time_function=clock.time
    )

    try:
        stopwatch.pause()

    except ValueError:
        pass

    else:
        raise ValueError("FAIL: Stopwatch allowed pause before start")

    stopwatch.start()

    try:
        stopwatch.start()

    except ValueError:
        pass

    else:
        raise ValueError("FAIL: Stopwatch allowed duplicate start")

    stopwatch.stop()

    try:
        stopwatch.stop()

    except ValueError:
        pass

    else:
        raise ValueError("FAIL: Stopwatch allowed duplicate stop")

    print("PASS: Stopwatch rejects invalid state changes")

def test_stopwatch_handles_multiple_pause_resume_cycles():
    clock = FakeClock()

    stopwatch = Stopwatch(
        time_function=clock.time
    )

    stopwatch.start()

    clock.advance(
        5
    )

    stopwatch.pause()

    clock.advance(
        100
    )

    stopwatch.resume()

    clock.advance(
        10
    )

    stopwatch.pause()

    clock.advance(
        100
    )

    stopwatch.resume()

    clock.advance(
        15
    )

    if stopwatch.elapsed_seconds() != 30.0:
        raise ValueError("FAIL: Stopwatch multiple pause/resume cycles returned incorrect time")

    print("PASS: Stopwatch handles multiple pause/resume cycles")

if __name__ == "__main__":
    test_workout_timer_starts()
    test_workout_timer_tracks_elapsed_time()
    test_workout_timer_pauses()
    test_workout_timer_resumes()
    test_workout_timer_stops()
    test_workout_timer_rejects_invalid_actions()
    test_workout_timer_handles_multiple_pause_resume_cycles()
    test_workout_timer_stops_while_paused()
    test_workout_timer_rounds_elapsed_time()

    test_rest_timer_starts()
    test_rest_timer_counts_down()
    test_rest_timer_finishes()
    test_rest_timer_does_not_go_negative()
    test_rest_timer_resets()
    test_rest_timer_can_restart_after_reset()
    test_rest_timer_rejects_invalid_duration()
    test_rest_timer_rejects_duplicate_start()
    test_rest_timer_pauses()
    test_rest_timer_resumes()
    test_rest_timer_rejects_invalid_pause_resume()
    test_rest_timer_not_finished_before_boundary()
    test_rest_timer_finishes_exactly_at_boundary()
    test_rest_timer_can_restart_after_finishing()

    test_stopwatch_starts_and_tracks_time()
    test_stopwatch_pauses()
    test_stopwatch_resumes()
    test_stopwatch_stops()
    test_stopwatch_resets()
    test_stopwatch_rejects_invalid_actions()
    test_stopwatch_handles_multiple_pause_resume_cycles()