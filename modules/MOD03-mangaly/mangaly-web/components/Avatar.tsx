import { resolveMediaUrl } from '@/lib/api';

/* Shared circular avatar — three states, deliberately visually distinct:
 * (1) a real photo, once one is unlocked/available; (2) an initials
 * placeholder in a name-derived color, for a party we know the name of but
 * have no photo for; (3) a generic silhouette, for a candidate whose
 * identity is still anonymized pre-connection (Discovery's own privacy
 * boundary — an anonymized card should visibly LOOK anonymized, not just
 * omit a name, so the state itself communicates "not yet revealed" rather
 * than reading as a broken image). */

const PALETTE = ['#c57a1e', '#1f7a55', '#7a4fc5', '#c54f6b', '#2b6fc5', '#8a8a1f'];

function colorFor(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  return PALETTE[hash % PALETTE.length];
}

function initialsFor(name: string): string {
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] ?? '';
  const last = parts.length > 1 ? parts[parts.length - 1][0] : '';
  return (first + last).toUpperCase();
}

export function Avatar({
  photoUrl,
  name,
  size = 44,
  anonymized = false,
}: {
  photoUrl?: string | null;
  name?: string | null;
  size?: number;
  anonymized?: boolean;
}) {
  const resolved = resolveMediaUrl(photoUrl);
  const style: React.CSSProperties = {
    width: size,
    height: size,
    borderRadius: '50%',
    flex: 'none',
    display: 'grid',
    placeItems: 'center',
    overflow: 'hidden',
    fontWeight: 700,
    fontSize: size * 0.38,
    color: '#fffdf9',
  };

  if (resolved) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={resolved} alt="" style={{ ...style, objectFit: 'cover' }} />
    );
  }

  if (name && !anonymized) {
    return (
      <span style={{ ...style, background: colorFor(name) }} aria-hidden="true">
        {initialsFor(name)}
      </span>
    );
  }

  return (
    <span
      style={{ ...style, background: 'var(--surface-sunken)', border: '1px solid var(--border-default)' }}
      aria-hidden="true"
    >
      <svg viewBox="0 0 24 24" width={size * 0.55} height={size * 0.55} fill="none">
        <circle cx="12" cy="8" r="3.6" stroke="var(--text-secondary)" strokeWidth="1.5" />
        <path d="M5 20a7 7 0 0 1 14 0" stroke="var(--text-secondary)" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    </span>
  );
}
