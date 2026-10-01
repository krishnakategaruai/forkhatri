"""Download the representative photo for each kind of wedding place, with
its credit, into the web app (mangaly-web/public/art/wedding/).

Wedding arrangements shows a place's own photo when there is one (a
partner's upload, or a photo OpenStreetMap links to). Most places have none,
so each card shows a photo of the *kind* of place instead — labelled
"Representative photo" on the card, never passed off as that venue — and
credits the photographer, as the free licences require.

Each kind of place has a few photos, used in turn down the list so the
cards do not all look alike. Every photo is from Wikimedia Commons under
CC0, CC BY or CC BY-SA, chosen by eye for a South Indian wedding and so
that no private person is the subject. To change one, edit PHOTOS and run:
    python -m scripts.fetch_wedding_photos
"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

WEB = Path(__file__).resolve().parents[2] / "mangaly-web"
OUT = WEB / "public" / "art" / "wedding"
UA = {"User-Agent": "Mangalya/1.0 (ForKhatri; wedding category photos)"}
WIDTH = 900

PHOTOS: dict[str, list[str]] = {
    "cafe": [
        "File:Foaming filter coffee.jpg",
        "File:South Indian filter coffee.JPG",
    ],
    "restaurant": [
        "File:A Thali, famous South Indian meal served on a banana leaf.jpg",
        "File:Andhra meals in restaurant.jpg",
        "File:Vegetarian Andhra Meal.jpg",
    ],
    "hall": [
        "File:Kalyana Mandapam Inside.jpg",
        "File:Reception Stage.jpg",
        "File:Wedding reception stage, decorations, Kochi.jpg",
    ],
    "photographer": [
        "File:Reflector of a professional wedding photographer.jpg",
    ],
    "jewellery": [
        "File:Bridal gold jewellery in Bangladeshi wedding.jpg",
    ],
    "clothes": [
        "File:Embroidery on a saree 01.jpg",
        "File:Embroidery on a saree 04.jpg",
    ],
    "decoration": [
        "File:Marigold garlands.jpg",
        "File:MarriageRECEPTION-India-tamilword23.2.jpg",
        "File:Garland,jasmine,Tamil Nadu354.JPG",
    ],
    "caterer": [
        "File:Andhra Combo Meal.JPG",
        "File:Kerala sadhya.jpg",
        "File:Degi Biryani.JPG",
    ],
    "beauty": [
        "File:Bridal mehndi (henna) is a central wedding tradition 02.jpg",
        "File:Bridal mehndi (henna) is a central wedding tradition 11.jpg",
        "File:Bridal mehndi (henna) is a central wedding tradition 05.jpg",
    ],
    "car_rental": [
        "File:2001 Hindustan Ambassador Contessa GLX.jpg",
        "File:Hindustan Ambassador, City Palace, Jaipur, 20191218 0937 9034.jpg",
    ],
}


def _get(url: str) -> bytes:
    for attempt in range(5):
        try:
            time.sleep(2)  # Commons asks clients not to hurry
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as exc:
            if exc.code != 429:
                raise
            time.sleep(20 * (attempt + 1))
    raise RuntimeError(f"Commons kept refusing {url}")


def _plain(value: str) -> str:
    """Commons metadata is HTML ("<a href=…>Name</a>"); keep the words."""
    return html.unescape(re.sub(r"<[^>]+>", "", value or "")).strip()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.jpg"):
        old.unlink()  # a photo dropped from PHOTOS leaves the app too
    credits: dict[str, list[dict]] = {}
    for key, titles in PHOTOS.items():
        credits[key] = []
        for i, title in enumerate(titles):
            params = {
                "action": "query",
                "format": "json",
                "titles": title,
                "prop": "imageinfo",
                "iiprop": "url|extmetadata",
                "iiurlwidth": str(WIDTH),
            }
            api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
            page = next(iter(json.loads(_get(api))["query"]["pages"].values()))
            info = page["imageinfo"][0]
            meta = info.get("extmetadata") or {}
            (OUT / f"{key}-{i}.jpg").write_bytes(_get(info["thumburl"]))
            artist = _plain((meta.get("Artist") or {}).get("value", ""))
            credits[key].append(
                {
                    "author": artist or "Wikimedia Commons",
                    "license": _plain((meta.get("LicenseShortName") or {}).get("value", "")),
                    "license_url": (meta.get("LicenseUrl") or {}).get("value"),
                    "source": info["descriptionurl"],
                }
            )
            print(f"{key}-{i}: {credits[key][-1]['author']} · {credits[key][-1]['license']}")
    (OUT / "credits.json").write_text(
        json.dumps(credits, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
