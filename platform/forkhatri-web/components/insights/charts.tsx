"use client";

/**
 * Hand-built SVG/HTML charts for the Members dashboard. Thin marks, one axis,
 * hairline grid, text in ink tokens (never the series colour), a hover tooltip
 * on plotted marks, and a legend whenever two series share a chart.
 */
import { useEffect, useRef, useState, type ReactNode } from "react";

export function useWidth<T extends HTMLElement>(): [React.RefObject<T | null>, number] {
  const ref = useRef<T | null>(null);
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.floor(entry.contentRect.width)));
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  return [ref, width];
}

export type Tip = { x: number; y: number; content: ReactNode } | null;

export function Tooltip({ tip }: { tip: Tip }) {
  if (!tip) return null;
  return (
    <div className="ins-tip" role="status" style={{ left: tip.x, top: tip.y }}>
      {tip.content}
    </div>
  );
}

/** Clean axis ticks: 0, then round steps up to at least `max`. */
export function niceTicks(max: number, count = 4): number[] {
  if (max <= 0) return [0, 1];
  const raw = max / count;
  const power = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((m) => m * power).find((s) => s >= raw) ?? raw;
  const ticks: number[] = [];
  for (let v = 0; v <= max + step * 0.001; v += step) ticks.push(Math.round(v));
  if (ticks[ticks.length - 1] < max) ticks.push(ticks[ticks.length - 1] + step);
  return ticks;
}

// ---------------------------------------------------------------------------
// Growth: total members by day (line + 10% wash), crosshair tooltip.
// ---------------------------------------------------------------------------

type GrowthPoint = { date: string; new: number; total: number };

export function GrowthChart({
  points,
  locale,
  labelTotal,
  labelNew,
}: {
  points: GrowthPoint[];
  locale: string;
  labelTotal: (n: number) => string;
  labelNew: (n: number) => string;
}) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  const height = 240;
  const pad = { top: 20, right: 12, bottom: 30, left: 36 };
  const innerW = Math.max(0, width - pad.left - pad.right);
  const innerH = height - pad.top - pad.bottom;
  const max = Math.max(1, ...points.map((p) => p.total));
  const ticks = niceTicks(max);
  const top = ticks[ticks.length - 1];
  const x = (i: number) => pad.left + (points.length <= 1 ? innerW / 2 : (i / (points.length - 1)) * innerW);
  const y = (v: number) => pad.top + innerH - (v / top) * innerH;
  const line = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.total).toFixed(1)}`).join("");
  const area = points.length ? `${line}L${x(points.length - 1).toFixed(1)},${y(0)}L${x(0).toFixed(1)},${y(0)}Z` : "";
  const day = new Intl.DateTimeFormat(locale, { day: "numeric", month: "short" });
  const labelCount = Math.max(2, Math.min(6, Math.floor(innerW / 110)));
  const labelIdx = [...new Set(Array.from({ length: labelCount }, (_, k) => Math.round((k * (points.length - 1)) / (labelCount - 1))))];
  const last = points[points.length - 1];

  function onMove(event: React.PointerEvent<SVGRectElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const ratio = (event.clientX - rect.left) / rect.width;
    setHover(Math.max(0, Math.min(points.length - 1, Math.round(ratio * (points.length - 1)))));
  }

  const hp = hover === null ? null : points[hover];
  return (
    <div className="ins-chart" ref={ref}>
      {width > 0 && (
        <svg width={width} height={height} role="img" aria-label={last ? labelTotal(last.total) : undefined}>
          {ticks.map((tick) => (
            <g key={tick}>
              <line className="ins-grid" x1={pad.left} x2={width - pad.right} y1={y(tick)} y2={y(tick)} />
              <text className="ins-axis" x={pad.left - 10} y={y(tick)} dy="0.32em" textAnchor="end">
                {tick.toLocaleString(locale)}
              </text>
            </g>
          ))}
          {labelIdx.map((i, k) => (
            <text
              key={points[i].date}
              className="ins-axis"
              x={x(i)}
              y={height - 8}
              textAnchor={k === 0 ? "start" : k === labelIdx.length - 1 ? "end" : "middle"}
            >
              {day.format(new Date(`${points[i].date}T00:00:00`))}
            </text>
          ))}
          <path d={area} className="ins-area" />
          <path d={line} className="ins-line" />
          {hp && hover !== null && <line className="ins-cross" x1={x(hover)} x2={x(hover)} y1={pad.top} y2={pad.top + innerH} />}
          {last && <circle cx={x(points.length - 1)} cy={y(last.total)} r={4} className="ins-dot" />}
          {hp && hover !== null && <circle cx={x(hover)} cy={y(hp.total)} r={5} className="ins-dot" />}
          <rect
            x={pad.left}
            y={pad.top}
            width={innerW}
            height={innerH}
            fill="transparent"
            onPointerMove={onMove}
            onPointerLeave={() => setHover(null)}
          />
        </svg>
      )}
      {hp && hover !== null && (
        <Tooltip
          tip={{
            x: Math.max(0, Math.min(x(hover) - 70, width - 170)),
            y: Math.max(0, y(hp.total) - 78),
            content: (
              <>
                <strong>{day.format(new Date(`${hp.date}T00:00:00`))}</strong>
                <span>{labelTotal(hp.total)}</span>
                <span className="ins-tip-muted">{labelNew(hp.new)}</span>
              </>
            ),
          }}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Meter list: label, value and share, with a thin track underneath.
// ---------------------------------------------------------------------------

export type MeterItem = { key: string; label: ReactNode; sub?: ReactNode; value: number };

export function MeterList({
  items,
  locale,
  total,
  ranked = false,
}: {
  items: MeterItem[];
  locale: string;
  /** Share denominator; defaults to the sum of the items. */
  total?: number;
  ranked?: boolean;
}) {
  const denominator = total ?? items.reduce((sum, i) => sum + i.value, 0);
  const max = Math.max(1, ...items.map((i) => i.value));
  const pct = new Intl.NumberFormat(locale, { style: "percent", maximumFractionDigits: 0 });
  return (
    <ol className={`ins-meters${ranked ? " is-ranked" : ""}`}>
      {items.map((item, index) => (
        <li key={item.key}>
          {ranked && <span className="ins-rank">{index + 1}</span>}
          <div className="ins-meter-body">
            <div className="ins-meter-top">
              <span className="ins-meter-label">
                {item.label}
                {item.sub && <span className="ins-meter-sub">{item.sub}</span>}
              </span>
              <span className="ins-meter-value">
                {item.value.toLocaleString(locale)}
                {denominator > 0 && <span className="ins-meter-pct">{pct.format(item.value / denominator)}</span>}
              </span>
            </div>
            <span className="ins-meter-track" aria-hidden>
              <span className="ins-meter-fill" style={{ width: `${(item.value / max) * 100}%` }} />
            </span>
          </div>
        </li>
      ))}
    </ol>
  );
}

// ---------------------------------------------------------------------------
// Share bar: one 100% bar split into segments with a 2px surface gap + legend.
// ---------------------------------------------------------------------------

export type Segment = { key: string; label: string; value: number; className: string };

export function ShareBar({ segments, locale }: { segments: Segment[]; locale: string }) {
  const total = segments.reduce((sum, s) => sum + s.value, 0);
  const pct = new Intl.NumberFormat(locale, { style: "percent", maximumFractionDigits: 0 });
  return (
    <div className="ins-share">
      <div className="ins-share-bar" role="img" aria-label={segments.map((s) => `${s.label} ${s.value}`).join(", ")}>
        {segments
          .filter((s) => s.value > 0)
          .map((s) => (
            <span key={s.key} className={`ins-share-seg ${s.className}`} style={{ flexGrow: s.value }} title={`${s.label}: ${s.value}`} />
          ))}
      </div>
      <ul className="ins-legend">
        {segments.map((s) => (
          <li key={s.key}>
            <span className={`ins-swatch ${s.className}`} aria-hidden />
            <span className="ins-legend-label">{s.label}</span>
            <span className="ins-legend-value">
              {s.value.toLocaleString(locale)} <span className="ins-muted">{total ? pct.format(s.value / total) : ""}</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Age pyramid: women to the left, men to the right, one shared scale.
// ---------------------------------------------------------------------------

export function AgePyramid({
  bands,
  left,
  right,
  locale,
  bandLabel,
}: {
  bands: { band: string; left: number; right: number }[];
  left: { label: string; className: string };
  right: { label: string; className: string };
  locale: string;
  bandLabel: (band: string) => string;
}) {
  const max = Math.max(1, ...bands.flatMap((b) => [b.left, b.right]));
  return (
    <div className="ins-pyramid">
      <div className="ins-pyramid-head">
        <span>
          <span className={`ins-swatch ${left.className}`} aria-hidden /> {left.label}
        </span>
        <span />
        <span>
          <span className={`ins-swatch ${right.className}`} aria-hidden /> {right.label}
        </span>
      </div>
      {bands.map((b) => (
        <div className="ins-pyramid-row" key={b.band} aria-label={`${bandLabel(b.band)}: ${left.label} ${b.left}, ${right.label} ${b.right}`}>
          <div className="ins-pyramid-side ins-pyramid-left">
            <span className="ins-pyramid-num">{b.left ? b.left.toLocaleString(locale) : ""}</span>
            <span className={`ins-pyramid-bar ${left.className}`} style={{ width: `${(b.left / max) * 100}%` }} title={`${left.label}: ${b.left}`} />
          </div>
          <span className="ins-pyramid-band">{b.band}</span>
          <div className="ins-pyramid-side">
            <span className={`ins-pyramid-bar ${right.className}`} style={{ width: `${(b.right / max) * 100}%` }} title={`${right.label}: ${b.right}`} />
            <span className="ins-pyramid-num">{b.right ? b.right.toLocaleString(locale) : ""}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
