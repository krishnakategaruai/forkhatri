"use client";

// A step line ("Step 1 of 3 · Who you are") with a segmented bar, so nobody
// has to guess how much is left (Apna's users "didn't know how many steps
// were left", design language §1). Done segments are ink, never brand: the
// one brand fill on the screen is the Continue button.
export default function Steps({ step, total, label, stepLabel }: { step: number; total: number; label: string; stepLabel: string }) {
  return (
    <div className="vy-acct-steps" role="group" aria-label={stepLabel}>
      <div className="vy-acct-steps-line">
        <span>{stepLabel}</span>
        <span style={{ textTransform: "none", letterSpacing: 0, color: "var(--text-secondary)" }}>{label}</span>
      </div>
      <div className="vy-acct-steps-bar" aria-hidden="true">
        {Array.from({ length: total }, (_, i) => (
          <span key={i} data-done={i < step ? "" : undefined} />
        ))}
      </div>
    </div>
  );
}
