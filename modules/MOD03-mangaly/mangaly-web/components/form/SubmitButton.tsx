'use client';

/* [UI03] Full-width CTA in the bottom third (thumb zone), saffron fill with
 * navy text — never white on saffron, which fails contrast. Loading swaps the
 * label for a spinner at a FIXED width so the button does not resize and shift
 * the layout under the user's thumb mid-tap. */

export function SubmitButton({
  label,
  busy,
  disabled,
}: {
  label: string;
  busy?: boolean;
  disabled?: boolean;
}) {
  return (
    <button type="submit" className="cta" disabled={busy || disabled} aria-busy={busy}>
      <span className={busy ? 'cta__label cta__label--hidden' : 'cta__label'}>{label}</span>
      {busy && <span className="cta__spinner" aria-hidden="true" />}
    </button>
  );
}
