import sqlite3

from src.database.setup_exercise_database import db_path

def setup_user_database():
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_exercise_preferences (
            preference_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exercise_id TEXT NOT NULL,
            preference TEXT NOT NULL
                CHECK (preference IN ('Preferred', 'Disliked')),

            UNIQUE (user_id, exercise_id),

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE,

            FOREIGN KEY (exercise_id)
                REFERENCES exercises(exercise_id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_limitations (
            limitation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            body_area TEXT NOT NULL,
            limitation_type TEXT NOT NULL,
            notes TEXT,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            age INTEGER,
            sex TEXT,
            height_cm REAL,
            weight_kg REAL,
            fitness_level TEXT,
            primary_goal TEXT,
            training_days_per_week INTEGER,
            session_duration_minutes INTEGER,
            preferred_environment TEXT,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_equipment_access (
            access_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            equipment TEXT NOT NULL,
            access_status TEXT NOT NULL
                CHECK (access_status IN ('Available', 'Unavailable')),

            UNIQUE (user_id, equipment),

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_nutrition_targets (
            nutrition_target_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,

            activity_level TEXT NOT NULL,
            nutrition_goal TEXT NOT NULL,

            bmr REAL NOT NULL CHECK (bmr > 0),
            tdee REAL NOT NULL CHECK (tdee > 0),
            calorie_target REAL NOT NULL CHECK (calorie_target > 0),

            protein_g REAL NOT NULL CHECK (protein_g > 0),
            fat_g REAL NOT NULL CHECK (fat_g > 0),
            carbs_g REAL NOT NULL CHECK (carbs_g >= 0),

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    connection.close()

if __name__ == '__main__':
    setup_user_database()


