# TASK: IMPLEMENT EARLY WARNING CENTER — BACKEND

You are the backend developer for PyroLens, a NASA Space Apps Challenge project.

Your task is to implement the backend component of the Early Warning Center independently, allowing the frontend developer to work in parallel.

## OBJECTIVE

Build a statistical anomaly detection service that analyzes satellite-detected fire activity from NASA FIRMS, compares recent activity against historical baselines, identifies anomalous grid cells, ranks alerts, and exposes results through FastAPI.

This is an anomaly detection system, not a real-time wildfire prediction system.

## 1. INSPECT BEFORE CODING

Inspect:
- FIRMS dataset structure
- Existing grid aggregation logic
- Existing prediction pipeline
- Data artifacts
- FastAPI routers and services
- Existing tests and conventions

Reuse existing logic wherever possible.

Do not modify the existing prediction model or unrelated modules.

## 2. ANOMALY DETECTION ENGINE

For each existing 0.25° geographic cell:

Calculate:
- Historical detection counts
- Historical median
- Historical variability using a robust statistical method
- Recent detection count
- Activity deviation
- Anomaly score
- Activity persistence across periods
- Alert severity

Handle sparse data, zero-heavy distributions and missing observations correctly.

Do not rely blindly on Z-scores. Choose a suitable method and explain the statistical reasoning.

Alert categories:
- NORMAL
- WATCH
- MODERATE
- HIGH

Thresholds must be configurable and justified.

Do not classify cells with insufficient history as high-confidence anomalies.

## 3. DATA VALIDATION

- Use actual FIRMS data.
- Respect temporal boundaries.
- Avoid data leakage.
- Clearly separate recent and historical periods.
- Do not compare incompatible observation periods without normalization.
- Handle missing data and insufficient history.
- Handle historical baselines of zero.
- Avoid interpreting MODIS and VIIRS detections as distinct fire events.
- Preserve provenance and sensor information.

If the available dataset ends in 2020, label results as HISTORICAL BACKTEST.

Never imply current or real-time monitoring if the data are historical.

## 4. API CONTRACT

Implement the following endpoints, adapting route conventions as necessary:

GET /api/v1/early-warning/summary

GET /api/v1/early-warning/alerts

GET /api/v1/early-warning/alerts/{cell_id}

The API must return JSON compatible with the frontend team's shared contract.

Include:
- Metadata
- Reference period
- Data coverage
- Cells monitored
- Alert counts
- Ranked alerts
- Coordinates
- Recent activity
- Historical baseline
- Anomaly score
- Persistence
- Sensor information
- Alert explanation
- Limitations

Create an example response fixture for frontend integration.

## 5. SUGGESTED STRUCTURE

Adapt to the current project architecture. Do not force this structure if equivalent modules already exist.

Potential modules:
- anomaly_detection.py
- early_warning_service.py
- early_warning_router.py
- schemas.py

Keep statistical calculations separate from API logic.

## 6. TESTS

Add tests for:
- Normal activity
- Activity spikes
- Sparse cells
- Zero historical baseline
- Missing observations
- Insufficient history
- Persistence
- Severity classification
- Invalid input
- API serialization
- API error handling

Run backend tests and report the results.

## 7. PRESERVE

Do not break:
- Existing prediction model
- Harmonization
- Overview
- Timeline
- Quality
- Risk
- Chatbot
- Existing API contracts

Avoid unnecessary dependencies.

## 8. DELIVERABLES

Report:
- Files created/modified
- Statistical methodology
- Severity classification logic
- API endpoints
- Fixture location
- Test results
- Data coverage
- Limitations

Do not fabricate metrics or test results.

Work only on the backend scope.