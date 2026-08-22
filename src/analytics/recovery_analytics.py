from datetime import date, datetime, timedelta

from src.database.query_workout_log_database import (
    get_connection
)


RECENT_RECOVERY_WINDOW_DAYS = 14

HIGH_RPE_THRESHOLD = 9.0
LOW_RIR_THRESHOLD = 1

MIN_RPE_OBSERVATIONS = 4
MIN_RIR_OBSERVATIONS = 4

HIGH_RPE_RATIO_THRESHOLD = 0.50
LOW_RIR_RATIO_THRESHOLD = 0.50


def validate_user_id(user_id):
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id < 1:
        raise ValueError("user_id must be a positive integer")


def validate_window_days(window_days):
    if not isinstance(window_days, int) or isinstance(window_days, bool):
        raise ValueError("window_days must be an integer")

    if window_days < 1 or window_days > 365:
        raise ValueError("window_days must be between 1 and 365")


def normalize_reference_date(reference_date=None):
    if reference_date is None:
        return date.today()

    if isinstance(reference_date, datetime):
        return reference_date.date()

    if isinstance(reference_date, date):
        return reference_date

    if isinstance(reference_date, str):
        value = reference_date.strip()

        if not value:
            raise ValueError("reference_date cannot be empty")

        try:
            return datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00"
                )
            ).date()

        except ValueError as error:
            raise ValueError("reference_date must be an ISO date or datetime") from error

    raise ValueError("reference_date must be a date, datetime, ISO string, or None")


def normalize_log_date(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        normalized = value.strip()

        if not normalized:
            return None

        try:
            return datetime.fromisoformat(
                normalized.replace(
                    "Z",
                    "+00:00"
                )
            ).date()

        except ValueError:
            return None

    return None


def calculate_ratio(
    numerator,
    denominator
):
    if denominator <= 0:
        return None

    return round(
        numerator / denominator,
        4
    )


def calculate_percentage(
    numerator,
    denominator
):
    if denominator <= 0:
        return 0.0

    return round(
        numerator
        / denominator
        * 100,
        2
    )


def calculate_average(values):
    if not values:
        return None

    return round(
        sum(values)
        / len(values),
        2
    )


def filter_recent_recovery_logs(
    logs,
    reference_date=None,
    window_days=RECENT_RECOVERY_WINDOW_DAYS
):
    if not isinstance(logs, list):
        raise ValueError("logs must be a list")

    validate_window_days(
        window_days
    )

    normalized_reference_date = normalize_reference_date(
        reference_date
    )

    start_date = (
        normalized_reference_date
        - timedelta(
            days=window_days - 1
        )
    )

    recent_logs = []

    for log in logs:
        if not isinstance(log, dict):
            continue

        started_at = normalize_log_date(
            log.get(
                "started_at"
            )
        )

        if started_at is None:
            continue

        if start_date <= started_at <= normalized_reference_date:
            recent_logs.append(
                log
            )

    return recent_logs


def summarize_recovery_logs(
    logs,
    reference_date=None,
    window_days=RECENT_RECOVERY_WINDOW_DAYS
):
    recent_logs = filter_recent_recovery_logs(
        logs,
        reference_date=reference_date,
        window_days=window_days
    )

    rpe_values = [
        float(
            log[
                "rpe_actual"
            ]
        )
        for log in recent_logs
        if log.get(
            "rpe_actual"
        ) is not None
    ]

    rir_values = [
        int(
            log[
                "rir_actual"
            ]
        )
        for log in recent_logs
        if log.get(
            "rir_actual"
        ) is not None
    ]

    high_rpe_count = sum(
        1
        for value in rpe_values
        if value >= HIGH_RPE_THRESHOLD
    )

    low_rir_count = sum(
        1
        for value in rir_values
        if value <= LOW_RIR_THRESHOLD
    )

    rpe_count = len(
        rpe_values
    )

    rir_count = len(
        rir_values
    )

    performance_log_count = len(
        recent_logs
    )

    high_rpe_ratio = calculate_ratio(
        high_rpe_count,
        rpe_count
    )

    low_rir_ratio = calculate_ratio(
        low_rir_count,
        rir_count
    )

    sufficient_rpe_data = (
        rpe_count
        >= MIN_RPE_OBSERVATIONS
    )

    sufficient_rir_data = (
        rir_count
        >= MIN_RIR_OBSERVATIONS
    )

    sufficient_exertion_data = (
        sufficient_rpe_data
        and sufficient_rir_data
    )

    high_exertion_signal = False

    if sufficient_exertion_data:
        high_exertion_signal = (
            high_rpe_ratio is not None
            and low_rir_ratio is not None
            and high_rpe_ratio
            >= HIGH_RPE_RATIO_THRESHOLD
            and low_rir_ratio
            >= LOW_RIR_RATIO_THRESHOLD
        )

    if not sufficient_exertion_data:
        signal_status = "insufficient_data"

    elif high_exertion_signal:
        signal_status = "high_exertion"

    else:
        signal_status = "normal"

    return {
        "reference_date": normalize_reference_date(
            reference_date
        ).isoformat(),
        "recent_window_days": window_days,
        "recent_performance_log_count": performance_log_count,
        "recent_rpe_log_count": rpe_count,
        "recent_rir_log_count": rir_count,
        "rpe_coverage_percentage": calculate_percentage(
            rpe_count,
            performance_log_count
        ),
        "rir_coverage_percentage": calculate_percentage(
            rir_count,
            performance_log_count
        ),
        "average_rpe": calculate_average(
            rpe_values
        ),
        "average_rir": calculate_average(
            rir_values
        ),
        "high_rpe_count": high_rpe_count,
        "low_rir_count": low_rir_count,
        "high_rpe_ratio": high_rpe_ratio,
        "low_rir_ratio": low_rir_ratio,
        "sufficient_rpe_data": sufficient_rpe_data,
        "sufficient_rir_data": sufficient_rir_data,
        "sufficient_exertion_data": sufficient_exertion_data,
        "high_exertion_signal": high_exertion_signal,
        "signal_status": signal_status
    }


def get_recovery_intensity_analytics(
    user_id,
    reference_date=None,
    window_days=RECENT_RECOVERY_WINDOW_DAYS
):
    validate_user_id(
        user_id
    )

    validate_window_days(
        window_days
    )

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                ws.workout_session_id,
                ws.started_at,
                wsl.set_log_id,
                wsl.rir_actual,
                wsl.rpe_actual
            FROM workout_set_logs AS wsl
            JOIN workout_session_exercises AS wse
                ON wse.session_exercise_id = wsl.session_exercise_id
            JOIN workout_sessions AS ws
                ON ws.workout_session_id = wse.workout_session_id
            WHERE ws.user_id = ?
              AND ws.status = 'Completed'
            ORDER BY
                ws.started_at ASC,
                wsl.set_log_id ASC
            """,
            (
                user_id,
            )
        ).fetchall()

        logs = [
            dict(
                row
            )
            for row in rows
        ]

    finally:
        connection.close()

    return summarize_recovery_logs(
        logs,
        reference_date=reference_date,
        window_days=window_days
    )