from dataclasses import asdict, dataclass


@dataclass
class RCAResult:
    root_cause: str
    confidence: float
    severity: str
    reasoning: list[str]
    recommended_action: str

    def to_dict(self) -> dict:
        return asdict(self)


class RCAEngine:
    def analyze(self, evidence: dict) -> RCAResult:
        health = evidence.get("health", {})
        container = evidence.get("container", {})
        metrics = evidence.get("metrics", {})

        reasoning = []

        container_running = False

        if container.get("available"):
            state = container.get("state", {})
            container_running = bool(
                state.get("Running", False)
            )

        if not container_running:
            reasoning.append(
                "Docker container is not running."
            )

            return RCAResult(
                root_cause="CONTAINER_DOWN",
                confidence=0.99,
                severity="CRITICAL",
                reasoning=reasoning,
                recommended_action="RESTART_CONTAINER",
            )

        if not health.get("reachable", False):
            error = health.get("error", "")

            if "timeout" in str(error).lower():
                reasoning.append(
                    "Health endpoint timed out while "
                    "container remained running."
                )

                return RCAResult(
                    root_cause="SERVICE_HANG_OR_LATENCY",
                    confidence=0.92,
                    severity="HIGH",
                    reasoning=reasoning,
                    recommended_action="RESTART_CONTAINER",
                )

            reasoning.append(
                "Service is unreachable while container "
                "is reported as running."
            )

            return RCAResult(
                root_cause="APPLICATION_UNREACHABLE",
                confidence=0.88,
                severity="HIGH",
                reasoning=reasoning,
                recommended_action="RESTART_CONTAINER",
            )

        status_code = health.get("status_code")

        if status_code is not None and status_code >= 500:
            reasoning.append(
                f"Health endpoint returned HTTP {status_code}."
            )

            return RCAResult(
                root_cause="APPLICATION_HEALTH_FAILURE",
                confidence=0.97,
                severity="HIGH",
                reasoning=reasoning,
                recommended_action="RESTART_CONTAINER",
            )

        error_metric = (
            metrics.get("error_rate", {}).get("value")
            or 0.0
        )

        latency_metric = (
            metrics.get("latency", {}).get("value")
            or 0.0
        )

        request_rate = (
            metrics.get("request_rate", {}).get("value")
            or 0.0
        )

        if error_metric >= 0.20:
            reasoning.append(
                f"Error rate is {error_metric * 100:.2f}%."
            )
            reasoning.append(
                "Container and health endpoint are alive, "
                "indicating request-path failure."
            )

            return RCAResult(
                root_cause="HIGH_APPLICATION_ERROR_RATE",
                confidence=0.94,
                severity="HIGH",
                reasoning=reasoning,
                recommended_action="RESTART_CONTAINER",
            )

        if latency_metric >= 1.0:
            reasoning.append(
                f"Average request latency is "
                f"{latency_metric:.3f}s."
            )
            reasoning.append(
                "Health endpoint is alive, suggesting "
                "performance degradation rather than outage."
            )

            return RCAResult(
                root_cause="APPLICATION_LATENCY_DEGRADATION",
                confidence=0.91,
                severity="HIGH",
                reasoning=reasoning,
                recommended_action="RESTART_CONTAINER",
            )

        if request_rate <= 0:
            reasoning.append(
                "No measurable incoming request traffic."
            )

            return RCAResult(
                root_cause="NO_TRAFFIC",
                confidence=0.70,
                severity="LOW",
                reasoning=reasoning,
                recommended_action="OBSERVE",
            )

        reasoning.append(
            "Container, health endpoint, error rate, and "
            "latency are within expected ranges."
        )

        return RCAResult(
            root_cause="NO_ACTIVE_FAILURE",
            confidence=0.95,
            severity="NORMAL",
            reasoning=reasoning,
            recommended_action="NONE",
        )
