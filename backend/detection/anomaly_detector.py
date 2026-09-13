from collections import deque
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Deque


@dataclass
class AnomalyResult:
    metric: str
    value: float
    anomalous: bool
    severity: str
    reason: str
    z_score: float


class RollingAnomalyDetector:
    def __init__(
        self,
        metric_name: str,
        window_size: int = 20,
        minimum_samples: int = 5,
        z_threshold: float = 2.5,
        hard_threshold: float | None = None,
    ):
        self.metric_name = metric_name
        self.window_size = window_size
        self.minimum_samples = minimum_samples
        self.z_threshold = z_threshold
        self.hard_threshold = hard_threshold
        self.history: Deque[float] = deque(maxlen=window_size)

    def evaluate(self, value: float) -> AnomalyResult:
        if (
            self.hard_threshold is not None
            and value >= self.hard_threshold
        ):
            result = AnomalyResult(
                metric=self.metric_name,
                value=value,
                anomalous=True,
                severity="HIGH",
                reason=(
                    f"hard threshold exceeded: "
                    f"{value:.4f} >= {self.hard_threshold:.4f}"
                ),
                z_score=0.0,
            )

            self.history.append(value)
            return result

        if len(self.history) < self.minimum_samples:
            self.history.append(value)

            return AnomalyResult(
                metric=self.metric_name,
                value=value,
                anomalous=False,
                severity="NORMAL",
                reason="baseline warming up",
                z_score=0.0,
            )

        baseline_mean = mean(self.history)
        baseline_std = pstdev(self.history)

        if baseline_std == 0:
            z_score = 0.0
        else:
            z_score = (value - baseline_mean) / baseline_std

        anomalous = z_score >= self.z_threshold

        if anomalous:
            if z_score >= 4:
                severity = "CRITICAL"
            elif z_score >= 3:
                severity = "HIGH"
            else:
                severity = "MEDIUM"

            reason = (
                f"statistical anomaly: z={z_score:.2f}, "
                f"baseline={baseline_mean:.4f}"
            )
        else:
            severity = "NORMAL"
            reason = (
                f"within baseline: z={z_score:.2f}, "
                f"baseline={baseline_mean:.4f}"
            )

        self.history.append(value)

        return AnomalyResult(
            metric=self.metric_name,
            value=value,
            anomalous=anomalous,
            severity=severity,
            reason=reason,
            z_score=z_score,
        )
