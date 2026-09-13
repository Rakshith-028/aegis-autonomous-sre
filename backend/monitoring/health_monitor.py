import time
from datetime import datetime

import requests

from backend.detection.failure_classifier import classify_failure
from backend.incidents.incident_manager import (
    create_incident,
    resolve_incident,
)
from backend.remediation.docker_remediator import restart_container


SERVICE_NAME = "orders"
CONTAINER_NAME = "aegis-orders"
HEALTH_URL = "http://localhost:8001/health"

CHECK_INTERVAL_SECONDS = 5
FAILURES_BEFORE_INCIDENT = 2
RECOVERY_WAIT_SECONDS = 3
RECOVERY_CHECK_ATTEMPTS = 5


def check_service() -> tuple[bool, str]:
    try:
        response = requests.get(
            HEALTH_URL,
            timeout=2,
        )

        if response.status_code == 200:
            return True, f"HTTP {response.status_code}"

        return False, f"HTTP {response.status_code}"

    except requests.Timeout:
        return False, "Request timed out"

    except requests.ConnectionError as error:
        return False, f"Connection failure: {error}"

    except requests.RequestException as error:
        return False, str(error)


def verify_recovery() -> bool:
    for attempt in range(1, RECOVERY_CHECK_ATTEMPTS + 1):
        time.sleep(RECOVERY_WAIT_SECONDS)

        healthy, detail = check_service()

        print(
            f"    Verification {attempt}/{RECOVERY_CHECK_ATTEMPTS}: "
            f"{'HEALTHY' if healthy else 'DOWN'} | {detail}"
        )

        if healthy:
            return True

    return False


def handle_failure(detail: str) -> None:
    failure_type = classify_failure(detail)

    print("\n" + "=" * 60)
    print("AEGIS INCIDENT DETECTED")
    print(f"Failure Type: {failure_type}")

    incident = create_incident(
        service_name=SERVICE_NAME,
        reason=f"{failure_type}: {detail}",
    )

    print(f"Incident: {incident['id']}")
    print(f"Service: {SERVICE_NAME}")
    print(f"Evidence: {detail}")

    if failure_type in {
        "SERVICE_DOWN",
        "HTTP_ERROR",
        "TIMEOUT",
    }:
        print("Decision: restart service")
    else:
        print("Decision: unknown failure - no automatic remediation")
        print("=" * 60 + "\n")
        return

    success, result = restart_container(CONTAINER_NAME)

    if not success:
        print(f"Remediation FAILED: {result}")
        print("=" * 60 + "\n")
        return

    print(f"Docker action successful: {result}")
    print("Verifying recovery...")

    recovered = verify_recovery()

    if recovered:
        resolve_incident(
            incident,
            remediation=(
                f"Restarted {CONTAINER_NAME} "
                f"after {failure_type}"
            ),
        )

        print("SERVICE RECOVERED")
        print(f"Incident {incident['id']} -> RESOLVED")

    else:
        print("Recovery verification FAILED")
        print(f"Incident {incident['id']} remains OPEN")

    print("=" * 60 + "\n")


def monitor() -> None:
    print("=" * 60)
    print("AEGIS FAILURE DETECTION + SELF-HEALING")
    print(f"Service: {SERVICE_NAME}")
    print(f"Container: {CONTAINER_NAME}")
    print(f"Target: {HEALTH_URL}")
    print("=" * 60)

    consecutive_failures = 0

    while True:
        healthy, detail = check_service()
        timestamp = datetime.now().strftime("%H:%M:%S")

        if healthy:
            if consecutive_failures > 0:
                print(
                    f"[{timestamp}] {SERVICE_NAME.upper()} "
                    f"-> RECOVERED | {detail}"
                )

            consecutive_failures = 0

        else:
            consecutive_failures += 1

            failure_type = classify_failure(detail)

            print(
                f"[{timestamp}] {SERVICE_NAME.upper()} "
                f"-> {failure_type} "
                f"{consecutive_failures}/{FAILURES_BEFORE_INCIDENT} "
                f"| {detail}"
            )

            if consecutive_failures >= FAILURES_BEFORE_INCIDENT:
                handle_failure(detail)
                consecutive_failures = 0

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    monitor()
