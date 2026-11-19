"""
Télécharge les 8 fichiers DRC manquants avec retries renforcés.
"""
import json, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "data" / "raw" / "archive"
FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/data/country"
UA = "PyroLens/0.2 (+drc-retry)"

MISSING = [
    ("viirs-snpp", 2020), ("viirs-snpp", 2021), ("viirs-snpp", 2022),
    ("viirs-snpp", 2024), ("viirs-snpp", 2025),
    ("modis", 2019), ("modis", 2020), ("modis", 2021),
]
COUNTRY = "Democratic_Republic_of_the_Congo"
MAX = 5
DELAY = 10
CHUNK = 1 << 20

def fetch(sensor, year):
    url = f"{FIRMS_BASE}/{sensor}/{year}/{sensor}_{year}_{COUNTRY}.csv"
    target = ARCHIVE / sensor / f"{year}_{COUNTRY}.csv"
    if target.exists() and target.stat().st_size > 0:
        return "cached", target.stat().st_size

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".part")
    last_exc = None

    for att in range(1, MAX + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=600) as resp:
                total = int(resp.headers.get("Content-Length") or 0)
                buf = bytearray()
                last_pct = 0
                while True:
                    c = resp.read(CHUNK)
                    if not c:
                        break
                    buf.extend(c)
                    if total:
                        pct = min(99, len(buf) // total * 100)
                        if pct >= last_pct + 20:
                            print(f"\r    ... {pct}% ({len(buf)//1048576} Mo)", end="", flush=True)
                            last_pct = pct
            if total and len(buf) != total:
                raise IOError(f"tronqué {len(buf)}/{total}")
            tmp.write_bytes(bytes(buf))
            tmp.replace(target)
            return "ok", len(buf)
        except Exception as e:
            last_exc = e
            tmp.unlink(missing_ok=True)
            print(f"\n    retry {att}/{MAX-1} — {e}")
            if att < MAX:
                time.sleep(DELAY * att)

    return "error", str(last_exc)


def main():
    print(f"DRC retry — {len(MISSING)} fichiers manquants")
    results = []
    for sensor, year in MISSING:
        print(f"\n[sensor={sensor}, year={year}]")
        status, size = fetch(sensor, year)
        if status == "ok":
            print(f"  OK ({size:,} B)")
        elif status == "cached":
            print(f"  CACHED ({size:,} B)")
        else:
            print(f"  ERREUR: {size}")
        results.append({"sensor": sensor, "year": year, "status": status})
        time.sleep(2)

    ok = sum(1 for r in results if r["status"] in ("ok", "cached"))
    print(f"\n=== {ok}/{len(MISSING)} DRC réussis ===")


if __name__ == "__main__":
    main()
