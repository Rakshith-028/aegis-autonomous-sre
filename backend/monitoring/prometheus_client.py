from dataclasses import dataclass
from typing import Optional

import requests

from backend.config import PROMETHEUS_URL


@dataclass
class MetricResult:
    name: str
    value: Optional[float]
    query: str
    success: bool
    error: Optional[str] = None


class PrometheusClient:
    def __init__(
        self,
        base_url: str = PROMETHEUS_URL,
    ):
        self.base_url = base_url.rstrip("/")

    def query(
        self,
        name: str,
        promql: str,
    ) -> MetricResult:
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/query",
                params={"query": promql},
                timeout=5,
            )

            response.raise_for_status()

            payload = response.json()

            if payload.get("status") != "success":
                return MetricResult(
                    name=name,
                    value=None,
                    query=promql,
                    success=False,
                    error=(
                        "Prometheus returned "
                        "non-success status"
                    ),
                )

            result = payload["data"]["result"]

            if not result:
                return MetricResult(
                    name=name,
                    value=0.0,
                    query=promql,
                    success=True,
                )

            value = float(
                result[0]["value"][1]
            )

            return MetricResult(
                name=name,
                value=value,
                query=promql,
                success=True,
            )

        except (
            requests.RequestException,
            KeyError,
            ValueError,
        ) as error:
            return MetricResult(
                name=name,
                value=None,
                query=promql,
                success=False,
                error=str(error),
            )
