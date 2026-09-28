"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { search, type DiscoverFilters } from "@/lib/discovery";
import {
  INCOME_BANDS,
  MOTHER_TONGUES,
  SUB_COMMUNITIES,
} from "@/lib/profileCategoryConfig";

/* Every filter the search supports, grouped in the order a biodata is read —
 * basics, location, community, education and work, lifestyle — instead of the
 * six the old sheet exposed. The apply button carries a live count ("Show 24
 * matches"), the pattern people know from Airbnb and every serious search:
 * you see the effect of a filter before you commit to it, and never land on
 * an empty page you had no warning of. */

const MARITAL = ["never_married", "divorced", "widowed", "awaiting_divorce"];
const EDUCATION = ["high_school", "bachelors", "masters", "doctorate", "other"];
const DIET = ["vegetarian", "non_vegetarian", "eggetarian", "vegan"];
const MANGLIK = ["no", "yes", "partial"] as const;

type Props = {
  initial: DiscoverFilters;
  forCandidate?: string;
  onApply: (next: DiscoverFilters) => void;
  onClose: () => void;
};

type ListKey =
  | "maritalStatus"
  | "education"
  | "diet"
  | "motherTongue"
  | "subCommunity"
  | "incomeBand";

export default function DiscoverFiltersSheet({
  initial,
  forCandidate,
  onApply,
  onClose,
}: Props) {
  const { t } = useTranslation(["discover", "profile"]);
  const [draft, setDraft] = useState<DiscoverFilters>(initial);
  const [count, setCount] = useState<number | null>(null);

  // A live count for the apply button, lightly debounced.
  useEffect(() => {
    let alive = true;
    const timer = window.setTimeout(async () => {
      const found = await search(draft, { forCandidate, page: 1 });
      if (alive) setCount(found.total ?? found.results.length);
    }, 300);
    return () => {
      alive = false;
      window.clearTimeout(timer);
    };
  }, [draft, forCandidate]);

  function toggle(key: ListKey, value: string) {
    setDraft((d) => {
      const list = d[key] ?? [];
      const next = list.includes(value)
        ? list.filter((v) => v !== value)
        : [...list, value];
      return { ...d, [key]: next.length ? next : undefined };
    });
  }

  function chip(label: string, on: boolean, onClick: () => void) {
    return (
      <button
        key={label}
        type="button"
        className={`fchip${on ? " is-on" : ""}`}
        aria-pressed={on}
        onClick={onClick}
      >
        {label}
      </button>
    );
  }

  function range(
    label: string,
    minKey: "ageMin" | "heightMin",
    maxKey: "ageMax" | "heightMax",
    bounds: [number, number],
    unit?: string,
  ) {
    const num = (v: string) => (v ? Number(v) : undefined);
    return (
      <div className="fgroup__row">
        <span className="fgroup__label">{label}</span>
        <div className="frange">
          <input
            className="field__input"
            type="number"
            inputMode="numeric"
            min={bounds[0]}
            max={bounds[1]}
            placeholder={t("discover:filters.min")}
            aria-label={`${label} ${t("discover:filters.min")}`}
            value={draft[minKey] ?? ""}
            onChange={(e) =>
              setDraft((d) => ({ ...d, [minKey]: num(e.target.value) }))
            }
          />
          <span aria-hidden="true">–</span>
          <input
            className="field__input"
            type="number"
            inputMode="numeric"
            min={bounds[0]}
            max={bounds[1]}
            placeholder={t("discover:filters.max")}
            aria-label={`${label} ${t("discover:filters.max")}`}
            value={draft[maxKey] ?? ""}
            onChange={(e) =>
              setDraft((d) => ({ ...d, [maxKey]: num(e.target.value) }))
            }
          />
          {unit && <span className="frange__unit">{unit}</span>}
        </div>
      </div>
    );
  }

  const opt = (key: string, v: string) => t(`profile:option.${key}.${v}`);

  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div
        className="sheet fsheet"
        role="dialog"
        aria-modal="true"
        aria-label={t("discover:filters.title")}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sheet__handle" aria-hidden="true" />
        <div className="fsheet__head">
          <h2 className="h2" style={{ margin: 0 }}>
            {t("discover:filters.title")}
          </h2>
          <button
            type="button"
            className="link link--button"
            onClick={() => setDraft({ sort: draft.sort })}
          >
            {t("discover:filters.reset")}
          </button>
        </div>

        <div className="fsheet__body">
          <section className="fgroup">
            <h3 className="fgroup__title">
              {t("discover:filters.group.basics")}
            </h3>
            {range(t("discover:filters.age"), "ageMin", "ageMax", [18, 70])}
            {range(
              t("discover:filters.height"),
              "heightMin",
              "heightMax",
              [120, 220],
              "cm",
            )}
            <div className="fgroup__row">
              <span className="fgroup__label">
                {t("discover:filters.maritalStatus")}
              </span>
              <div className="fchips">
                {MARITAL.map((v) =>
                  chip(
                    opt("marital_status", v),
                    !!draft.maritalStatus?.includes(v),
                    () => toggle("maritalStatus", v),
                  ),
                )}
              </div>
            </div>
          </section>

          <section className="fgroup">
            <h3 className="fgroup__title">{t("discover:filters.location")}</h3>
            <div className="fchips">
              {chip(
                t("discover:filters.nearbyCity"),
                draft.nearby === "city",
                () =>
                  setDraft((d) => ({
                    ...d,
                    nearby: d.nearby === "city" ? undefined : "city",
                  })),
              )}
              {chip(
                t("discover:filters.nearbyState"),
                draft.nearby === "state",
                () =>
                  setDraft((d) => ({
                    ...d,
                    nearby: d.nearby === "state" ? undefined : "state",
                  })),
              )}
              {chip(
                t("discover:filters.openToRelocate"),
                !!draft.openToRelocate,
                () =>
                  setDraft((d) => ({
                    ...d,
                    openToRelocate: d.openToRelocate ? undefined : true,
                  })),
              )}
            </div>
            <input
              className="field__input"
              type="text"
              placeholder={t("discover:filters.cityPlaceholder")}
              aria-label={t("discover:filters.city")}
              value={draft.city ?? ""}
              onChange={(e) =>
                setDraft((d) => ({ ...d, city: e.target.value || undefined }))
              }
            />
          </section>

          <section className="fgroup">
            <h3 className="fgroup__title">
              {t("discover:filters.group.community")}
            </h3>
            <div className="fgroup__row">
              <span className="fgroup__label">
                {t("profile:field.community.sub_community")}
              </span>
              <div className="fchips">
                {SUB_COMMUNITIES.map((v) =>
                  chip(
                    opt("sub_community", v),
                    !!draft.subCommunity?.includes(v),
                    () => toggle("subCommunity", v),
                  ),
                )}
              </div>
            </div>
            <div className="fgroup__row">
              <span className="fgroup__label">
                {t("profile:field.basics.mother_tongue")}
              </span>
              <div className="fchips">
                {MOTHER_TONGUES.map((v) =>
                  chip(
                    opt("mother_tongue", v),
                    !!draft.motherTongue?.includes(v),
                    () => toggle("motherTongue", v),
                  ),
                )}
              </div>
            </div>
            <div className="fgroup__row">
              <span className="fgroup__label">
                {t("profile:field.horoscope.manglik")}
              </span>
              <div className="fchips">
                {MANGLIK.map((v) =>
                  chip(opt("manglik", v), draft.manglik === v, () =>
                    setDraft((d) => ({
                      ...d,
                      manglik: d.manglik === v ? undefined : v,
                    })),
                  ),
                )}
              </div>
            </div>
          </section>

          {/* [Owner, 2026-09-27] Optional horoscope filter: a minimum Guna
              Milan with the person searched for, and Mangal Dosha. Uses both
              kundlis; people without birth details drop out while it is on. */}
          <section className="fgroup">
            <h3 className="fgroup__title">{t("horoscope:filter.title")}</h3>
            <div className="fgroup__row">
              <span className="fgroup__label">{t("horoscope:filter.minGuna")}</span>
              <div className="fchips">
                {[18, 21, 24, 28].map((v) =>
                  chip(t("horoscope:filter.atLeast", { n: v }), draft.minGuna === v, () =>
                    setDraft((d) => ({ ...d, minGuna: d.minGuna === v ? undefined : v })),
                  ),
                )}
              </div>
            </div>
            <div className="fgroup__row">
              <span className="fgroup__label">{t("horoscope:filter.porutham")}</span>
              <div className="fchips">
                {[6, 7, 8].map((v) =>
                  chip(t("horoscope:filter.poruthamAtLeast", { n: v }), draft.minPorutham === v, () =>
                    setDraft((d) => ({ ...d, minPorutham: d.minPorutham === v ? undefined : v })),
                  ),
                )}
                {chip(t("horoscope:filter.essentials"), !!draft.poruthamEssentials, () =>
                  setDraft((d) => ({ ...d, poruthamEssentials: d.poruthamEssentials ? undefined : true })),
                )}
              </div>
            </div>
            <div className="fgroup__row">
              <span className="fgroup__label">{t("horoscope:mangal.title")}</span>
              <div className="fchips">
                {(["match", "none"] as const).map((v) =>
                  chip(t(`horoscope:filter.mangal.${v}`), draft.mangal === v, () =>
                    setDraft((d) => ({ ...d, mangal: d.mangal === v ? undefined : v })),
                  ),
                )}
              </div>
            </div>
            <p className="caption">{t("horoscope:filter.help")}</p>
          </section>

          <section className="fgroup">
            <h3 className="fgroup__title">
              {t("discover:filters.group.work")}
            </h3>
            <div className="fgroup__row">
              <span className="fgroup__label">
                {t("discover:filters.education")}
              </span>
              <div className="fchips">
                {EDUCATION.map((v) =>
                  chip(
                    opt("highest_education_level", v),
                    !!draft.education?.includes(v),
                    () => toggle("education", v),
                  ),
                )}
              </div>
            </div>
            <div className="fgroup__row">
              <span className="fgroup__label">
                {t("profile:field.education_career.income_band")}
              </span>
              <div className="fchips">
                {INCOME_BANDS.filter((v) => v !== "prefer_not").map((v) =>
                  chip(
                    opt("income_band", v),
                    !!draft.incomeBand?.includes(v),
                    () => toggle("incomeBand", v),
                  ),
                )}
              </div>
            </div>
          </section>

          <section className="fgroup">
            <h3 className="fgroup__title">{t("discover:filters.diet")}</h3>
            <div className="fchips">
              {DIET.map((v) =>
                chip(opt("diet", v), !!draft.diet?.includes(v), () =>
                  toggle("diet", v),
                ),
              )}
            </div>
          </section>
        </div>

        <div className="fsheet__foot">
          <button
            type="button"
            className="btn btn--primary fsheet__apply"
            onClick={() => onApply(draft)}
          >
            {count === null
              ? t("discover:filters.apply")
              : t("discover:filters.applyCount", { count })}
          </button>
        </div>
      </div>
    </div>
  );
}
