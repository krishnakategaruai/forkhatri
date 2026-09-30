"use client";

// [FE2 — imp-backend-b §4] Service packages, the owner's side: up to three
// tiers, each a short form (name · price · delivery days · revisions · up to
// five "included" lines · optional description). Offering fewer tiers is
// fine: a tier left without a name and price is simply not offered. Saving
// upserts by tier (PUT); "Stop offering" removes one tier. Three columns on
// a wide screen, stacked on a phone.
import { useState } from "react";
// [Trust pack §1] packages are checked as the owner types (fees on applicants, "send ₹… to 98…")
import { ScamShieldNote, scamFromError, useScamShieldFields } from "@/app/components/trust/ScamShield";
import { useTranslation } from "react-i18next";
import type { PackageTier, ServicePackage, ServicePackageInput } from "@/lib/sdk";
import { paiseToInput, rupeesToPaise } from "@/lib/format";

const TIERS: PackageTier[] = ["basic", "standard", "premium"];

interface TierDraft {
  id: string | null;
  name: string;
  price: string;
  delivery: string;
  revisions: string;
  includes: string[];
  description: string;
}

function toDraft(p?: ServicePackage): TierDraft {
  return {
    id: p?.id ?? null,
    name: p?.name ?? "",
    price: paiseToInput(p?.price_paise ?? null),
    delivery: p?.delivery_days != null ? String(p.delivery_days) : "",
    revisions: p?.revisions != null ? String(p.revisions) : "",
    includes: p?.includes?.length ? [...p.includes] : [""],
    description: p?.description ?? "",
  };
}

export default function PackagesEditor({
  packages,
  onSave,
  onRemove,
}: {
  packages: ServicePackage[];
  onSave: (input: ServicePackageInput[]) => Promise<void>;
  onRemove: (packageId: string) => Promise<void>;
}) {
  const { t } = useTranslation(["packages", "common"]);
  const [drafts, setDrafts] = useState<Record<PackageTier, TierDraft>>(() => ({
    basic: toDraft(packages.find((p) => p.tier === "basic")),
    standard: toDraft(packages.find((p) => p.tier === "standard")),
    premium: toDraft(packages.find((p) => p.tier === "premium")),
  }));
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const tierText = (d: TierDraft) => [d.name, d.description, ...d.includes].map((x) => x.trim()).filter(Boolean).join(" · ");
  const shield = useScamShieldFields(
    { basic: tierText(drafts.basic), standard: tierText(drafts.standard), premium: tierText(drafts.premium) },
    "package",
  );

  const set = (tier: PackageTier, patch: Partial<TierDraft>) => {
    setDrafts((d) => ({ ...d, [tier]: { ...d[tier], ...patch } }));
    setMessage(null);
  };

  async function save() {
    const input: ServicePackageInput[] = [];
    for (const [i, tier] of TIERS.entries()) {
      const d = drafts[tier];
      const filled = d.name.trim() || d.price.trim();
      if (!filled) continue;
      const price = rupeesToPaise(d.price);
      if (!d.name.trim() || !price) {
        setMessage({ ok: false, text: t("packages:editor.errTier", { tier: t(`packages:tierName.${tier}`) }) });
        return;
      }
      input.push({
        tier,
        name: d.name.trim(),
        description: d.description.trim() || null,
        price_paise: price,
        delivery_days: d.delivery ? Number(d.delivery) : null,
        revisions: d.revisions ? Number(d.revisions) : null,
        includes: d.includes.map((x) => x.trim()).filter(Boolean).slice(0, 5),
        sort: i,
      });
    }
    if (input.length === 0) {
      setMessage({ ok: false, text: t("packages:editor.errNone") });
      return;
    }
    setBusy(true);
    try {
      await onSave(input);
      setMessage({ ok: true, text: t("packages:editor.saved") });
    } catch (e) {
      const scam = scamFromError(e);
      setMessage({ ok: false, text: scam?.message ?? (e instanceof Error && e.message ? e.message : t("common:state.actionFailed")) });
    } finally {
      setBusy(false);
    }
  }

  async function remove(tier: PackageTier) {
    const id = drafts[tier].id;
    if (!id) {
      set(tier, toDraft());
      return;
    }
    setBusy(true);
    try {
      await onRemove(id);
      set(tier, toDraft());
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="vy-card vy-card-nested vy-stack" style={{ gap: 16 }} aria-labelledby="pkg-edit-title">
      <div className="vy-stack" style={{ gap: 4 }}>
        <h2 id="pkg-edit-title" className="vy-card-title">{t("packages:editor.title")}</h2>
        <p className="vy-muted">{t("packages:editor.subtitle")}</p>
      </div>
      <div className="vy-pkg-editor">
        {TIERS.map((tier) => {
          const d = drafts[tier];
          return (
            <fieldset key={tier} className="vy-stack" style={{ gap: 10, border: "1px solid var(--border-hairline)", borderRadius: "var(--radius-md)", padding: 14, margin: 0 }} disabled={busy}>
              <legend className="vy-eyebrow" style={{ padding: "0 6px" }}>{t(`packages:tierName.${tier}`)}</legend>
              <label className="vy-field">
                <span className="vy-label">{t("packages:editor.name")}</span>
                <input className="vy-input" maxLength={120} value={d.name} onChange={(e) => set(tier, { name: e.target.value })} placeholder={t(`packages:editor.namePlaceholder.${tier}`)} />
              </label>
              <div className="vy-field-pair">
                <label className="vy-field">
                  <span className="vy-label">{t("packages:editor.price")}</span>
                  <input className="vy-input" inputMode="decimal" value={d.price} onChange={(e) => set(tier, { price: e.target.value })} />
                </label>
                <label className="vy-field">
                  <span className="vy-label">{t("packages:editor.delivery")}</span>
                  <input className="vy-input" type="number" min={1} max={365} value={d.delivery} onChange={(e) => set(tier, { delivery: e.target.value })} />
                </label>
              </div>
              <label className="vy-field">
                <span className="vy-label">
                  {t("packages:editor.revisions")} <span className="vy-optional">· {t("hiring:fields.optional")}</span>
                </span>
                <input className="vy-input" type="number" min={0} max={20} value={d.revisions} onChange={(e) => set(tier, { revisions: e.target.value })} />
              </label>
              <div className="vy-stack" style={{ gap: 6 }}>
                <span className="vy-label">{t("packages:editor.includes")}</span>
                {d.includes.map((x, i) => (
                  <input
                    key={i}
                    className="vy-input"
                    maxLength={80}
                    value={x}
                    aria-label={t("packages:editor.includeN", { n: i + 1 })}
                    onChange={(e) => set(tier, { includes: d.includes.map((y, j) => (j === i ? e.target.value : y)) })}
                  />
                ))}
                {d.includes.length < 5 && (
                  <button type="button" className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start", fontSize: 13 }} onClick={() => set(tier, { includes: [...d.includes, ""] })}>
                    + {t("packages:editor.addInclude")}
                  </button>
                )}
              </div>
              <label className="vy-field">
                <span className="vy-label">{t("packages:editor.description")}</span>
                <textarea className="vy-textarea" rows={2} maxLength={500} value={d.description} onChange={(e) => set(tier, { description: e.target.value })} />
              </label>
              <ScamShieldNote finding={shield[tier]} />
              {(d.id || d.name || d.price) && (
                <button type="button" className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start", fontSize: 13 }} onClick={() => remove(tier)}>
                  {t("packages:editor.remove")}
                </button>
              )}
            </fieldset>
          );
        })}
      </div>
      <div className="vy-row" style={{ gap: 12, flexWrap: "wrap" }}>
        <button className="vy-btn vy-btn-primary" disabled={busy} onClick={save}>
          {busy ? t("packages:sending") : t("packages:editor.save")}
        </button>
        {message && <span className={message.ok ? "vy-muted" : "vy-error"} role="status">{message.ok ? `✓ ${message.text}` : message.text}</span>}
      </div>
    </section>
  );
}
