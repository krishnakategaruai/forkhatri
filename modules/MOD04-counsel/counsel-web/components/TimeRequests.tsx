"use client";

import Link from "next/link";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import { Clock } from "lucide-react";
import { money, timeRangeZone } from "@/lib/format";
import { Avatar, useAsync, useToast } from "@/components/ui";
import { DateBadge } from "@/components/BookingCard";

export type TimeRequest = {
  id: string; service_id: string; title: string; duration_min: number; price_minor: number; currency: string; starts_at: string;
  brief: string; note: string | null; reply: string | null; status: string; booking_id: string | null; role: "seeker" | "provider";
  seeker_name: string; provider_name: string;
};

/** Custom time requests, for either side. `role` limits which ones are shown. */
export function TimeRequests({ role, pendingOnly = false }: { role: "seeker" | "provider"; pendingOnly?: boolean }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const toast = useToast();
  const { data, reload } = useAsync(() => api<TimeRequest[]>("/time-requests"), []);
  const [declining, setDeclining] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  // Accepted requests become bookings and are listed there; showing them here too would duplicate them.
  const list = (data ?? []).filter((r) => r.role === role && (pendingOnly ? r.status === "pending" : ["pending", "declined"].includes(r.status)));
  if (!list.length) return null;

  const act = async (fn: () => Promise<unknown>, ok: string) => {
    try { await fn(); toast(ok); await reload(); } catch (e) { toast(t(`errors.${(e as ApiError).code}`, { defaultValue: (e as Error).message })); }
  };

  return (
    <section className="stack" style={{ gap: 10 }}>
      <h3 className={`bgroup${role === "provider" ? " action" : ""}`}>{role === "provider" ? t("requests.to_you") : t("requests.yours")}<span className="bcount">{list.length}</span></h3>
      <div className="bgrid">
        {list.map((r) => (
          <article key={r.id} className="bcard fade-in">
            <DateBadge iso={r.starts_at} muted={r.status !== "pending"} />
            <div className="bcard-main">
              <div className="bcard-top">
                <span className="bcard-name">{r.title}</span>
                <span className={`tag ${r.status === "accepted" ? "tag-ok" : r.status === "pending" ? "tag-warn" : ""}`}>{t(`requests.status.${r.status}`)}</span>
              </div>
              <div className="bcard-who small">
                <Avatar name={role === "provider" ? r.seeker_name : r.provider_name} size={24} />
                <span>{role === "provider" ? t("bookings.booked_by", { name: r.seeker_name }) : t("bookings.with", { name: r.provider_name })}</span>
              </div>
              <div className="bcard-meta small">
                <span className="row" style={{ gap: 4 }}><Clock size={14} />{timeRangeZone(r.starts_at, new Date(new Date(r.starts_at).getTime() + r.duration_min * 60000).toISOString(), lang)}</span>
                <span>{t("service.minutes", { n: r.duration_min })}</span>
                <span className="num">{money(r.price_minor, r.currency, lang)}</span>
              </div>
              {r.note && <div className="tiny muted">“{r.note}”</div>}
              {role === "provider" && r.brief && <p className="bcard-brief small clamp-2">{r.brief}</p>}
              {r.reply && <div className="tiny" style={{ color: "var(--warn)" }}>{r.reply}</div>}
            </div>
            {(r.status === "pending" || (r.status === "accepted" && r.booking_id && role === "seeker")) && (
              <div className="bcard-foot">
                <div className="bcard-hint">{r.status === "pending" && <span className="bhint">{role === "provider" ? t("requests.reply_hint") : t("requests.waiting_hint", { name: r.provider_name })}</span>}</div>
                {r.status === "pending" && role === "provider" && declining !== r.id && (
                  <div className="bcard-actions">
                    <button className="btn btn-ghost btn-sm" onClick={() => { setDeclining(r.id); setReply(""); }}>{t("requests.decline")}</button>
                    <button className="btn btn-primary btn-sm" onClick={() => void act(() => api(`/time-requests/${r.id}/accept`, { method: "POST" }), t("requests.accepted_toast"))}>{t("requests.accept")}</button>
                  </div>
                )}
                {declining === r.id && (
                  <div className="row" style={{ width: "100%", flexWrap: "nowrap" }}>
                    <input className="input" value={reply} onChange={(e) => setReply(e.target.value)} placeholder={t("requests.decline_placeholder")} />
                    <button className="btn btn-secondary btn-sm" onClick={() => void act(() => api(`/time-requests/${r.id}/decline`, { body: { reply } }), t("requests.declined_toast")).then(() => setDeclining(null))}>{t("requests.decline")}</button>
                  </div>
                )}
                {r.status === "pending" && role === "seeker" && <div className="bcard-actions"><button className="btn btn-ghost btn-sm" onClick={() => void act(() => api(`/time-requests/${r.id}/withdraw`, { method: "POST" }), t("requests.withdrawn_toast"))}>{t("requests.withdraw")}</button></div>}
                {r.status === "accepted" && r.booking_id && role === "seeker" && <div className="bcard-actions"><Link href={`/bookings/${r.booking_id}`} className="btn btn-primary btn-sm">{t("requests.pay_now")}</Link></div>}
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
