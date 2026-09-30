"use client";

// A segmented control built from buttons (the shell's .vy-segmented look:
// a sunken track, the chosen segment a raised white pill). Used wherever a
// native <select> with two to four options used to be: how you work, who
// sees your number, whether you are looking for work.
export interface SegmentOption<T extends string> {
  value: T;
  label: string;
}

export default function Segmented<T extends string>({
  options,
  value,
  onChange,
  ariaLabel,
  disabled,
}: {
  options: SegmentOption<T>[];
  value: T;
  onChange: (next: T) => void;
  ariaLabel: string;
  disabled?: boolean;
}) {
  return (
    <div className="vy-segmented vy-acct-segmented" role="group" aria-label={ariaLabel}>
      {options.map((o) => (
        <button key={o.value} type="button" aria-pressed={value === o.value} disabled={disabled} onClick={() => onChange(o.value)} title={o.label}>
          {o.label}
        </button>
      ))}
    </div>
  );
}
