'use client';

/* QR codes are generated on the device (no third-party image service): a
 * share link or a check-in token must work offline at a park gate, and a
 * check-in token must never leave the organizer's phone via a URL to someone
 * else's server. */

import { useEffect, useState } from 'react';
import QR from 'qrcode';

export default function QrCode({ value, size = 180, label }: { value: string; size?: number; label: string }) {
  const [src, setSrc] = useState<string | null>(null);
  useEffect(() => {
    let alive = true;
    QR.toDataURL(value, { width: size * 2, margin: 1, color: { dark: '#0b1220', light: '#ffffff' } })
      .then((u) => { if (alive) setSrc(u); })
      .catch(() => { if (alive) setSrc(null); });
    return () => { alive = false; };
  }, [value, size]);
  return (
    <div className="qr" style={{ minHeight: size + 32 }}>
      {src ? <img src={src} width={size} height={size} alt={label} /> : <div className="sk" style={{ width: size, height: size }} />}
    </div>
  );
}
