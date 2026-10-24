"use client";

// [Owner, 2026-09-30: "locality can be taken current right"] The locality
// field that never starts as an empty required box when the app can know it:
//   - known (first run, the profile): shown filled, editable;
//   - unknown: a one-tap "Use my current location" first. When the service
//     names the area, it is filled; otherwise the areas Vyapar already knows
//     are offered as one-tap chips, and typing stays as the fallback.
// The coordinates found are handed up so the profile is saved with them.
// [Start flow 2026-10, decision 6 — audit: Kakinada and Delhi were offered
// Hyderabad areas] Chips are offered only for areas that really are nearby
// (the locate call's `nearby`, within about 25 km); when the service cannot
// name the area it says so and asks the member to type it. Any town typed
// is accepted as written.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { LocateFixed } from "lucide-react";
import { locateMe } from "./useMyProfile";

export default function LocalityField({
  id,
  value,
  onChange,
  onCoords,
  label,
  placeholder,
  hint,
  useLocationLabel,
}: {
  id: string;
  value: string;
  onChange: (v: string) => void;
  onCoords?: (lat: number, lng: number) => void;
  label: string;
  placeholder?: string;
  hint?: string;
  /** Wording of the one-tap button, e.g. "Use where I am now". */
  useLocationLabel?: string;
}) {
  const { t } = useTranslation(["listings"]);
  const [state, setState] = useState<"idle" | "busy" | "pick" | "unnamed" | "denied">("idle");
  const [nearby, setNearby] = useState<string[]>([]);

  async function locate() {
    setState("busy");
    try {
      const r = await locateMe();
      onCoords?.(r.lat, r.lng);
      setNearby(r.nearby);
      if (r.locality) {
        onChange(r.locality);
        setState("idle");
      } else {
        setState(r.nearby.length ? "pick" : "unnamed");
      }
    } catch {
      setState("denied");
    }
  }

  return (
    <div className="vy-acct-field">
      <label className="vy-label" htmlFor={id}>{label}</label>
      {!value.trim() && (
        <button type="button" className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} disabled={state === "busy"} onClick={locate}>
          <LocateFixed size={18} strokeWidth={2} aria-hidden="true" />
          {state === "busy" ? t("listings:new.locating") : useLocationLabel ?? t("listings:new.useLocation")}
        </button>
      )}
      {state === "pick" && nearby.length > 0 && !value.trim() && (
        <div className="vy-stack" style={{ gap: 6 }}>
          <span className="vy-acct-hint">{t("listings:new.pickArea")}</span>
          <div className="vy-acct-inline-choices" role="group" aria-label={t("listings:new.pickArea")}>
            {nearby.map((l) => (
              <button key={l} type="button" className="vy-chip" onClick={() => onChange(l)}>
                {l}
              </button>
            ))}
          </div>
        </div>
      )}
      {state === "unnamed" && !value.trim() && <span className="vy-acct-hint" role="status">{t("listings:new.locationUnnamed")}</span>}
      {state === "denied" && <span className="vy-acct-hint" role="status">{t("listings:new.locationDenied")}</span>}
      <input id={id} className="vy-input" value={value} autoComplete="address-level3" onChange={(e) => onChange(e.target.value)} placeholder={placeholder} />
      {hint && <span className="vy-acct-hint">{hint}</span>}
    </div>
  );
}
