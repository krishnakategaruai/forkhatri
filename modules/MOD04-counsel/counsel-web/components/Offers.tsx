"use client";

import Link from "next/link";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { MessageSquareText, Package as PackageIcon } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { dateLong, money } from "@/lib/format";
import { Avatar, Dialog, useAsync, useToast } from "@/components/ui";
import { useIdentity } from "@/lib/identity";
import { entranceSignInUrl } from "@/lib/platform";

export type Pkg = { id: string; sessions: number; price_minor: number; valid_days: number };
export type Purchase = {
  id: string; kind: "package" | "question"; role: "buyer" | "provider"; status: string; service_id: string; title: string; duration_min: number;
  sessions_total: number | null; sessions_used: number; expires_at: string | null; currency: string; gross_minor: number; refund_minor: number;
  question: string | null; answer: string | null; due_at: string | null; answered_at: string | null; buyer_name: string; provider_name: string; created_at: string;
};

const errText = (t: (k: string, o?: Record<string, unknown>) => string, e: unknown) => t(`errors.${(e as ApiError).code}`, { defaultValue: (e as Error).message });

/** Session packages on a service (MentorCruise / Topmate style bundles). */
export function PackageOffer({ packages, priceMinor, currency, providerName, onBought, hideTitle = false }: {
  packages: Pkg[]; priceMinor: number; currency: string; providerName: string; onBought: (purchaseId: string) => void; hideTitle?: boolean;
}) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const toast = useToast();
  const { me } = useIdentity();
  const [pick, setPick] = useState<Pkg | null>(null);
  const [busy, setBusy] = useState(false);
  if (!packages.length) return null;

  const buy = async () => {
    if (!pick) return;
    setBusy(true);
    try {
      const r = await api<{ id: string }>(`/packages/${pick.id}/buy`, { method: "POST" });
      await api(`/purchases/${r.id}/pay`, { body: { proof: { mock_result: "success" } } });
      toast(t("offers.package_bought"));
      setPick(null);
      onBought(r.id);
    } catch (e) { toast(errText(t, e)); } finally { setBusy(false); }
  };

  return (
    <div className="stack" style={{ gap: 8 }}>
      {!hideTitle && <span className="eyebrow row" style={{ gap: 6 }}><PackageIcon size={13} />{t("offers.packages")}</span>}
      {packages.map((p) => {
        const save = priceMinor * p.sessions - p.price_minor;
        return (
          <button key={p.id} className="offer" onClick={() => (me ? setPick(p) : window.location.assign(entranceSignInUrl()))}>
            <span className="strong">{t("offers.sessions", { count: p.sessions })}</span>
            <span className="num">{money(p.price_minor, currency, lang)}</span>
            <span className="tiny" style={{ color: "var(--ok)" }}>{t("offers.save", { amount: money(save, currency, lang) })}</span>
          </button>
        );
      })}
      <Dialog open={!!pick} onClose={() => setPick(null)} title={pick ? t("offers.buy_title", { name: providerName }) : ""}>
        {pick && (
          <>
            <div className="between"><span className="muted">{t("offers.price")}</span><span className="serif" style={{ fontSize: "1.3rem" }}>{money(pick.price_minor, currency, lang)}</span></div>
            <ul className="small" style={{ margin: 0, paddingLeft: 18, color: "var(--ink-2)" }}>
              <li>{t("offers.rule_valid", { days: pick.valid_days })}</li>
              <li>{t("offers.rule_book")}</li>
              <li>{t("offers.rule_cancel")}</li>
              <li>{t("offers.rule_refund")}</li>
            </ul>
            <p className="tiny muted">{t("book.mock_note")}</p>
            <div className="row" style={{ justifyContent: "flex-end" }}>
              <button className="btn btn-ghost" onClick={() => setPick(null)}>{t("common.cancel")}</button>
              <button className="btn btn-primary" disabled={busy} onClick={() => void buy()}>{t("offers.pay", { amount: money(pick.price_minor, currency, lang) })}</button>
            </div>
          </>
        )}
      </Dialog>
    </div>
  );
}

/** Paid written question (Topmate Priority DM / JustAnswer), refunded if unanswered in time. */
export function AskQuestion({ serviceId, priceMinor, days, currency, providerName }: { serviceId: string; priceMinor: number | null | undefined; days: number; currency: string; providerName: string }) {
  const { t, i18n } = useTranslation();
  const toast = useToast();
  const { me } = useIdentity();
  const [open, setOpen] = useState(false);
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  if (!priceMinor) return null;
  const send = async () => {
    setBusy(true);
    try {
      const r = await api<{ id: string }>(`/services/${serviceId}/questions`, { body: { body } });
      await api(`/purchases/${r.id}/pay`, { body: { proof: { mock_result: "success" } } });
      toast(t("offers.question_sent"));
      setOpen(false); setBody("");
    } catch (e) { toast(errText(t, e)); } finally { setBusy(false); }
  };
  return (
    <>
      <button className="offer" onClick={() => (me ? setOpen(true) : window.location.assign(entranceSignInUrl()))}>
        <span className="strong row" style={{ gap: 6 }}><MessageSquareText size={15} />{t("offers.ask")}</span>
        <span className="num">{money(priceMinor, currency, i18n.language)}</span>
        <span className="tiny muted">{t("offers.answered_within", { n: days })}</span>
      </button>
      <Dialog open={open} onClose={() => setOpen(false)} title={t("offers.ask_title", { name: providerName })}>
        <p className="small muted">{t("offers.ask_body", { n: days })}</p>
        <textarea className="textarea" value={body} onChange={(e) => setBody(e.target.value.slice(0, 3000))} placeholder={t("offers.ask_placeholder")} />
        <div className="row" style={{ justifyContent: "flex-end" }}>
          <button className="btn btn-ghost" onClick={() => setOpen(false)}>{t("common.cancel")}</button>
          <button className="btn btn-primary" disabled={busy || body.trim().length < 10} onClick={() => void send()}>{t("offers.pay", { amount: money(priceMinor, currency, i18n.language) })}</button>
        </div>
      </Dialog>
    </>
  );
}

/** A person's packages and questions, on either side. */
export function MyPurchases({ role }: { role: "buyer" | "provider" }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const toast = useToast();
  const { data, reload } = useAsync(() => api<Purchase[]>("/purchases"), []);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const list = (data ?? []).filter((p) => p.role === role && p.status !== "pending_payment");
  if (!list.length) return null;
  const packages = list.filter((p) => p.kind === "package");
  const questions = list.filter((p) => p.kind === "question");

  const act = async (fn: () => Promise<unknown>, ok: string) => {
    try { await fn(); toast(ok); await reload(); } catch (e) { toast(errText(t, e)); }
  };

  return (
    <div className="stack">
      {packages.length > 0 && (
        <section className="stack" style={{ gap: 10 }}>
          <h3 className="bgroup">{role === "buyer" ? t("offers.your_packages") : t("offers.sold_packages")}<span className="bcount">{packages.length}</span></h3>
          <div className="bgrid">
            {packages.map((p) => {
              const total = p.sessions_total ?? 0;
              const left = total - p.sessions_used;
              return (
                <article key={p.id} className="bcard nobadge fade-in">
                  <div className="bcard-main">
                    <div className="bcard-top"><span className="bcard-name">{p.title}</span><span className={`tag ${p.status === "active" ? "tag-ok" : ""}`}>{t(`offers.status.${p.status}`)}</span></div>
                    <div className="bcard-who small"><Avatar name={role === "buyer" ? p.provider_name : p.buyer_name} size={24} /><span>{role === "buyer" ? t("bookings.with", { name: p.provider_name }) : t("bookings.booked_by", { name: p.buyer_name })}</span></div>
                    <div className="small">{t("offers.left", { left, total })}{p.expires_at ? <span className="muted"> · {t("offers.until", { when: dateLong(p.expires_at, lang) })}</span> : null}</div>
                    {total > 0 && <div className="meter light" role="progressbar" aria-valuenow={p.sessions_used} aria-valuemin={0} aria-valuemax={total} aria-label={t("offers.left", { left, total })}><span style={{ width: `${(p.sessions_used / total) * 100}%` }} /></div>}
                    {p.refund_minor ? <div className="tiny muted">{t("booking.refunded")} {money(p.refund_minor, p.currency, lang)}</div> : null}
                  </div>
                  {role === "buyer" && p.status === "active" && (
                    <div className="bcard-foot">
                      <div className="bcard-hint" />
                      <div className="bcard-actions">
                        <button className="btn btn-ghost btn-sm" onClick={() => void act(() => api(`/purchases/${p.id}/cancel`, { method: "POST" }), t("offers.package_cancelled"))}>{t("offers.cancel_package")}</button>
                        {left > 0 && <Link className="btn btn-primary btn-sm" href={`/book/${p.service_id}?package=${p.id}`}>{t("offers.book_session")}</Link>}
                      </div>
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        </section>
      )}
      {questions.length > 0 && (
        <section className="stack" style={{ gap: 8 }}>
          <h3 className={`bgroup${role === "provider" && questions.some((q) => q.status === "active") ? " action" : ""}`}>{role === "buyer" ? t("offers.your_questions") : t("offers.questions_to_you")}<span className="bcount">{questions.length}</span></h3>
          <div className="bgrid">
            {questions.map((p) => (
              <div key={p.id} className="card card-pad stack" style={{ gap: 8 }}>
                <div className="between"><span className="small strong">{p.title} · {role === "buyer" ? p.provider_name : p.buyer_name}</span><span className={`tag ${p.status === "answered" ? "tag-ok" : p.status === "active" ? "tag-warn" : ""}`}>{t(`offers.qstatus.${p.status}`)}</span></div>
                <p className="small" style={{ whiteSpace: "pre-wrap" }}>{p.question}</p>
                {p.answer && <div className="answer small" style={{ whiteSpace: "pre-wrap" }}>{p.answer}</div>}
                {p.status === "active" && p.due_at && <span className="tiny muted">{t("offers.due", { when: dateLong(p.due_at, lang) })}</span>}
                {p.status === "refunded" && <span className="tiny muted">{t("offers.refunded_unanswered")}</span>}
                {role === "provider" && p.status === "active" && (
                  <>
                    <textarea className="textarea" value={answers[p.id] ?? ""} onChange={(e) => setAnswers({ ...answers, [p.id]: e.target.value })} placeholder={t("offers.answer_placeholder")} />
                    <div><button className="btn btn-primary btn-sm" disabled={(answers[p.id] ?? "").trim().length < 10} onClick={() => void act(() => api(`/purchases/${p.id}/answer`, { body: { answer: answers[p.id] } }), t("offers.answer_sent"))}>{t("offers.send_answer")}</button></div>
                  </>
                )}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
