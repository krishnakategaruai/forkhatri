/* First run (ONBOARDING-REDESIGN-2026-10.md §9, decided 2026-10-06).
 *
 * One screen, one answer: the member's place. Language comes from ForKhatri and
 * is never asked or overwritten; interests are optional and asked later on Home.
 * This file holds the pieces the first-run screen, the shell and Home share. */

import type { PickedPlace } from '@/components/PlacePicker';

/** Big cities offered as one-tap "city only" choices. Names are stored in English (as the place
 *  search stores them, so members of every language meet at the same "Hyderabad"); the screen
 *  shows `firstRun.city.<key>` in the member's language. Centres are approximate (two decimals). */
export const CITIES: Record<string, PickedPlace> = {
  hyderabad: { locality_city: 'Hyderabad', locality_state: 'Telangana', locality_zone: null, locality_locality: null, lat: 17.39, lon: 78.49 },
  vijayawada: { locality_city: 'Vijayawada', locality_state: 'Andhra Pradesh', locality_zone: null, locality_locality: null, lat: 16.51, lon: 80.65 },
  visakhapatnam: { locality_city: 'Visakhapatnam', locality_state: 'Andhra Pradesh', locality_zone: null, locality_locality: null, lat: 17.69, lon: 83.22 },
  bengaluru: { locality_city: 'Bengaluru', locality_state: 'Karnataka', locality_zone: null, locality_locality: null, lat: 12.97, lon: 77.59 },
  mysuru: { locality_city: 'Mysuru', locality_state: 'Karnataka', locality_zone: null, locality_locality: null, lat: 12.3, lon: 76.64 },
  chennai: { locality_city: 'Chennai', locality_state: 'Tamil Nadu', locality_zone: null, locality_locality: null, lat: 13.08, lon: 80.27 },
  mumbai: { locality_city: 'Mumbai', locality_state: 'Maharashtra', locality_zone: null, locality_locality: null, lat: 19.08, lon: 72.88 },
  pune: { locality_city: 'Pune', locality_state: 'Maharashtra', locality_zone: null, locality_locality: null, lat: 18.52, lon: 73.86 },
  nagpur: { locality_city: 'Nagpur', locality_state: 'Maharashtra', locality_zone: null, locality_locality: null, lat: 21.15, lon: 79.09 },
  delhi: { locality_city: 'Delhi', locality_state: 'Delhi', locality_zone: null, locality_locality: null, lat: 28.61, lon: 77.21 },
  jaipur: { locality_city: 'Jaipur', locality_state: 'Rajasthan', locality_zone: null, locality_locality: null, lat: 26.91, lon: 75.79 },
  lucknow: { locality_city: 'Lucknow', locality_state: 'Uttar Pradesh', locality_zone: null, locality_locality: null, lat: 26.85, lon: 80.95 },
  ahmedabad: { locality_city: 'Ahmedabad', locality_state: 'Gujarat', locality_zone: null, locality_locality: null, lat: 23.02, lon: 72.57 },
};

/* "A short list of nearby big cities" (Q1) before we know where the person is: the cities
 * people who read this language most often live in come first. Six, so they fit two rows at 390px. */
const CITIES_BY_LANGUAGE: Record<string, string[]> = {
  te: ['hyderabad', 'vijayawada', 'visakhapatnam', 'bengaluru', 'chennai', 'mumbai'],
  hi: ['delhi', 'jaipur', 'lucknow', 'mumbai', 'ahmedabad', 'hyderabad'],
  mr: ['pune', 'mumbai', 'nagpur', 'hyderabad', 'bengaluru', 'delhi'],
  kn: ['bengaluru', 'mysuru', 'hyderabad', 'chennai', 'mumbai', 'pune'],
  en: ['hyderabad', 'delhi', 'mumbai', 'bengaluru', 'pune', 'chennai'],
};
export function citiesFor(lang: string): string[] {
  return CITIES_BY_LANGUAGE[lang] ?? CITIES_BY_LANGUAGE.en;
}

/** Where the member was going when Milavn asked for their place: an in-app path only (never
 *  another site, never the first-run screen itself). */
export function safeNext(raw: string | null | undefined): string | null {
  if (!raw || raw.length > 500 || !raw.startsWith('/') || raw.startsWith('//') || raw.includes('\\')) return null;
  if (raw.startsWith('/onboarding') || raw.startsWith('/welcome')) return null;
  return raw;
}

/** Home ideas for "start one in a minute": each opens Create already filled in. */
export const TEMPLATES = ['satsang', 'walk', 'chai', 'games'] as const;
export type TemplateKey = (typeof TEMPLATES)[number];
export const TEMPLATE_FILL: Record<TemplateKey, { icon: string; category: string; format: string }> = {
  satsang: { icon: '🙏', category: 'celebrate', format: 'satsang' },
  walk: { icon: '🥾', category: 'explore', format: '' },
  chai: { icon: '☕', category: 'meet', format: 'meetup' },
  games: { icon: '🎲', category: 'play', format: '' },
};
