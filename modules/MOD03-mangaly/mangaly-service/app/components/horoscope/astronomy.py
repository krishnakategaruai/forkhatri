"""Sidereal positions for a birth moment: Moon, Sun, Mars and the Lagna.

Skyfield (MIT) + the JPL DE421 ephemeris, never the Swiss Ephemeris (AGPL).
DE421 covers 1899-07-29 .. 2053-10-09, which holds every birth date this
product accepts (a member must be an adult, and nobody born before 1899 is
marrying through an app). A birth outside that range raises `EphemerisRange`
and the chart falls back to "unavailable" rather than a wrong answer.

The ephemeris file is loaded once per process from
`mangaly-service/.local-ephemeris/de421.bsp` (16.8 MB; gitignored; set
`MANGALY_EPHEMERIS_DIR` to point elsewhere). If it is missing it is fetched
from JPL on first use, so a fresh checkout works with no manual step.

Lahiri ayanamsa
---------------
Sidereal longitude = tropical longitude - ayanamsa. The Lahiri (Chitra
Paksha) ayanamsa is India's official one (Indian Calendar Reform Committee,
1955) and what every Indian panchang and matching site uses, so it is the
only one implemented. Definition used here, the same one the Swiss Ephemeris
uses for SE_SIDM_LAHIRI: the ayanamsa was 23 deg 15' 00.658" on 1956-03-21
0h TT (JD 2435553.5); at any other time it is that value plus the general
precession in longitude accumulated since, taken from the IAU 2006 series
p_A = 5028.796195" T + 1.1054348" T^2 (T in Julian centuries from J2000).
Higher-order terms and the ~17" nutation wobble are not modelled.

Accuracy: checked against Drik Panchang's published Lahiri ayanamsa
(2000-01-01: 23.863781, 2026-09-22: 24.237131): the series above was 7.6"
low on both dates - a constant offset, so it is folded into the epoch value
(`_AYAN_T0`). After that the agreement is better than 1", far inside the
1 arc-minute that would matter (the Moon crosses a nakshatra pada, 3 deg 20',
in about six hours; a 1' error moves a boundary by two minutes of clock time).

Lagna
-----
Ascendant from local apparent sidereal time (Skyfield's `gast` + longitude)
and the mean obliquity of date, by the standard spherical-astronomy formula
(Meeus, "Astronomical Algorithms", ch. 25). Checked against Drik Panchang's
Udaya Lagna table for Hyderabad on 2026-09-22 (see the test in
`scripts/check_horoscope.py`).
"""

from __future__ import annotations

import logging
import math
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)

EPHEMERIS_FILE: Final = "de421.bsp"
EPHEMERIS_URL: Final = "https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de421.bsp"

# J2000 in Julian days (TT) and the Julian century.
_J2000: Final = 2451545.0
_CENTURY: Final = 36525.0
# Lahiri epoch: 1956-03-21 0h, 23 deg 15' 00.658", plus the 7.6" calibration
# against Drik Panchang described above.
_AYAN_JD0: Final = 2435553.5
_AYAN_T0: Final = 23.250182778 + 7.6 / 3600.0


class EphemerisRange(ValueError):
    """The birth moment lies outside the DE421 span."""


def lahiri_ayanamsa(jd_tt: float) -> float:
    """Lahiri ayanamsa in degrees at the given Julian day (TT)."""

    def precession_deg(t: float) -> float:
        return (5028.796195 * t + 1.1054348 * t * t) / 3600.0

    t = (jd_tt - _J2000) / _CENTURY
    t0 = (_AYAN_JD0 - _J2000) / _CENTURY
    return _AYAN_T0 + precession_deg(t) - precession_deg(t0)


def mean_obliquity_deg(jd_tt: float) -> float:
    t = (jd_tt - _J2000) / _CENTURY
    # IAU 2006 mean obliquity, arc-seconds -> degrees; the T^3.. terms are
    # below 0.1" inside DE421's span.
    return (84381.406 - 46.836769 * t - 0.0001831 * t * t) / 3600.0


@dataclass(frozen=True, slots=True)
class Positions:
    """Sidereal (Lahiri) longitudes in degrees, 0 <= x < 360."""

    moon: float
    sun: float
    mars: float
    lagna: float | None
    ayanamsa: float


class _Ephemeris:
    """Process-wide, lazily loaded Skyfield objects."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._loaded = False
        self._ts = None
        self._earth = None
        self._moon = None
        self._sun = None
        self._mars = None

    def _directory(self) -> Path:
        configured = os.environ.get("MANGALY_EPHEMERIS_DIR")
        if configured:
            return Path(configured)
        # mangaly-service/.local-ephemeris (this file is app/components/horoscope/)
        return Path(__file__).resolve().parents[3] / ".local-ephemeris"

    def _load(self) -> None:
        from skyfield.api import Loader

        directory = self._directory()
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / EPHEMERIS_FILE
        if not path.exists() or path.stat().st_size < 1_000_000:
            logger.info("downloading %s to %s", EPHEMERIS_URL, path)
            import urllib.request

            urllib.request.urlretrieve(EPHEMERIS_URL, path)  # noqa: S310 - fixed JPL URL
        loader = Loader(str(directory), verbose=False)
        eph = loader(EPHEMERIS_FILE)
        self._ts = loader.timescale(builtin=True)
        self._earth = eph["earth"]
        self._moon = eph["moon"]
        self._sun = eph["sun"]
        self._mars = eph["mars"]
        self._loaded = True

    def ensure(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if not self._loaded:
                self._load()

    def positions(self, when: datetime, lat: float | None, lon: float | None) -> Positions:
        from skyfield.errors import EphemerisRangeError
        from skyfield.framelib import ecliptic_frame

        self.ensure()
        assert self._ts is not None and self._earth is not None
        if when.tzinfo is None:
            raise ValueError("birth moment must be timezone-aware")
        t = self._ts.from_datetime(when.astimezone(timezone.utc))
        jd_tt = float(t.tt)
        ayan = lahiri_ayanamsa(jd_tt)
        here = self._earth.at(t)

        def sidereal(body) -> float:  # type: ignore[no-untyped-def]
            try:
                _lat, lon_, _dist = here.observe(body).apparent().frame_latlon(ecliptic_frame)
            except EphemerisRangeError as exc:
                raise EphemerisRange(str(exc)) from exc
            return (float(lon_.degrees) - ayan) % 360.0

        moon = sidereal(self._moon)
        sun = sidereal(self._sun)
        mars = sidereal(self._mars)

        lagna: float | None = None
        if lat is not None and lon is not None:
            # Local apparent sidereal time in degrees.
            theta = math.radians((float(t.gast) * 15.0 + lon) % 360.0)
            eps = math.radians(mean_obliquity_deg(jd_tt))
            phi = math.radians(lat)
            # Meeus 25.? : tan(asc) = cos(theta) / -(sin(theta) cos(eps) + tan(phi) sin(eps))
            y = math.cos(theta)
            x = -(math.sin(theta) * math.cos(eps) + math.tan(phi) * math.sin(eps))
            tropical_asc = math.degrees(math.atan2(y, x)) % 360.0
            lagna = (tropical_asc - ayan) % 360.0

        return Positions(moon=moon, sun=sun, mars=mars, lagna=lagna, ayanamsa=ayan)


_EPHEMERIS = _Ephemeris()


def positions_at(when: datetime, lat: float | None = None, lon: float | None = None) -> Positions:
    """Sidereal Moon/Sun/Mars longitudes at `when` (tz-aware), and the Lagna
    when a place is known."""
    return _EPHEMERIS.positions(when, lat, lon)
