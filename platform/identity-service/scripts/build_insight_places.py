"""Build the place list the Members dashboard uses to put cities on the map.

Derived from Mangaly's bundled GeoNames list (CC BY 4.0; see
modules/MOD03-mangaly/mangaly-service/app/components/places/data/ATTRIBUTION.md),
which is itself rebuilt from GeoNames by that module's `scripts/build_places.py`.
The platform keeps its own copy rather than reading another service's files:

  * India: every place (population >= 5,000), so district and taluk towns resolve.
  * Elsewhere: places with population >= 100,000, enough for members abroad.

Run from platform/identity-service/:  .venv/Scripts/python scripts/build_insight_places.py
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "modules/MOD03-mangaly/mangaly-service/app/components/places/data/places.tsv"
OUT = Path(__file__).resolve().parents[1] / "app/components/insights/data/places.tsv"

with SOURCE.open(encoding="utf-8", newline="") as src, OUT.open("w", encoding="utf-8", newline="") as out:
    reader = csv.DictReader(src, delimiter="\t")
    writer = csv.writer(out, delimiter="\t", lineterminator="\n")
    writer.writerow(["name", "ascii", "alternates", "region", "cc", "lat", "lon", "population"])
    kept = 0
    for row in reader:
        population = int(row["population"] or 0)
        if row["cc"] != "IN" and population < 100_000:
            continue
        writer.writerow([row["name"], row["ascii"], row["alternates"], row["region"], row["cc"], row["lat"], row["lon"], population])
        kept += 1
print(f"wrote {kept} places to {OUT}")
