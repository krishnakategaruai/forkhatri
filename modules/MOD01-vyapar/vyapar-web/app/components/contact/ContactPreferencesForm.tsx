"use client";

// [FE2 — imp-backend-b §1, research §4] One compact form for "when can the
// people I accept reach me": calls on/off, WhatsApp on/off, days (seven
// chips, none = every day), hours (any time, or a from/to pair of hour
// pickers — no typing), calls per day (a stepper with "No limit"), and who
// may call. A live sentence under it says exactly what callers will
// experience ("People you accepted can call you Mon–Sat, 10 am–6 pm, up to
// 20 calls a day."), so the member never has to imagine the effect.
//
// Presentational: the value in, onChange out. The account screen and the
// per-listing override on the listing owner view both use it.
import { useTranslation } from "react-i18next";
import type { ContactPreferences, Weekday } from "@/lib/sdk";
import { formatClock } from "@/lib/format";
import { WEEKDAYS, dayShort, describeDays, describeHours } from "./callWindow";

export type ContactPrefsValue = Omit<ContactPreferences, "timezone">;

const HOURS = Array.from({ length: 24 }, (_, h) => `${String(h).padStart(2, "0")}:00`);
const CAP_STEPS = [1, 2, 3, 5, 10, 15, 20, 30, 50];

export function usePreviewSentence() {
  const { t, i18n } = useTranslation(["contact"]);
  return (v: ContactPrefsValue): string[] => {
    const lines: string[] = [];
    if (v.call_ok) {
      const days = describeDays(v.call_days, i18n.language) ?? t("contact:preview.everyDay");
      const hours = describeHours(v.call_hours_start, v.call_hours_end, i18n.language) ?? t("contact:preview.anyTime");
      lines.push(
        v.max_calls_per_day != null
          ? t("contact:preview.callsCapped", { days, hours, count: v.max_calls_per_day })
          : t("contact:preview.callsUncapped", { days, hours }),
      );
      if (v.calls_from === "matching_only") lines.push(t("contact:preview.matchingOnly"));
    } else {
      lines.push(t("contact:preview.callsOff"));
    }
    lines.push(v.whatsapp_ok ? t("contact:preview.whatsappOn") : t("contact:preview.whatsappOff"));
    return lines;
  };
}

export function ContactPreview({ value }: { value: ContactPrefsValue }) {
  const { t } = useTranslation(["contact"]);
  const sentence = usePreviewSentence()(value);
  return (
    <div className="vy-stack" style={{ gap: 8 }}>
      <span className="vy-eyebrow">{t("contact:prefs.previewTitle")}</span>
      <p className="vy-prefs-preview" aria-live="polite">
        {sentence.join(" ")}
      </p>
      <p className="vy-muted">{t("contact:prefs.timezone")}</p>
    </div>
  );
}

export default function ContactPreferencesForm({
  value,
  onChange,
  disabled,
}: {
  value: ContactPrefsValue;
  onChange: (next: ContactPrefsValue) => void;
  disabled?: boolean;
}) {
  const { t, i18n } = useTranslation(["contact"]);
  const set = (patch: Partial<ContactPrefsValue>) => onChange({ ...value, ...patch });
  const hasHours = !!(value.call_hours_start && value.call_hours_end);
  const capIndex = value.max_calls_per_day == null ? CAP_STEPS.length : CAP_STEPS.findIndex((n) => n >= (value.max_calls_per_day ?? 0));

  function toggleDay(day: Weekday) {
    const has = value.call_days.includes(day);
    const next = has ? value.call_days.filter((d) => d !== day) : [...value.call_days, day];
    set({ call_days: WEEKDAYS.filter((d) => next.includes(d)) });
  }

  function stepCap(dir: -1 | 1) {
    const i = Math.min(CAP_STEPS.length, Math.max(0, (capIndex < 0 ? CAP_STEPS.length : capIndex) + dir));
    set({ max_calls_per_day: i >= CAP_STEPS.length ? null : CAP_STEPS[i] });
  }

  return (
    <fieldset className="vy-stack" style={{ gap: 20, border: "none", padding: 0, margin: 0 }} disabled={disabled}>
      <label className="vy-toggle-row">
        <span>{t("contact:prefs.callsToggle")}</span>
        <input type="checkbox" checked={value.call_ok} onChange={(e) => set({ call_ok: e.target.checked })} />
      </label>

      {value.call_ok && (
        <>
          <div className="vy-stack" style={{ gap: 8 }}>
            <span className="vy-label">{t("contact:prefs.days")}</span>
            <div className="vy-day-chips" role="group" aria-label={t("contact:prefs.days")}>
              {WEEKDAYS.map((d) => (
                <button key={d} type="button" className="vy-chip" aria-pressed={value.call_days.includes(d)} onClick={() => toggleDay(d)}>
                  {dayShort(d, i18n.language)}
                </button>
              ))}
            </div>
            <span className="vy-muted">{t("contact:prefs.everyDayHint")}</span>
          </div>

          <div className="vy-stack" style={{ gap: 8 }}>
            <span className="vy-label">{t("contact:prefs.hours")}</span>
            <div className="vy-segmented" role="group" aria-label={t("contact:prefs.hours")}>
              <button type="button" aria-pressed={!hasHours} onClick={() => set({ call_hours_start: null, call_hours_end: null })}>
                {t("contact:prefs.anyTime")}
              </button>
              <button
                type="button"
                aria-pressed={hasHours}
                onClick={() => !hasHours && set({ call_hours_start: "10:00", call_hours_end: "18:00" })}
              >
                {t("contact:prefs.setHours")}
              </button>
            </div>
            {hasHours && (
              <div className="vy-time-pair">
                <select
                  className="vy-select"
                  aria-label={t("contact:prefs.from")}
                  value={(value.call_hours_start ?? "10:00").slice(0, 5)}
                  onChange={(e) => set({ call_hours_start: e.target.value })}
                >
                  {HOURS.map((h) => (
                    <option key={h} value={h}>
                      {formatClock(h, i18n.language)}
                    </option>
                  ))}
                </select>
                <span aria-hidden="true">–</span>
                <select
                  className="vy-select"
                  aria-label={t("contact:prefs.to")}
                  value={(value.call_hours_end ?? "18:00").slice(0, 5)}
                  onChange={(e) => set({ call_hours_end: e.target.value })}
                >
                  {HOURS.filter((h) => h > (value.call_hours_start ?? "00:00").slice(0, 5)).map((h) => (
                    <option key={h} value={h}>
                      {formatClock(h, i18n.language)}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
            <span className="vy-label">{t("contact:prefs.cap")}</span>
            <div className="vy-stepper">
              <button type="button" aria-label={t("contact:prefs.decrease")} disabled={capIndex === 0} onClick={() => stepCap(-1)}>
                −
              </button>
              <output aria-live="polite">
                {value.max_calls_per_day == null ? t("contact:prefs.noLimit") : t("contact:prefs.capValue", { count: value.max_calls_per_day })}
              </output>
              <button type="button" aria-label={t("contact:prefs.increase")} disabled={value.max_calls_per_day == null} onClick={() => stepCap(1)}>
                +
              </button>
            </div>
          </div>

          <div className="vy-stack" style={{ gap: 8 }}>
            <span className="vy-label">{t("contact:prefs.who")}</span>
            <div className="vy-segmented" role="group" aria-label={t("contact:prefs.who")}>
              <button type="button" aria-pressed={value.calls_from === "anyone"} onClick={() => set({ calls_from: "anyone" })}>
                {t("contact:prefs.anyone")}
              </button>
              <button type="button" aria-pressed={value.calls_from === "matching_only"} onClick={() => set({ calls_from: "matching_only" })}>
                {t("contact:prefs.matching")}
              </button>
            </div>
          </div>
        </>
      )}

      <label className="vy-toggle-row">
        <span>{t("contact:prefs.whatsappToggle")}</span>
        <input type="checkbox" checked={value.whatsapp_ok} onChange={(e) => set({ whatsapp_ok: e.target.checked })} />
      </label>
    </fieldset>
  );
}

/** The editable part of a preferences response. */
export function toValue(p: ContactPreferences): ContactPrefsValue {
  return {
    call_hours_start: p.call_hours_start ? p.call_hours_start.slice(0, 5) : null,
    call_hours_end: p.call_hours_end ? p.call_hours_end.slice(0, 5) : null,
    call_days: p.call_days ?? [],
    max_calls_per_day: p.max_calls_per_day,
    calls_from: p.calls_from ?? "anyone",
    whatsapp_ok: p.whatsapp_ok,
    call_ok: p.call_ok,
  };
}
