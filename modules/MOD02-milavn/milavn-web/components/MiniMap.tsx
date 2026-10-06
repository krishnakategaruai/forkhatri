'use client';

/* "Where" at a glance on the detail page (UX06): a small, non-interactive map
 * centred on the activity's approximate locality (FR038 — never a precise
 * home address). Tapping it opens directions. Same tile source as Map mode. */

import { useEffect, useRef } from 'react';
import type { Map as LeafletMap } from 'leaflet';
import 'leaflet/dist/leaflet.css';

const TILE_URL = process.env.NEXT_PUBLIC_MAP_TILE_URL ?? 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
const TILE_ATTR = process.env.NEXT_PUBLIC_MAP_TILE_ATTR ?? '&copy; OpenStreetMap contributors';

// `exact` [054]: the venue's own pin (shown only to confirmed attendees and organizers) — closer zoom, no area circle.
export default function MiniMap({ lat, lng, label, exact = false }: { lat: number; lng: number; label: string; exact?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LeafletMap | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const L = (await import('leaflet')).default;
      if (cancelled || !ref.current || mapRef.current) return;
      const map = L.map(ref.current, {
        zoomControl: false, attributionControl: true, dragging: false, scrollWheelZoom: false, doubleClickZoom: false, touchZoom: false, boxZoom: false, keyboard: false,
      }).setView([lat, lng], exact ? 16 : 14);
      L.tileLayer(TILE_URL, { attribution: TILE_ATTR, maxZoom: 18, className: 'muted-tiles' }).addTo(map);
      const icon = L.divIcon({ className: '', html: '<div class="pin"></div>', iconSize: [30, 30], iconAnchor: [15, 30] });
      L.marker([lat, lng], { icon, title: label, interactive: false }).addTo(map);
      if (!exact) L.circle([lat, lng], { radius: 350, color: 'var(--accent-primary)', weight: 1, fillOpacity: 0.08, interactive: false }).addTo(map);
      mapRef.current = map;
    })();
    return () => { cancelled = true; mapRef.current?.remove(); mapRef.current = null; };
  }, [lat, lng, label, exact]);

  return <div ref={ref} className="minimap" style={{ height: 150, flex: 'none' }} role="img" aria-label={label} />;
}
