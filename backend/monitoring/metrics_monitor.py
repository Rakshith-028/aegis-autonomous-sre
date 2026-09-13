import time
from datetime import datetime

from backend.detection.anomaly_detector import RollingAnomalyDetector
from backend.incidents.incident_manager import (
    create_or_get_incident,
    get_active_incident,
    resolve_incident,
)
from backend.monitoring.prometheus_client import PrometheusClient


SERVICE_NAME = "orders"

CHECK_INTERVAL_SECONDS = 5
ANOMALIES_BEFORE_INCIDENT = 2
NORMAL_CYCLES_BEFORE_RESOLVE = 3


QUERIES = {
    "request_rate": (
        'sum(rate(orders_requests_total[1m]))'
    ),
    "error_rate": (
        'sum(rate(orders_requests_total{status_code=~"5.."}[1m])) '
        '/ clamp_min(sum(rate(orders_requests_total[1m])), 0.001)'
    ),
    "average_latency": (
        'sum(rate(orders_request_latency_seconds_sum[1m])) '
        '/ clamp_min('
        'sum(rate(orders_request_latency_seconds_count[1m])), '
        '0.001)'
    ),
}


class MetricIncidentTracker:
    def __init__(
        self,
        metric_name: str,
        incident_key: str,
    ):
        self.metric_name = metric_name
        self.incident_key = incident_key
        self.consecutive_anomalies = 0
        self.consecutive_normal = 0

    def process(
        self,
        result,
        value: float,
    ) -> None:
        if result.anomalous:
            self.consecutive_anomalies += 1
            self.consecutive_normal = 0

            print(
                f"  [ANOMALY] {self.metric_name.upper()} "
                f"{result.severity}: {result.reason}"
            )

            if (
                self.consecutive_anomalies
                >= ANOMALIES_BEFORE_INCIDENT
            ):
                incident, created = create_or_get_incident(
                    service_name=SERVICE_NAME,
                    incident_key=self.incident_key,
                    reason=result.reason,
                    severity=result.severity,
                    source="prometheus",
                    failure_type=(
                        f"{self.metric_name.upper()}_ANOMALY"
                    ),
                    metadata={
                        "metric": self.metric_name,
                        "value": value,
                        "z_score": result.z_score,
                    },
                )

                if created:
                    print(
                        f"  [INCIDENT OPENED] "
                        f"{incident['id']} | "
                        f"{incident['failure_type']}"
                    )
                else:
                    print(
                        f"  [DEDUPLICATED] Existing incident "
                        f"{incident['id']}"
                    )

        else:
            self.consecutive_anomalies = 0
            self.consecutive_normal += 1

            active = get_active_incident(
                SERVICE_NAME,
                self.incident_key,
            )

            if (
                active is not None
                and self.consecutive_normal
                >= NORMAL_CYCLES_BEFORE_RESOLVE
            ):
                resolved = resolve_incident(
                    active,
                    remediation=(
                        "Metric returned to normal baseline "
                        "without active remediation"
                    ),
                    metadata={
                        "recovery_type": "natural",
                        "final_value": value,
                    },
                )

                print(
                    f"  [INCIDENT RESOLVED] "
                    f"{resolved['id']} | "
                    f"{self.metric_name} normalized"
                )

                self.consecutive_normal = 0


def main() -> None:
    prometheus = PrometheusClient()

    latency_detector = RollingAnomalyDetector(
        metric_name="average_latency",
        window_size=20,
        minimum_samples=5,
        z_threshold=2.5,
        hard_threshold=1.0,
    )

    error_detector = RollingAnomalyDetector(
        metric_name="error_rate",
        window_size=20,
        minimum_samples=5,
        z_threshold=2.5,
        hard_threshold=0.20,
    )

    latency_tracker = MetricIncidentTracker(
        metric_name="average_latency",
        incident_key="metrics:orders:latency",
    )

    error_tracker = MetricIncidentTracker(
        metric_name="error_rate",
        incident_key="metrics:orders:error_rate",
    )

    print("=" * 76)
    print("AEGIS METRICS INTELLIGENCE ENGINE")
    print(f"Service: {SERVICE_NAME}")
    print(
        "Pipeline: Prometheus -> Detection -> "
        "Deduplication -> Incident State"
    )
    print("=" * 76)

    while True:
        timestamp = datetime.now().strftime("%H:%M:%S")

        request_rate = prometheus.query(
            "request_rate",
            QUERIES["request_rate"],
        )

        error_rate = prometheus.query(
            "error_rate",
            QUERIES["error_rate"],
        )

        latency = prometheus.query(
            "average_latency",
            QUERIES["average_latency"],
        )

        results = [
            request_rate,
            error_rate,
            latency,
        ]

        if not all(result.success for result in results):
            print(
                f"[{timestamp}] "
                "PROMETHEUS QUERY FAILURE"
            )

            for result in results:
                if not result.success:
                    print(
                        f"  {result.name}: "
                        f"{result.error}"
                    )

            time.sleep(CHECK_INTERVAL_SECONDS)
            continue

        request_value = request_rate.value or 0.0
        error_value = error_rate.value or 0.0
        latency_value = latency.value or 0.0

        latency_result = latency_detector.evaluate(
            latency_value
        )

        error_result = error_detector.evaluate(
            error_value
        )

        print(
            f"[{timestamp}] "
            f"RPS={request_value:.3f} | "
            f"ERROR={error_value * 100:.2f}% | "
            f"LATENCY={latency_value * 1000:.2f}ms"
        )

        latency_tracker.process(
            latency_result,
            latency_value,
        )

        error_tracker.process(
            error_result,
            error_value,
        )

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
