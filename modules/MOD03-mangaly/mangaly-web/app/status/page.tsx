'use client';

import { useEffect, useState } from 'react';
import { getHealth, type HealthResult } from '@/lib/api';
import {
  FOUNDATIONS,
  PHASE_PLAN,
  STATUS_LABEL,
  TOTALS,
  overallCounts,
  phaseCounts,
  type Chain,
  type ReqStatus,
} from '@/lib/requirements';

const PILL: Record<ReqStatus, string> = {
  live: 'pill pill--live',
  wip: 'pill pill--wip',
  pending: 'pill pill--pending',
};

function ConnectionBanner() {
  const [health, setHealth] = useState<HealthResult | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    const check = async () => {
      const result = await getHealth(controller.signal);
      if (active) setHealth(result);
    };

    check();
    // Poll so the banner flips as soon as the backend comes up, without a reload.
    const timer = setInterval(check, 5000);
    return () => {
      active = false;
      controller.abort();
      clearInterval(timer);
    };
  }, []);

  const dot =
    health === null ? 'dot dot--wait' : health.state === 'ok' ? 'dot dot--ok' : 'dot dot--bad';

  return (
    <div className="conn">
      <span className={dot} aria-hidden="true" />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 600 }}>
          {health === null
            ? 'Checking API…'
            : health.state === 'ok'
              ? 'API connected'
              : 'API not running'}
        </div>
        <div className="caption">
          {health === null
            ? 'localhost:8000'
            : health.state === 'ok'
              ? 'localhost:8000 · mangaly @ localhost:5433'
              : `localhost:8000 — ${health.reason}`}
        </div>
      </div>
    </div>
  );
}

/** The parent-artifact chain for one FR, rendered as its real IDs. */
function ChainRow({ chain }: { chain: Chain }) {
  const parts: [string, string[]][] = [
    ['BR', chain.BR],
    ['UX', chain.UX],
    ['UI', chain.UI],
    ['TS', chain.TS],
    ['IA', chain.IA],
    ['TR', chain.TR],
    ['SP', chain.SP],
  ];

  return (
    <div className="chain">
      {parts.map(([kind, ids]) =>
        ids.length === 0 ? null : (
          <span className="chain__seg" key={kind}>
            <span className="chain__kind">{kind}</span>
            <span className="chain__ids">
              {ids.length > 3 ? `${ids.slice(0, 3).join(' ')} +${ids.length - 3}` : ids.join(' ')}
            </span>
          </span>
        ),
      )}
    </div>
  );
}

export default function HomePage() {
  const counts = overallCounts();
  const pct = Math.round((counts.live / counts.total) * 100);

  return (
    <>
      <header className="topbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
          <span className="brand-mark" aria-hidden="true">
            m
          </span>
          <h1>Mangaly</h1>
        </div>
        <span className="pill pill--wip">In build</span>
      </header>

      <main className="screen">
        <ConnectionBanner />

        <section className="card">
          <div className="req-group__head">
            <h2 className="h2">Build progress</h2>
            <span className="caption">
              {counts.live} of {counts.total} live
            </span>
          </div>
          <div
            className="progress"
            role="progressbar"
            aria-valuenow={pct}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Requirements live"
          >
            <div className="progress__bar" style={{ width: `${pct}%` }} />
          </div>
          <p className="caption" style={{ margin: 0 }}>
            Every row below carries its real parent IDs, extracted from the sealed
            pipeline documents rather than typed by hand. A row turns{' '}
            <strong>Live</strong> only once it works end to end against the database.
          </p>
          <div className="totals">
            {(
              [
                ['BR', TOTALS.br],
                ['FR', TOTALS.fr],
                ['UX', TOTALS.ux],
                ['UI', TOTALS.ui],
                ['TS', TOTALS.ts],
                ['IA', TOTALS.ia],
                ['TR', TOTALS.tr],
                ['SP', TOTALS.sp],
              ] as [string, number][]
            ).map(([kind, n]) => (
              <span className="totals__cell" key={kind}>
                <strong>{n}</strong>
                <span className="label">{kind}</span>
              </span>
            ))}
          </div>
        </section>

        <section className="req-group">
          <div className="req-group__head">
            <h2 className="h2">Foundations</h2>
            <span className="caption">
              {FOUNDATIONS.filter((f) => f.status === 'live').length}/{FOUNDATIONS.length}
            </span>
          </div>
          <p className="caption" style={{ margin: '0 0 8px' }}>
            Cross-cutting infrastructure every feature sits on. Not user-visible, but
            nothing else is correct without it.
          </p>
          <ul className="req-list">
            {FOUNDATIONS.map((f, i) => (
              <li className="req" key={`${f.ref}-${i}`}>
                <span className="req__id">{f.ref}</span>
                <span className="req__title">{f.title}</span>
                <span className={PILL[f.status]}>{STATUS_LABEL[f.status]}</span>
              </li>
            ))}
          </ul>
        </section>

        {PHASE_PLAN.map((phase) => {
          const c = phaseCounts(phase);
          return (
            <section key={phase.key} className="req-group">
              <div className="req-group__head">
                <h2 className="h2">{phase.title}</h2>
                <span className="caption">
                  {c.live}/{c.total}
                </span>
              </div>
              <p className="caption" style={{ margin: '0 0 8px' }}>
                {phase.blurb}
              </p>
              <ul className="req-list">
                {phase.rows.map((row) => (
                  <li className="req req--stacked" key={row.fr}>
                    <div className="req__main">
                      <span className="req__id">{row.fr}</span>
                      <span className="req__title">{row.title}</span>
                      <span className={PILL[row.status]}>{STATUS_LABEL[row.status]}</span>
                    </div>
                    <ChainRow chain={row.chain} />
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
      </main>
    </>
  );
}
