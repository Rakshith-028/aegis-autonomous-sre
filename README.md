<div align="center">

AEGIS

Autonomous AI SRE / Self-Healing Cloud Engineer

Observe -> Detect -> Diagnose -> Decide -> Remediate -> Verify -> Recover

<p>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-Control_Plane-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Next.js-16-000000?style=for-the-badge&logo=nextdotjs&logoColor=white" />
  <img src="https://img.shields.io/badge/TypeScript-Frontend-3178C6?style=for-the-badge&logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-Self_Healing-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/Prometheus-Observability-E6522C?style=for-the-badge&logo=prometheus&logoColor=white" />
</p>

<p>
  <img src="https://img.shields.io/badge/Precision-100%25-success?style=flat-square" />
  <img src="https://img.shields.io/badge/Recall-100%25-success?style=flat-square" />
  <img src="https://img.shields.io/badge/F1-100%25-success?style=flat-square" />
  <img src="https://img.shields.io/badge/RCA_Accuracy-100%25-success?style=flat-square" />
  <img src="https://img.shields.io/badge/Recovery-100%25-success?style=flat-square" />
  <img src="https://img.shields.io/badge/False_Positive_Rate-0%25-blue?style=flat-square" />
</p>

An autonomous reliability control plane that goes beyond monitoring and actively attempts to repair failing services.

</div>

What is AEGIS?

Traditional observability platforms tell engineers that something is broken.

AEGIS attempts to fix it.

AEGIS continuously gathers operational evidence, identifies likely root causes, evaluates whether remediation is safe, executes an approved recovery action, verifies that the service actually recovered, and records the incident.

Observe
  |
  v
Detect
  |
  v
Collect Evidence
  |
  v
Root Cause Analysis
  |
  v
Policy Decision
  |
  v
Remediation
  |
  v
Recovery Verification
  |
  v
Resolve / Re-diagnose

The core recovery loop is deterministic and does not depend on a paid LLM API.

Core Capabilities

Capability

Description

Live Monitoring

Tracks service health, request rate, error rate, and latency

Prometheus Telemetry

Queries operational metrics from Prometheus

Root Cause Analysis

Evidence-driven deterministic failure diagnosis

Incident Engine

Creates, deduplicates, and resolves incidents

Policy Engine

Controls which remediation actions may execute autonomously

Self-Healing

Automatically restarts supported failed or degraded Docker services

Recovery Verification

Confirms remediation actually restored service health

Bounded Retry

Re-collects evidence and re-diagnoses when recovery fails

Chaos Engineering

Injects latency, errors, hangs, and service failures

Postmortems

Generates incident recovery records

Benchmarking

Measures detection, RCA, and recovery performance

SRE Dashboard

Live Next.js command center with WebSocket telemetry

Tech Stack

<div align="center">

Layer

Technologies

Frontend

Next.js, TypeScript, Tailwind CSS, Recharts, Lucide

Backend

Python, FastAPI, Uvicorn

Observability

Prometheus

Infrastructure

Docker, Docker Compose

Testing

Pytest

Communication

REST, WebSockets

Reliability Logic

Statistical detection, rule-based RCA, policy engine

</div>

Architecture

flowchart TD
    UI["Next.js SRE Dashboard"]
    API["FastAPI Control Plane"]
    EVIDENCE["Evidence Collector"]
    RCA["RCA Engine"]
    INCIDENT["Incident Manager"]
    POLICY["Policy Engine"]
    REMEDIATION["Remediation Engine"]
    VERIFY["Recovery Verifier"]
    POST["Postmortem"]
    PROM["Prometheus"]
    ORDERS["Orders Service"]
    DOCKER["Docker Engine"]

    UI -->|REST + WebSocket| API
    API --> EVIDENCE
    API --> INCIDENT
    EVIDENCE --> PROM
    EVIDENCE --> ORDERS
    EVIDENCE --> DOCKER
    EVIDENCE --> RCA
    RCA --> POLICY
    POLICY --> REMEDIATION
    REMEDIATION --> DOCKER
    REMEDIATION --> VERIFY
    VERIFY --> ORDERS
    VERIFY -->|Healthy| INCIDENT
    VERIFY -->|Still Unhealthy| EVIDENCE
    INCIDENT --> POST

Detailed system documentation is available in docs/ARCHITECTURE.md.

Autonomous Recovery Lifecycle

Observe - collect service health, Docker state, request rate, error rate, latency, and recent logs.

Diagnose - determine the most likely failure with confidence, severity, reasoning, and a recommended action.

Decide - evaluate the recommended action against explicit safety policy.

Remediate - execute an allowed recovery action.

Verify - confirm service reachability, HTTP status, and response latency.

Retry if needed - collect fresh evidence and re-run RCA within a bounded attempt limit.

Resolve - close the incident and persist a postmortem.

Root-Cause Classes

AEGIS currently identifies:

CONTAINER_DOWN
APPLICATION_UNREACHABLE
APPLICATION_HEALTH_FAILURE
SERVICE_HANG_OR_LATENCY
HIGH_APPLICATION_ERROR_RATE
APPLICATION_LATENCY_DEGRADATION
NO_TRAFFIC
NO_ACTIVE_FAILURE

Example diagnosis:

{
  "root_cause": "APPLICATION_LATENCY_DEGRADATION",
  "confidence": 0.91,
  "severity": "HIGH",
  "recommended_action": "RESTART_CONTAINER"
}

Safety-First Autonomy

AEGIS separates diagnosis from permission to execute an action.

Risk Level

Autonomous Behaviour

LOW

Can auto-execute when confidence is sufficient

MEDIUM

Requires human approval

HIGH

Blocked from autonomous execution

This prevents the remediation engine from blindly executing every recommendation.

Chaos Engineering Laboratory

The demo environment supports controlled failure injection.

Scenario

Failure

Healthy Control

Normal system behaviour

Latency Degradation

Artificial request delay

High Error Rate

Elevated HTTP 5xx responses

Health Endpoint Failure

Health endpoint returns failure

Service Hang

Health request becomes extremely slow

Container Down

Entire service container stops

These scenarios exercise the complete reliability loop rather than isolated functions.

Verified Benchmark

AEGIS was evaluated using a controlled six-scenario autonomous SRE benchmark.

Metric

Result

Total Scenarios

6

True Positives

5

True Negatives

1

False Positives

0

False Negatives

0

Precision

100%

Recall

100%

F1 Score

100%

RCA Accuracy

100%

Recovery Success

100%

False Positive Rate

0%

Average MTTD

5.621 s

Average MTTR

10.03 s

Scenario Performance

Scenario

Detection

RCA

Recovery

Healthy Control

PASS

PASS

PASS

Latency Degradation

PASS

PASS

PASS

High Error Rate

PASS

PASS

PASS

Health Endpoint Failure

PASS

PASS

PASS

Service Hang

PASS

PASS

PASS

Container Down

PASS

PASS

PASS

These results describe the included controlled six-scenario benchmark and are not production-wide reliability guarantees.

Benchmark reports are persisted under:

benchmarks/results/

SRE Command Center

The dashboard provides a live operational view of:

service state

request throughput

error rate

latency

active incidents

RCA diagnosis and severity

live telemetry graph

chaos controls

recovery status

incident history

Live updates are delivered through WebSockets from the AEGIS control plane.

Demo Flow

1. Open the dashboard
2. Generate normal traffic
3. Observe healthy telemetry
4. Inject latency or another chaos scenario
5. Watch telemetry degrade
6. Trigger the autonomous cycle
7. AEGIS performs RCA
8. Policy engine approves an allowed remediation
9. Docker service is restarted
10. Recovery verifier confirms health
11. Dashboard returns to healthy
12. Incident is resolved

The latency scenario is particularly visual because the telemetry graph rises sharply and returns toward baseline after recovery.

Run the Complete Stack

Requirements

Docker Desktop

Docker Compose

From the repository root:

docker compose up -d --build

Check system state:

docker compose ps

Services

Service

Address

AEGIS Dashboard

http://localhost:3000

AEGIS Control Plane

http://localhost:8080

Orders Demo Service

http://localhost:8001

Prometheus

http://localhost:9090

Tests

Install development dependencies:

python -m pip install -r backend/requirements-dev.txt

Run:

pytest -q

Current automated test suite:

9 passed

Run the Benchmark

Windows PowerShell

$env:PYTHONPATH="."
python benchmarks\evaluate_aegis.py

Each execution creates a timestamped JSON report under benchmarks/results/.

Repository Structure

aegis/
|-- backend/
|   |-- api/
|   |-- detection/
|   |-- incidents/
|   |-- monitoring/
|   |-- policies/
|   |-- rca/
|   |-- remediation/
|   `-- verification/
|-- benchmarks/
|   `-- results/
|-- chaos/
|-- demo-system/
|   `-- orders/
|-- docs/
|   `-- ARCHITECTURE.md
|-- frontend/
|-- observability/
|   `-- prometheus/
|-- tests/
|-- docker-compose.yml
`-- README.md

Design Principles

Evidence Before Action

Every diagnosis is grounded in operational evidence.

Deterministic Core

Self-healing does not depend on an external AI API.

Safety Before Autonomy

Remediation recommendations pass through explicit policy checks.

Verify Every Recovery

Executing a command is not considered success until service health is restored.

Measure, Don't Just Demo

AEGIS includes a benchmark suite for precision, recall, F1, RCA accuracy, false-positive rate, MTTD, MTTR, and recovery success.

Future Roadmap

OpenTelemetry distributed tracing

Dependency-aware causal RCA

PostgreSQL-backed incident persistence

Kubernetes remediation

Horizontal autoscaling

Deployment rollback

Configuration restoration

Human approval workflows

Local open-source LLM investigation assistant

Multi-service dependency graph

Larger chaos benchmark suite

Long-running reliability evaluation

Security Note

The local demo mounts the Docker socket into the backend so AEGIS can execute container-level remediation.

Docker socket access is highly privileged. A production architecture should replace this with a restricted execution agent, scoped service account, or dedicated remediation API.

Why This Project Is Different

AEGIS is not just:

a monitoring dashboard

an alerting wrapper

a chatbot over logs

a static DevOps visualization

It implements a real autonomous feedback loop:

Detection
   |
   v
Diagnosis
   |
   v
Safety Decision
   |
   v
Real Infrastructure Action
   |
   v
Recovery Verification
   |
   v
Measurement

<div align="center">

AEGIS

Autonomous reliability engineering from detection to verified recovery.

Python | FastAPI | Next.js | TypeScript | Prometheus | Docker

</div>