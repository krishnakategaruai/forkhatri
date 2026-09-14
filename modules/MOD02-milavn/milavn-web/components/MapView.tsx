'use client';

/* Map mode (FR005 · UX05/UI05): simple pin-per-activity map at approximate
 * locality centroids (FR038), muted base tiles, accent pins, tap -> preview
 * sheet. Tile provider is config-swappable (TR03: MapTiler placeholder;
 * OpenStreetMap tiles for development). */

import { useEffect, useRef } from 'react';
import type { Map as LeafletMap } from 'leaflet';
import 'leaflet/dist/leaflet.css';

import type { Card } from '@/lib/api';

const TILE_URL = process.env.NEXT_PUBLIC_MAP_TILE_URL ?? 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
const TILE_ATTR = process.env.NEXT_PUBLIC_MAP_TILE_ATTR ?? '&copy; OpenStreetMap contributors';

export default function MapView({ cards, onSelect }: { cards: Card[]; onSelect: (c: Card) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LeafletMap | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const L = (await import('leaflet')).default;
      if (cancelled || !ref.current || mapRef.current) return;
      const map = L.map(ref.current, { zoomControl: false, attributionControl: true }).setView([17.43, 78.42], 11);
      L.tileLayer(TILE_URL, { attribution: TILE_ATTR, maxZoom: 18, className: 'muted-tiles' }).addTo(map);
      L.control.zoom({ position: 'bottomright' }).addTo(map);
      mapRef.current = map;
      renderPins(L, map);
    })();
    return () => { cancelled = true; mapRef.current?.remove(); mapRef.current = null; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    (async () => {
      const L = (await import('leaflet')).default;
      if (mapRef.current) renderPins(L, mapRef.current);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cards]);

  function renderPins(L: typeof import('leaflet'), map: LeafletMap) {
    map.eachLayer((layer) => { if ((layer as { _milavnPin?: boolean })._milavnPin) map.removeLayer(layer); });
    const pts: [number, number][] = [];
    const seen: Record<string, number> = {};
    cards.forEach((c) => {
      if (c.lat === null || c.lng === null) return;
      // Spread multiple pins in the same locality centroid a little so all are tappable.
      const key = `${c.lat},${c.lng}`;
      const n = (seen[key] = (seen[key] ?? 0) + 1);
      const lat = c.lat + (n - 1) * 0.0022 * Math.cos(n);
      const lng = c.lng + (n - 1) * 0.0022 * Math.sin(n);
      const icon = L.divIcon({ className: '', html: '<div class="pin"></div>', iconSize: [30, 30], iconAnchor: [15, 30] });
      const m = L.marker([lat, lng], { icon, title: c.title }) as import('leaflet').Marker & { _milavnPin?: boolean };
      m._milavnPin = true;
      m.on('click', () => onSelect(c));
      m.addTo(map);
      pts.push([lat, lng]);
    });
    if (pts.length) map.fitBounds(pts, { padding: [40, 40], maxZoom: 13 });
  }

  // Explicit size: a flex child inside `.screen` must never collapse the map to 0px.
  return <div ref={ref} className="map" style={{ height: '58vh', minHeight: 360, flex: 'none' }} role="region" aria-label="Map of activities" />;
}
