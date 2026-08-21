import sqlite3

from pathlib import Path


DATABASE_PATH = Path(
    "data/database/ai_fitness.db"
)


def setup_progress_database():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS progress_entries (
            progress_entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            weight_kg REAL CHECK (weight_kg > 0),
            body_fat_percentage REAL
                CHECK (
                    body_fat_percentage >= 0
                    AND body_fat_percentage <= 100
                ),
            notes TEXT,
            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS body_measurements (
            body_measurement_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            body_area TEXT NOT NULL,
            measurement_cm REAL NOT NULL
                CHECK (measurement_cm > 0),
            notes TEXT,
            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_logs (
            activity_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            duration_minutes REAL
                CHECK (duration_minutes >= 0),
            distance_km REAL
                CHECK (distance_km >= 0),
            steps INTEGER
                CHECK (steps >= 0),
            average_speed_kmh REAL
                CHECK (average_speed_kmh >= 0),
            estimated_calories REAL
                CHECK (estimated_calories >= 0),
            notes TEXT,
            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS progress_photos (
            progress_photo_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT NOT NULL,
            view_type TEXT NOT NULL
                CHECK (
                    view_type IN (
                        'Front',
                        'Side',
                        'Back',
                        'Other'
                    )
                ),
            is_private INTEGER NOT NULL DEFAULT 1
                CHECK (is_private IN (0, 1)),
            notes TEXT,
            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_progress_photos_user_id
        ON progress_photos(user_id)
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS scheduled_workouts (
            scheduled_workout_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            scheduled_for TEXT NOT NULL,
            primary_goal TEXT,
            planned_duration_minutes REAL
                CHECK (
                    planned_duration_minutes IS NULL
                    OR planned_duration_minutes > 0
                ),
            status TEXT NOT NULL DEFAULT 'Planned'
                CHECK (
                    status IN (
                        'Planned',
                        'Completed',
                        'Skipped',
                        'Cancelled'
                    )
                ),
            workout_session_id INTEGER,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE,
            FOREIGN KEY (workout_session_id)
                REFERENCES workout_sessions(workout_session_id)
                ON DELETE SET NULL
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS scheduled_workout_exercises (
            scheduled_exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheduled_workout_id INTEGER NOT NULL,
            exercise_id TEXT NOT NULL,
            exercise_order INTEGER NOT NULL
                CHECK (exercise_order > 0),
            planned_sets INTEGER
                CHECK (
                    planned_sets IS NULL
                    OR planned_sets > 0
                ),
            planned_reps TEXT,
            planned_rest_seconds REAL
                CHECK (
                    planned_rest_seconds IS NULL
                    OR planned_rest_seconds >= 0
                ),
            planned_duration_minutes REAL
                CHECK (
                    planned_duration_minutes IS NULL
                    OR planned_duration_minutes > 0
                ),
            FOREIGN KEY (scheduled_workout_id)
                REFERENCES scheduled_workouts(scheduled_workout_id)
                ON DELETE CASCADE,
            FOREIGN KEY (exercise_id)
                REFERENCES exercises(exercise_id)
                ON DELETE RESTRICT,
            UNIQUE (
                scheduled_workout_id,
                exercise_order
            )
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_scheduled_workouts_user_id
        ON scheduled_workouts(user_id)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_scheduled_workouts_scheduled_for
        ON scheduled_workouts(scheduled_for)
        """
    )



    connection.commit()

    connection.close()

if __name__ == "__main__":
    setup_progress_database()

    print("Progress database setup complete")