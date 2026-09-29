"""Build the bundled place-of-birth list from GeoNames.

Source: GeoNames (https://www.geonames.org), licensed CC BY 4.0 — attribution
is kept in app/components/places/data/ATTRIBUTION.md and shown next to the
place picker.

  * India: every place in `cities5000` (population >= 5,000), so district
    towns and most taluk towns are there.
  * Elsewhere: `cities15000` (population >= 15,000), for members born abroad.

Each row carries the place's IANA time zone, which is what makes a birth time
convertible to UTC correctly (India's +06:30 war time, daylight saving
abroad). Coordinates are rounded to 4 decimals (~11 m).

Run from mangaly-service/:  .venv/Scripts/python scripts/build_places.py
"""

from __future__ import annotations

import csv
import io
import re
import unicodedata
import urllib.request
import zipfile
from pathlib import Path

BASE = "https://download.geonames.org/export/dump/"
OUT = Path(__file__).resolve().parents[1] / "app" / "components" / "places" / "data" / "places.tsv"
ASCII_WORD = re.compile(r"^[A-Za-z][A-Za-z .'\-]{1,40}$")


def fetch(name: str) -> bytes:
    with urllib.request.urlopen(BASE + name, timeout=120) as response:  # noqa: S310 - fixed https host
        return response.read()


def rows_from_zip(name: str) -> list[list[str]]:
    data = zipfile.ZipFile(io.BytesIO(fetch(name)))
    text = data.read(name.replace(".zip", ".txt")).decode("utf-8")
    return [line.split("\t") for line in text.splitlines() if line]


def fold(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c)).lower()


CURATED = Path(__file__).resolve().parents[1] / "app" / "components" / "places" / "data" / "indian_district_towns.csv"


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math

    p = math.pi / 180
    a = 0.5 - math.cos((lat2 - lat1) * p) / 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2
    return 12742 * math.asin(math.sqrt(a))


def apply_curated_indian_names(places: dict[str, list[str]]) -> None:
    """GeoNames sometimes files a city under a locality's name (Visakhapatnam
    appears as "Rasapudipalem"). The hand-made list of Indian district towns
    holds the names families use.

      1. A GeoNames place of the same name within 30 km is that town: the
         curated spellings join its alternates, and any bigger place within
         12 km that merely lists the town's name as an alternate (GeoNames'
         duplicate record of the same city) is dropped.
      2. Otherwise the most populous place within 12 km takes the curated
         name, its old name becoming an alternate.
      3. Otherwise the curated town is added as its own row."""

    def merge_alts(row: list[str], extra: list[str]) -> None:
        alts = [*extra, *row[3].split("|")]
        seen: list[str] = []
        for a in alts:
            if a and fold(a) != fold(row[2]) and fold(a) not in {fold(s) for s in seen}:
                seen.append(a)
        row[3] = "|".join(seen[:8])

    with CURATED.open(encoding="utf-8") as f:
        for town in csv.DictReader(f):
            indian = [r for r in places.values() if r[5] == "IN"]
            lat, lon = float(town["lat"]), float(town["lon"])
            name = fold(town["name"])
            aliases = [a.strip() for a in (town.get("aliases") or "").split("|") if a.strip()]
            near = [(r, _km(lat, lon, float(r[7]), float(r[8]))) for r in indian]
            same = [(r, d) for r, d in near if d < 30 and fold(r[2]) == name]
            if same:
                row = max(same, key=lambda x: int(x[0][10]))[0]
                merge_alts(row, aliases)
                for r, d in near:
                    if r is not row and d < 12 and fold(r[2]) != name and name in {fold(a) for a in r[3].split("|")}:
                        places.pop(r[0], None)
                continue
            close = [(r, d) for r, d in near if d < 12]
            if close:
                row = max(close, key=lambda x: int(x[0][10]))[0]
                old = row[2]
                row[1] = row[2] = town["name"]
                merge_alts(row, [*aliases, old])
                continue
            key = f"in-{fold(town['name']).replace(' ', '-')}"
            places[key] = [key, town["name"], town["name"], "|".join(aliases[:6]), town["state"], "IN", "India",
                           f"{lat:.4f}", f"{lon:.4f}", "Asia/Kolkata", "0"]


def main() -> None:
    admin1 = {}
    for line in fetch("admin1CodesASCII.txt").decode("utf-8").splitlines():
        code, name, ascii_name, _ = line.split("\t")
        admin1[code] = ascii_name or name
    countries = {}
    for line in fetch("countryInfo.txt").decode("utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        cols = line.split("\t")
        countries[cols[0]] = cols[4]

    places: dict[str, list[str]] = {}
    for source, keep in (("cities5000.zip", lambda cc: cc == "IN"), ("cities15000.zip", lambda cc: cc != "IN")):
        for r in rows_from_zip(source):
            geonameid, name, ascii_name, alternates, lat, lon = r[0], r[1], r[2], r[3], r[4], r[5]
            cc, adm1, population, tz = r[8], r[10], r[14], r[17]
            if not keep(cc) or not tz:
                continue
            # A few ASCII alternate spellings help search ("Vizag", "Bombay").
            alts = sorted({a for a in alternates.split(",") if ASCII_WORD.match(a) and fold(a) != fold(ascii_name)})[:6]
            places[geonameid] = [
                geonameid,
                name,
                ascii_name,
                "|".join(alts),
                admin1.get(f"{cc}.{adm1}", ""),
                cc,
                countries.get(cc, cc),
                f"{float(lat):.4f}",
                f"{float(lon):.4f}",
                tz,
                population or "0",
            ]

    apply_curated_indian_names(places)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["id", "name", "ascii", "alternates", "region", "cc", "country", "lat", "lon", "tz", "population"])
        for row in sorted(places.values(), key=lambda r: (-int(r[10]), r[0])):
            w.writerow(row)
    print(f"wrote {len(places)} places to {OUT}")


if __name__ == "__main__":
    main()
