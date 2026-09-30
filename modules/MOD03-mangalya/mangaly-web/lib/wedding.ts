/* Wedding arrangements — migration 062, `mangaly-service/app/api/routes/wedding.py`.
 *
 * An accepted match has a stage that either family moves forward; each stage
 * offers only the kinds of place that help at it. Places are Mangalya
 * partners (always labelled as a partner offer) and OpenStreetMap places
 * nearest first. */

import { getJson, postJson, query, type Outcome } from './api';

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
