"""
Génère la vidéo de démonstration 30s de PyroLens.
Utilise MoviePy 2.x (API moderne, pas moviepy.editor).
"""
import sys
from pathlib import Path

try:
    import moviepy as mp
except ImportError:
    print("ERREUR: pip install moviepy")
    sys.exit(1)

OUT = Path(__file__).parent / "video" / "PyroLens_Demo_30s.mp4"
SCREENSHOTS = Path(__file__).parent / "screenshots"

# ── Scénario 30s ──
SCENES = [
    (5, "01_map_risk.png",
     "PyroLens — a reproducible platform for comparing NASA MODIS and VIIRS fire observations."),
    (5, "02_sensor_comparison.png",
     "MODIS and VIIRS see different things. Jaccard overlap quantifies their agreement — not accuracy."),
    (5, "03_historical_calendar.png",
     "Historical calendar: inter-sensor divergence per day, 2013 to 2020."),
    (5, "04_risk_model.png",
     "Detection-probability model: Random Forest, isotonic calibration, PR-AUC 0.926."),
    (5, "05_jobs_dashboard.png",
     "Live pipeline: jobs, data quality, and full provenance of every artifact."),
    (5, "06_data_quality.png",
     "No detection does not mean no fire. PyroLens keeps that honesty visible in every view."),
]

def main():
    clips = []

    for dur, fname, subtitle in SCENES:
        img = SCREENSHOTS / fname
        if not img.exists():
            print(f"WARN: {fname} introuvable — placeholder")
            clip = mp.ColorClip(size=(1280, 720), color=(14, 42, 37), duration=dur)
        else:
            # Image 1440x900 → resize à 1280x720 avec letterbox
            base = mp.ImageClip(str(img)).resized((1280, 720))
            clip = base.with_duration(dur)

        # Texte de sous-titre en bas — police système Windows
        try:
            FONT = r"C:\Windows\Fonts\arial.ttf"
            text = mp.TextClip(
                subtitle,
                font=FONT,
                font_size=28,
                color="white",
            )
            text = text.with_position(("center", 660)).with_duration(dur)
            clip = mp.CompositeVideoClip([clip, text])
        except Exception as e:
            print(f"WARN: texte sous-titre échoué ({e}) — clip sans texte")

        clips.append(clip)
        print(f"  Scene {len(clips)}: {fname} ({dur}s)")

    final = mp.concatenate_videoclips(clips, method="compose")
    print(f"Vidéo totale: {final.duration:.1f}s")

    # Bande sonore (si disponible)
    music = Path(__file__).parent / "video" / "bgm.mp3"
    if music.exists():
        audio = mp.AudioFileClip(str(music))
        audio = audio.with_volume_scaled(0.15)
        if audio.duration > final.duration:
            audio = audio.subclip(0, int(final.duration))
        final = final.with_audio(audio)

    final.write_videofile(
        str(OUT),
        fps=30,
        codec="libx264",
        audio_codec="aac",
        threads=4,
    )
    print(f"\nOK: {OUT}")


if __name__ == "__main__":
    main()
