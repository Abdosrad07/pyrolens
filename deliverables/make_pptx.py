"""
Génère la présentation PowerPoint PyroLens_NASA_2026.pptx (7 slides, 16:9).
Chaque slide a un texte modifiable + notes de présentation.
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pathlib import Path
from PIL import Image
import json

ROOT = Path(__file__).parent.parent.parent
SCREENSHOTS = Path(__file__).parent / "screenshots"
OUT = Path(__file__).parent / "presentation" / "PyroLens_NASA_2026.pptx"

# ── Couleurs ──
CANOPY = RGBColor(0x0E, 0x2A, 0x25)
EMBER = RGBColor(0xF2, 0x54, 0x1B)
SULPHUR = RGBColor(0xFF, 0xC8, 0x3D)
ASH = RGBColor(0xF2, 0xF6, 0xF4)
TEXT = RGBColor(0x14, 0x23, 0x1F)
MUTED = RGBColor(0x3E, 0x51, 0x4B)
INFO_BG = RGBColor(0xDC, 0xEB, 0xF7)
OK_BG = RGBColor(0xDC, 0xF2, 0xE8)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)


def add_title_slide(title: str, subtitle: str, notes: str, image: Path | None = None):
    """Slide 16:9 avec titre + sous-titre + image + notes."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    # Background
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = ASH

    # Title box
    left, top = Inches(0.7), Inches(0.5)
    width, height = Inches(11.5), Inches(1.2)
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = title
    run.font.size = Pt(36)
    run.font.bold = True
    run.font.color.rgb = CANOPY

    # Subtitle
    tb2 = slide.shapes.add_textbox(left, top + Inches(1.1), width, Inches(0.6))
    p2 = tb2.text_frame.paragraphs[0]
    p2.alignment = PP_ALIGN.LEFT
    r2 = p2.add_run()
    r2.text = subtitle
    r2.font.size = Pt(18)
    r2.font.color.rgb = MUTED

    # Image
    if image and image.exists():
        try:
            slide.shapes.add_picture(str(image), Inches(0.7), Inches(2.0), width=Inches(12.0))
        except Exception:
            pass

    # Notes
    notes_slide = slide.notes_slide
    notes_slide.notes_text_frame.text = notes

    return slide


def add_content_slide(title: str, bullets: list[str], notes: str,
                      image: Path | None = None, image_col: int = 0):
    """Slide avec titre + liste à puces + optionnellement une image."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = ASH

    # Title
    tb = slide.shapes.add_textbox(Inches(0.7), Inches(0.4), Inches(11.5), Inches(1.0))
    p = tb.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = title
    run.font.size = Pt(32)
    run.font.bold = True
    run.font.color.rgb = CANOPY

    # Bullets
    top = Inches(1.8)
    if image and image.exists():
        # Left: image
        try:
            slide.shapes.add_picture(str(image), Inches(0.7), top, height=Inches(4.5))
        except Exception:
            pass
        left = Inches(7.0)
        width = Inches(5.5)
    else:
        left = Inches(0.7)
        width = Inches(11.5)

    tb2 = slide.shapes.add_textbox(left, top, width, Inches(4.5))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    for i, b in enumerate(bullets):
        p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(8)
        run = p.add_run()
        run.text = "•  " + b
        run.font.size = Pt(16)
        run.font.color.rgb = TEXT

    # Notes
    notes_slide = slide.notes_slide
    notes_slide.notes_text_frame.text = notes

    return slide


# ── SLIDE 1 — The Challenge ──
add_title_slide(
    "The Challenge",
    "Making multi-sensor fire monitoring transparent.",
    "MODIS Terra/Aqua and VIIRS observe thermal anomalies differently — different spatial "
    "resolutions, observation times, and confidence scales. We need a transparent way to "
    "compare them before trusting any single-sensor picture.",
)

# ── SLIDE 2 — Our Solution ──
add_content_slide(
    "PyroLens in One Sentence",
    [
        "A reproducible Python pipeline + interactive monitoring platform + calibrated "
        "detection-probability model.",
        "Sensor comparison — Jaccard set overlap between MODIS and VIIRS detection sets.",
        "On-demand zone analysis — NRT (5 days) and historical country archives.",
        "Detection activity probability — Random Forest + isotonic calibration, "
        "historical backtest only.",
    ],
    "PyroLens connects three layers: NASA FIRMS data → harmonized 0.25° grid → "
    "Jaccard overlap + RF probability model. It does NOT predict fires; it estimates "
    "the probability that a satellite will DETECT at least one thermal anomaly in a cell "
    "within a given time window.",
)

# ── SLIDE 3 — Data Credibility ──
add_content_slide(
    "Data Credibility",
    [
        "1,170 NASA FIRMS files — MODIS standard processing + VIIRS SNPP, 2013–2020.",
        "4.46 million detection records audited against schema, date, and range rules.",
        "data_origin = nasa_firms — open-access, no credentials required.",
        "SHA-256 manifest tracks every file for reproducibility.",
        "Jaccard index (sensor overlap): 0.335 — set similarity, NOT accuracy.",
        "Interpretation note: no detection ≠ no fire; observation gaps exist.",
    ],
    "All data comes from NASA FIRMS open-access archive. The 0.335 Jaccard value means "
    "MODIS and VIIRS detect roughly one-third of the same cells in a given window — "
    "they are complementary, not redundant. This is a measure of set overlap, not "
    "model accuracy. Any figure claiming otherwise would be misleading.",
)

# ── SLIDE 4 — Scientific Methodology ──
add_content_slide(
    "Scientific Rigor",
    [
        "Spatial resolution: 0.25° grid (each cell ≈ 27.7 km × 27.7 km at equator).",
        "Temporal windows: 5-day and 8-day trailing feature windows.",
        "Chronological split: Train 2013–2016, Validation 2017–2018, Test 2019–2020.",
        "Eight-day purge at every temporal boundary — no leakage by design.",
        "Features computed exclusively from past observations (trailing windows only).",
        "Isotonic calibration fitted on validation data ONLY.",
        "Model selection: RF retained only if PR-AUC > baseline × 1.05 on validation.",
    ],
    "The scientific core of PyroLens is its anti-leakage design. Every feature is "
    "computed from data strictly before the prediction reference date. The purge at "
    "boundaries ensures no training label can contaminate a validation or test sample. "
    "Calibration is fitted on validation only; test is used once, at the end. "
    "This is a historical backtest, not an operational forecast.",
)

# ── SLIDE 5 — Interactive Platform ──
img_map = SCREENSHOTS / "01_map_risk.png"
add_content_slide(
    "Explore PyroLens",
    [
        "Interactive Leaflet map with NASA GIBS satellite layers.",
        "Risk layer: probability of satellite-detected fire activity per cell.",
        "Historical calendar: inter-sensor divergence by day, 2013–2020.",
        "Live job dashboard + data-quality audit report.",
    ],
    "The web app runs at localhost:5174 with a FastAPI backend at port 8010. "
    "All views read real data from the artifacts directory — no mock data. "
    "The map uses NASA GIBS for satellite imagery and Esri for base maps.",
    image=img_map,
)

# ── SLIDE 6 — Results and Impact ──
add_content_slide(
    "Transparency. Reproducibility. Scientific Honesty.",
    [
        "PR-AUC: 0.926  ·  F1: 0.841  ·  Brier: 0.072  (historical test, 2019–2020).",
        "Baseline (frequency): PR-AUC 0.875 — Random Forest beats it by 5.7% relative.",
        "Four commitments: transparent provenance, no false 'no-fire' claims, "
        "reproducible pipeline, open-access country archives.",
        "NO DETECTION ≠ NO FIRE — observation gaps are always disclosed.",
        "Estimate type: historical_backtest — not an operational forecast.",
    ],
    "All model metrics come from the historical backtest on 2019–2020 data. "
    "PR-AUC of 0.926 means the model ranks positive cells above negative ones with "
    "very high precision. The Brier score of 0.072 reflects well-calibrated "
    "probabilities. None of these numbers claim to predict current fires — they "
    "characterize the model's performance on historical data.",
)

# ── SLIDE 7 — Future Directions ──
add_content_slide(
    "Beyond Cameroon",
    [
        "Expand continental coverage: West Africa, East Africa, Southern Africa.",
        "Integrate ERA5 weather drivers (humidity, wind, soil moisture) as features.",
        "Improve spatial calibration for high-latitude and cloud-obscured regions.",
        "Support operational decision-making: fire-risk dashboards for NGOs.",
        "Early-warning tooling: alert when detection probability exceeds threshold.",
        "Open-source: MIT-licensed pipeline + public artifact API.",
    ],
    "The current pipeline is Cameroon-focused. The architecture already supports "
    "multi-country expansion via the FIRMS country archive system (no API key needed). "
    "Adding ERA5 weather features would improve the model's ability to separate "
    "true fire activity from observation artifacts. All future work remains "
    "transparent: provenance, version, and provenance of each cell.",
)

# ── Save ──
OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(str(OUT))
print(f"✓ PPTX généré: {OUT}")
print(f"  Slides: {len(prs.slides)}")
