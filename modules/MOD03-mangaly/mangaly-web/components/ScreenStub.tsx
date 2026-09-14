/* Placeholder for a tab whose requirements are not built yet.
 *
 * Deliberately states which TRs will fill the screen, so an empty tab reads as
 * "not built yet, here's what's coming" rather than as a broken screen. These
 * are replaced by real screens as each requirement lands. */

export default function ScreenStub({
  title,
  blurb,
  reqs,
}: {
  title: string;
  blurb: string;
  reqs: { id: string; title: string }[];
}) {
  return (
    <>
      <header className="topbar">
        <h1>{title}</h1>
        <span className="pill pill--pending">Not yet built</span>
      </header>

      <main className="screen">
        <div className="empty">
          <span className="empty__mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="26" height="26">
              <path
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4 7h16M4 12h10M4 17h7"
              />
            </svg>
          </span>
          <p className="body-lg" style={{ margin: 0, color: 'var(--text-primary)' }}>
            {blurb}
          </p>
          <p className="caption" style={{ margin: 0 }}>
            This tab lights up as the requirements below are implemented.
          </p>
        </div>

        <section>
          <h2 className="h2" style={{ marginBottom: 8 }}>
            Planned here
          </h2>
          <ul className="req-list">
            {reqs.map((r) => (
              <li className="req" key={r.id + r.title}>
                <span className="req__id">{r.id}</span>
                <span className="req__title">{r.title}</span>
                <span className="pill pill--pending">Not yet</span>
              </li>
            ))}
          </ul>
        </section>
      </main>
    </>
  );
}
