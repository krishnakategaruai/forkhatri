/* Wedding arrangements — migration 062, `mangaly-service/app/api/routes/wedding.py`.
 *
 * An accepted match has a stage that either family moves forward; each stage
 * offers only the kinds of place that help at it. Places are Mangalya
 * partners (always labelled as a partner offer) and OpenStreetMap places
 * nearest first. */

import { getJson, postJson, query, type Outcome } from './api';
import { openDirect, openFamilyConversation, sendMessage, threadHref } from './messages';
import photoCredits from '@/public/art/wedding/credits.json';

export type Stage = 'first_meeting' | 'families_agreed' | 'wedding_fixed';
export const STAGES: Stage[] = ['first_meeting', 'families_agreed', 'wedding_fixed'];

export type StageInfo = {
  connection_id: string;
  stage: Stage;
  categories: string[];
  updated_by_me: boolean;
  updated_at: string | null;
};

export type Centre = { kind: 'between' | 'mine' | 'theirs'; label: string };

export type PartnerPlace = {
  id: string;
  name: string;
  distance_km: number;
  latitude: number;
  longitude: number;
  address: string | null;
  phone: string | null;
  website: string | null;
  /** The partner's own photo of their place. */
  photo: string | null;
  verified: boolean;
  offer: string | null;
  terms: string | null;
  discount_percent: number | null;
  valid_until: string | null;
};

export type OsmPlace = {
  ref: string;
  name: string;
  distance_km: number;
  latitude: number;
  longitude: number;
  address: string | null;
  cuisine: string | null;
  vegetarian: boolean;
  phone: string | null;
  website: string | null;
  opening_hours: string | null;
  /** A photo of this very place (Wikimedia Commons), when OSM links one. */
  photo: string | null;
  photo_source: string | null;
};

export type Suggestions = {
  category: string;
  centres: Centre[];
  centre: Centre | null;
  partners: PartnerPlace[];
  places: OsmPlace[];
  places_updated?: string | null;
};

export async function getStages(connectionIds: string[], forCandidate?: string): Promise<StageInfo[]> {
  if (!connectionIds.length) return [];
  return (await getJson<StageInfo[]>(`/wedding/stages${query({ ids: connectionIds, for_candidate: forCandidate })}`)) ?? [];
}

export async function setStage(connectionId: string, stage: Stage, forCandidate?: string): Promise<Outcome<StageInfo>> {
  return postJson(`/wedding/${connectionId}/stage${query({ for_candidate: forCandidate })}`, { stage });
}

export async function getSuggestions(
  connectionId: string,
  category: string,
  near?: string,
  forCandidate?: string,
): Promise<Suggestions | null> {
  return getJson<Suggestions>(
    `/wedding/${connectionId}/places${query({ category, near, for_candidate: forCandidate })}`,
  );
}

/** Opens the exact spot in the phone's maps app (the name is on our card). */
export function mapLink(lat: number, lon: number): string {
  return `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`;
}

/** Representative photos per kind of place (public/art/wedding, written by
 * mangaly-service/scripts/fetch_wedding_photos.py with each one's credit). */
export type PhotoCredit = { author: string; license: string; license_url?: string | null; source: string };
export const PHOTO_CREDITS = photoCredits as Record<string, PhotoCredit[]>;

/** The `index`-th photo of this kind of place, taking them in turn. */
export function categoryPhoto(category: string, index = 0): string | null {
  const count = PHOTO_CREDITS[category]?.length ?? 0;
  return count ? `/art/wedding/${category}-${index % count}.jpg` : null;
}

/* ---- Sharing a place with family ----------------------------------------
 * A shared place travels as an ordinary chat message, readable anywhere
 * (notifications, any client):
 *   📍 Meena Garden Function Hall
 *   Function halls · 1.1 km · Hyderabad
 *   https://www.google.com/maps/search/?api=1&query=17.38,78.47
 * The chat recognises that shape and draws it as a place card. */

const PIN = '📍 ';
const MAP_URL = /^https:\/\/www\.google\.com\/maps\/search\/\?api=1&query=-?[\d.]+,-?[\d.]+$/;

export function placeMessage(name: string, detail: string, lat: number, lon: number): string {
  return [`${PIN}${name}`, detail, mapLink(lat, lon)].join("\n");
}

export type SharedPlace = { name: string; detail: string; map: string };

export function parsePlaceMessage(content: string): SharedPlace | null {
  const lines = content.split("\n");
  if (lines.length !== 3 || !lines[0].startsWith(PIN) || !MAP_URL.test(lines[2].trim())) return null;
  return { name: lines[0].slice(PIN.length).trim(), detail: lines[1].trim(), map: lines[2].trim() };
}

export type ShareTarget =
  | { kind: 'direct'; accountId: string }
  | { kind: 'family'; connectionId: string }
  | { kind: 'candidate'; connectionId: string };

/** Send the place into the right chat; returns where that chat lives. */
export async function sharePlace(target: ShareTarget, text: string): Promise<string | null> {
  if (target.kind === 'direct') {
    const opened = await openDirect(target.accountId);
    if (!opened.ok || !opened.data) return null;
    const sent = await sendMessage(opened.data.conversation_id, text, 'direct');
    return sent.ok ? threadHref(opened.data.conversation_id, 'direct') : null;
  }
  if (target.kind === 'family') {
    // Opening is idempotent: it returns the families' chat if it is already open.
    await openFamilyConversation(target.connectionId);
    const sent = await sendMessage(target.connectionId, text, 'family');
    return sent.ok ? threadHref(target.connectionId, 'family') : null;
  }
  const sent = await sendMessage(target.connectionId, text, 'candidate');
  return sent.ok ? threadHref(target.connectionId, 'candidate') : null;
}
