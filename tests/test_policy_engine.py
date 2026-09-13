from backend.policies.policy_engine import (
    PolicyEngine,
)


def test_restart_allowed_with_confidence():
    result = PolicyEngine().evaluate(
        "RESTART_CONTAINER",
        0.95,
    )

    assert result.allowed is True
    assert (
        result.requires_approval
        is False
    )


def test_restart_blocked_low_confidence():
    result = PolicyEngine().evaluate(
        "RESTART_CONTAINER",
        0.50,
    )

    assert result.allowed is False


def test_high_risk_action_blocked():
    result = PolicyEngine().evaluate(
        "ROLLBACK_DEPLOYMENT",
        0.99,
    )

    assert result.allowed is False

    assert (
        result.requires_approval
        is True
    )
