from dataclasses import dataclass

from backend.config import CONTAINER_NAME
from backend.remediation.docker_remediator import (
    restart_container,
)


@dataclass
class RemediationResult:
    success: bool
    action: str
    detail: str


class RemediationEngine:
    def execute(
        self,
        action: str,
    ) -> RemediationResult:

        if action == "RESTART_CONTAINER":
            success, detail = restart_container(
                CONTAINER_NAME
            )

            return RemediationResult(
                success=success,
                action=action,
                detail=detail,
            )

        if action == "OBSERVE":
            return RemediationResult(
                success=True,
                action=action,
                detail=(
                    "No active remediation executed."
                ),
            )

        if action == "NONE":
            return RemediationResult(
                success=True,
                action=action,
                detail=(
                    "No remediation required."
                ),
            )

        return RemediationResult(
            success=False,
            action=action,
            detail=(
                "Unsupported autonomous action: "
                f"{action}"
            ),
        )
