import sqlite3

from src.database.setup_workout_log_database import (
    DATABASE_PATH,
    setup_workout_log_database
)

from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.database.query_workout_log_database import (
    get_connection,
    start_workout_session,
    add_workout_session_exercise,
    log_workout_set,
    update_workout_set,
    delete_workout_set,
    mark_session_exercise_complete,
    mark_session_exercise_incomplete,
    finish_workout_session,
    cancel_workout_session,
    get_workout_session,
    get_workout_session_exercises,
    get_workout_set_logs,
    get_workout_session_details,
    get_user_workout_history,
    get_active_workout_session,
    get_workout_progress,
    delete_workout_session,
    start_workout_from_plan
)


def create_basic_workout(
    primary_goal="General Fitness",
    planned_duration_minutes=60,
    exercise_id="E001"
):
    user_id = create_user()

    workout_session_id = start_workout_session(
        user_id,
        primary_goal=primary_goal,
        planned_duration_minutes=planned_duration_minutes
    )

    session_exercise_id = add_workout_session_exercise(
        workout_session_id,
        exercise_id,
        1,
        planned_sets=3,
        planned_reps="8-12",
        planned_rest_seconds=60
    )

    return (
        user_id,
        workout_session_id,
        session_exercise_id
    )


def test_workout_log_tables_exist():
    setup_workout_log_database()

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        expected_tables = {
            "workout_sessions",
            "workout_session_exercises",
            "workout_set_logs"
        }

        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

        existing_tables = {
            row[0]
            for row in rows
        }

        if not expected_tables.issubset(existing_tables):
            raise ValueError("FAIL: One or more workout log tables are missing")

        print("PASS: Workout log tables exist")

    finally:
        connection.close()


def test_workout_log_indexes_exist():
    setup_workout_log_database()

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        expected_indexes = {
            "idx_workout_sessions_user_id",
            "idx_workout_sessions_status",
            "idx_workout_session_exercises_session_id",
            "idx_workout_set_logs_session_exercise_id"
        }

        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'index'
            """
        ).fetchall()

        existing_indexes = {
            row[0]
            for row in rows
        }

        if not expected_indexes.issubset(existing_indexes):
            raise ValueError("FAIL: One or more workout log indexes are missing")

        print("PASS: Workout log indexes exist")

    finally:
        connection.close()


def test_workout_sessions_foreign_key_exists():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        rows = connection.execute(
            """
            PRAGMA foreign_key_list(workout_sessions)
            """
        ).fetchall()

        references_users = any(
            row[2] == "users"
            and row[3] == "user_id"
            and row[4] == "user_id"
            and row[6] == "CASCADE"
            for row in rows
        )

        if not references_users:
            raise ValueError("FAIL: workout_sessions user foreign key is missing")

        print("PASS: Workout sessions user foreign key exists")

    finally:
        connection.close()


def test_session_exercise_foreign_keys_exist():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        rows = connection.execute(
            """
            PRAGMA foreign_key_list(workout_session_exercises)
            """
        ).fetchall()

        tables = {
            row[2]
            for row in rows
        }

        if "workout_sessions" not in tables:
            raise ValueError("FAIL: Session exercise workout foreign key is missing")

        if "exercises" not in tables:
            raise ValueError("FAIL: Session exercise exercise foreign key is missing")

        print("PASS: Session exercise foreign keys exist")

    finally:
        connection.close()


def test_set_log_foreign_key_exists():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        rows = connection.execute(
            """
            PRAGMA foreign_key_list(workout_set_logs)
            """
        ).fetchall()

        references_session_exercises = any(
            row[2] == "workout_session_exercises"
            and row[6] == "CASCADE"
            for row in rows
        )

        if not references_session_exercises:
            raise ValueError("FAIL: Set-log session-exercise foreign key is missing")

        print("PASS: Set-log foreign key exists")

    finally:
        connection.close()


def test_query_connection_enables_foreign_keys():
    connection = get_connection()

    try:
        enabled = connection.execute(
            """
            PRAGMA foreign_keys
            """
        ).fetchone()[0]

        if enabled != 1:
            raise ValueError("FAIL: Query connection did not enable foreign keys")

        print("PASS: Query connection enables foreign keys")

    finally:
        connection.close()


def test_invalid_workout_status_rejected():
    user_id = create_user()

    connection = get_connection()

    try:
        try:
            connection.execute(
                """
                INSERT INTO workout_sessions (
                    user_id,
                    status
                )
                VALUES (?, ?)
                """,
                (
                    user_id,
                    "Invalid Status"
                )
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.rollback()

        else:
            raise ValueError("FAIL: Invalid workout status was accepted")

        print("PASS: Invalid workout status rejected")

    finally:
        connection.close()
        delete_user(user_id)


def test_duplicate_exercise_order_rejected():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            add_workout_session_exercise(
                workout_session_id,
                "E006",
                1
            )

        except sqlite3.IntegrityError:
            pass

        else:
            raise ValueError("FAIL: Duplicate exercise order was accepted")

        print("PASS: Duplicate exercise order rejected")

    finally:
        delete_user(user_id)


def test_invalid_completed_flag_rejected():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    connection = get_connection()

    try:
        try:
            connection.execute(
                """
                UPDATE workout_session_exercises
                SET completed = 2
                WHERE session_exercise_id = ?
                """,
                (
                    session_exercise_id,
                )
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.rollback()

        else:
            raise ValueError("FAIL: Invalid completed flag was accepted")

        print("PASS: Invalid completed flag rejected")

    finally:
        connection.close()
        delete_user(user_id)


def test_duplicate_set_number_rejected():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        log_workout_set(
            session_exercise_id,
            1,
            reps_completed=10
        )

        try:
            log_workout_set(
                session_exercise_id,
                1,
                reps_completed=8
            )

        except sqlite3.IntegrityError:
            pass

        else:
            raise ValueError("FAIL: Duplicate set number was accepted")

        print("PASS: Duplicate set number rejected")

    finally:
        delete_user(user_id)


def test_user_delete_cascades_workout_data():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    set_log_id = log_workout_set(
        session_exercise_id,
        1,
        reps_completed=10
    )

    delete_user(
        user_id
    )

    connection = get_connection()

    try:
        session_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM workout_sessions
            WHERE workout_session_id = ?
            """,
            (
                workout_session_id,
            )
        ).fetchone()[0]

        exercise_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM workout_session_exercises
            WHERE session_exercise_id = ?
            """,
            (
                session_exercise_id,
            )
        ).fetchone()[0]

        set_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM workout_set_logs
            WHERE set_log_id = ?
            """,
            (
                set_log_id,
            )
        ).fetchone()[0]

        if session_count != 0:
            raise ValueError("FAIL: User deletion did not remove workout session")

        if exercise_count != 0:
            raise ValueError("FAIL: User deletion did not remove session exercise")

        if set_count != 0:
            raise ValueError("FAIL: User deletion did not remove set log")

        print("PASS: User deletion cascades through workout data")

    finally:
        connection.close()


def test_start_workout_session_returns_id():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        if not isinstance(workout_session_id, int):
            raise ValueError("FAIL: Workout session ID is not an integer")

        if workout_session_id <= 0:
            raise ValueError("FAIL: Workout session ID is not positive")

        print("PASS: Starting workout returns workout session ID")

    finally:
        delete_user(user_id)


def test_start_workout_session_uses_default_status():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        session = get_workout_session(
            workout_session_id
        )

        if session["status"] != "In Progress":
            raise ValueError("FAIL: New workout did not start In Progress")

        if session["started_at"] is None:
            raise ValueError("FAIL: New workout did not receive start timestamp")

        if session["completed_at"] is not None:
            raise ValueError("FAIL: New workout incorrectly received completion timestamp")

        print("PASS: New workout uses correct default status and timestamps")

    finally:
        delete_user(user_id)


def test_start_workout_session_saves_optional_fields():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id,
            primary_goal="Strength",
            planned_duration_minutes=75,
            notes="Test workout"
        )

        session = get_workout_session(
            workout_session_id
        )

        if session["primary_goal"] != "Strength":
            raise ValueError("FAIL: Workout primary goal was not saved")

        if session["planned_duration_minutes"] != 75:
            raise ValueError("FAIL: Planned duration was not saved")

        if session["notes"] != "Test workout":
            raise ValueError("FAIL: Workout notes were not saved")

        print("PASS: Workout optional start fields saved correctly")

    finally:
        delete_user(user_id)


def test_second_active_workout_rejected():
    user_id = create_user()

    try:
        start_workout_session(
            user_id
        )

        try:
            start_workout_session(
                user_id
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Second active workout was accepted")

        print("PASS: Second active workout rejected")

    finally:
        delete_user(user_id)


def test_new_workout_allowed_after_completion():
    user_id = create_user()

    try:
        first_session_id = start_workout_session(
            user_id
        )

        finish_workout_session(
            first_session_id,
            actual_duration_minutes=30
        )

        second_session_id = start_workout_session(
            user_id
        )

        if second_session_id == first_session_id:
            raise ValueError("FAIL: New workout session ID was not created")

        print("PASS: New workout allowed after completion")

    finally:
        delete_user(user_id)


def test_new_workout_allowed_after_cancellation():
    user_id = create_user()

    try:
        first_session_id = start_workout_session(
            user_id
        )

        cancel_workout_session(
            first_session_id
        )

        second_session_id = start_workout_session(
            user_id
        )

        if second_session_id == first_session_id:
            raise ValueError("FAIL: New workout session ID was not created after cancellation")

        print("PASS: New workout allowed after cancellation")

    finally:
        delete_user(user_id)


def test_start_workout_rejects_missing_user():
    try:
        start_workout_session(
            999999999
        )

    except sqlite3.IntegrityError:
        print("PASS: Missing user rejected when starting workout")

    else:
        raise ValueError("FAIL: Workout started for missing user")


def test_add_session_exercise_returns_id():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        session_exercise_id = add_workout_session_exercise(
            workout_session_id,
            "E001",
            1
        )

        if not isinstance(session_exercise_id, int):
            raise ValueError("FAIL: Session exercise ID is not an integer")

        if session_exercise_id <= 0:
            raise ValueError("FAIL: Session exercise ID is not positive")

        print("PASS: Adding session exercise returns ID")

    finally:
        delete_user(user_id)


def test_add_session_exercise_saves_planned_fields():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        session_exercise_id = add_workout_session_exercise(
            workout_session_id,
            "E001",
            1,
            planned_sets=4,
            planned_reps="4-6",
            planned_rest_seconds=180,
            planned_duration_minutes=None
        )

        exercises = get_workout_session_exercises(
            workout_session_id
        )

        exercise = exercises[0]

        if exercise["session_exercise_id"] != session_exercise_id:
            raise ValueError("FAIL: Saved session exercise ID was incorrect")

        if exercise["planned_sets"] != 4:
            raise ValueError("FAIL: Planned sets were not saved")

        if exercise["planned_reps"] != "4-6":
            raise ValueError("FAIL: Planned reps were not saved")

        if exercise["planned_rest_seconds"] != 180:
            raise ValueError("FAIL: Planned rest was not saved")

        if exercise["completed"] != 0:
            raise ValueError("FAIL: New exercise did not default to incomplete")

        print("PASS: Planned exercise fields saved correctly")

    finally:
        delete_user(user_id)


def test_add_duration_based_session_exercise():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id,
            primary_goal="Endurance"
        )

        add_workout_session_exercise(
            workout_session_id,
            "E006",
            1,
            planned_duration_minutes=10
        )

        exercises = get_workout_session_exercises(
            workout_session_id
        )

        if exercises[0]["planned_duration_minutes"] != 10:
            raise ValueError("FAIL: Duration-based exercise duration was not saved")

        if exercises[0]["planned_sets"] is not None:
            raise ValueError("FAIL: Duration-based exercise unexpectedly has planned sets")

        print("PASS: Duration-based session exercise saved correctly")

    finally:
        delete_user(user_id)


def test_add_session_exercise_rejects_missing_workout():
    try:
        add_workout_session_exercise(
            999999999,
            "E001",
            1
        )

    except ValueError:
        print("PASS: Missing workout rejected when adding exercise")

    else:
        raise ValueError("FAIL: Exercise added to missing workout")


def test_add_session_exercise_rejects_missing_exercise():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        try:
            add_workout_session_exercise(
                workout_session_id,
                "DOES_NOT_EXIST",
                1
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Missing exercise was accepted")

        print("PASS: Missing exercise rejected")

    finally:
        delete_user(user_id)


def test_add_exercise_rejected_after_workout_completion():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        finish_workout_session(
            workout_session_id
        )

        try:
            add_workout_session_exercise(
                workout_session_id,
                "E001",
                1
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Exercise added after workout completion")

        print("PASS: Exercise rejected after workout completion")

    finally:
        delete_user(user_id)


def test_log_workout_set_returns_id():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        set_log_id = log_workout_set(
            session_exercise_id,
            1,
            reps_completed=10
        )

        if not isinstance(set_log_id, int):
            raise ValueError("FAIL: Set-log ID is not an integer")

        if set_log_id <= 0:
            raise ValueError("FAIL: Set-log ID is not positive")

        print("PASS: Logging workout set returns ID")

    finally:
        delete_user(user_id)


def test_log_workout_set_saves_all_fields():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        set_log_id = log_workout_set(
            session_exercise_id,
            1,
            reps_completed=8,
            weight_kg=80.5,
            duration_seconds=42.5,
            rir_actual=2,
            rpe_actual=8.0
        )

        logs = get_workout_set_logs(
            session_exercise_id
        )

        log = logs[0]

        if log["set_log_id"] != set_log_id:
            raise ValueError("FAIL: Set-log ID was not saved correctly")

        if log["reps_completed"] != 8:
            raise ValueError("FAIL: Completed reps were not saved")

        if log["weight_kg"] != 80.5:
            raise ValueError("FAIL: Weight was not saved")

        if log["duration_seconds"] != 42.5:
            raise ValueError("FAIL: Set duration was not saved")

        if log["rir_actual"] != 2:
            raise ValueError("FAIL: RIR was not saved")

        if log["rpe_actual"] != 8.0:
            raise ValueError("FAIL: RPE was not saved")

        if log["completed_at"] is None:
            raise ValueError("FAIL: Set did not receive completed timestamp")

        print("PASS: Workout set saves all actual-performance fields")

    finally:
        delete_user(user_id)


def test_log_duration_only_set():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id,
            primary_goal="Endurance"
        )

        session_exercise_id = add_workout_session_exercise(
            workout_session_id,
            "E006",
            1,
            planned_duration_minutes=10
        )

        log_workout_set(
            session_exercise_id,
            1,
            duration_seconds=600
        )

        logs = get_workout_set_logs(
            session_exercise_id
        )

        if logs[0]["duration_seconds"] != 600:
            raise ValueError("FAIL: Duration-only log did not save duration")

        if logs[0]["reps_completed"] is not None:
            raise ValueError("FAIL: Duration-only log unexpectedly has reps")

        print("PASS: Duration-only workout set logged correctly")

    finally:
        delete_user(user_id)


def test_log_set_rejects_missing_session_exercise():
    try:
        log_workout_set(
            999999999,
            1,
            reps_completed=10
        )

    except ValueError:
        print("PASS: Missing session exercise rejected when logging set")

    else:
        raise ValueError("FAIL: Set logged for missing session exercise")


def test_log_set_rejected_after_workout_completion():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        finish_workout_session(
            workout_session_id
        )

        try:
            log_workout_set(
                session_exercise_id,
                1,
                reps_completed=10
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Set logged after workout completion")

        print("PASS: Set rejected after workout completion")

    finally:
        delete_user(user_id)


def test_update_workout_set():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        set_log_id = log_workout_set(
            session_exercise_id,
            1,
            reps_completed=8,
            weight_kg=60
        )

        update_workout_set(
            set_log_id,
            reps_completed=10,
            weight_kg=62.5,
            duration_seconds=45,
            rir_actual=1,
            rpe_actual=9
        )

        logs = get_workout_set_logs(
            session_exercise_id
        )

        log = logs[0]

        if log["reps_completed"] != 10:
            raise ValueError("FAIL: Updated reps were not saved")

        if log["weight_kg"] != 62.5:
            raise ValueError("FAIL: Updated weight was not saved")

        if log["rir_actual"] != 1:
            raise ValueError("FAIL: Updated RIR was not saved")

        if log["rpe_actual"] != 9:
            raise ValueError("FAIL: Updated RPE was not saved")

        print("PASS: Workout set updates correctly")

    finally:
        delete_user(user_id)


def test_update_missing_workout_set_rejected():
    try:
        update_workout_set(
            999999999,
            reps_completed=10
        )

    except ValueError:
        print("PASS: Missing workout set rejected during update")

    else:
        raise ValueError("FAIL: Missing workout set update was accepted")


def test_update_set_rejected_after_workout_completion():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        set_log_id = log_workout_set(
            session_exercise_id,
            1,
            reps_completed=8
        )

        finish_workout_session(
            workout_session_id
        )

        try:
            update_workout_set(
                set_log_id,
                reps_completed=10
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Completed-workout set was updated")

        print("PASS: Set update rejected after workout completion")

    finally:
        delete_user(user_id)


def test_delete_workout_set():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        set_log_id = log_workout_set(
            session_exercise_id,
            1,
            reps_completed=10
        )

        delete_workout_set(
            set_log_id
        )

        logs = get_workout_set_logs(
            session_exercise_id
        )

        if logs:
            raise ValueError("FAIL: Workout set was not deleted")

        print("PASS: Workout set deletes correctly")

    finally:
        delete_user(user_id)


def test_delete_missing_workout_set_rejected():
    try:
        delete_workout_set(
            999999999
        )

    except ValueError:
        print("PASS: Missing workout set rejected during deletion")

    else:
        raise ValueError("FAIL: Missing workout set deletion was accepted")


def test_delete_set_rejected_after_workout_completion():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        set_log_id = log_workout_set(
            session_exercise_id,
            1,
            reps_completed=10
        )

        finish_workout_session(
            workout_session_id
        )

        try:
            delete_workout_set(
                set_log_id
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Completed-workout set was deleted")

        print("PASS: Set deletion rejected after workout completion")

    finally:
        delete_user(user_id)


def test_mark_session_exercise_complete():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        mark_session_exercise_complete(
            session_exercise_id
        )

        exercises = get_workout_session_exercises(
            workout_session_id
        )

        if exercises[0]["completed"] != 1:
            raise ValueError("FAIL: Session exercise was not marked complete")

        print("PASS: Session exercise marked complete")

    finally:
        delete_user(user_id)


def test_mark_session_exercise_incomplete():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        mark_session_exercise_complete(
            session_exercise_id
        )

        mark_session_exercise_incomplete(
            session_exercise_id
        )

        exercises = get_workout_session_exercises(
            workout_session_id
        )

        if exercises[0]["completed"] != 0:
            raise ValueError("FAIL: Session exercise was not marked incomplete")

        print("PASS: Session exercise marked incomplete")

    finally:
        delete_user(user_id)


def test_mark_missing_session_exercise_rejected():
    try:
        mark_session_exercise_complete(
            999999999
        )

    except ValueError:
        print("PASS: Missing session exercise rejected during completion")

    else:
        raise ValueError("FAIL: Missing session exercise was marked complete")


def test_mark_exercise_rejected_after_workout_completion():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        finish_workout_session(
            workout_session_id
        )

        try:
            mark_session_exercise_complete(
                session_exercise_id
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Exercise completion changed after workout completion")

        print("PASS: Exercise completion change rejected after workout completion")

    finally:
        delete_user(user_id)


def test_finish_workout_session():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        finish_workout_session(
            workout_session_id,
            actual_duration_minutes=52.5,
            notes="Strong session"
        )

        session = get_workout_session(
            workout_session_id
        )

        if session["status"] != "Completed":
            raise ValueError("FAIL: Workout status did not become Completed")

        if session["completed_at"] is None:
            raise ValueError("FAIL: Completed workout has no completion timestamp")

        if session["actual_duration_minutes"] != 52.5:
            raise ValueError("FAIL: Actual workout duration was not saved")

        if session["notes"] != "Strong session":
            raise ValueError("FAIL: Completion notes were not saved")

        print("PASS: Workout session finishes correctly")

    finally:
        delete_user(user_id)


def test_finish_missing_workout_rejected():
    try:
        finish_workout_session(
            999999999
        )

    except ValueError:
        print("PASS: Missing workout rejected during finish")

    else:
        raise ValueError("FAIL: Missing workout was finished")


def test_finish_workout_twice_rejected():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        finish_workout_session(
            workout_session_id
        )

        try:
            finish_workout_session(
                workout_session_id
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Completed workout was finished twice")

        print("PASS: Finishing workout twice is rejected")

    finally:
        delete_user(user_id)


def test_cancel_workout_session():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        cancel_workout_session(
            workout_session_id,
            notes="Stopped early"
        )

        session = get_workout_session(
            workout_session_id
        )

        if session["status"] != "Cancelled":
            raise ValueError("FAIL: Workout status did not become Cancelled")

        if session["completed_at"] is None:
            raise ValueError("FAIL: Cancelled workout has no end timestamp")

        if session["notes"] != "Stopped early":
            raise ValueError("FAIL: Cancellation notes were not saved")

        print("PASS: Workout session cancels correctly")

    finally:
        delete_user(user_id)


def test_cancel_missing_workout_rejected():
    try:
        cancel_workout_session(
            999999999
        )

    except ValueError:
        print("PASS: Missing workout rejected during cancellation")

    else:
        raise ValueError("FAIL: Missing workout was cancelled")


def test_cancel_completed_workout_rejected():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        finish_workout_session(
            workout_session_id
        )

        try:
            cancel_workout_session(
                workout_session_id
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Completed workout was cancelled")

        print("PASS: Completed workout cannot be cancelled")

    finally:
        delete_user(user_id)


def test_get_workout_session():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id,
            primary_goal="Strength",
            planned_duration_minutes=60
        )

        session = get_workout_session(
            workout_session_id
        )

        if session is None:
            raise ValueError("FAIL: Saved workout session was not returned")

        if session["workout_session_id"] != workout_session_id:
            raise ValueError("FAIL: Returned workout session ID was incorrect")

        if session["user_id"] != user_id:
            raise ValueError("FAIL: Returned workout user ID was incorrect")

        print("PASS: Workout session retrieval works")

    finally:
        delete_user(user_id)


def test_get_missing_workout_session_returns_none():
    session = get_workout_session(
        999999999
    )

    if session is not None:
        raise ValueError("FAIL: Missing workout session did not return None")

    print("PASS: Missing workout session returns None")


def test_get_session_exercises_ordered():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        add_workout_session_exercise(
            workout_session_id,
            "E006",
            2
        )

        add_workout_session_exercise(
            workout_session_id,
            "E001",
            1
        )

        exercises = get_workout_session_exercises(
            workout_session_id
        )

        orders = [
            exercise["exercise_order"]
            for exercise in exercises
        ]

        if orders != [1, 2]:
            raise ValueError("FAIL: Session exercises were not returned in order")

        print("PASS: Session exercises returned in exercise order")

    finally:
        delete_user(user_id)


def test_get_set_logs_ordered():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        log_workout_set(
            session_exercise_id,
            2,
            reps_completed=8
        )

        log_workout_set(
            session_exercise_id,
            1,
            reps_completed=10
        )

        logs = get_workout_set_logs(
            session_exercise_id
        )

        set_numbers = [
            log["set_number"]
            for log in logs
        ]

        if set_numbers != [1, 2]:
            raise ValueError("FAIL: Set logs were not returned by set number")

        print("PASS: Set logs returned in set-number order")

    finally:
        delete_user(user_id)


def test_get_workout_session_details():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        log_workout_set(
            session_exercise_id,
            1,
            reps_completed=10
        )

        log_workout_set(
            session_exercise_id,
            2,
            reps_completed=8
        )

        details = get_workout_session_details(
            workout_session_id
        )

        if details["workout_session_id"] != workout_session_id:
            raise ValueError("FAIL: Workout details session ID was incorrect")

        if len(details["exercises"]) != 1:
            raise ValueError("FAIL: Workout details exercise count was incorrect")

        if len(details["exercises"][0]["sets"]) != 2:
            raise ValueError("FAIL: Workout details did not include nested set logs")

        print("PASS: Workout session details include nested exercises and sets")

    finally:
        delete_user(user_id)


def test_get_missing_workout_details_returns_none():
    details = get_workout_session_details(
        999999999
    )

    if details is not None:
        raise ValueError("FAIL: Missing workout details did not return None")

    print("PASS: Missing workout details return None")


def test_user_workout_history_returns_newest_first():
    user_id = create_user()

    try:
        first_session_id = start_workout_session(
            user_id
        )

        finish_workout_session(
            first_session_id
        )

        second_session_id = start_workout_session(
            user_id
        )

        finish_workout_session(
            second_session_id
        )

        history = get_user_workout_history(
            user_id
        )

        history_ids = [
            session["workout_session_id"]
            for session in history
        ]

        if history_ids[:2] != [
            second_session_id,
            first_session_id
        ]:
            raise ValueError("FAIL: Workout history is not newest first")

        print("PASS: Workout history returns newest sessions first")

    finally:
        delete_user(user_id)


def test_user_workout_history_filters_status():
    user_id = create_user()

    try:
        completed_id = start_workout_session(
            user_id
        )

        finish_workout_session(
            completed_id
        )

        cancelled_id = start_workout_session(
            user_id
        )

        cancel_workout_session(
            cancelled_id
        )

        history = get_user_workout_history(
            user_id,
            status="Completed"
        )

        if len(history) != 1:
            raise ValueError("FAIL: Completed-history filter returned wrong count")

        if history[0]["status"] != "Completed":
            raise ValueError("FAIL: History status filter returned wrong status")

        print("PASS: Workout history filters by status")

    finally:
        delete_user(user_id)


def test_user_workout_history_applies_limit():
    user_id = create_user()

    try:
        for _ in range(3):
            workout_session_id = start_workout_session(
                user_id
            )

            finish_workout_session(
                workout_session_id
            )

        history = get_user_workout_history(
            user_id,
            limit=2
        )

        if len(history) != 2:
            raise ValueError("FAIL: Workout-history limit was not applied")

        print("PASS: Workout history applies result limit")

    finally:
        delete_user(user_id)


def test_user_workout_history_rejects_invalid_status():
    user_id = create_user()

    try:
        try:
            get_user_workout_history(
                user_id,
                status="Unknown"
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Invalid workout-history status was accepted")

        print("PASS: Workout history rejects invalid status")

    finally:
        delete_user(user_id)


def test_user_workout_history_is_user_specific():
    user_one = create_user()
    user_two = create_user()

    try:
        user_one_session = start_workout_session(
            user_one
        )

        finish_workout_session(
            user_one_session
        )

        user_two_session = start_workout_session(
            user_two
        )

        finish_workout_session(
            user_two_session
        )

        history = get_user_workout_history(
            user_one
        )

        history_ids = {
            session["workout_session_id"]
            for session in history
        }

        if user_two_session in history_ids:
            raise ValueError("FAIL: Another user's workout appeared in history")

        if user_one_session not in history_ids:
            raise ValueError("FAIL: User's own workout missing from history")

        print("PASS: Workout history is isolated by user")

    finally:
        delete_user(user_one)
        delete_user(user_two)


def test_get_active_workout_session():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        active = get_active_workout_session(
            user_id
        )

        if active is None:
            raise ValueError("FAIL: Active workout was not returned")

        if active["workout_session_id"] != workout_session_id:
            raise ValueError("FAIL: Wrong active workout returned")

        print("PASS: Active workout session retrieval works")

    finally:
        delete_user(user_id)

def test_get_active_workout_returns_none_after_completion():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        finish_workout_session(
            workout_session_id
        )

        active = get_active_workout_session(
            user_id
        )

        if active is not None:
            raise ValueError("FAIL: Completed workout still appears active")

        print("PASS: No active workout returned after completion")

    finally:
        delete_user(user_id)


def test_workout_progress_empty_session():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        progress = get_workout_progress(
            workout_session_id
        )

        if progress["total_exercises"] != 0:
            raise ValueError("FAIL: Empty workout has nonzero total exercises")

        if progress["completed_exercises"] != 0:
            raise ValueError("FAIL: Empty workout has completed exercises")

        if progress["logged_sets"] != 0:
            raise ValueError("FAIL: Empty workout has logged sets")

        if progress["completion_percentage"] != 0.0:
            raise ValueError("FAIL: Empty workout completion is not 0 percent")

        print("PASS: Empty workout progress calculated correctly")

    finally:
        delete_user(user_id)


def test_workout_progress_partial_completion():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        first_exercise_id = add_workout_session_exercise(
            workout_session_id,
            "E001",
            1
        )

        second_exercise_id = add_workout_session_exercise(
            workout_session_id,
            "E006",
            2
        )

        log_workout_set(
            first_exercise_id,
            1,
            reps_completed=10
        )

        mark_session_exercise_complete(
            first_exercise_id
        )

        progress = get_workout_progress(
            workout_session_id
        )

        if progress["total_exercises"] != 2:
            raise ValueError("FAIL: Progress total exercise count was incorrect")

        if progress["completed_exercises"] != 1:
            raise ValueError("FAIL: Progress completed exercise count was incorrect")

        if progress["logged_sets"] != 1:
            raise ValueError("FAIL: Progress logged set count was incorrect")

        if progress["completion_percentage"] != 50.0:
            raise ValueError("FAIL: Progress completion percentage was incorrect")

        print("PASS: Partial workout progress calculated correctly")

    finally:
        delete_user(user_id)


def test_workout_progress_complete():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        session_exercise_id = add_workout_session_exercise(
            workout_session_id,
            "E001",
            1
        )

        mark_session_exercise_complete(
            session_exercise_id
        )

        progress = get_workout_progress(
            workout_session_id
        )

        if progress["completion_percentage"] != 100.0:
            raise ValueError("FAIL: Completed workout progress is not 100 percent")

        print("PASS: Complete workout progress calculated correctly")

    finally:
        delete_user(user_id)


def test_workout_progress_rejects_missing_session():
    try:
        get_workout_progress(
            999999999
        )

    except ValueError:
        print("PASS: Missing workout rejected during progress calculation")

    else:
        raise ValueError("FAIL: Progress calculated for missing workout")


def test_delete_workout_session_cascades():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    set_log_id = log_workout_set(
        session_exercise_id,
        1,
        reps_completed=10
    )

    try:
        delete_workout_session(
            workout_session_id
        )

        connection = get_connection()

        try:
            exercise_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM workout_session_exercises
                WHERE session_exercise_id = ?
                """,
                (
                    session_exercise_id,
                )
            ).fetchone()[0]

            set_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM workout_set_logs
                WHERE set_log_id = ?
                """,
                (
                    set_log_id,
                )
            ).fetchone()[0]

            if exercise_count != 0:
                raise ValueError("FAIL: Session deletion did not cascade to exercises")

            if set_count != 0:
                raise ValueError("FAIL: Session deletion did not cascade to set logs")

        finally:
            connection.close()

        print("PASS: Workout session deletion cascades correctly")

    finally:
        delete_user(user_id)


def test_delete_missing_workout_session_rejected():
    try:
        delete_workout_session(
            999999999
        )

    except ValueError:
        print("PASS: Missing workout rejected during deletion")

    else:
        raise ValueError("FAIL: Missing workout deletion was accepted")


def test_start_workout_from_plan():
    user_id = create_user()

    try:
        plan = {
            "primary_goal": "General Fitness",
            "session_duration_minutes": 60,
            "exercises": [
                {
                    "exercise_id": "E001",
                    "order": 1,
                    "sets": 3,
                    "reps": "8-12",
                    "rest_seconds": 60,
                    "duration_minutes": None
                },
                {
                    "exercise_id": "E006",
                    "order": 2,
                    "sets": None,
                    "reps": None,
                    "rest_seconds": 0,
                    "duration_minutes": 10
                }
            ]
        }

        workout_session_id = start_workout_from_plan(
            user_id,
            plan
        )

        session = get_workout_session(
            workout_session_id
        )

        exercises = get_workout_session_exercises(
            workout_session_id
        )

        if session["primary_goal"] != "General Fitness":
            raise ValueError("FAIL: Workout plan primary goal was not copied")

        if session["planned_duration_minutes"] != 60:
            raise ValueError("FAIL: Workout plan duration was not copied")

        if len(exercises) != 2:
            raise ValueError("FAIL: Workout plan exercises were not copied")

        if exercises[0]["planned_sets"] != 3:
            raise ValueError("FAIL: Sets/reps exercise prescription was not copied")

        if exercises[1]["planned_duration_minutes"] != 10:
            raise ValueError("FAIL: Duration-based prescription was not copied")

        print("PASS: Workout can start directly from recommendation plan")

    finally:
        delete_user(user_id)


def test_start_workout_from_plan_uses_default_order():
    user_id = create_user()

    try:
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
                    "duration_minutes": 5
                }
            ]
        }

        workout_session_id = start_workout_from_plan(
            user_id,
            plan
        )

        exercises = get_workout_session_exercises(
            workout_session_id
        )

        orders = [
            exercise["exercise_order"]
            for exercise in exercises
        ]

        if orders != [1, 2]:
            raise ValueError("FAIL: Workout plan did not assign default exercise order")

        print("PASS: Workout plan assigns default exercise order")

    finally:
        delete_user(user_id)


def test_start_workout_from_plan_rolls_back_on_invalid_exercise():
    user_id = create_user()

    try:
        plan = {
            "primary_goal": "Strength",
            "session_duration_minutes": 60,
            "exercises": [
                {
                    "exercise_id": "E001",
                    "order": 1
                },
                {
                    "exercise_id": "DOES_NOT_EXIST",
                    "order": 2
                }
            ]
        }

        try:
            start_workout_from_plan(
                user_id,
                plan
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Invalid workout plan exercise was accepted")

        history = get_user_workout_history(
            user_id
        )

        if history:
            raise ValueError("FAIL: Invalid workout plan left partial session in database")

        print("PASS: Invalid workout plan rolls back entire transaction")

    finally:
        delete_user(user_id)


def test_start_workout_from_plan_rejects_second_active_workout():
    user_id = create_user()

    try:
        start_workout_session(
            user_id
        )

        plan = {
            "primary_goal": "General Fitness",
            "session_duration_minutes": 45,
            "exercises": []
        }

        try:
            start_workout_from_plan(
                user_id,
                plan
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Workout plan started while another workout was active")

        print("PASS: Workout plan respects single active workout rule")

    finally:
        delete_user(user_id)


def test_start_workout_rejects_negative_planned_duration():
    user_id = create_user()

    try:
        try:
            start_workout_session(
                user_id,
                planned_duration_minutes=-1
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: negative planned duration was accepted")

        print("PASS: Negative planned duration rejected")

    finally:
        delete_user(user_id)


def test_start_workout_rejects_text_planned_duration():
    user_id = create_user()

    try:
        try:
            start_workout_session(
                user_id,
                planned_duration_minutes="60"
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: text planned duration was accepted")

        print("PASS: Text planned duration rejected")

    finally:
        delete_user(user_id)


def test_start_workout_rejects_boolean_planned_duration():
    user_id = create_user()

    try:
        try:
            start_workout_session(
                user_id,
                planned_duration_minutes=True
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: boolean planned duration was accepted")

        print("PASS: Boolean planned duration rejected")

    finally:
        delete_user(user_id)


def test_add_exercise_rejects_zero_order():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        try:
            add_workout_session_exercise(
                workout_session_id,
                "E001",
                0
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: zero exercise order was accepted")

        print("PASS: Zero exercise order rejected")

    finally:
        delete_user(user_id)


def test_add_exercise_rejects_negative_order():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        try:
            add_workout_session_exercise(
                workout_session_id,
                "E001",
                -1
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: negative exercise order was accepted")

        print("PASS: Negative exercise order rejected")

    finally:
        delete_user(user_id)


def test_add_exercise_rejects_float_order():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        try:
            add_workout_session_exercise(
                workout_session_id,
                "E001",
                1.5
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: float exercise order was accepted")

        print("PASS: Float exercise order rejected")

    finally:
        delete_user(user_id)


def test_add_exercise_rejects_boolean_order():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        try:
            add_workout_session_exercise(
                workout_session_id,
                "E001",
                True
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: boolean exercise order was accepted")

        print("PASS: Boolean exercise order rejected")

    finally:
        delete_user(user_id)


def test_add_exercise_rejects_zero_planned_sets():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        try:
            add_workout_session_exercise(
                workout_session_id,
                "E001",
                1,
                planned_sets=0
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: zero planned sets was accepted")

        print("PASS: Zero planned sets rejected")

    finally:
        delete_user(user_id)


def test_add_exercise_rejects_negative_planned_sets():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        try:
            add_workout_session_exercise(
                workout_session_id,
                "E001",
                1,
                planned_sets=-2
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: negative planned sets was accepted")

        print("PASS: Negative planned sets rejected")

    finally:
        delete_user(user_id)


def test_add_exercise_rejects_float_planned_sets():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        try:
            add_workout_session_exercise(
                workout_session_id,
                "E001",
                1,
                planned_sets=3.5
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: float planned sets was accepted")

        print("PASS: Float planned sets rejected")

    finally:
        delete_user(user_id)


def test_add_exercise_rejects_boolean_planned_sets():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        try:
            add_workout_session_exercise(
                workout_session_id,
                "E001",
                1,
                planned_sets=True
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: boolean planned sets was accepted")

        print("PASS: Boolean planned sets rejected")

    finally:
        delete_user(user_id)


def test_add_exercise_rejects_negative_rest():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        try:
            add_workout_session_exercise(
                workout_session_id,
                "E001",
                1,
                planned_rest_seconds=-1
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: negative planned rest was accepted")

        print("PASS: Negative planned rest rejected")

    finally:
        delete_user(user_id)


def test_add_exercise_rejects_float_rest():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        try:
            add_workout_session_exercise(
                workout_session_id,
                "E001",
                1,
                planned_rest_seconds=30.5
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: float planned rest was accepted")

        print("PASS: Float planned rest rejected")

    finally:
        delete_user(user_id)


def test_add_exercise_rejects_boolean_rest():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        try:
            add_workout_session_exercise(
                workout_session_id,
                "E001",
                1,
                planned_rest_seconds=True
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: boolean planned rest was accepted")

        print("PASS: Boolean planned rest rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_zero_set_number():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                0,
                reps_completed=10
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: zero set number was accepted")

        print("PASS: Zero set number rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_negative_set_number():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                -1,
                reps_completed=10
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: negative set number was accepted")

        print("PASS: Negative set number rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_float_set_number():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                1.5,
                reps_completed=10
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: float set number was accepted")

        print("PASS: Float set number rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_boolean_set_number():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                True,
                reps_completed=10
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: boolean set number was accepted")

        print("PASS: Boolean set number rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_negative_reps():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                1,
                reps_completed=-1
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: negative completed reps was accepted")

        print("PASS: Negative completed reps rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_float_reps():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                1,
                reps_completed=8.5
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: float completed reps was accepted")

        print("PASS: Float completed reps rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_boolean_reps():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                1,
                reps_completed=True
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: boolean completed reps was accepted")

        print("PASS: Boolean completed reps rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_negative_weight():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                1,
                weight_kg=-1
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: negative weight was accepted")

        print("PASS: Negative weight rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_boolean_weight():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                1,
                weight_kg=True
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: boolean weight was accepted")

        print("PASS: Boolean weight rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_negative_duration():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                1,
                duration_seconds=-1
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: negative set duration was accepted")

        print("PASS: Negative set duration rejected")

    finally:
        delete_user(user_id)

def test_log_set_rejects_boolean_duration():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                1,
                duration_seconds=True
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: boolean set duration was accepted")

        print("PASS: Boolean set duration rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_rir_below_zero():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                1,
                rir_actual=-1
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: RIR below zero was accepted")

        print("PASS: RIR below zero rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_rir_above_ten():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                1,
                rir_actual=11
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: RIR above ten was accepted")

        print("PASS: RIR above ten rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_float_rir():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                1,
                rir_actual=2.5
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: float RIR was accepted")

        print("PASS: float RIR rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_boolean_rir():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                1,
                rir_actual=True
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: boolean RIR was accepted")

        print("PASS: boolean RIR rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_rpe_below_zero():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                1,
                rpe_actual=-0.5
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: RPE below zero was accepted")

        print("PASS: RPE below zero rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_rpe_above_ten():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                1,
                rpe_actual=10.5
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: RPE above ten was accepted")

        print("PASS: RPE above ten rejected")

    finally:
        delete_user(user_id)


def test_log_set_rejects_boolean_rpe():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    try:
        try:
            log_workout_set(
                session_exercise_id,
                1,
                rpe_actual=True
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: boolean RPE was accepted")

        print("PASS: boolean RPE rejected")

    finally:
        delete_user(user_id)


def test_finish_workout_rejects_negative_actual_duration():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        try:
            finish_workout_session(
                workout_session_id,
                actual_duration_minutes=-1
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: negative actual duration was accepted")

        session = get_workout_session(
            workout_session_id
        )

        if session["status"] != "In Progress":
            raise ValueError("FAIL: Invalid finish changed workout status")

        print("PASS: Negative actual duration rejected")

    finally:
        delete_user(user_id)


def test_finish_workout_rejects_text_actual_duration():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        try:
            finish_workout_session(
                workout_session_id,
                actual_duration_minutes="30"
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: text actual duration was accepted")

        session = get_workout_session(
            workout_session_id
        )

        if session["status"] != "In Progress":
            raise ValueError("FAIL: Invalid finish changed workout status")

        print("PASS: Text actual duration rejected")

    finally:
        delete_user(user_id)


def test_finish_workout_rejects_boolean_actual_duration():
    user_id = create_user()

    try:
        workout_session_id = start_workout_session(
            user_id
        )

        try:
            finish_workout_session(
                workout_session_id,
                actual_duration_minutes=True
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: boolean actual duration was accepted")

        session = get_workout_session(
            workout_session_id
        )

        if session["status"] != "In Progress":
            raise ValueError("FAIL: Invalid finish changed workout status")

        print("PASS: Boolean actual duration rejected")

    finally:
        delete_user(user_id)


def test_workout_history_rejects_zero_limit():
    user_id = create_user()

    try:
        try:
            get_user_workout_history(
                user_id,
                limit=0
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: zero history limit was accepted")

        print("PASS: Zero history limit rejected")

    finally:
        delete_user(user_id)


def test_workout_history_rejects_negative_limit():
    user_id = create_user()

    try:
        try:
            get_user_workout_history(
                user_id,
                limit=-1
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: negative history limit was accepted")

        print("PASS: Negative history limit rejected")

    finally:
        delete_user(user_id)


def test_workout_history_rejects_float_limit():
    user_id = create_user()

    try:
        try:
            get_user_workout_history(
                user_id,
                limit=2.5
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: float history limit was accepted")

        print("PASS: Float history limit rejected")

    finally:
        delete_user(user_id)


def test_workout_history_rejects_boolean_limit():
    user_id = create_user()

    try:
        try:
            get_user_workout_history(
                user_id,
                limit=True
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: boolean history limit was accepted")

        print("PASS: Boolean history limit rejected")

    finally:
        delete_user(user_id)


def test_start_workout_from_plan_rejects_non_dictionary():
    user_id = create_user()

    try:
        try:
            start_workout_from_plan(
                user_id,
                []
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Non-dictionary workout plan was accepted")

        print("PASS: Non-dictionary workout plan rejected")

    finally:
        delete_user(user_id)


def test_start_workout_from_plan_rejects_missing_exercise_list():
    user_id = create_user()

    try:
        try:
            start_workout_from_plan(
                user_id,
                {
                    "primary_goal": "Strength"
                }
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Workout plan without exercise list was accepted")

        print("PASS: Workout plan without exercise list rejected")

    finally:
        delete_user(user_id)


def test_start_workout_from_plan_rejects_non_dictionary_exercise():
    user_id = create_user()

    try:
        try:
            start_workout_from_plan(
                user_id,
                {
                    "primary_goal": "Strength",
                    "exercises": [
                        "E001"
                    ]
                }
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Non-dictionary plan exercise was accepted")

        history = get_user_workout_history(
            user_id
        )

        if history:
            raise ValueError("FAIL: Invalid exercise entry left partial workout")

        print("PASS: Non-dictionary workout-plan exercise rejected")

    finally:
        delete_user(user_id)


def test_database_rejects_zero_set_number():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    connection = get_connection()

    try:
        try:
            connection.execute(
                """
                INSERT INTO workout_set_logs (
                    session_exercise_id,
                    set_number
                )
                VALUES (?, ?)
                """,
                (
                    session_exercise_id,
                    0
                )
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.rollback()

        else:
            raise ValueError("FAIL: Database accepted zero set number")

        print("PASS: Database rejected zero set number")

    finally:
        connection.close()
        delete_user(user_id)


def test_database_rejects_negative_reps():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    connection = get_connection()

    try:
        try:
            connection.execute(
                """
                INSERT INTO workout_set_logs (
                    session_exercise_id,
                    set_number,
                    reps_completed
                )
                VALUES (?, ?, ?)
                """,
                (
                    session_exercise_id,
                    1,
                    -1
                )
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.rollback()

        else:
            raise ValueError("FAIL: Database accepted negative reps")

        print("PASS: Database rejected negative reps")

    finally:
        connection.close()
        delete_user(user_id)


def test_database_rejects_negative_weight():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    connection = get_connection()

    try:
        try:
            connection.execute(
                """
                INSERT INTO workout_set_logs (
                    session_exercise_id,
                    set_number,
                    weight_kg
                )
                VALUES (?, ?, ?)
                """,
                (
                    session_exercise_id,
                    1,
                    -1
                )
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.rollback()

        else:
            raise ValueError("FAIL: Database accepted negative weight")

        print("PASS: Database rejected negative weight")

    finally:
        connection.close()
        delete_user(user_id)


def test_database_rejects_negative_duration():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    connection = get_connection()

    try:
        try:
            connection.execute(
                """
                INSERT INTO workout_set_logs (
                    session_exercise_id,
                    set_number,
                    duration_seconds
                )
                VALUES (?, ?, ?)
                """,
                (
                    session_exercise_id,
                    1,
                    -1
                )
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.rollback()

        else:
            raise ValueError("FAIL: Database accepted negative duration")

        print("PASS: Database rejected negative duration")

    finally:
        connection.close()
        delete_user(user_id)


def test_database_rejects_rir_below_zero():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    connection = get_connection()

    try:
        try:
            connection.execute(
                """
                INSERT INTO workout_set_logs (
                    session_exercise_id,
                    set_number,
                    rir_actual
                )
                VALUES (?, ?, ?)
                """,
                (
                    session_exercise_id,
                    1,
                    -1
                )
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.rollback()

        else:
            raise ValueError("FAIL: Database accepted RIR below zero")

        print("PASS: Database rejected RIR below zero")

    finally:
        connection.close()
        delete_user(user_id)


def test_database_rejects_rir_above_ten():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    connection = get_connection()

    try:
        try:
            connection.execute(
                """
                INSERT INTO workout_set_logs (
                    session_exercise_id,
                    set_number,
                    rir_actual
                )
                VALUES (?, ?, ?)
                """,
                (
                    session_exercise_id,
                    1,
                    11
                )
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.rollback()

        else:
            raise ValueError("FAIL: Database accepted RIR above ten")

        print("PASS: Database rejected RIR above ten")

    finally:
        connection.close()
        delete_user(user_id)


def test_database_rejects_rpe_below_zero():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    connection = get_connection()

    try:
        try:
            connection.execute(
                """
                INSERT INTO workout_set_logs (
                    session_exercise_id,
                    set_number,
                    rpe_actual
                )
                VALUES (?, ?, ?)
                """,
                (
                    session_exercise_id,
                    1,
                    -1
                )
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.rollback()

        else:
            raise ValueError("FAIL: Database accepted RPE below zero")

        print("PASS: Database rejected RPE below zero")

    finally:
        connection.close()
        delete_user(user_id)


def test_database_rejects_rpe_above_ten():
    user_id, workout_session_id, session_exercise_id = create_basic_workout()

    connection = get_connection()

    try:
        try:
            connection.execute(
                """
                INSERT INTO workout_set_logs (
                    session_exercise_id,
                    set_number,
                    rpe_actual
                )
                VALUES (?, ?, ?)
                """,
                (
                    session_exercise_id,
                    1,
                    11
                )
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.rollback()

        else:
            raise ValueError("FAIL: Database accepted RPE above ten")

        print("PASS: Database rejected RPE above ten")

    finally:
        connection.close()
        delete_user(user_id)



if __name__ == "__main__":
    setup_workout_log_database()

    test_workout_log_tables_exist()
    test_workout_log_indexes_exist()
    test_workout_sessions_foreign_key_exists()
    test_session_exercise_foreign_keys_exist()
    test_set_log_foreign_key_exists()
    test_query_connection_enables_foreign_keys()
    test_invalid_workout_status_rejected()
    test_duplicate_exercise_order_rejected()
    test_invalid_completed_flag_rejected()
    test_duplicate_set_number_rejected()
    test_user_delete_cascades_workout_data()
    test_start_workout_session_returns_id()
    test_start_workout_session_uses_default_status()
    test_start_workout_session_saves_optional_fields()
    test_second_active_workout_rejected()
    test_new_workout_allowed_after_completion()
    test_new_workout_allowed_after_cancellation()
    test_start_workout_rejects_missing_user()
    test_add_session_exercise_returns_id()
    test_add_session_exercise_saves_planned_fields()
    test_add_duration_based_session_exercise()
    test_add_session_exercise_rejects_missing_workout()
    test_add_session_exercise_rejects_missing_exercise()
    test_add_exercise_rejected_after_workout_completion()
    test_log_workout_set_returns_id()
    test_log_workout_set_saves_all_fields()
    test_log_duration_only_set()
    test_log_set_rejects_missing_session_exercise()
    test_log_set_rejected_after_workout_completion()
    test_update_workout_set()
    test_update_missing_workout_set_rejected()
    test_update_set_rejected_after_workout_completion()
    test_delete_workout_set()
    test_delete_missing_workout_set_rejected()
    test_delete_set_rejected_after_workout_completion()
    test_mark_session_exercise_complete()
    test_mark_session_exercise_incomplete()
    test_mark_missing_session_exercise_rejected()
    test_mark_exercise_rejected_after_workout_completion()
    test_finish_workout_session()
    test_finish_missing_workout_rejected()
    test_finish_workout_twice_rejected()
    test_cancel_workout_session()
    test_cancel_missing_workout_rejected()
    test_cancel_completed_workout_rejected()
    test_get_workout_session()
    test_get_missing_workout_session_returns_none()
    test_get_session_exercises_ordered()
    test_get_set_logs_ordered()
    test_get_workout_session_details()
    test_get_missing_workout_details_returns_none()
    test_user_workout_history_returns_newest_first()
    test_user_workout_history_filters_status()
    test_user_workout_history_applies_limit()
    test_user_workout_history_rejects_invalid_status()
    test_user_workout_history_is_user_specific()
    test_get_active_workout_session()
    test_get_active_workout_returns_none_after_completion()
    test_workout_progress_empty_session()
    test_workout_progress_partial_completion()
    test_workout_progress_complete()
    test_workout_progress_rejects_missing_session()
    test_delete_workout_session_cascades()
    test_delete_missing_workout_session_rejected()
    test_start_workout_from_plan()
    test_start_workout_from_plan_uses_default_order()
    test_start_workout_from_plan_rolls_back_on_invalid_exercise()
    test_start_workout_from_plan_rejects_second_active_workout()
    test_start_workout_rejects_negative_planned_duration()
    test_start_workout_rejects_text_planned_duration()
    test_start_workout_rejects_boolean_planned_duration()
    test_add_exercise_rejects_zero_order()
    test_add_exercise_rejects_negative_order()
    test_add_exercise_rejects_float_order()
    test_add_exercise_rejects_boolean_order()
    test_add_exercise_rejects_zero_planned_sets()
    test_add_exercise_rejects_negative_planned_sets()
    test_add_exercise_rejects_float_planned_sets()
    test_add_exercise_rejects_boolean_planned_sets()
    test_add_exercise_rejects_negative_rest()
    test_add_exercise_rejects_float_rest()
    test_add_exercise_rejects_boolean_rest()
    test_log_set_rejects_zero_set_number()
    test_log_set_rejects_negative_set_number()
    test_log_set_rejects_float_set_number()
    test_log_set_rejects_boolean_set_number()
    test_log_set_rejects_negative_reps()
    test_log_set_rejects_float_reps()
    test_log_set_rejects_boolean_reps()
    test_log_set_rejects_negative_weight()
    test_log_set_rejects_boolean_weight()
    test_log_set_rejects_negative_duration()
    test_log_set_rejects_boolean_duration()
    test_log_set_rejects_rir_below_zero()
    test_log_set_rejects_rir_above_ten()
    test_log_set_rejects_float_rir()
    test_log_set_rejects_boolean_rir()
    test_log_set_rejects_rpe_below_zero()
    test_log_set_rejects_rpe_above_ten()
    test_log_set_rejects_boolean_rpe()
    test_finish_workout_rejects_negative_actual_duration()
    test_finish_workout_rejects_text_actual_duration()
    test_finish_workout_rejects_boolean_actual_duration()
    test_workout_history_rejects_zero_limit()
    test_workout_history_rejects_negative_limit()
    test_workout_history_rejects_float_limit()
    test_workout_history_rejects_boolean_limit()
    test_start_workout_from_plan_rejects_non_dictionary()
    test_start_workout_from_plan_rejects_missing_exercise_list()
    test_start_workout_from_plan_rejects_non_dictionary_exercise()
    test_database_rejects_zero_set_number()
    test_database_rejects_negative_reps()
    test_database_rejects_negative_weight()
    test_database_rejects_negative_duration()
    test_database_rejects_rir_below_zero()
    test_database_rejects_rir_above_ten()
    test_database_rejects_rpe_below_zero()
    test_database_rejects_rpe_above_ten()