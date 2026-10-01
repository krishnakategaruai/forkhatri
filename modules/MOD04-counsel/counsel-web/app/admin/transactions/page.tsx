"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";
import { dateTime, money } from "@/lib/format";
import { Empty, Skeleton, StatusTag, useAsync } from "@/components/ui";

type Tx = { id: string; service_title: string; provider_name: string; seeker_name: string; starts_at: string; status: string; gross_minor: number; platform_fee_minor: number; refund_minor: number; provider_payable_minor: number; payout_status: string; currency: string };

export default function AdminTransactions() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const { data, loading } = useAsync(() => api<Tx[]>("/admin/transactions"), []);
  if (loading) return <Skeleton h={60} n={4} />;
  if (!data?.length) return <Empty title={t("earn.none")} />;
  return (
    <div className="card list" style={{ padding: "0 18px" }}>
      {data.map((b) => (
        <Link key={b.id} href={`/bookings/${b.id}`} className="item">
          <div className="grow"><div className="small strong">{b.service_title}</div><div className="tiny muted">{b.seeker_name} → {b.provider_name} · {dateTime(b.starts_at, lang)} · <StatusTag status={b.status} /> · {t(`payout.${b.payout_status}`)}</div></div>
          <div style={{ textAlign: "right" }}><div className="num">{money(b.gross_minor, b.currency, lang)}</div><div className="tiny muted num">{t("admin.fee")} {money(b.platform_fee_minor, b.currency, lang)}{b.refund_minor ? ` · ${t("booking.refunded")} ${money(b.refund_minor, b.currency, lang)}` : ""}</div></div>
        </Link>
      ))}
    </div>
  );
}
