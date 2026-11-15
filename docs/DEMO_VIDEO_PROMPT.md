# Prompt for AI Agent: Create PyroLens Demo Video and PowerPoint Presentation

## Project Overview

**PyroLens** is a NASA Space Apps Challenge 2026 project that provides reproducible comparison, harmonization, and risk modeling of MODIS and VIIRS thermal anomaly detections over Cameroon and West Africa.

### Key Concept
PyroLens does **NOT** predict wildfires. It predicts the probability that a satellite will *detect* at least one fire hotspot in a grid cell. This is a critical distinction that must be emphasized throughout all materials.

### Golden Rule
A satellite detection is an **observation**, not a wildfire. An empty cell **never** means "no fire" — clouds, night, viewing angles, and overpass times create blind spots. Every output carries `data_origin` and `estimate_kind` for full provenance.

---

## Task 1: 30-Second Demo Video

### Video Structure (30 seconds total)

**0-4 seconds: Opening Hook**
- Show world map → zoom to Cameroon
- Display NASA FIRMS hotspots lighting up
- Voiceover/text: "Two NASA sensors see the same fires differently"

**4-10 seconds: Sensor Comparison**
- Click on a zone on the map
- Show analysis panel appearing
- Display Jaccard VIIRS/MODIS comparison metrics
- Highlight the set overlap concept (not accuracy)

**10-16 seconds: Historical Analysis**
- Switch to "Historique" (History) view
- Show multi-year calendar spanning 2019-2025
- Display historical detection patterns

**16-22 seconds: Risk Model**
- Activate risk layer on the map
- Show heatmap of 1,215 grid cells with calibrated probabilities
- Display metrics: PR-AUC 0.926, F1 0.841
- Label clearly: "Historical backtest (2019-2020)"

**22-27 seconds: Data Quality & Jobs**
- Show Calendar view with real divergence data
- Show Quality view with audit.json statistics
- Show Jobs view with a real job in progress

**27-30 seconds: Closing**
- Logo + tagline: "PyroLens — reproducible, honest fire monitoring"
- Fade to black

### Required Screenshots
1. Map with hotspots + active risk layer
2. Zone analysis panel with Jaccard metrics
3. Historical multi-year calendar
4. Risk panel with model metrics (PR-AUC, F1, Brier score)
5. Jobs view with real job
6. Quality view (audit.json)

### Technical Requirements
- Video format: MP4, 1920x1080 or higher
- English subtitles burned into the video
- Smooth transitions between screens
- Professional, clean aesthetic
- No NASA logos reproduced (use attribution text only)

---

## Task 2: PowerPoint Presentation (7 slides alternative)

### Slide 1: Problem
**Title:** The Challenge
**Content:**
- Two NASA sensors (MODIS Terra/Aqua, VIIRS) measure the same fires differently
- Need for harmonization and comparison
- Subtitle: "Making multi-sensor fire monitoring transparent"

**Visual:** Photo of wildfires + sensor logos (text representation, not actual NASA logos)

### Slide 2: Solution
**Title:** PyroLens in One Sentence
**Content:**
- Reproducible Python pipeline + interactive map + calibrated risk model
- Three core capabilities:
  1. Sensor comparison (Jaccard overlap)
  2. On-demand zone analysis (NRT + historical)
  3. Detected activity probability prediction

**Visual:** Simplified architecture diagram

### Slide 3: Data
**Title:** Data Credibility
**Content:**
- 1,171 FIRMS files (2013-2020) — ~1.8M detections
- Country archives (2013-2025) — 18 countries, open access
- Validated zone comparison: 410k VIIRS + 80k MODIS detections, Jaccard 0.335
- All data with full provenance (`data_origin`, SHA-256 manifests)

**Visual:** Data volume table + coverage map

### Slide 4: Methodology
**Title:** Scientific Rigor
**Content:**
- 0.25° grid, 5-day/8-day windows
- Jaccard = set overlap (NOT accuracy)
- Chronological split: train 2013-16 / validation 2017-18 / test 2019-20
- 8-day purge at boundaries (no temporal leakage)
- Isotonic calibration on validation only

**Visual:** Feature → RF → Calibration diagram

### Slide 5: Platform Demo
**Title:** Interactive Platform
**Content:**
- Screenshots of:
  - Map with risk layer
  - Zone analysis with Jaccard
  - Historical calendar
  - Jobs dashboard
  - Data quality audit

**Visual:** 3-4 real screenshots arranged cleanly

### Slide 6: Impact
**Title:** Benefits & Honesty
**Content:**
- Transparency: provenance everywhere
- Honesty: never claims "no fire"
- Reproducibility: fixed seeds, 119 tests
- Open access: country archives without API key
- Model performance: PR-AUC 0.926 on held-out test

**Visual:** Metrics highlighted + honesty checklist

### Slide 7: Vision
**Title:** Future Directions
**Content:**
- Extend to continental Africa
- Add weather drivers (ERA5)
- Support operational early-warning for NGOs
- Improve spatial calibration

**Visual:** Africa map + roadmap timeline

---

## Critical Constraints

### Scientific Honesty (MUST be respected)
1. **Never say "predicts wildfires"** — always "predicts detected fire activity"
2. **Never say "accuracy" for Jaccard** — always "set overlap" or "Jaccard index"
3. **Never claim "no fire"** — always "no detection" or "unknown observability"
4. **Label model outputs as "historical backtest"** — not operational forecasts
5. **Show provenance** — `data_origin` and `generated_at` visible in all displays

### Attribution Requirements
- NASA FIRMS, GIBS, CMR data sources credited
- Esri attribution for map tiles
- OpenStreetMap attribution for geocoding
- MIT License for code
- No NASA logos reproduced (use text attribution only)

### Technical Access
The AI agent has access to:
- Frontend React app (http://localhost:5174)
- Fire Monitor standalone (web/public/fire-monitor.html)
- API documentation (http://127.0.0.1:8010/api/v1/docs)
- All artifacts in web/public/artifacts/
- Source code and documentation

### Brand Guidelines
- Professional, scientific aesthetic
- Clean, modern design
- Blue/orange color scheme (matching badges)
- Clear typography
- No excessive animations or effects

---

## Deliverables

1. **Video file**: MP4, 30 seconds, English subtitles, 1920x1080 minimum
2. **PowerPoint file**: 7 slides, editable, speaker notes included
3. **Screenshots folder**: High-resolution PNGs of all captured screens
4. **Script document**: Full voiceover script for video with timing

---

## Additional Notes

- The project uses French/English bilingual interface — capture English version
- The AI assistant in the app is deterministic (rules-based), not an LLM — do not present it as AI-powered
- All model metrics are from historical backtest (2019-2020) — clearly label as such
- The risk model has PR-AUC 0.926 on test set — highlight this achievement
- Jaccard values range from 0.103 to 0.659 depending on grid/window — show realistic values
