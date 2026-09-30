"use client";

// ======================================================================
// [Trust pack §5, 2026-09-30] Council registrations.
//
// REQUIREMENT: a CA, doctor, allied health professional, advocate or
// architect adds their registration once ("Add a registration" → council →
// number); the badge reads "Pending check" until a real check, then
// "Registered with Bar Council of Telangana · Checked on 30 Sep 2026". A
// claim never draws a tick. Numbers are validated by the API (its message,
// in the reader's language, lands under the field it names).
// APPROACH:
//  - <CouncilBadges>: the public entries under a name (profile header,
//    directory cards). Verified: a tick + label · checked on. Claimed: a
//    quiet hourglass + label, no tick.
//  - <CouncilCredentialsPanel>: the owner's card on their Work profile —
//    each registration with its status, Check again and Remove, and the
//    add form in place (FieldSelect for the register and the council,
//    FieldSelect suggestions or a typed council, the number with the
//    register's own hint, the date, a DigiLocker link when needed).
// ======================================================================

import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { BadgeCheck, Hourglass, Landmark, Plus, RefreshCw, Trash2, TriangleAlert } from "lucide-react";
import { ApiError, type CouncilBadge, type Credential, type CredentialType } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { FieldSelect } from "@/app/components/ui/FieldSelect";
import DisabledReason from "@/app/components/DisabledReason";

function statusVisual(status: string) {
  if (status === "verified") return { icon: BadgeCheck, tone: "verified" as const };
  if (status === "claimed") return { icon: Hourglass, tone: "pending" as const };
  return { icon: TriangleAlert, tone: "warn" as const };
}

/** Public council entries: "Registered with … · Checked on …", or a pending claim without a tick. */
export function CouncilBadges({ badges, compact = false }: { badges: CouncilBadge[] | null | undefined; compact?: boolean }) {
  const shown = (badges ?? []).filter((b) => b.status === "verified" || b.status === "claimed");
  if (shown.length === 0) return null;
  const list = compact ? shown.slice(0, 1) : shown;
  return (
    <ul className={`vy-council${compact ? " vy-council-compact" : ""}`}>
      {list.map((b) => {
        const v = statusVisual(b.status);
        const Icon = v.icon;
        return (
          <li key={b.id} className="vy-council-item" data-tone={v.tone}>
            <Icon size={compact ? 15 : 16} strokeWidth={2} aria-hidden="true" />
            <span>
              {b.label}
              {!compact && b.status === "verified" && b.checked_on_label && <span className="vy-council-date vy-num"> · {b.checked_on_label}</span>}
              {!compact && <span className="vy-council-number vy-num">{b.registration_number}</span>}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

const OTHER = "__other__";

function AddCredentialForm({ types, onAdded, onCancel }: { types: CredentialType[]; onAdded: () => void; onCancel: () => void }) {
  const { t } = useTranslation(["verification", "common"]);
  const sdk = useSdk();
  const [type, setType] = useState<string | null>(null);
  const [councilPick, setCouncilPick] = useState<string | null>(null);
  const [councilText, setCouncilText] = useState("");
  const [number, setNumber] = useState("");
  const [registeredOn, setRegisteredOn] = useState("");
  const [documentUri, setDocumentUri] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const def = types.find((x) => x.credential_type === type) ?? null;
  const council = def?.fixed_council ?? (councilPick === OTHER ? councilText.trim() : (councilPick ?? ""));
  const ready = !!def && !!number.trim() && !!council && (!def.needs_document_uri || !!documentUri.trim());
  const today = new Date().toISOString().slice(0, 10);

  async function save() {
    if (!def) return;
    setBusy(true);
    setErrors({});
    setFormError(null);
    try {
      await sdk.trustPack.addCredential({
        credential_type: def.credential_type,
        registration_number: number.trim(),
        council: def.fixed_council ? null : council,
        registered_on: registeredOn || null,
        document_uri: def.needs_document_uri ? documentUri.trim() : null,
      });
      onAdded();
    } catch (e) {
      const msg = e instanceof ApiError ? (typeof e.detail === "string" ? e.detail : String((e.detail as { message?: string })?.message ?? "")) : "";
      const field = e instanceof ApiError && typeof e.details?.field === "string" ? e.details.field : null;
      const text = msg || t("common:state.somethingWentWrong");
      if (field && ["registration_number", "council", "document_uri"].includes(field)) setErrors({ [field]: text });
      else setFormError(text);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="vy-acct-form vy-council-form">
      <div className="vy-acct-field">
        <span className="vy-label">{t("verification:council.form.type")}</span>
        <FieldSelect
          options={types.map((x) => ({ value: x.credential_type, label: x.label }))}
          value={type}
          onChange={(v) => {
            setType(v);
            setCouncilPick(null);
            setCouncilText("");
            setErrors({});
          }}
          placeholder={t("verification:council.form.typePlaceholder")}
          allowClear={false}
          ariaLabel={t("verification:council.form.type")}
        />
      </div>

      {def && (
        <>
          <div className="vy-acct-field">
            <span className="vy-label">{t("verification:council.form.council")}</span>
            {def.fixed_council ? (
              <p className="vy-council-fixed">{def.fixed_council}</p>
            ) : (
              <>
                {def.council_suggestions.length > 0 && (
                  <FieldSelect
                    options={[...def.council_suggestions.map((c) => ({ value: c, label: c })), { value: OTHER, label: t("verification:council.form.otherCouncil") }]}
                    value={councilPick}
                    onChange={setCouncilPick}
                    placeholder={t("verification:council.form.councilPlaceholder")}
                    allowClear={false}
                    ariaLabel={t("verification:council.form.council")}
                  />
                )}
                {(councilPick === OTHER || def.council_suggestions.length === 0) && (
                  <input
                    className="vy-input"
                    value={councilText}
                    maxLength={120}
                    onChange={(e) => setCouncilText(e.target.value)}
                    placeholder={t("verification:council.form.councilTyped")}
                    aria-label={t("verification:council.form.council")}
                    aria-invalid={!!errors.council || undefined}
                  />
                )}
              </>
            )}
            {errors.council && <p className="vy-error">{errors.council}</p>}
          </div>

          <div className="vy-acct-field">
            <label className="vy-label" htmlFor="vy-cred-number">
              {t("verification:council.form.number")}
            </label>
            <input
              id="vy-cred-number"
              className="vy-input vy-num"
              value={number}
              maxLength={60}
              autoCapitalize="characters"
              onChange={(e) => {
                setNumber(e.target.value);
                setErrors((x) => ({ ...x, registration_number: "" }));
              }}
              aria-describedby="vy-cred-number-hint"
              aria-invalid={!!errors.registration_number || undefined}
            />
            {/* the register's own format, until the API says what is wrong with it */}
            {errors.registration_number ? (
              <p id="vy-cred-number-hint" className="vy-error">
                {errors.registration_number}
              </p>
            ) : (
              <span id="vy-cred-number-hint" className="vy-field-hint">
                {def.number_hint}
              </span>
            )}
          </div>

          {def.needs_document_uri && (
            <div className="vy-acct-field">
              <label className="vy-label" htmlFor="vy-cred-uri">
                {t("verification:council.form.documentUri")}
              </label>
              <input
                id="vy-cred-uri"
                className="vy-input"
                value={documentUri}
                onChange={(e) => setDocumentUri(e.target.value)}
                placeholder="in.gov.…"
                aria-invalid={!!errors.document_uri || undefined}
              />
              {errors.document_uri && <p className="vy-error">{errors.document_uri}</p>}
            </div>
          )}

          <div className="vy-acct-field">
            <label className="vy-label" htmlFor="vy-cred-date">
              {t("verification:council.form.registeredOn")}
            </label>
            <input id="vy-cred-date" type="date" className="vy-input vy-num" style={{ maxWidth: 220 }} max={today} value={registeredOn} onChange={(e) => setRegisteredOn(e.target.value)} />
          </div>
        </>
      )}

      {formError && (
        <p className="vy-error" role="alert">
          {formError}
        </p>
      )}
      <div className="vy-row" style={{ flexWrap: "wrap", gap: 8 }}>
        <button type="button" className="vy-btn vy-btn-primary" disabled={!ready || busy} aria-describedby={!ready ? "vy-cred-why" : undefined} onClick={save}>
          {busy ? t("common:state.saving") : t("verification:council.form.save")}
        </button>
        <button type="button" className="vy-btn vy-btn-ghost" disabled={busy} onClick={onCancel}>
          {t("common:action.cancel")}
        </button>
      </div>
      <DisabledReason id="vy-cred-why" show={!ready && !busy}>
        {!def ? t("verification:council.form.whyType") : !council ? t("verification:council.form.whyCouncil") : t("verification:council.form.whyNumber")}
      </DisabledReason>
    </div>
  );
}

/** The owner's council registrations on their Work profile. */
export function CouncilCredentialsPanel({ onChanged }: { onChanged?: () => void }) {
  const { t, i18n } = useTranslation(["verification", "common"]);
  const sdk = useSdk();
  const [items, setItems] = useState<Credential[] | null>(null);
  const [types, setTypes] = useState<CredentialType[]>([]);
  const [adding, setAdding] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    return Promise.all([sdk.trustPack.myCredentials(), sdk.trustPack.credentialTypes()])
      .then(([mine, kinds]) => {
        setItems(mine);
        setTypes(kinds);
      })
      .catch(() => setItems([]));
  }, [sdk]);

  useEffect(() => {
    queueMicrotask(() => void load());
  }, [load, i18n.language]);

  async function run(id: string, fn: () => Promise<unknown>) {
    setBusyId(id);
    setError(null);
    try {
      await fn();
      await load();
      onChanged?.();
    } catch (e) {
      setError(e instanceof ApiError && typeof e.detail === "string" ? e.detail : t("common:state.somethingWentWrong"));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="vy-card vy-acct-card" aria-labelledby="council-title">
      <div className="vy-acct-card-head">
        <span className="vy-acct-tile" data-tint="indigo" aria-hidden="true">
          <Landmark size={20} strokeWidth={1.9} />
        </span>
        <h2 id="council-title">{t("verification:council.panel.title")}</h2>
        <p>{t("verification:council.panel.purpose")}</p>
      </div>

      {items === null && <div className="vy-skeleton" style={{ height: 56 }} aria-hidden="true" />}
      {items && items.length > 0 && (
        <ul className="vy-council-rows">
          {items.map((c) => {
            const v = statusVisual(c.status);
            const Icon = v.icon;
            return (
              <li key={c.id} className="vy-council-row">
                <div className="vy-council-row-text">
                  <strong>{c.type_label}</strong>
                  <span className="vy-num">
                    {c.council} · {c.registration_number}
                  </span>
                  <span className="vy-council-item" data-tone={v.tone}>
                    <Icon size={15} strokeWidth={2} aria-hidden="true" />
                    <span>
                      {c.label}
                      {c.status === "verified" && c.checked_on_label && <span className="vy-num"> · {c.checked_on_label}</span>}
                    </span>
                  </span>
                  {c.check_note && <span className="vy-field-hint">{c.check_note}</span>}
                </div>
                <div className="vy-council-row-actions">
                  {(c.status === "expired" || c.status === "failed") && (
                    <button type="button" className="vy-btn vy-btn-ghost" disabled={busyId === c.id} onClick={() => run(c.id, () => sdk.trustPack.recheckCredential(c.id))}>
                      <RefreshCw size={16} strokeWidth={2} aria-hidden="true" />
                      {t("verification:council.panel.recheck")}
                    </button>
                  )}
                  <button
                    type="button"
                    className="vy-iconbtn"
                    aria-label={t("verification:council.panel.remove", { name: c.type_label })}
                    title={t("verification:council.panel.remove", { name: c.type_label })}
                    disabled={busyId === c.id}
                    onClick={() => run(c.id, () => sdk.trustPack.deleteCredential(c.id))}
                  >
                    <Trash2 size={18} strokeWidth={1.9} aria-hidden="true" />
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
      {error && (
        <p className="vy-error" role="alert">
          {error}
        </p>
      )}

      {adding ? (
        <AddCredentialForm
          types={types}
          onCancel={() => setAdding(false)}
          onAdded={() => {
            setAdding(false);
            void load();
            onChanged?.();
          }}
        />
      ) : (
        items !== null && (
          <button type="button" className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} onClick={() => setAdding(true)}>
            <Plus size={18} strokeWidth={2} aria-hidden="true" />
            {t("verification:council.panel.add")}
          </button>
        )
      )}
      <p className="vy-field-hint">{t("verification:council.panel.howChecked")}</p>
    </section>
  );
}
