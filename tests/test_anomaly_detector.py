from backend.detection.anomaly_detector import (
    RollingAnomalyDetector,
)


def test_hard_threshold_detection():
    detector = RollingAnomalyDetector(
        metric_name="latency",
        hard_threshold=1.0,
    )

    result = detector.evaluate(
        1.5
    )

    assert result.anomalous is True
    assert result.severity == "HIGH"


def test_baseline_warmup():
    detector = RollingAnomalyDetector(
        metric_name="latency",
        minimum_samples=5,
    )

    result = detector.evaluate(
        0.1
    )

    assert result.anomalous is False
    assert (
        result.reason
        == "baseline warming up"
    )
