"use client";

/** The module registry: open a module to every member, or keep it being built or planned. Owners only change it. */
import { useState } from "react";
import { admin, type AdminModule } from "@/lib/admin-api";
import { Badge, Chips, Dialog, errorMessage, ErrorLine, Field, formatNumber, Loading, PageHead, useConsole, useLoad } from "./kit";

type Availability = AdminModule["availability"];
const STATES: Availability[] = ["available", "in_development", "planned"];

export default function Modules() {
  const { t, lang, can, changed } = useConsole();
  const list = useLoad(() => admin.modules(), []);
  const rows = list.data;
  const [actionError, setError] = useState<string | null>(null);
  const error = actionError ?? (list.error ? errorMessage(t, list.error) : null);
  const [change, setChange] = useState<{ module: AdminModule; to: Availability } | null>(null);
  const [note, setNote] = useState("");

  const label = (a: Availability) => t(`availability_${a}`);

  return (
    <div className="adm-page">
      <PageHead title={t("modulesTitle")} sub={t("modulesSub")} />
      <ErrorLine error={error} />
      {!rows ? (
        <Loading />
      ) : (
        <ul className="adm-list adm-card">
          {rows.map((m) => (
            <li key={m.key} className="adm-row is-static adm-module-row">
              <span className="adm-row-main">
                <span className="adm-row-title">{m.name}</span>
                <span className="adm-row-sub">{t("moduleMembers", { n: formatNumber(m.members, lang) })}</span>
              </span>
              {can("modules.manage") ? (
                <Chips
                  label={m.name}
                  value={m.availability}
                  onChange={(to) => {
                    if (to !== m.availability) {
                      setNote("");
                      setChange({ module: m, to });
                    }
                  }}
                  options={STATES.map((s) => ({ value: s, label: label(s) }))}
                />
              ) : (
                <Badge tone={m.availability === "available" ? "ok" : "neutral"}>{label(m.availability)}</Badge>
              )}
            </li>
          ))}
        </ul>
      )}
      <Dialog open={!!change} onClose={() => setChange(null)} title={change ? `${change.module.name}: ${label(change.to)}` : ""}>
        <Field label={t("changeReason")}>
          <textarea className="adm-input" rows={3} value={note} onChange={(e) => setNote(e.target.value)} />
        </Field>
        <div className="adm-actions end">
          <button type="button" className="adm-btn" onClick={() => setChange(null)}>
            {t("cancel")}
          </button>
          <button
            type="button"
            className="adm-btn primary"
            disabled={note.trim().length < 3}
            onClick={async () => {
              if (!change) return;
              try {
                list.set(await admin.setModule(change.module.key, change.to, note));
                setChange(null);
                changed();
              } catch (e) {
                setError(errorMessage(t, e));
                setChange(null);
              }
            }}
          >
            {t("confirm")}
          </button>
        </div>
      </Dialog>
    </div>
  );
}
