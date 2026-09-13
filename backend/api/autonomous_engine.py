import json
import time

from backend.config import (
    MAX_REMEDIATION_ATTEMPTS,
    SERVICE_NAME,
)
from backend.incidents.incident_manager import (
    create_or_get_incident,
    resolve_incident,
)
from backend.incidents.postmortem import (
    generate_postmortem,
)
from backend.policies.policy_engine import (
    PolicyEngine,
)
from backend.rca.evidence_collector import (
    EvidenceCollector,
)
from backend.rca.rca_engine import RCAEngine
from backend.remediation.remediation_engine import (
    RemediationEngine,
)
from backend.verification.recovery_verifier import (
    RecoveryVerifier,
)


class AutonomousEngine:
    def __init__(self):
        self.collector = EvidenceCollector()
        self.rca_engine = RCAEngine()
        self.policy_engine = PolicyEngine()
        self.remediation_engine = (
            RemediationEngine()
        )
        self.verifier = RecoveryVerifier()

    def run_once(self) -> dict:
        started = time.perf_counter()

        print()
        print("=" * 72)
        print("AEGIS AUTONOMOUS SRE CYCLE")
        print("=" * 72)

        print("[1/6] Collecting evidence...")

        evidence = self.collector.collect()

        print("[2/6] Running RCA...")

        rca = self.rca_engine.analyze(
            evidence
        )

        print(
            f"      Root cause: "
            f"{rca.root_cause}"
        )
        print(
            f"      Confidence: "
            f"{rca.confidence:.2f}"
        )

        if rca.root_cause in {
            "NO_ACTIVE_FAILURE",
            "NO_TRAFFIC",
        }:
            print(
                "[AEGIS] No actionable incident."
            )

            return {
                "status": "HEALTHY",
                "evidence": evidence,
                "rca": rca.to_dict(),
            }

        incident_key = (
            f"autonomous:{SERVICE_NAME}:"
            f"{rca.root_cause}"
        )

        incident, created = (
            create_or_get_incident(
                service_name=SERVICE_NAME,
                incident_key=incident_key,
                reason="; ".join(
                    rca.reasoning
                ),
                severity=rca.severity,
                source="autonomous_engine",
                failure_type=rca.root_cause,
                metadata={
                    "confidence": (
                        rca.confidence
                    ),
                },
            )
        )

        print(
            f"[3/6] Incident "
            f"{incident['id']} "
            f"({'NEW' if created else 'EXISTING'})"
        )

        all_verification = []
        attempts = []

        current_rca = rca

        for attempt in range(
            1,
            MAX_REMEDIATION_ATTEMPTS + 1,
        ):
            policy = (
                self.policy_engine.evaluate(
                    action=(
                        current_rca
                        .recommended_action
                    ),
                    confidence=(
                        current_rca.confidence
                    ),
                )
            )

            print(
                f"[4/6] Policy: "
                f"{policy.risk_level}"
            )
            print(
                f"      Allowed: "
                f"{policy.allowed}"
            )

            if not policy.allowed:
                print(
                    "[AEGIS] Autonomous remediation "
                    "blocked by policy."
                )

                return {
                    "status": "BLOCKED",
                    "incident": incident,
                    "rca": (
                        current_rca.to_dict()
                    ),
                    "policy": policy.__dict__,
                    "attempts": attempts,
                }

            print(
                f"[5/6] Executing "
                f"{current_rca.recommended_action} "
                f"(attempt {attempt}/"
                f"{MAX_REMEDIATION_ATTEMPTS})..."
            )

            remediation = (
                self.remediation_engine.execute(
                    current_rca
                    .recommended_action
                )
            )

            attempt_record = {
                "attempt": attempt,
                "root_cause": (
                    current_rca.root_cause
                ),
                "action": (
                    current_rca
                    .recommended_action
                ),
                "remediation": (
                    remediation.__dict__
                ),
            }

            if not remediation.success:
                attempt_record[
                    "verification"
                ] = []

                attempts.append(
                    attempt_record
                )

                if (
                    attempt
                    >= MAX_REMEDIATION_ATTEMPTS
                ):
                    return {
                        "status": (
                            "REMEDIATION_FAILED"
                        ),
                        "incident": incident,
                        "rca": (
                            current_rca.to_dict()
                        ),
                        "policy": (
                            policy.__dict__
                        ),
                        "attempts": attempts,
                    }

                continue

            print(
                "[6/6] Verifying recovery..."
            )

            recovered, verification = (
                self.verifier.verify()
            )

            attempt_record[
                "verification"
            ] = verification

            attempts.append(
                attempt_record
            )

            all_verification.extend(
                verification
            )

            if recovered:
                resolved = resolve_incident(
                    incident,
                    remediation=(
                        current_rca
                        .recommended_action
                    ),
                    metadata={
                        "verified": True,
                        "remediation_attempts": (
                            attempt
                        ),
                    },
                )

                elapsed = (
                    time.perf_counter()
                    - started
                )

                postmortem_path = (
                    generate_postmortem(
                        incident=resolved,
                        rca=(
                            current_rca
                            .to_dict()
                        ),
                        policy=(
                            policy.__dict__
                        ),
                        remediation=(
                            remediation.__dict__
                        ),
                        verification=(
                            all_verification
                        ),
                    )
                )

                print()
                print(
                    "[AEGIS] SERVICE RECOVERED"
                )
                print(
                    f"Incident: "
                    f"{resolved['id']}"
                )
                print(
                    f"Attempts: {attempt}"
                )
                print(
                    f"Recovery time: "
                    f"{elapsed:.2f}s"
                )

                return {
                    "status": "RECOVERED",
                    "incident": resolved,
                    "rca": (
                        current_rca.to_dict()
                    ),
                    "policy": (
                        policy.__dict__
                    ),
                    "remediation": (
                        remediation.__dict__
                    ),
                    "attempts": attempts,
                    "verification": (
                        all_verification
                    ),
                    "recovery_seconds": elapsed,
                    "postmortem": str(
                        postmortem_path
                    ),
                }

            if (
                attempt
                < MAX_REMEDIATION_ATTEMPTS
            ):
                print(
                    "[AEGIS] Verification failed. "
                    "Collecting fresh evidence..."
                )

                refreshed_evidence = (
                    self.collector.collect()
                )

                current_rca = (
                    self.rca_engine.analyze(
                        refreshed_evidence
                    )
                )

                print(
                    "[AEGIS] Updated hypothesis: "
                    f"{current_rca.root_cause}"
                )

        return {
            "status": "VERIFICATION_FAILED",
            "incident": incident,
            "rca": current_rca.to_dict(),
            "attempts": attempts,
            "verification": all_verification,
        }


def main():
    engine = AutonomousEngine()

    result = engine.run_once()

    print()
    print("=" * 72)
    print("FINAL CYCLE RESULT")
    print("=" * 72)

    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
