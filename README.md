<div align="center">

âš¡ AEGIS

Autonomous AI SRE / Self-Healing Cloud Engineer

Observe â†’ Detect â†’ Diagnose â†’ Decide â†’ Remediate â†’ Verify â†’ Recover

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
  <img src="https://img.shields.io/badge/RCA_Accuracy-100%25-success?style=flat-square" />
  <img src="https://img.shields.io/badge/Recovery-100%25-success?style=flat-square" />
  <img src="https://img.shields.io/badge/False_Positive_Rate-0%25-blue?style=flat-square" />
</p>

An autonomous reliability control plane that goes beyond monitoring and actively repairs failing services.

</div>

ðŸš€ What is AEGIS?

Traditional observability platforms tell engineers that something is broken.

AEGIS attempts to fix it.

It continuously gathers operational evidence, identifies likely root causes, evaluates whether remediation is safe, executes an approved recovery action, verifies that the service actually recovered, and records the incident.

Observe
   â†“
Detect
   â†“
Collect Evidence
   â†“
Root Cause Analysis
   â†“
Policy Decision
   â†“
Remediation
   â†“
Recovery Verification
   â†“
Resolve / Re-diagnose

The core recovery loop is deterministic and does not depend on a paid LLM API.

âœ¨ Core Capabilities

Capability

Description

ðŸ“¡ Live Monitoring

Tracks service health, request rate, error rate and latency

ðŸ“Š Prometheus Telemetry

Queries real operational metrics from Prometheus

ðŸ§  Root Cause Analysis

Evidence-driven deterministic failure diagnosis

ðŸš¨ Incident Engine

Creates, deduplicates and resolves incidents

ðŸ›¡ï¸ Policy Engine

Controls which remediation actions can execute autonomously

ðŸ”§ Self-Healing

Automatically restarts failed or degraded Docker services

âœ… Recovery Verification

Confirms remediation actually restored service health

ðŸ” Bounded Retry

Re-collects evidence and re-diagnoses if recovery fails

ðŸ’¥ Chaos Engineering

Injects latency, errors, hangs and service failures

ðŸ“ Postmortems

Generates incident recovery records

ðŸ“ˆ Benchmarking

Measures detection, RCA and recovery performance

ðŸ–¥ï¸ SRE Dashboard

Live Next.js command center with WebSocket telemetry

ðŸ§° Tech Stack

<div align="center">

Layer

Technologies

Frontend

Next.js Â· TypeScript Â· Tailwind CSS Â· Recharts Â· Lucide

Backend

Python Â· FastAPI Â· Uvicorn

Observability

Prometheus

Infrastructure

Docker Â· Docker Compose

Testing

Pytest

Communication

REST Â· WebSockets

Reliability Logic

Statistical detection Â· Rule-based RCA Â· Policy engine

</div>

ðŸ—ï¸ Architecture

flowchart TD
    UI["ðŸ–¥ï¸ Next.js SRE Dashboard"]
    API["âš¡ FastAPI Control Plane"]
    EVIDENCE["ðŸ”Ž Evidence Collector"]
    RCA["ðŸ§  RCA Engine"]
    INCIDENT["ðŸš¨ Incident Manager"]
    POLICY["ðŸ›¡ï¸ Policy Engine"]
    REMEDIATION["ðŸ”§ Remediation Engine"]
    VERIFY["âœ… Recovery Verifier"]
    POST["ðŸ“ Postmortem"]
    PROM["ðŸ“Š Prometheus"]
    ORDERS["ðŸ“¦ Orders Service"]
    DOCKER["ðŸ³ Docker Engine"]

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

ðŸ”„ Autonomous Recovery Lifecycle

Observe â€” collect service health, Docker state, request rate, error rate, latency and recent logs.

Diagnose â€” determine the most likely failure with confidence, severity, reasoning and recommended action.

Decide â€” evaluate the action against explicit safety policy.

Remediate â€” execute an allowed recovery action.

Verify â€” confirm service reachability, HTTP status and response latency.

Retry if needed â€” collect fresh evidence and re-run RCA within a bounded attempt limit.

Resolve â€” close the incident and persist a postmortem.

ðŸ§  Root-Cause Classes

CONTAINER_DOWN
APPLICATION_UNREACHABLE
APPLICATION_HEALTH_FAILURE
SERVICE_HANG_OR_LATENCY
HIGH_APPLICATION_ERROR_RATE
APPLICATION_LATENCY_DEGRADATION
NO_TRAFFIC
NO_ACTIVE_FAILURE

Example:

{
  "root_cause": "APPLICATION_LATENCY_DEGRADATION",
  "confidence": 0.91,
  "severity": "HIGH",
  "recommended_action": "RESTART_CONTAINER"
}

ðŸ›¡ï¸ Safety-First Autonomy

AEGIS does not blindly execute every recommended action.

Risk Level

Autonomous Behaviour

ðŸŸ¢ LOW

Can auto-execute with sufficient confidence

ðŸŸ¡ MEDIUM

Requires human approval

ðŸ”´ HIGH

Blocked from autonomous execution

This keeps diagnosis, recommendation and permission to execute as separate concerns.

ðŸ’¥ Chaos Engineering Laboratory

The demo environment supports controlled failure injection.

Scenario

Failure

ðŸŸ¢ Healthy Control

Normal system behaviour

ðŸŸ  Latency Degradation

Artificial request delay

ðŸ”´ High Error Rate

Elevated HTTP 5xx responses

ðŸ”´ Health Failure

/health returns failure

ðŸŸ£ Service Hang

Health request becomes extremely slow

âš« Container Down

Entire service container stops

ðŸ“Š Verified Benchmark

AEGIS was evaluated using a six-scenario autonomous SRE benchmark.

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

âœ…

âœ…

âœ…

Latency Degradation

âœ…

âœ…

âœ…

High Error Rate

âœ…

âœ…

âœ…

Health Endpoint Failure

âœ…

âœ…

âœ…

Service Hang

âœ…

âœ…

âœ…

Container Down

âœ…

âœ…

âœ…

These results describe the included controlled six-scenario benchmark and are not production-wide reliability guarantees.

Reports are persisted under:

benchmarks/results/

ðŸ–¥ï¸ SRE Command Center

The dashboard provides a live operational view of:

service state

request throughput

error rate

latency

active incidents

RCA diagnosis

severity

live telemetry graph

chaos controls

recovery status

incident history

Live updates are delivered through WebSockets from the AEGIS control plane.

ðŸŽ¬ Demo Flow

1. Open the dashboard
2. Generate normal traffic
3. Observe healthy telemetry
4. Inject latency or another chaos scenario
5. Watch telemetry degrade
6. Trigger the autonomous cycle
7. AEGIS performs RCA
8. Policy engine approves remediation
9. Docker service is restarted
10. Recovery verifier confirms health
11. Dashboard returns to healthy
12. Incident is resolved

The latency scenario is especially visual because the graph spikes and then drops back toward baseline after recovery.

ðŸ³ Run the Complete Stack

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

ðŸ–¥ï¸ AEGIS Dashboard

http://localhost:3000

âš¡ AEGIS Control Plane

http://localhost:8080

ðŸ“¦ Orders Demo Service

http://localhost:8001

ðŸ“Š Prometheus

http://localhost:9090

ðŸ§ª Tests

Install development dependencies:

python -m pip install -r backend/requirements-dev.txt

Run:

pytest -q

Current automated test suite:

9 passed

ðŸ“ˆ Run the Benchmark

Windows PowerShell

$env:PYTHONPATH="."
python benchmarks\evaluate_aegis.py

Each benchmark execution creates a timestamped JSON report under:

benchmarks/results/

ðŸ“ Repository Structure

aegis/
â”‚
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ api/
â”‚   â”œâ”€â”€ detection/
â”‚   â”œâ”€â”€ incidents/
â”‚   â”œâ”€â”€ monitoring/
â”‚   â”œâ”€â”€ policies/
â”‚   â”œâ”€â”€ rca/
â”‚   â”œâ”€â”€ remediation/
â”‚   â””â”€â”€ verification/
â”‚
â”œâ”€â”€ benchmarks/
â”‚   â””â”€â”€ results/
â”œâ”€â”€ chaos/
â”œâ”€â”€ demo-system/
â”‚   â””â”€â”€ orders/
â”œâ”€â”€ docs/
â”‚   â””â”€â”€ ARCHITECTURE.md
â”œâ”€â”€ frontend/
â”œâ”€â”€ observability/
â”‚   â””â”€â”€ prometheus/
â”œâ”€â”€ tests/
â””â”€â”€ docker-compose.yml

ðŸ§© Design Principles

Evidence Before Action

Every diagnosis is grounded in operational evidence.

Deterministic Core

Self-healing does not depend on an external AI API.

Safety Before Autonomy

Remediation recommendations pass through explicit policy checks.

Verify Every Recovery

Executing a restart is not considered success until the service is healthy again.

Measure, Don't Just Demo

AEGIS contains a benchmark suite for precision, recall, F1, RCA accuracy, false-positive rate, MTTD, MTTR and recovery success.

ðŸ—ºï¸ Future Roadmap

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

ðŸ” Security Note

The local demo mounts the Docker socket into the backend so AEGIS can execute container-level remediation.

Docker socket access is highly privileged. For production, this should be replaced with a restricted execution agent, scoped service account, or dedicated remediation API.

ðŸ’¡ Why This Project Is Different

AEGIS is not:

a monitoring dashboard

an alerting wrapper

a chatbot over logs

a static DevOps visualization

It implements a real autonomous feedback loop:

Detection
    â†“
Diagnosis
    â†“
Safety Decision
    â†“
Real Infrastructure Action
    â†“
Recovery Verification
    â†“
Measurement

<div align="center">

âš¡ AEGIS

Autonomous reliability engineering from detection to verified recovery.

Python Â· FastAPI Â· Next.js Â· TypeScript Â· Prometheus Â· Docker

</div>