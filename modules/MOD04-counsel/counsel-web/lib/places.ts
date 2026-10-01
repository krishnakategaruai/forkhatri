/* Listed cities for "near me" and the consultant's city picker. The list and
 * coordinates come from the Counsel API (GET /places); the browser's own
 * location, when the person allows it, is matched to the nearest listed city
 * here, so nothing is sent to any outside service. */

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export type City = { id: string; name: string; value: string; lat: number; lng: number };
export type Places = { cities: City[]; nearby_km: number };

const KEY = "counsel.near";

export function usePlaces(lang: string): Places | null {
  const [p, setP] = useState<Places | null>(null);
  useEffect(() => { void api<Places>("/places").then(setP).catch(() => setP({ cities: [], nearby_km: 150 })); }, [lang]);
  return p;
}

function km(aLat: number, aLng: number, bLat: number, bLng: number): number {
  const r = (d: number) => (d * Math.PI) / 180;
  const h = Math.sin(r(bLat - aLat) / 2) ** 2 + Math.cos(r(aLat)) * Math.cos(r(bLat)) * Math.sin(r(bLng - aLng) / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
}

export function nearestCity(cities: City[], lat: number, lng: number): City | null {
  let best: City | null = null;
  let bestKm = Infinity;
  for (const c of cities) {
    const d = km(lat, lng, c.lat, c.lng);
    if (d < bestKm) { best = c; bestKm = d; }
  }
  return best;
}

/** Ask the browser for its position (the person decides) and return the nearest listed city. */
export function locate(cities: City[]): Promise<City | null> {
  return new Promise((resolve) => {
    if (typeof navigator === "undefined" || !navigator.geolocation) { resolve(null); return; }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve(nearestCity(cities, pos.coords.latitude, pos.coords.longitude)),
      () => resolve(null),
      { maximumAge: 3_600_000, timeout: 10_000 },
    );
  });
}

export function savedNear(): string {
  try { return localStorage.getItem(KEY) ?? ""; } catch { return ""; }
}

export function saveNear(id: string) {
  try { if (id) localStorage.setItem(KEY, id); else localStorage.removeItem(KEY); } catch { /* storage may be blocked */ }
}
