"use client";

// A setting as one row: label, one-line explanation, and a real switch on
// the right (the shell styles input[role="switch"]). The whole row is the
// label, so the tap target is the full 52px row, not a 16px checkbox.
export default function SwitchRow({
  id,
  label,
  hint,
  checked,
  disabled,
  onChange,
}: {
  id: string;
  label: string;
  hint?: string;
  checked: boolean;
  disabled?: boolean;
  onChange: (next: boolean) => void;
}) {
  return (
    <label className="vy-acct-switch" htmlFor={id}>
      <span className="vy-acct-switch-text">
        <span className="vy-acct-switch-label">{label}</span>
        {hint && <span className="vy-acct-switch-hint">{hint}</span>}
      </span>
      <input id={id} type="checkbox" role="switch" checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)} />
    </label>
  );
}
