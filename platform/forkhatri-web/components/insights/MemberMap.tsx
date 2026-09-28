"use client";

/**
 * Choropleth + city circles, drawn with d3-geo into plain SVG.
 *
 * Regions are shaded on a one-hue sequential ramp (5 steps, log-spaced so one
 * big city does not flatten every other region into the lightest step); a
 * region with no members stays the neutral surface. Each city is a small
 * fixed-size accent dot with a surface ring (owner, 2026-09-27: circles sized by
 * members covered the map and wasted space); the state shading carries the
 * magnitude and the tooltip gives the city's count.
 *
 * The two views encode differently (owner feedback, 2026-09-27):
 *   - India: per-state choropleth + a small dot per city with members. City
 *     dots belong only here — at world scale they collapsed into one blob.
 *   - World: a flat, neutral backdrop + one marker and label per country
 *     with members (the Datadog/Stripe world-map pattern). Shading a lone
 *     country's real political shape at ~150px reads as broken — India's
 *     mainland and Northeast joined by the thin Siliguri corridor looked
 *     like detached fragments — and "filling" that corridor is impossible
 *     without painting over Bangladesh and Nepal.
 * Boundaries follow India's official view (public/geo/ATTRIBUTION.md).
 */
import { geoMercator, geoNaturalEarth1, geoPath, type GeoProjection } from "d3-geo";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { feature } from "topojson-client";
import type { Topology } from "topojson-specification";
import { Tooltip, useWidth, type Tip } from "./charts";

type Props = {
  kind: "india" | "world";
  values: Map<string, number>;
  regionTip: (key: string, name: string, value: number) => ReactNode;
  cities: { key: string; lat: number; lon: number; members: number; tip: ReactNode }[];
  ariaLabel: string;
  /** Display name for a region key (a country in the reader's language). */
  regionName: (key: string, fallback: string) => string;
  locale: string;
};

type Shape = Feature<Geometry, { name: string; iso?: string }>;

const SOURCES = {
  india: { url: "/geo/india-states.topo.json", object: "states" },
  world: { url: "/geo/world.topo.json", object: "countries" },
} as const;

const cache = new Map<string, Promise<Shape[]>>();

function loadShapes(kind: Props["kind"]): Promise<Shape[]> {
  const source = SOURCES[kind];
  let pending = cache.get(kind);
  if (!pending) {
    pending = fetch(source.url)
      .then((r) => r.json() as Promise<Topology>)
      .then((topology) => {
        const collection = feature(topology, topology.objects[source.object]) as unknown as FeatureCollection<Geometry, { name: string; iso?: string }>;
        return collection.features.filter((f) => f.properties.name !== "Antarctica");
      });
    cache.set(kind, pending);
  }
  return pending;
}

/** 0 = none, 1..5 = log-spaced steps up to the largest region. */
export function step(value: number, max: number): number {
  if (value <= 0) return 0;
  if (max <= 1) return 5;
  return 1 + Math.min(4, Math.floor((4 * Math.log(value)) / Math.log(max) + 1e-9));
}

export default function MemberMap({ kind, values, regionTip, cities, ariaLabel, regionName, locale }: Props) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [shapes, setShapes] = useState<Shape[] | null>(null);
  const [tip, setTip] = useState<Tip>(null);
  const [active, setActive] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    void loadShapes(kind).then((loaded) => alive && setShapes(loaded));
    return () => {
      alive = false;
    };
  }, [kind]);

  // India is taller than wide; cap it so the card never turns into a long scroll.
  const height = kind === "india" ? Math.min(Math.round(width * 1.1), 600) : Math.round(width * 0.5);
  const projection = useMemo<GeoProjection | null>(() => {
    if (!shapes || width === 0) return null;
    const collection = { type: "FeatureCollection", features: shapes } as FeatureCollection;
    const base = kind === "india" ? geoMercator() : geoNaturalEarth1();
    return base.fitExtent(
      [
        [8, 8],
        [width - 8, height - 8],
      ],
      collection,
    );
  }, [shapes, width, height, kind]);

  const path = useMemo(() => (projection ? geoPath(projection) : null), [projection]);
  const keyOf = (s: Shape) => (kind === "india" ? s.properties.name : (s.properties.iso ?? ""));

  /** The centroid of a shape's single largest polygon, not the whole (possibly
   * multi-part) feature — a country whose territory is one big landmass plus a
   * thin-necked appendage (India's mainland + Northeast, joined by the narrow
   * "Chicken's Neck" corridor) has a combined centroid that can fall in the gap
   * between the two, landing a label outside solid ground. Anchoring on the
   * biggest single polygon instead keeps every label inside real territory. */
  function anchorCentroid(shape: Shape, pathGen: NonNullable<typeof path>): [number, number] {
    const polygons: Feature<Geometry>[] =
      shape.geometry.type === "MultiPolygon"
        ? shape.geometry.coordinates.map((coordinates) => ({ type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates } }))
        : [shape];
    const biggest = polygons.reduce((best, candidate) => (Math.abs(pathGen.area(candidate)) > Math.abs(pathGen.area(best)) ? candidate : best));
    return pathGen.centroid(biggest);
  }
  const max = Math.max(1, ...values.values());
  const radius = kind === "india" ? 4 : 5;

  // Direct labels on the busiest regions (name + count), greedily skipping any
  // that would collide with one already placed; the side list carries the rest.
  // On the world map these anchors also carry the country markers.
  const labels = useMemo(() => {
    if (!path || !shapes) return [];
    const placed: { key: string; name: string; value: number; x: number; y: number; w: number }[] = [];
    // Labels dodge the India map's city dots, and on the world map the country
    // markers (which sit exactly on each anchor, pushing the label above them).
    const dots =
      kind === "india"
        ? cities.map((c) => projection?.([c.lon, c.lat])).filter((p): p is [number, number] => Boolean(p))
        : shapes.filter((s) => (values.get(keyOf(s)) ?? 0) > 0).map((s) => anchorCentroid(s, path));
    const ranked = shapes
      .map((shape) => ({ shape, key: keyOf(shape), value: values.get(keyOf(shape)) ?? 0 }))
      .filter((r) => r.value > 0)
      .sort((a, b) => b.value - a.value);
    for (const { shape, key, value } of ranked) {
      if (placed.length >= 3 || placed.some((p) => p.key === key)) continue;
      const [cx, cy] = anchorCentroid(shape, path);
      if (!Number.isFinite(cx)) continue;
      const name = kind === "world" ? regionName(key, shape.properties.name) : shape.properties.name;
      const w = Math.max(name.length, 4) * 6.4 + 8;
      // Try the centroid, then nudge above/below/sideways so a label never sits
      // on a city dot or on another label.
      for (const [dx, dy] of [[0, 0], [0, -24], [0, 24], [-w / 2 - 10, 0], [w / 2 + 10, 0]]) {
        const x = cx + dx;
        const y = cy + dy;
        const onDot = dots.some(([px, py]) => Math.abs(px - x) < w / 2 + 6 && py > y - 22 && py < y + 16);
        const onLabel = placed.some((p) => Math.abs(p.x - x) < (p.w + w) / 2 && Math.abs(p.y - y) < 34);
        if (!onDot && !onLabel) {
          placed.push({ key, name, value, x, y, w });
          break;
        }
      }
    }
    return placed;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, shapes, values, kind, cities]);

  function place(event: React.PointerEvent<SVGElement>, content: ReactNode) {
    const box = (event.currentTarget.ownerSVGElement ?? (event.currentTarget as SVGSVGElement)).getBoundingClientRect();
    setTip({ x: Math.min(event.clientX - box.left + 12, width - 190), y: event.clientY - box.top + 12, content });
  }

  return (
    <div className="ins-map" ref={ref} style={{ minHeight: height || undefined }}>
      {path && projection && (
        <svg width={width} height={height} role="img" aria-label={ariaLabel} onPointerLeave={() => (setTip(null), setActive(null))}>
          <g>
            {shapes!.map((shape, i) => {
              const key = keyOf(shape);
              const value = values.get(key) ?? 0;
              return (
                <path
                  key={`${key}-${i}`}
                  d={path(shape) ?? undefined}
                  // The world map stays a flat, neutral backdrop — shading a
                  // single country by value paints its full political shape,
                  // and at ~150px wide a real shape like India's (mainland +
                  // Northeast joined by the thin Siliguri corridor) reads as
                  // broken, not informative (owner, 2026-09-27). Markers on
                  // the anchor points carry the data instead, the way
                  // world-level maps in Datadog/Stripe dashboards do. The
                  // India map keeps its per-state choropleth.
                  className={`ins-region ${kind === "world" ? "ins-q0" : `ins-q${step(value, max)}`}${active === key ? " is-active" : ""}`}
                  onPointerMove={(e) => {
                    setActive(key);
                    place(e, regionTip(key, shape.properties.name, value));
                  }}
                />
              );
            })}
          </g>
          {kind === "world" && (
            <g>
              {shapes!
                .filter((shape) => (values.get(keyOf(shape)) ?? 0) > 0)
                .map((shape) => {
                  const key = keyOf(shape);
                  const [cx, cy] = anchorCentroid(shape, path);
                  if (!Number.isFinite(cx)) return null;
                  return (
                    <circle
                      key={key}
                      cx={cx}
                      cy={cy}
                      r={radius}
                      className="ins-city"
                      onPointerMove={(e) => {
                        e.stopPropagation();
                        setActive(key);
                        place(e, regionTip(key, shape.properties.name, values.get(key) ?? 0));
                      }}
                    />
                  );
                })}
            </g>
          )}
          <g className="ins-region-labels" aria-hidden>
            {labels.map((l) => (
              <text key={l.key} x={l.x} y={l.y - 6} textAnchor="middle">
                <tspan className="ins-rl-name">{l.name}</tspan>
                <tspan className="ins-rl-value" x={l.x} dy="1.25em">
                  {l.value.toLocaleString(locale)}
                </tspan>
              </text>
            ))}
          </g>
          {kind === "india" && (
            <g>
              {[...cities]
                .sort((a, b) => b.members - a.members)
                .map((city) => {
                  const point = projection([city.lon, city.lat]);
                  if (!point) return null;
                  return (
                    <circle
                      key={city.key}
                      cx={point[0]}
                      cy={point[1]}
                      r={radius}
                      className="ins-city"
                      onPointerMove={(e) => {
                        e.stopPropagation();
                        setActive(null);
                        place(e, city.tip);
                      }}
                    />
                  );
                })}
            </g>
          )}
        </svg>
      )}
      <Tooltip tip={tip} />
    </div>
  );
}
