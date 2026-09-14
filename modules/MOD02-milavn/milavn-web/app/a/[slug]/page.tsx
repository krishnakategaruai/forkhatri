import type { Metadata } from 'next';

import DetailClient, { type PublicPage } from '@/components/DetailClient';

/* Public event page (FR046-FR050 · UX11 · UI11) — server-rendered so the
 * eight required content elements and SEO metadata are in the initial HTML
 * (FR048), without login (FR046). A non-public item is a 404 here (FR050);
 * an authenticated viewer who may see it still gets it client-side via the
 * authenticated route. The same route serves the signed-in detail (UX06). */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8001';

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
  return {
    title: page.seo.title,
    description: page.seo.description,
    openGraph: { title: page.seo.title, description: page.seo.description, images: page.seo.image ? [page.seo.image] : [], type: 'website' },
    alternates: { canonical: `/a/${slug}` },
  };
}

export default async function PublicActivityPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const page = await fetchPublic(slug);
  return <DetailClient slug={slug} initial={page} />;
}
