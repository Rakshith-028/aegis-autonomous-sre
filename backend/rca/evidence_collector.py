import json
import subprocess
from datetime import datetime

import requests

from backend.config import (
    CONTAINER_NAME,
    HEALTH_URL,
    SERVICE_NAME,
)
from backend.monitoring.prometheus_client import (
    PrometheusClient,
)


class EvidenceCollector:
    def __init__(self):
        self.prometheus = PrometheusClient()

    def _docker_state(self) -> dict:
        try:
            result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    CONTAINER_NAME,
                    "--format",
                    "{{json .State}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            if result.returncode != 0:
                return {
                    "available": False,
                    "error": (
                        result.stderr.strip()
                        or result.stdout.strip()
                    ),
                }

            return {
                "available": True,
                "state": json.loads(
                    result.stdout.strip()
                ),
            }

        except Exception as error:
            return {
                "available": False,
                "error": str(error),
            }

    def _recent_logs(self) -> list[str]:
        try:
            result = subprocess.run(
                [
                    "docker",
                    "logs",
                    "--tail",
                    "30",
                    CONTAINER_NAME,
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            content = (
                result.stdout
                + "\n"
                + result.stderr
            ).strip()

            if not content:
                return []

            return content.splitlines()[-30:]

        except Exception as error:
            return [
                f"log collection failed: {error}"
            ]

    def _health(self) -> dict:
        try:
            response = requests.get(
                HEALTH_URL,
                timeout=2,
            )

            return {
                "reachable": True,
                "status_code": (
                    response.status_code
                ),
                "latency_seconds": (
                    response.elapsed
                    .total_seconds()
                ),
            }

        except requests.Timeout:
            return {
                "reachable": False,
                "status_code": None,
                "error": "timeout",
            }

        except requests.RequestException as error:
            return {
                "reachable": False,
                "status_code": None,
                "error": str(error),
            }

    def _metric(
        self,
        name: str,
        query: str,
    ) -> dict:
        result = self.prometheus.query(
            name,
            query,
        )

        return {
            "success": result.success,
            "value": result.value,
            "error": result.error,
        }

    def collect(self) -> dict:
        return {
            "service": SERVICE_NAME,
            "timestamp": (
                datetime.now().isoformat(
                    timespec="seconds"
                )
            ),
            "health": self._health(),
            "container": self._docker_state(),
            "metrics": {
                "request_rate": self._metric(
                    "request_rate",
                    (
                        'sum(rate('
                        'orders_requests_total'
                        '{endpoint="/"}[20s]))'
                    ),
                ),
                "error_rate": self._metric(
                    "error_rate",
                    (
                        'sum(rate('
                        'orders_requests_total'
                        '{endpoint="/",'
                        'status_code=~"5.."}'
                        '[20s])) '
                        '/ clamp_min('
                        'sum(rate('
                        'orders_requests_total'
                        '{endpoint="/"}[20s]'
                        ')), 0.001)'
                    ),
                ),
                "latency": self._metric(
                    "latency",
                    (
                        'sum(rate('
                        'orders_request_latency_seconds_sum'
                        '{endpoint="/"}[20s]'
                        ')) / clamp_min('
                        'sum(rate('
                        'orders_request_latency_seconds_count'
                        '{endpoint="/"}[20s]'
                        ')), 0.001)'
                    ),
                ),
            },
            "logs": self._recent_logs(),
        }
