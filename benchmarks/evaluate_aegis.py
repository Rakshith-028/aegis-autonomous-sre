import json
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import requests

from backend.api.autonomous_engine import (
    AutonomousEngine,
)
from backend.rca.evidence_collector import (
    EvidenceCollector,
)
from backend.rca.rca_engine import RCAEngine


ORDERS_URL = "http://localhost:8001"
CONTAINER_NAME = "aegis-orders"

REPORT_DIR = Path(
    "benchmarks/results"
)

POLL_INTERVAL_SECONDS = 2
MAX_DETECTION_SECONDS = 35
RESET_COOLDOWN_SECONDS = 12

stop_traffic = threading.Event()


SCENARIOS = [
    {
        "name": "healthy_control",
        "expected_failure": False,
        "expected_root_cause": (
            "NO_ACTIVE_FAILURE"
        ),
        "chaos": "reset",
    },
    {
        "name": "latency_degradation",
        "expected_failure": True,
        "expected_root_cause": (
            "APPLICATION_LATENCY_DEGRADATION"
        ),
        "chaos": "latency",
    },
    {
        "name": "high_error_rate",
        "expected_failure": True,
        "expected_root_cause": (
            "HIGH_APPLICATION_ERROR_RATE"
        ),
        "chaos": "errors",
    },
    {
        "name": "health_endpoint_failure",
        "expected_failure": True,
        "expected_root_cause": (
            "APPLICATION_HEALTH_FAILURE"
        ),
        "chaos": "error",
    },
    {
        "name": "service_hang",
        "expected_failure": True,
        "expected_root_cause": (
            "SERVICE_HANG_OR_LATENCY"
        ),
        "chaos": "slow",
    },
    {
        "name": "container_down",
        "expected_failure": True,
        "expected_root_cause": (
            "CONTAINER_DOWN"
        ),
        "chaos": "container_down",
    },
]


def traffic_worker():
    while not stop_traffic.is_set():
        try:
            requests.get(
                f"{ORDERS_URL}/",
                timeout=4,
            )
        except requests.RequestException:
            pass

        time.sleep(0.15)


def start_traffic_workers(
    count: int = 5,
):
    workers = []

    for _ in range(count):
        thread = threading.Thread(
            target=traffic_worker,
            daemon=True,
        )

        thread.start()
        workers.append(thread)

    return workers


def reset_environment():
    subprocess.run(
        [
            "docker",
            "start",
            CONTAINER_NAME,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    time.sleep(2)

    try:
        requests.post(
            f"{ORDERS_URL}/chaos/reset",
            timeout=5,
        )
    except requests.RequestException:
        pass

    time.sleep(
        RESET_COOLDOWN_SECONDS
    )


def inject_scenario(
    chaos: str,
):
    if chaos == "container_down":
        subprocess.run(
            [
                "docker",
                "stop",
                CONTAINER_NAME,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        return

    requests.post(
        f"{ORDERS_URL}/chaos/{chaos}",
        timeout=5,
    ).raise_for_status()


def detect_until_timeout(
    expected_failure: bool,
):
    collector = EvidenceCollector()
    engine = RCAEngine()

    started = time.perf_counter()

    last_rca = None

    while (
        time.perf_counter() - started
        < MAX_DETECTION_SECONDS
    ):
        evidence = collector.collect()

        rca = engine.analyze(
            evidence
        )

        last_rca = rca

        failure_detected = (
            rca.root_cause
            not in {
                "NO_ACTIVE_FAILURE",
                "NO_TRAFFIC",
            }
        )

        if (
            expected_failure
            and failure_detected
        ):
            return (
                rca,
                time.perf_counter()
                - started,
            )

        if not expected_failure:
            time.sleep(
                POLL_INTERVAL_SECONDS
            )
            continue

        time.sleep(
            POLL_INTERVAL_SECONDS
        )

    return (
        last_rca,
        None,
    )


def execute_scenario(
    scenario: dict,
) -> dict:
    print()
    print("=" * 76)
    print(
        f"SCENARIO: "
        f"{scenario['name']}"
    )
    print("=" * 76)

    reset_environment()

    injected_at = time.perf_counter()

    inject_scenario(
        scenario["chaos"]
    )

    print(
        f"Chaos injected: "
        f"{scenario['chaos']}"
    )

    if not scenario[
        "expected_failure"
    ]:
        time.sleep(10)

        collector = EvidenceCollector()
        rca_engine = RCAEngine()

        rca = rca_engine.analyze(
            collector.collect()
        )

        mttd = None

    else:
        rca, mttd = (
            detect_until_timeout(
                expected_failure=True
            )
        )

    predicted_root_cause = (
        rca.root_cause
        if rca is not None
        else None
    )

    failure_detected = (
        predicted_root_cause
        not in {
            None,
            "NO_ACTIVE_FAILURE",
            "NO_TRAFFIC",
        }
    )

    detection_correct = (
        failure_detected
        == scenario[
            "expected_failure"
        ]
    )

    rca_correct = (
        predicted_root_cause
        == scenario[
            "expected_root_cause"
        ]
    )

    if scenario["expected_failure"]:
        result = (
            AutonomousEngine()
            .run_once()
        )

        recovery_success = (
            result.get("status")
            == "RECOVERED"
        )

    else:
        result = {
            "status": "HEALTHY"
        }

        recovery_success = True

    finished_at = time.perf_counter()

    mttr = (
        finished_at
        - injected_at
        if scenario[
            "expected_failure"
        ]
        else None
    )

    record = {
        "scenario": scenario["name"],
        "expected_failure": (
            scenario[
                "expected_failure"
            ]
        ),
        "failure_detected": (
            failure_detected
        ),
        "detection_correct": (
            detection_correct
        ),
        "expected_root_cause": (
            scenario[
                "expected_root_cause"
            ]
        ),
        "predicted_root_cause": (
            predicted_root_cause
        ),
        "rca_correct": rca_correct,
        "engine_status": (
            result.get("status")
        ),
        "recovery_success": (
            recovery_success
        ),
        "mttd_seconds": (
            round(mttd, 3)
            if mttd is not None
            else None
        ),
        "mttr_seconds": (
            round(mttr, 3)
            if mttr is not None
            else None
        ),
    }

    print()
    print("BENCHMARK RESULT")

    print(
        json.dumps(
            record,
            indent=2,
        )
    )

    return record


def percentage(
    numerator: int,
    denominator: int,
) -> float:
    if denominator == 0:
        return 0.0

    return round(
        numerator
        / denominator
        * 100,
        2,
    )


def main():
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 76)
    print(
        "AEGIS AUTONOMOUS SRE BENCHMARK"
    )
    print("=" * 76)

    start_traffic_workers()

    results = []

    try:
        for scenario in SCENARIOS:
            results.append(
                execute_scenario(
                    scenario
                )
            )

    finally:
        stop_traffic.set()
        reset_environment()

    tp = sum(
        1
        for item in results
        if (
            item["expected_failure"]
            and item["failure_detected"]
        )
    )

    fp = sum(
        1
        for item in results
        if (
            not item["expected_failure"]
            and item["failure_detected"]
        )
    )

    tn = sum(
        1
        for item in results
        if (
            not item["expected_failure"]
            and not item[
                "failure_detected"
            ]
        )
    )

    fn = sum(
        1
        for item in results
        if (
            item["expected_failure"]
            and not item[
                "failure_detected"
            ]
        )
    )

    precision = (
        tp / (tp + fp)
        if (tp + fp)
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn)
        else 0.0
    )

    f1 = (
        2
        * precision
        * recall
        / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    total = len(results)

    rca_correct = sum(
        1
        for item in results
        if item["rca_correct"]
    )

    failure_results = [
        item
        for item in results
        if item["expected_failure"]
    ]

    recovery_successes = sum(
        1
        for item in failure_results
        if item[
            "recovery_success"
        ]
    )

    mttds = [
        item["mttd_seconds"]
        for item in failure_results
        if item[
            "mttd_seconds"
        ] is not None
    ]

    mttrs = [
        item["mttr_seconds"]
        for item in failure_results
        if (
            item["mttr_seconds"]
            is not None
            and item[
                "recovery_success"
            ]
        )
    ]

    summary = {
        "generated_at": (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        ),
        "total_scenarios": total,
        "confusion_matrix": {
            "true_positive": tp,
            "false_positive": fp,
            "true_negative": tn,
            "false_negative": fn,
        },
        "precision_percent": round(
            precision * 100,
            2,
        ),
        "recall_percent": round(
            recall * 100,
            2,
        ),
        "f1_percent": round(
            f1 * 100,
            2,
        ),
        "rca_accuracy_percent": (
            percentage(
                rca_correct,
                total,
            )
        ),
        "recovery_success_percent": (
            percentage(
                recovery_successes,
                len(failure_results),
            )
        ),
        "false_positive_rate_percent": (
            percentage(
                fp,
                fp + tn,
            )
        ),
        "average_mttd_seconds": (
            round(
                sum(mttds)
                / len(mttds),
                3,
            )
            if mttds
            else None
        ),
        "average_mttr_seconds": (
            round(
                sum(mttrs)
                / len(mttrs),
                3,
            )
            if mttrs
            else None
        ),
        "results": results,
    }

    timestamp = (
        datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
    )

    report_path = (
        REPORT_DIR
        / f"benchmark_{timestamp}.json"
    )

    with report_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            summary,
            file,
            indent=2,
        )

    print()
    print("=" * 76)
    print(
        "AEGIS BENCHMARK SUMMARY"
    )
    print("=" * 76)

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )

    print()
    print(
        f"Report saved: "
        f"{report_path}"
    )


if __name__ == "__main__":
    main()
