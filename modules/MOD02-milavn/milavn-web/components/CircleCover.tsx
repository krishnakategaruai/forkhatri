'use client';

/* A circle's cover, the same everywhere it appears (list card, rail tile, page hero).
 * Design brief 2026-09-28 (critique agent): real photos lead, never initials on a gradient.
 *   1. the organizer's cover photo;
 *   2. for someone inside the circle, a 2×2 mosaic of members' faces (organizer first) —
 *      member lists are members-only, so non-members never get this;
 *   3. a typographic cover: flat surface, place · type caption, one short accent rule,
 *      the name in the display serif — safe for anyone, legible in both themes. */

import { resolveMediaUrl } from '@/lib/api';

type Face = { member_id: string; display_name: string; avatar: string | null };

/** Which cover a circle gets — lets a card drop its media block when the cover would only repeat its own text. */
export function coverKind(coverUrl?: string | null, faces?: Face[]): 'photo' | 'mosaic' | 'type' {
  if (coverUrl) return 'photo';
  return (faces ?? []).filter((f) => f.avatar).length >= 3 ? 'mosaic' : 'type';
}

export default function CircleCover({
  name, coverUrl, faces, caption, variant,
}: {
  name: string;
  coverUrl?: string | null;
  faces?: Face[];
  caption?: string | null;
  variant: 'card' | 'tile' | 'hero';
}) {
  const cls = `ccv ccv--${variant}`;
  if (coverUrl) {
    return <div className={cls}><img className="ccv__img" src={resolveMediaUrl(coverUrl) ?? ''} alt="" loading={variant === 'hero' ? 'eager' : 'lazy'} /></div>;
  }
  const withPhotos = (faces ?? []).filter((f) => f.avatar).slice(0, 4);
  if (withPhotos.length >= 3) {
    return (
      <div className={`${cls} ccv__mosaic ccv__mosaic--${withPhotos.length}`} aria-hidden="true">
        {withPhotos.map((f) => <img key={f.member_id} src={resolveMediaUrl(f.avatar) ?? ''} alt="" loading="lazy" />)}
      </div>
    );
  }
  return (
    <div className={`${cls} ccv__type`} aria-hidden="true">
      {caption && variant !== 'tile' && <span className="ccv__caption">{caption}</span>}
      {variant !== 'tile' && <span className="ccv__rule" />}
      <span className="ccv__name">{variant === 'tile' ? Array.from(name.trim())[0] ?? '' : name}</span>
    </div>
  );
}
