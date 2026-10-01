"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ArrowRight, Search, Sparkles } from "lucide-react";
import { api, type Card, type Expertise } from "@/lib/api";
import { ProviderCard } from "@/components/ProviderCard";
import { Skeleton, useAsync } from "@/components/ui";
import { useIdentity } from "@/lib/identity";

type Home = { featured: Card[]; recent: Card[]; areas: Expertise[] };

export default function HomePage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { me } = useIdentity();
  const [q, setQ] = useState("");
  const { data, loading } = useAsync(() => api<Home>("/home"), []);

  const go = (e: React.FormEvent) => {
    e.preventDefault();
    const text = q.trim();
    router.push(text ? `/discover?need=${encodeURIComponent(text)}` : "/discover");
  };

  return (
    <div className="wrap page stack-lg">
      <section className="hero stack">
        <span className="eyebrow">{t("home.eyebrow")}</span>
        <h1>{t("home.title")}</h1>
        <p className="lede">{t("home.lede")}</p>
        <form className="search search-lg" onSubmit={go} style={{ marginTop: 16, maxWidth: 720 }}>
          <Search size={20} className="muted" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("home.placeholder")} aria-label={t("home.placeholder")} />
          <button className="btn btn-primary" type="submit" aria-label={t("home.find")}><Sparkles size={16} /><span className="hide-sm">{t("home.find")}</span></button>
        </form>
        <div className="row tiny muted" style={{ marginTop: 4 }}>
          <span>{t("home.try")}</span>
          {[t("home.ex1"), t("home.ex2"), t("home.ex3")].map((ex) => (
            <button key={ex} className="chip" type="button" onClick={() => router.push(`/discover?need=${encodeURIComponent(ex)}`)}>{ex}</button>
          ))}
        </div>
      </section>

      {me?.upcoming ? (
        <Link href="/bookings" className="card card-pad between">
          <div>
            <div className="eyebrow">{t("home.upcoming_eyebrow")}</div>
            <div className="serif" style={{ fontSize: "1.2rem" }}>{t("home.upcoming", { n: me.upcoming })}</div>
          </div>
          <ArrowRight />
        </Link>
      ) : null}

      <section>
        <div className="section-title">
          <h2>{t("home.areas")}</h2>
          <Link href="/discover" className="link small">{t("home.all_areas")}</Link>
        </div>
        {loading ? <Skeleton h={70} n={2} /> : (
          <div className="areas">
            {data?.areas.map((a) => (
              <Link key={a.id} href={`/discover?area=${a.id}`} className="area">
                <span className="n">{a.name}</span>
                <span className="c">{t("home.n_people", { count: a.providers })}</span>
              </Link>
            ))}
          </div>
        )}
      </section>

      {data?.recent && data.recent.length > 0 && (
        <section>
          <div className="section-title"><h2>{t("home.recent")}</h2></div>
          <div className="grid grid-2">{data.recent.map((c) => <ProviderCard key={c.id} c={c} />)}</div>
        </section>
      )}

      <section>
        <div className="section-title">
          <h2>{t("home.trusted")}</h2>
          <Link href="/discover" className="link small">{t("home.see_all")}</Link>
        </div>
        {loading ? <Skeleton h={150} n={3} /> : <div className="grid grid-2">{data?.featured.map((c) => <ProviderCard key={c.id} c={c} />)}</div>}
      </section>

      <section className="card card-pad between">
        <div className="stack" style={{ gap: 4 }}>
          <h3>{t("home.provide_title")}</h3>
          <p className="muted small">{t("home.provide_body")}</p>
        </div>
        <Link href="/provide" className="btn btn-secondary">{t("home.provide_cta")}</Link>
      </section>
    </div>
  );
}
