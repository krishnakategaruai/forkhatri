"use client";

// [Owner, 2026-09-30: "locality can be taken current right"] The locality
// field that never starts as an empty required box when the app can know it:
//   - known (first run, the profile): shown filled, editable;
//   - unknown: a one-tap "Use my current location" first. When the service
//     names the area, it is filled; otherwise the areas Vyapar already knows
//     are offered as one-tap chips, and typing stays as the fallback.
// The coordinates found are handed up so the profile is saved with them.
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { LocateFixed } from "lucide-react";
import { api } from "@/lib/api";
import { locateMe } from "./useMyProfile";

export default function LocalityField({
  id,
  value,
  onChange,
  onCoords,
  label,
  placeholder,
  hint,
}: {
  id: string;
  value: string;
  onChange: (v: string) => void;
  onCoords?: (lat: number, lng: number) => void;
  label: string;
  placeholder?: string;
  hint?: string;
}) {
  const { t, i18n } = useTranslation(["listings"]);
  const [state, setState] = useState<"idle" | "busy" | "pick" | "denied">("idle");
  const [known, setKnown] = useState<string[]>([]);

  useEffect(() => {
    if ((state !== "pick" && state !== "denied") || known.length) return;
    api
      .get<{ localities: string[] }>("/v1/listings/search-suggestions")
      .then((d) => setKnown(d.localities ?? []))
      .catch(() => setKnown([]));
  }, [state, known.length, i18n.language]);

  async function locate() {
    setState("busy");
    try {
      const r = await locateMe();
      onCoords?.(r.lat, r.lng);
      if (r.locality) {
        onChange(r.locality);
        setState("idle");
      } else {
        setState("pick");
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
          {state === "busy" ? t("listings:new.locating") : t("listings:new.useLocation")}
        </button>
      )}
      {(state === "pick" || state === "denied") && known.length > 0 && !value.trim() && (
        <div className="vy-stack" style={{ gap: 6 }}>
          <span className="vy-acct-hint">{t("listings:new.pickArea")}</span>
          <div className="vy-acct-inline-choices" role="group" aria-label={t("listings:new.pickArea")}>
            {known.map((l) => (
              <button key={l} type="button" className="vy-chip" onClick={() => onChange(l)}>
                {l}
              </button>
            ))}
          </div>
        </div>
      )}
      {state === "denied" && <span className="vy-acct-hint" role="status">{t("listings:new.locationDenied")}</span>}
      <input id={id} className="vy-input" value={value} autoComplete="address-level3" onChange={(e) => onChange(e.target.value)} placeholder={placeholder} />
      {hint && <span className="vy-acct-hint">{hint}</span>}
    </div>
  );
}
