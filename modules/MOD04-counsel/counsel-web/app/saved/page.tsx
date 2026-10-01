"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";
import { api, type Card } from "@/lib/api";
import { ProviderCard } from "@/components/ProviderCard";
import { Empty, Skeleton, useAsync } from "@/components/ui";

export default function SavedPage() {
  const { t } = useTranslation();
  const { data, loading } = useAsync(() => api<Card[]>("/me/saved"), []);
  return (
    <div className="wrap page stack">
      <h1 style={{ fontSize: "clamp(1.7rem,3vw,2.3rem)" }}>{t("saved.title")}</h1>
      {loading ? <Skeleton h={160} n={2} /> : !data?.length ? <Empty title={t("saved.empty")} body={t("saved.empty_body")} action={<Link href="/discover" className="btn btn-primary">{t("bookings.find")}</Link>} /> : <div className="grid grid-2">{data.map((c) => <ProviderCard key={c.id} c={c} />)}</div>}
    </div>
  );
}
