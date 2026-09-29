/* A person's picture, or their initials on a quiet disc when there is none
 * (same idea as the Circles `.cx-av`) — never an empty circle. Uses the
 * global `.avatar` sizes: default 28px, `lg` 44px, `xl` 64px. */

import { resolveMediaUrl } from '@/lib/api';

export function initials(name: string | null | undefined): string {
  const parts = (name ?? '').trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '';
  const first = Array.from(parts[0])[0] ?? '';
  const last = parts.length > 1 ? Array.from(parts[parts.length - 1])[0] ?? '' : '';
  return (first + last).toUpperCase();
}

export default function Avatar({ src, name, size, className = '', style }: { src?: string | null; name?: string | null; size?: 'lg' | 'xl'; className?: string; style?: React.CSSProperties }) {
  const cls = `avatar${size ? ` avatar--${size}` : ''}${className ? ` ${className}` : ''}`;
  const url = src ? resolveMediaUrl(src) : null;
  if (url) return <img className={cls} src={url} alt="" style={style} />;
  return <span className={cls} style={style} aria-hidden="true">{initials(name)}</span>;
}
