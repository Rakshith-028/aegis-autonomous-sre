from dataclasses import dataclass


@dataclass
class PolicyDecision:
    allowed: bool
    risk_level: str
    requires_approval: bool
    reason: str


class PolicyEngine:
    LOW_RISK_ACTIONS = {
        "RESTART_CONTAINER",
        "OBSERVE",
        "NONE",
    }

    MEDIUM_RISK_ACTIONS = {
        "SCALE_SERVICE",
    }

    HIGH_RISK_ACTIONS = {
        "ROLLBACK_DEPLOYMENT",
        "RESTORE_CONFIGURATION",
        "DELETE_RESOURCE",
    }

    def evaluate(
        self,
        action: str,
        confidence: float,
    ) -> PolicyDecision:

        if action == "NONE":
            return PolicyDecision(
                allowed=False,
                risk_level="NONE",
                requires_approval=False,
                reason="No remediation required.",
            )

        if action == "OBSERVE":
            return PolicyDecision(
                allowed=False,
                risk_level="LOW",
                requires_approval=False,
                reason="Observation-only decision.",
            )

        if action in self.LOW_RISK_ACTIONS:
            if confidence < 0.80:
                return PolicyDecision(
                    allowed=False,
                    risk_level="LOW",
                    requires_approval=False,
                    reason=(
                        "RCA confidence below autonomous "
                        "execution threshold."
                    ),
                )

            return PolicyDecision(
                allowed=True,
                risk_level="LOW",
                requires_approval=False,
                reason=(
                    "Low-risk remediation with sufficient "
                    "RCA confidence."
                ),
            )

        if action in self.MEDIUM_RISK_ACTIONS:
            return PolicyDecision(
                allowed=False,
                risk_level="MEDIUM",
                requires_approval=True,
                reason=(
                    "Medium-risk action requires "
                    "human approval."
                ),
            )

        return PolicyDecision(
            allowed=False,
            risk_level="HIGH",
            requires_approval=True,
            reason=(
                "High-risk remediation blocked from "
                "autonomous execution."
            ),
        )
