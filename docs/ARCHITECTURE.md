# AEGIS Architecture

AEGIS is an autonomous Site Reliability Engineering control plane that observes a service, diagnoses failures, applies policy-aware remediation, verifies recovery, and records postmortems.

## Closed-loop lifecycle

`mermaid
flowchart LR
    A[Observe] --> B[Detect]
    B --> C[Collect Evidence]
    C --> D[Root Cause Analysis]
    D --> E[Policy Engine]
    E --> F[Remediation]
    F --> G[Recovery Verification]
    G -->|Healthy| H[Resolve Incident]
    G -->|Still unhealthy| C
    H --> I[Postmortem]
`",
",


`mermaid
flowchart TB
    UI[Next.js Command Center]
    API[FastAPI Control Plane]
    RCA[RCA Engine]
    POLICY[Policy Engine]
    REM[Remediation Engine]
    VERIFY[Recovery Verifier]
    INC[Incident Store]
    PROM[Prometheus]
    ORDERS[Orders Service]
    DOCKER[Docker Engine]

    UI --> API
    API --> RCA
    RCA --> PROM
    RCA --> ORDERS
    RCA --> DOCKER
    RCA --> POLICY
    POLICY --> REM
    REM --> DOCKER
    REM --> VERIFY
    VERIFY --> ORDERS
    API --> INC
`",
",


- service health endpoint
- Docker container state
- request throughput
- HTTP error rate
- request latency
- recent container logs

Prometheus request metrics are scoped to the business request path and evaluated over a recent 20-second window.

## Root-cause classes

- CONTAINER_DOWN
- APPLICATION_UNREACHABLE
- APPLICATION_HEALTH_FAILURE
- SERVICE_HANG_OR_LATENCY
- HIGH_APPLICATION_ERROR_RATE
- APPLICATION_LATENCY_DEGRADATION
- NO_TRAFFIC
- NO_ACTIVE_FAILURE

## Safety model

LOW-risk actions may execute automatically with sufficient confidence.
MEDIUM-risk actions require human approval.
HIGH-risk actions are blocked from autonomous execution.

## Recovery semantics

After remediation AEGIS verifies service recovery. If verification fails, it collects fresh evidence, re-runs RCA, re-evaluates policy, and retries within a bounded attempt limit.

## Benchmarking

The benchmark suite measures precision, recall, F1, RCA accuracy, false positive rate, recovery success, MTTD, and MTTR.
