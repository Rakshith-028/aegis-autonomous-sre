from backend.rca.rca_engine import (
    RCAEngine,
)


def base_evidence():
    return {
        "health": {
            "reachable": True,
            "status_code": 200,
        },
        "container": {
            "available": True,
            "state": {
                "Running": True,
            },
        },
        "metrics": {
            "error_rate": {
                "value": 0.0,
            },
            "latency": {
                "value": 0.001,
            },
            "request_rate": {
                "value": 2.0,
            },
        },
    }


def test_healthy_service():
    result = RCAEngine().analyze(
        base_evidence()
    )

    assert (
        result.root_cause
        == "NO_ACTIVE_FAILURE"
    )


def test_container_down():
    evidence = base_evidence()

    evidence["container"]["state"][
        "Running"
    ] = False

    result = RCAEngine().analyze(
        evidence
    )

    assert (
        result.root_cause
        == "CONTAINER_DOWN"
    )

    assert (
        result.recommended_action
        == "RESTART_CONTAINER"
    )


def test_latency_degradation():
    evidence = base_evidence()

    evidence["metrics"]["latency"][
        "value"
    ] = 1.5

    result = RCAEngine().analyze(
        evidence
    )

    assert (
        result.root_cause
        == "APPLICATION_LATENCY_DEGRADATION"
    )


def test_error_rate_failure():
    evidence = base_evidence()

    evidence["metrics"]["error_rate"][
        "value"
    ] = 0.7

    result = RCAEngine().analyze(
        evidence
    )

    assert (
        result.root_cause
        == "HIGH_APPLICATION_ERROR_RATE"
    )
