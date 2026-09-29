"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { Avatar } from "@/components/Avatar";
import { exportBiodata, formatDay, type BiodataExport } from "@/lib/agents";
import { resolveMediaUrl } from "@/lib/api";

import "../agent.css";

/* [DEC-V1-033] The agent's biodata export: one page per person, the layout an
 * Indian family expects from a printed biodata (photo, name, then the facts
 * by section), stamped with the agent's bureau and the date so a forwarded
 * copy says whose it is. The browser prints it or saves it as a PDF. Each
 * family in it can see, on their agent dashboard, that it was made. */

/* The sections a family reads on a biodata, whatever table each fact lives in
 * (the profile keeps education in two categories, family in two, and so on). */
const GROUPS: [string, string[]][] = [
  ["basics", ["basics", "marital_history", "self_expression"]],
  ["education_career", ["education", "education_career", "profession"]],
  ["family", ["family", "family_involvement_expectations"]],
  ["community", ["community"]],
  ["horoscope", ["horoscope"]],
  ["lifestyle", ["lifestyle", "relocation", "food_travel_hobbies", "career_children_living_financial"]],
];

const SKIP_KEYS = new Set(["birth_place_geo", "matching_required", "matching_system", "brief", "priorities", "scales"]);

function readable(value: unknown): string {
  if (value == null) return "";
  if (Array.isArray(value)) return value.map(readable).filter(Boolean).join(", ");
  if (typeof value === "object") {
    const v = value as Record<string, unknown>;
    if ("label" in v) return String(v.label);
    if ("min" in v || "max" in v) return [v.min, v.max].filter((x) => x != null).join(" – ");
    return Object.values(v).map(readable).filter(Boolean).join(", ");
  }
  const s = String(value);
  return /^[a-z0-9_]+$/.test(s) ? s.replace(/_/g, " ") : s;
}

function BiodataPrint() {
  const { t, i18n } = useTranslation(["agents", "profile", "common"]);
  const params = useSearchParams();
  const ids = (params.get("ids") ?? "").split(",").filter(Boolean);
  const withNumbers = params.get("numbers") !== "0";
  const [data, setData] = useState<BiodataExport | null | undefined>(undefined);

  useEffect(() => {
    if (!ids.length) return;
    let alive = true;
    exportBiodata(ids, withNumbers).then((out) => alive && setData(out.ok ? out.data : null));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  const label = (category: string, key: string) =>
    t(`profile:fieldView.${category}.${key}`, {
      defaultValue: t(`profile:field.${category}.${key}`, { defaultValue: key.replace(/_/g, " ") }),
    });
  // An option key ("masters") reads as its label in the reader's language.
  const value = (key: string, v: unknown) =>
    typeof v === "string" && /^[a-z0-9_]+$/.test(v)
      ? t(`profile:option.${key}.${v}`, { defaultValue: readable(v) })
      : readable(v);

  return (
    <main className="screen ag-screen">
      <div className="ag-print-bar">
        <Link className="link" href="/agent">
          ‹ {t("agents:workspace.title")}
        </Link>
        {data && data.people.length > 0 && (
          <button type="button" className="btn btn--primary" onClick={() => window.print()}>
            {t("agents:biodata.print")}
          </button>
        )}
      </div>
      {data === undefined && ids.length > 0 ? (
        <p className="caption">{t("agents:biodata.loading")}</p>
      ) : !data || data.people.length === 0 ? (
        <p className="caption">{t("agents:biodata.empty")}</p>
      ) : (
        data.people.map((p) => {
          const known = new Set(GROUPS.flatMap(([, cats]) => cats));
          const sections = GROUPS.map(([group, cats]) => {
            const seen = new Set<string>();
            const entries: [string, string, unknown][] = [];
            for (const category of [...cats, ...(group === "lifestyle" ? Object.keys(p.biodata).filter((c) => !known.has(c)) : [])]) {
              for (const [k, v] of Object.entries(p.biodata[category] ?? {})) {
                // The same fact kept in two places is shown once.
                if (SKIP_KEYS.has(k) || !readable(v) || seen.has(k)) continue;
                seen.add(k);
                entries.push([category, k, v]);
              }
            }
            return [group, entries] as const;
          }).filter(([, entries]) => entries.length > 0);
          return (
            <article key={p.account_id} className="ag-bio">
              <div className="ag-bio__head">
                <div className="ag-bio__photo">
                  {p.photo_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={resolveMediaUrl(p.photo_url) ?? ""} alt="" />
                  ) : (
                    <Avatar anonymized size={96} />
                  )}
                </div>
                <div className="ag-head">
                  <p className="ag-eyebrow">{t("agents:biodata.title")}</p>
                  <h2 className="ag-bio__name">{p.name ?? t("agents:family.age", { age: p.age ?? "" })}</h2>
                  <span className="caption">
                    {[p.age != null ? t("agents:family.age", { age: p.age }) : null, p.city].filter(Boolean).join(" · ")}
                  </span>
                  {p.contacts.length > 0 && (
                    <div className="ag-phones">
                      <span className="label">{t("agents:biodata.contacts")}</span>
                      {p.contacts.map((c) => (
                        <span key={c.account_id}>
                          {c.display_name} ({t(`agents:clients.relation.${c.relation}`, { defaultValue: c.relation })}): {c.phone}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <div className="ag-bio__sections">
                {sections.map(([category, entries]) => (
                  <section key={category} className="ag-bio__section">
                    <h3>{t(`agents:section.${category}`, { defaultValue: category.replace(/_/g, " ") })}</h3>
                    <dl className="ag-facts">
                      {entries.map(([cat, k, v]) => (
                        <FactRow key={k} label={label(cat, k)} value={value(k, v)} />
                      ))}
                    </dl>
                  </section>
                ))}
              </div>
              <p className="ag-bio__stamp">
                {t("agents:biodata.stamp", { agent: data.agent_name, date: formatDay(data.made_on, i18n.language) })}
                {data.agent_phone ? ` · ${data.agent_phone}` : ""}
              </p>
            </article>
          );
        })
      )}
    </main>
  );
}

function FactRow({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  );
}

export default function BiodataPage() {
  return (
    <Suspense fallback={null}>
      <BiodataPrint />
    </Suspense>
  );
}
