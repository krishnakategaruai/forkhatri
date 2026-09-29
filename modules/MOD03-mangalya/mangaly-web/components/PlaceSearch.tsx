"use client";

import { useEffect, useId, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { getJson, query } from "@/lib/api";

/* Place of birth: one search box. Type a few letters ("vizag", "guntur",
 * "london"), pick a place; its region, country, coordinates and time zone
 * come with it from the server. No district → town → village dropdowns. */

export type PlaceHit = { id: string; label: string; name: string; region: string; country: string; timezone: string };
export type PlaceValue = { label: string; place_id?: string };

type Props = {
  value: PlaceValue | null;
  onChange: (next: PlaceValue | null) => void;
  label: string;
  disabled?: boolean;
};

export default function PlaceSearch({ value, onChange, label, disabled }: Props) {
  const { t } = useTranslation("profile");
  const [text, setText] = useState(value?.label ?? "");
  const [hits, setHits] = useState<PlaceHit[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [searched, setSearched] = useState(false);
  const listId = useId();
  const seq = useRef(0);

  // A chosen place shows its full label; typing starts a new search.
  const chosen = !!value?.place_id && text === value.label;

  useEffect(() => {
    if (chosen) return;
    const q = text.trim();
    if (q.length < 2) {
      setHits([]);
      setSearched(false);
      return;
    }
    const mine = ++seq.current;
    const timer = window.setTimeout(async () => {
      const found = await getJson<PlaceHit[]>(`/profile/places/search${query({ q, limit: 8 })}`);
      if (mine !== seq.current) return;
      setHits(found ?? []);
      setActive(0);
      setSearched(true);
      setOpen(true);
    }, 180);
    return () => window.clearTimeout(timer);
  }, [text, chosen]);

  function pick(hit: PlaceHit) {
    onChange({ label: hit.label, place_id: hit.id });
    setText(hit.label);
    setOpen(false);
  }

  const showList = open && !chosen && text.trim().length >= 2;
  // A saved place from before the list existed: shown, but must be re-picked to be used.
  const legacy = !!value && !value.place_id && text === value.label && text !== "";

  return (
    <div className="place-search">
      <input
        className="field__input"
        type="search"
        name="birth_place_search"
        role="combobox"
        aria-label={label}
        aria-expanded={showList}
        aria-controls={listId}
        aria-autocomplete="list"
        autoComplete="off"
        placeholder={t("editor.place.placeholder")}
        value={text}
        disabled={disabled}
        onChange={(e) => {
          setText(e.target.value);
          setOpen(true);
          if (value?.place_id) onChange(null);
        }}
        onKeyDown={(e) => {
          if (!showList || hits.length === 0) return;
          if (e.key === "ArrowDown") {
            e.preventDefault();
            setActive((a) => Math.min(a + 1, hits.length - 1));
          } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setActive((a) => Math.max(a - 1, 0));
          } else if (e.key === "Enter") {
            e.preventDefault();
            const hit = hits[active];
            if (hit) pick(hit);
          } else if (e.key === "Escape") {
            setOpen(false);
          }
        }}
      />
      {chosen && <p className="place-search__chosen caption">✓ {t("editor.place.chosen")}</p>}
      {legacy && <p className="place-search__hint caption">{t("editor.place.repick")}</p>}
      {showList && (
        <ul className="place-search__list" id={listId} role="listbox" aria-label={label}>
          {hits.map((hit, i) => (
            <li key={hit.id} role="option" aria-selected={i === active}>
              <button
                type="button"
                className={`place-search__item${i === active ? " is-active" : ""}`}
                onMouseEnter={() => setActive(i)}
                onClick={() => pick(hit)}
              >
                <span className="place-search__name">{hit.name}</span>
                <span className="place-search__where">
                  {[hit.region && hit.region !== hit.name ? hit.region : null, hit.country].filter(Boolean).join(", ")}
                </span>
              </button>
            </li>
          ))}
          {searched && hits.length === 0 && <li className="place-search__empty caption">{t("editor.place.none")}</li>}
          <li className="place-search__credit" aria-hidden="true">
            {t("editor.place.credit")}
          </li>
        </ul>
      )}
      <p className="caption place-search__help">{t("editor.place.help")}</p>
    </div>
  );
}
