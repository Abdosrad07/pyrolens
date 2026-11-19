# TASK — IMPLEMENT PYROLENS EARLY WARNING CENTER

## Objective
Add a new feature called **Early Warning Center** to PyroLens.

Its purpose is to detect unusual increases in satellite-detected fire activity by comparing recent activity with historical patterns, rank anomalous geographic cells, and explain why each alert was triggered.

This is an anomaly detection system, NOT a real-time disaster prediction system.

## 1. BEFORE CODING
- Inspect the existing backend, data structures, prediction artifacts, grid system, API and frontend architecture.
- Identify existing functions that can be reused.
- Report briefly the implementation plan and relevant files.
- Do not duplicate existing logic or modify unrelated features.

## 2. DETECTION ENGINE
Implement a Python anomaly detection engine using available FIRMS data.

For each 0.25° grid cell:
- Calculate historical detection frequency.
- Calculate historical median and dispersion.
- Calculate recent detection activity.
- Compare recent activity with its historical baseline.
- Detect unusually high activity.
- Measure persistence across consecutive periods.
- Rank anomalous cells by severity.

Prefer robust statistics such as median/MAD or appropriate count-based methods when standard Z-scores are unsuitable for sparse, zero-heavy data.

### Alert levels
Create 4 levels:
- NORMAL
- WATCH
- MODERATE
- HIGH

Thresholds must be configurable and statistically defensible. Avoid arbitrary thresholds where possible.

Each alert must include:
- Cell ID
- Latitude / longitude
- Recent detection count
- Historical baseline
- Relative change
- Anomaly score
- Persistence
- Severity
- Sensors involved
- Observation period
- Explanation of why it was flagged

Do not invent data or explanations.

## 3. SCIENTIFIC AND DATA INTEGRITY RULES
- Use only existing data and verifiable observations.
- Clearly distinguish historical and recent periods.
- Prevent temporal leakage.
- Ensure baseline and recent periods do not overlap improperly.
- Handle missing data and insufficient history.
- Avoid misleading percentage changes when the historical baseline is zero.
- Do not treat MODIS and VIIRS detections as independent fires.
- Do not call an anomaly a confirmed wildfire.
- Never label this feature as real-time if the data are historical.
- Preserve the existing 0.25° grid and data provenance.

If the current dataset does not contain suitable recent observations, implement and test the system using historical periods, clearly labeling the results as a historical demonstration.

## 4. BACKEND
Create a modular anomaly detection service.

Reuse existing project conventions and avoid unnecessary dependencies.

Expose the results through an API endpoint compatible with the existing FastAPI architecture.

The endpoint must return:
- Summary statistics
- Total anomalous cells
- Alert counts by severity
- Ranked alerts
- Geographic coordinates
- Historical/recent comparison
- Data coverage and reference period
- Limitations

Ensure appropriate handling of errors, empty datasets and missing artifacts.

## 5. FRONTEND — EARLY WARNING CENTER
Create a new dashboard page consistent with the existing PyroLens design system and dark theme.

Include:

### Summary cards
- Cells monitored
- Anomalies detected
- High-priority alerts
- Increasing activity zones

### Alert table/list
Display:
- Alert level
- Geographic area / coordinates
- Recent activity
- Historical baseline
- Activity variation
- Persistence

Allow sorting by severity and activity.

### Interactive map
- Display anomalous cells geographically.
- Distinguish alert severity visually.
- Clicking a cell must open its detailed information.
- Reuse the existing Leaflet implementation.

### Alert details
When an alert is selected, show:
- Recent vs historical activity chart
- Anomaly score
- Sensors involved
- Period analyzed
- Reason for alert
- Data limitations

### UX
- Loading state
- Empty state
- API error state
- Responsive layout
- Navigation access to Early Warning Center

## 6. ALERT EXPLANATION
Generate explanations from actual metrics, not an LLM.

Example:
"Activity in this cell reached 24 detections during the recent observation period, compared with a historical median of 5. Activity is unusually elevated relative to the selected baseline."

Do not claim that wind, drought, human activity or any other factor caused the anomaly unless supported by data.

## 7. TESTS
Add tests covering:
- Normal activity
- Unusual activity spikes
- Zero historical baseline
- Missing data
- Insufficient history
- Persistence
- Severity ranking
- Invalid periods
- API responses
- Frontend build

Run:
- pytest
- Frontend production build

Fix regressions introduced by this feature.

## 8. PRESERVE EXISTING FEATURES
Do not redesign or break:
- Overview
- Harmonization Lab
- Timeline / Fire Calendar
- Quality
- Risk
- Existing prediction model
- Chatbot
- Existing API contracts
- Existing data artifacts

Avoid modifying the current prediction model or its scientific evaluation.

## 9. FINAL REPORT
At completion, report:
1. Files created and modified
2. Detection methodology
3. Severity thresholds and justification
4. API endpoint
5. Frontend components and navigation
6. Data period actually used
7. Tests executed and results
8. Known limitations
9. Screenshots or a short demonstration of the feature

Work incrementally. Prioritize scientific correctness, reuse, clarity and a working feature over visual complexity.

Do not fabricate test results or metrics.