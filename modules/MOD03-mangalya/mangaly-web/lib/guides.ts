/* Guides — migration 063, `mangaly-service/app/api/routes/guides.py`. Short
 * articles (and later videos) in the reader's language, English otherwise. */

import { getJson } from './api';

export type GuideSection = { h?: string; p?: string; points?: string[] };

export type GuideSummary = {
  slug: string;
  category: string;
  minutes: number;
  has_video: boolean;
  title: string;
  summary: string;
  language: string;
};

export type Guide = GuideSummary & {
  sections: GuideSection[];
  video_url: string | null;
  action_href: string | null;
};

export async function listGuides(): Promise<GuideSummary[] | null> {
  return getJson<GuideSummary[]>('/guides');
}

export async function getGuide(slug: string): Promise<Guide | null> {
  return getJson<Guide>(`/guides/${encodeURIComponent(slug)}`);
}
