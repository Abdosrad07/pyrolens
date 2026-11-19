# TASK: IMPLEMENT EARLY WARNING CENTER — FRONTEND

You are the frontend developer for PyroLens, a NASA Space Apps Challenge project.

Implement the Early Warning Center interface independently while the backend developer works on anomaly detection and APIs.

## OBJECTIVE

Create a professional dashboard for monitoring statistical anomalies in satellite-detected fire activity.

Users must be able to identify anomalous areas, compare recent activity with historical baselines, visualize their geographic distribution, rank alerts and inspect explanations.

This feature must not imply real-time wildfire prediction.

## 1. INSPECT BEFORE CODING

Inspect:
- Frontend architecture
- Existing routes and navigation
- Design system
- Dark theme
- Existing Leaflet maps
- Existing chart libraries
- API service patterns
- Responsive behavior

Reuse existing components and styles.

Do not redesign unrelated pages.

## 2. DASHBOARD

Create a new Early Warning Center page.

### Summary cards

Display:
- Cells monitored
- Anomalies detected
- High-priority alerts
- Increasing activity zones

Cards must use values provided by the API.

### ALERT LIST

Create a ranked alerts list or table with:
- Severity
- Cell ID / location
- Recent detections
- Historical baseline
- Activity variation
- Persistence
- Sensor information

Features:
- Sort by severity
- Sort by activity
- Filter by severity
- Select an alert to inspect it

### INTERACTIVE MAP

Reuse the existing Leaflet infrastructure.

Requirements:
- Display anomalous cells
- Distinguish alert levels visually
- Clicking a cell selects its alert
- Synchronize map selection with the alert list
- Fit map bounds appropriately
- Handle missing coordinates
- Display a clear map legend

Do not create another map engine or duplicate map infrastructure.

### ALERT DETAILS

When the user selects an alert, show:
- Cell coordinates
- Severity
- Recent detections
- Historical median/baseline
- Anomaly score
- Persistence
- Sensors
- Observation period
- Reason for alert
- Limitations

Provide a chart comparing recent and historical activity using the existing charting library where possible.

## 3. API INTEGRATION

Expected endpoints:

GET /api/v1/early-warning/summary

GET /api/v1/early-warning/alerts

GET /api/v1/early-warning/alerts/{cell_id}

Use the shared API contract.

Until the backend is ready:
- Create a mock JSON fixture.
- Use the fixture through a service abstraction.
- Keep the interface ready to switch to real API data.
- Do not hardcode metrics inside components.

Keep API calls separated from UI logic.

## 4. STATES

Implement:
- Loading
- Successful response
- No anomalies
- API error
- Missing data
- Historical-data warning

Clearly display the data period and historical status.

If the API reports historical_backtest, display a visible notice that these are historical analytical results, not live alerts.

## 5. DESIGN

Follow PyroLens's existing visual identity:
- Dark interface
- Professional scientific monitoring aesthetic
- Consistent spacing and typography
- Existing colors and component conventions
- Responsive layout
- Avoid excessive animations
- No unnecessary visual clutter

The page must look like an operational scientific monitoring dashboard, not a generic admin template.

## 6. NAVIGATION

- Add Early Warning Center to the existing navigation.
- Ensure access from the main dashboard.
- Implement appropriate back-navigation where consistent with the application.
- Do not break existing navigation.

## 7. TESTING

- Test rendering with mock data.
- Test empty states.
- Test alert selection.
- Test filters and sorting.
- Test map/list synchronization.
- Test responsive behavior.
- Run frontend production build.

## 8. PRESERVE

Do not modify the scientific model or backend files.

Do not break:
- Overview
- Harmonization Lab
- Timeline
- Quality
- Risk
- Chatbot
- Existing navigation
- Existing API integrations

## 9. DELIVERABLES

Report:
- Files created/modified
- Components created
- Route added
- Mock fixture location
- API integration approach
- Tests executed
- Build result
- Screenshots of the completed dashboard

Work only on frontend scope.