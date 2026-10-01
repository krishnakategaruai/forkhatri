"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { api, type Notification } from "@/lib/api";
import { dateTime, money, relative } from "@/lib/format";
import { Empty, Skeleton, useAsync } from "@/components/ui";
import { badgeLabel } from "@/components/Badges";
import { useIdentity } from "@/lib/identity";

export default function NotificationsPage() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const { reload } = useIdentity();
  const { data, loading } = useAsync(() => api<Notification[]>("/me/notifications"), []);
  useEffect(() => { void api("/me/notifications/read", { method: "POST" }).then(reload); }, [reload]);

  const text = (n: Notification) => {
    const p = n.params as Record<string, string | number>;
    if (n.kind === "badge.earned") return t("notif.badge.earned", { badge: badgeLabel(t, String(p.badge_id), Number(p.n)) });
    return t(`notif.${n.kind}`, { ...p, when: p.starts_at ? dateTime(String(p.starts_at), lang) : "", amount: p.amount_minor !== undefined ? money(Number(p.amount_minor), "INR", lang) : "", refund: p.refund_minor ? money(Number(p.refund_minor), "INR", lang) : "", defaultValue: n.kind });
  };
  return (
    <div className="wrap page stack" style={{ maxWidth: 760 }}>
      <h1 style={{ fontSize: "clamp(1.7rem,3vw,2.3rem)" }}>{t("nav.notifications")}</h1>
      {loading ? <Skeleton h={60} n={4} /> : !data?.length ? <Empty title={t("notif.empty")} /> : (
        <div className="card list" style={{ padding: "0 18px" }}>
          {data.map((n) => {
            const inner = <><div className="grow small" style={{ fontWeight: n.read_at ? 400 : 600 }}>{text(n)}</div><div className="tiny muted">{relative(n.created_at, lang)}</div></>;
            return n.booking_id ? <Link key={n.id} href={`/bookings/${n.booking_id}`} className="item">{inner}</Link> : <div key={n.id} className="item">{inner}</div>;
          })}
        </div>
      )}
    </div>
  );
}
