import json

from backend.rca.evidence_collector import EvidenceCollector
from backend.rca.rca_engine import RCAEngine


def main():
    collector = EvidenceCollector()
    engine = RCAEngine()

    print("=" * 70)
    print("AEGIS ROOT CAUSE ANALYSIS")
    print("=" * 70)

    print("Collecting evidence...")

    evidence = collector.collect()

    print(
        json.dumps(
            evidence,
            indent=2,
        )
    )

    print()
    print("=" * 70)
    print("RCA RESULT")
    print("=" * 70)

    result = engine.analyze(evidence)

    print(
        json.dumps(
            result.to_dict(),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
