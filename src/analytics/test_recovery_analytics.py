from src.analytics.recovery_analytics import (
    filter_recent_recovery_logs,
    get_recovery_intensity_analytics,
    summarize_recovery_logs
)

from src.database.query_user_database import (
    create_user,
    delete_user
)


REFERENCE_DATE = "2026-08-21"


def normal_logs():
    return [
        {
            "started_at": "2026-08-10T10:00:00",
            "rpe_actual": 7.0,
            "rir_actual": 3
        },
        {
            "started_at": "2026-08-12T10:00:00",
            "rpe_actual": 8.0,
            "rir_actual": 2
        },
        {
            "started_at": "2026-08-15T10:00:00",
            "rpe_actual": 7.5,
            "rir_actual": 3
        },
        {
            "started_at": "2026-08-18T10:00:00",
            "rpe_actual": 8.0,
            "rir_actual": 2
        }
    ]


def high_exertion_logs():
    return [
        {
            "started_at": "2026-08-10T10:00:00",
            "rpe_actual": 9.0,
            "rir_actual": 1
        },
        {
            "started_at": "2026-08-12T10:00:00",
            "rpe_actual": 9.5,
            "rir_actual": 0
        },
        {
            "started_at": "2026-08-15T10:00:00",
            "rpe_actual": 9.0,
            "rir_actual": 1
        },
        {
            "started_at": "2026-08-18T10:00:00",
            "rpe_actual": 8.5,
            "rir_actual": 2
        },
        {
            "started_at": "2026-08-20T10:00:00",
            "rpe_actual": 10.0,
            "rir_actual": 0
        }
    ]


def test_empty_logs_are_insufficient():
    result = summarize_recovery_logs(
        [],
        reference_date=REFERENCE_DATE
    )

    if result["signal_status"] != "insufficient_data":
        raise ValueError("FAIL: Empty exertion data did not return insufficient status")

    if result["recent_performance_log_count"] != 0:
        raise ValueError("FAIL: Empty exertion log count is incorrect")

    print("PASS: Recovery analytics handles users without exertion logs safely")


def test_normal_exertion_is_not_high_signal():
    result = summarize_recovery_logs(
        normal_logs(),
        reference_date=REFERENCE_DATE
    )

    if result["signal_status"] != "normal":
        raise ValueError(f"FAIL: Normal exertion returned {result['signal_status']}")

    if result["high_exertion_signal"]:
        raise ValueError("FAIL: Normal exertion was classified as high exertion")

    print("PASS: Moderate recorded exertion remains a normal signal")


def test_high_rpe_and_low_rir_create_high_signal():
    result = summarize_recovery_logs(
        high_exertion_logs(),
        reference_date=REFERENCE_DATE
    )

    if result["signal_status"] != "high_exertion":
        raise ValueError("FAIL: High RPE plus low RIR did not create exertion signal")

    if result["high_exertion_signal"] is not True:
        raise ValueError("FAIL: High exertion boolean was not set")

    print("PASS: Repeated high RPE and low RIR create conservative high-exertion signal")


def test_too_few_observations_remain_insufficient():
    result = summarize_recovery_logs(
        high_exertion_logs()[:2],
        reference_date=REFERENCE_DATE
    )

    if result["signal_status"] != "insufficient_data":
        raise ValueError("FAIL: Too few RPE/RIR observations produced an adaptation signal")

    print("PASS: Recovery analytics requires multiple exertion observations")


def test_old_logs_are_excluded():
    logs = normal_logs()

    logs.append(
        {
            "started_at": "2026-07-01T10:00:00",
            "rpe_actual": 10.0,
            "rir_actual": 0
        }
    )

    recent = filter_recent_recovery_logs(
        logs,
        reference_date=REFERENCE_DATE
    )

    if len(recent) != 4:
        raise ValueError(f"FAIL: Expected 4 recent recovery logs, got {len(recent)}")

    print("PASS: Recovery analytics excludes exertion records outside recent window")


def test_average_rpe_and_rir_are_computed():
    result = summarize_recovery_logs(
        normal_logs(),
        reference_date=REFERENCE_DATE
    )

    if result["average_rpe"] != 7.62:
        raise ValueError(f"FAIL: Average RPE is incorrect: {result['average_rpe']}")

    if result["average_rir"] != 2.5:
        raise ValueError(f"FAIL: Average RIR is incorrect: {result['average_rir']}")

    print("PASS: Recovery analytics computes deterministic RPE and RIR averages")


def test_database_query_handles_new_user_without_logs():
    user_id = create_user()

    try:
        result = get_recovery_intensity_analytics(
            user_id,
            reference_date=REFERENCE_DATE
        )

        if result["recent_performance_log_count"] != 0:
            raise ValueError("FAIL: New user unexpectedly has recovery log data")

        if result["signal_status"] != "insufficient_data":
            raise ValueError("FAIL: New user did not return insufficient recovery data")

        print("PASS: Recovery analytics database query handles empty user history")

    finally:
        delete_user(
            user_id
        )


if __name__ == "__main__":
    test_empty_logs_are_insufficient()
    test_normal_exertion_is_not_high_signal()
    test_high_rpe_and_low_rir_create_high_signal()
    test_too_few_observations_remain_insufficient()
    test_old_logs_are_excluded()
    test_average_rpe_and_rir_are_computed()
    test_database_query_handles_new_user_without_logs()