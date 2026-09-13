import time

import requests

from backend.config import HEALTH_URL


class RecoveryVerifier:
    def __init__(
        self,
        attempts: int = 5,
        delay_seconds: int = 2,
    ):
        self.attempts = attempts
        self.delay_seconds = delay_seconds

    def verify(
        self,
    ) -> tuple[bool, list[dict]]:
        results = []

        for attempt in range(
            1,
            self.attempts + 1,
        ):
            time.sleep(
                self.delay_seconds
            )

            started = time.perf_counter()

            try:
                response = requests.get(
                    HEALTH_URL,
                    timeout=2,
                )

                latency = (
                    time.perf_counter()
                    - started
                )

                healthy = (
                    response.status_code == 200
                    and latency < 1.0
                )

                result = {
                    "attempt": attempt,
                    "status_code": (
                        response.status_code
                    ),
                    "latency_seconds": round(
                        latency,
                        4,
                    ),
                    "healthy": healthy,
                }

            except requests.RequestException as error:
                result = {
                    "attempt": attempt,
                    "status_code": None,
                    "latency_seconds": None,
                    "healthy": False,
                    "error": str(error),
                }

            results.append(result)

            if result["healthy"]:
                return True, results

        return False, results
