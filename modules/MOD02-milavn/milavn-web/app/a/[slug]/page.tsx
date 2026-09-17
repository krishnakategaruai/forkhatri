import type { Metadata } from 'next';

import DetailClient, { type PublicPage } from '@/components/DetailClient';
import { resolveMediaUrl } from '@/lib/api';
import { withBasePath } from '@/lib/base-path';

/* Public event page (FR046-FR050 · UX11 · UI11) — server-rendered so the
 * eight required content elements and SEO metadata are in the initial HTML
 * (FR048), without login (FR046). A non-public item is a 404 here (FR050);
 * an authenticated viewer who may see it still gets it client-side via the
 * authenticated route. The same route serves the signed-in detail (UX06). */

// On the server, a deployment reaches the API over its private network
// (MILAVN_API_INTERNAL_URL); locally both are the public API base.
const API_BASE = process.env.MILAVN_API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8001';

async function fetchPublic(slug: string): Promise<PublicPage | null> {
  try {
    const res = await fetch(`${API_BASE}/public/occurrences/${encodeURIComponent(slug)}`, { cache: 'no-store' });
    if (!res.ok) return null;
    return (await res.json()) as PublicPage;
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const page = await fetchPublic(slug);
  if (!page) return { title: 'Milavn', robots: { index: false } };
  const image = resolveMediaUrl(page.seo.image);
  return {
    title: page.seo.title,
    description: page.seo.description,
    openGraph: { title: page.seo.title, description: page.seo.description, images: image ? [image] : [], type: 'website' },
    alternates: { canonical: withBasePath(`/a/${slug}`) },
  };
}

export default async function PublicActivityPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const page = await fetchPublic(slug);
  return <DetailClient slug={slug} initial={page} />;
}
