"use client";

// ======================================================================
// [FE1 — 2026-09-28] Freelance proposal composer (Upwork pattern,
// research §2) — terms first, then the answers, then the note:
//   bid type (fixed / hourly, defaulted from the project) → bid amount,
//   with what the freelancer receives → timeline in days (chips) →
//   optional milestones that must add up to the bid, with a live
//   "left to assign" counter → an answer to every screening question →
//   cover text (voice or typed) with "Improve with AI" (improveProposal:
//   a suggested text the person accepts or edits, and a suggested bid
//   range with the basis it came from) → an optional work sample.
// Everything is validated in place before sending; the server's codes
// (bid_required, milestones_total, screening_answers_required,
// message_too_short…) land next to the field they concern, localized.
// ======================================================================

import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError, type BudgetType, type Opportunity, type ProposalHelp } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import AcceptancePrompt, { acceptanceKind, type LegalKind } from "@/app/components/respond/AcceptancePrompt";
import { formatRupeeRange, formatRupees, rupeesToPaise, paiseToRupeeInput } from "@/lib/money";
import FileUpload from "@/app/components/FileUpload";
import VoiceInput, { appendSpoken } from "@/app/components/VoiceInput";
import { FieldBlock, MoneyInput, OptionChips, Segmented } from "@/app/components/composer/fields";

const TIMELINE_CHIPS = [7, 14, 30, 60, 90] as const;
const MAX_MILESTONES = 5;
const MIN_COVER = 20;

interface MilestoneRow {
  title: string;
  amount: string;
  days: string;
}

type Field = "bid" | "timeline" | "milestones" | "answers" | "cover" | "form";

export default function ProposalComposer({ opportunity, onSent }: { opportunity: Opportunity; onSent: (enquiryId: string) => void }) {
  const { t, i18n } = useTranslation(["hiring", "common"]);
  const lang = i18n.language;
  const sdk = useSdk();
  const s = opportunity.structured;
  const questions = (s?.screening_questions ?? []).filter((q) => q.id && q.text);
  const projectBudgetType: BudgetType = s?.budget_type ?? (s?.hourly_rate_min_paise != null || s?.hourly_rate_max_paise != null ? "hourly" : "fixed");

  const [bidType, setBidType] = useState<BudgetType>(projectBudgetType);
  const [bid, setBid] = useState("");
  const [days, setDays] = useState<number | null>(null);
  const [daysOther, setDaysOther] = useState("");
  const [useMilestones, setUseMilestones] = useState(false);
  const [rows, setRows] = useState<MilestoneRow[]>([{ title: "", amount: "", days: "" }]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [cover, setCover] = useState("");
  const [attachment, setAttachment] = useState("");
  const [help, setHelp] = useState<ProposalHelp | null>(null);
  const [helpBusy, setHelpBusy] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<Field, string>>>({});
  const [sending, setSending] = useState(false);
  const [existing, setExisting] = useState<string | null>(null);
  const [needsAccept, setNeedsAccept] = useState<LegalKind | null>(null);
  const [idemKey] = useState(() => (typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `propose-${Date.now()}`));

  const bidPaise = rupeesToPaise(bid);
  const timeline = days ?? (Number(daysOther) > 0 ? Number(daysOther) : null);
  const milestonesOn = useMilestones && bidType === "fixed";
  const assigned = useMemo(() => rows.reduce((sum, r) => sum + (rupeesToPaise(r.amount) ?? 0), 0), [rows]);
  const remaining = (bidPaise ?? 0) - assigned;

  const budgetLine =
    projectBudgetType === "hourly"
      ? formatRupeeRange(s?.hourly_rate_min_paise, s?.hourly_rate_max_paise, lang)
      : formatRupeeRange(s?.budget_min_paise, s?.budget_max_paise, lang);

  function clearError(f: Field) {
    setErrors((e) => ({ ...e, [f]: undefined, form: undefined }));
  }

  function validate(): Partial<Record<Field, string>> {
    const e: Partial<Record<Field, string>> = {};
    if (!bidPaise) e.bid = t("hiring:proposal.error.bid");
    if (!timeline) e.timeline = t("hiring:proposal.error.timeline");
    if (milestonesOn) {
      const bad = rows.some((r) => r.title.trim().length < 2 || !rupeesToPaise(r.amount) || !(Number(r.days) > 0));
      if (bad) e.milestones = t("hiring:proposal.error.milestoneRow");
      else if (bidPaise && remaining !== 0) e.milestones = t("hiring:errors.milestones_total");
    }
    if (questions.some((q) => !(answers[q.id as string] ?? "").trim())) e.answers = t("hiring:errors.screening_answers_required");
    if (cover.trim().length < MIN_COVER) e.cover = t("hiring:proposal.error.cover", { min: MIN_COVER });
    return e;
  }

  async function improve() {
    setHelpBusy(true);
    try {
      setHelp(await sdk.ai.improveProposal({ opportunity_id: opportunity.id, text: cover.trim(), language: lang }));
    } catch (e) {
      setErrors((x) => ({ ...x, cover: e instanceof ApiError && e.code ? t(`hiring:errors.${e.code}`, { defaultValue: String(e.detail) }) : t("common:state.somethingWentWrong") }));
    } finally {
      setHelpBusy(false);
    }
  }

  async function send() {
    const e = validate();
    setErrors(e);
    setExisting(null);
    if (Object.keys(e).length) {
      document.getElementById(`vy-field-p-${Object.keys(e)[0]}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    setSending(true);
    try {
      const r = await sdk.responses.create(
        {
          opportunity_id: opportunity.id,
          message: cover.trim(),
          bid_type: bidType,
          bid_amount_paise: bidPaise as number,
          timeline_days: timeline as number,
          milestones: milestonesOn
            ? rows.map((r) => ({ title: r.title.trim(), amount_paise: rupeesToPaise(r.amount) as number, due_days: Number(r.days) }))
            : undefined,
          screening_answers: questions.length ? questions.map((q) => ({ question_id: q.id as string, answer: (answers[q.id as string] ?? "").trim() })) : undefined,
          attachment_url: attachment || undefined,
          applied_via: "form",
        },
        idemKey,
      );
      onSent(r.id);
    } catch (err) {
      const legal = acceptanceKind(err);
      if (legal) {
        setNeedsAccept(legal);
        return;
      }
      if (err instanceof ApiError && err.status === 409 && err.detail && typeof err.detail === "object") {
        setExisting((err.detail as { existing_enquiry_id?: string }).existing_enquiry_id ?? null);
        setErrors({ form: err.code === "already_declined" ? t("hiring:errors.already_declined") : t("hiring:apply.alreadyApplied") });
      } else if (err instanceof ApiError && err.code) {
        const map: Record<string, Field> = {
          bid_required: "bid",
          milestones_total: "milestones",
          milestones_hourly: "milestones",
          screening_answers_required: "answers",
          unknown_screening_question: "answers",
          message_too_short: "cover",
        };
        const msg = t(`hiring:errors.${err.code}`, { defaultValue: typeof err.detail === "string" ? err.detail : t("common:state.somethingWentWrong") });
        setErrors({ [map[err.code] ?? "form"]: msg });
      } else {
        setErrors({ form: err instanceof ApiError && err.status === 429 ? t("hiring:apply.dailyCap") : t("common:state.somethingWentWrong") });
      }
    } finally {
      setSending(false);
    }
  }

  const basisKey = help?.bid.basis ?? "none";
  // The assistant only reads the cover text: drop hints this form already
  // satisfies (the answers and the price live in their own fields).
  const allAnswered = questions.every((q) => (answers[q.id as string] ?? "").trim());
  const improvements = (help?.improvements ?? []).filter(
    (i) => !(i.code === "answer_screening_questions" && allAnswered) && !(i.code === "state_price" && !!bidPaise),
  );
  const budgetFloor = projectBudgetType === "hourly" ? s?.hourly_rate_min_paise : s?.budget_min_paise;
  const belowBudget = help?.bid.max_paise != null && budgetFloor != null && help.bid.max_paise < budgetFloor;

  return (
    <div className="vy-stack" style={{ gap: 22 }}>
      <div>
        <FieldBlock code="p-bidtype" label={t("hiring:proposal.howCharge")}>
          <Segmented
            options={["fixed", "hourly"] as const}
            value={bidType}
            onChange={(v) => {
              setBidType(v);
              clearError("milestones");
            }}
            label={(v) => t(`hiring:proposal.bidType.${v}`)}
          />
        </FieldBlock>
      </div>

      <FieldBlock
        code="p-bid"
        label={bidType === "hourly" ? t("hiring:proposal.hourlyRate") : t("hiring:proposal.totalPrice")}
        error={errors.bid}
        hint={budgetLine ? t(projectBudgetType === "hourly" ? "hiring:proposal.theirRate" : "hiring:proposal.theirBudget", { range: budgetLine }) : undefined}
      >
        <MoneyInput
          value={bid}
          onChange={(v) => {
            setBid(v);
            clearError("bid");
          }}
          placeholder={t("hiring:proposal.bidPlaceholder")}
          ariaLabel={bidType === "hourly" ? t("hiring:proposal.hourlyRate") : t("hiring:proposal.totalPrice")}
          readbackSuffix={bidType === "hourly" ? t("hiring:proposal.anHour") : undefined}
        />
        {bidPaise ? (
          <span className="vy-readback">
            {t(bidType === "hourly" ? "hiring:proposal.netHourly" : "hiring:proposal.net", { amount: formatRupees(bidPaise, lang) })}
          </span>
        ) : null}
      </FieldBlock>

      <div>
        <FieldBlock code="p-timeline" label={t("hiring:proposal.timeline")} error={errors.timeline}>
          <div className="vy-row" style={{ flexWrap: "wrap", gap: 6 }}>
            <OptionChips
              options={TIMELINE_CHIPS}
              value={days as (typeof TIMELINE_CHIPS)[number] | null}
              onChange={(v) => {
                setDays(v);
                setDaysOther("");
                clearError("timeline");
              }}
              label={(v) => t("hiring:proposal.days", { count: v })}
            />
            <input
              className="vy-input"
              style={{ width: 120 }}
              inputMode="numeric"
              placeholder={t("hiring:proposal.otherDays")}
              aria-label={t("hiring:proposal.otherDays")}
              value={daysOther}
              onChange={(e) => {
                setDaysOther(e.target.value.replace(/[^\d]/g, "").slice(0, 4));
                setDays(null);
                clearError("timeline");
              }}
            />
          </div>
        </FieldBlock>
      </div>

      {bidType === "fixed" && (
        <div>
          <FieldBlock code="p-milestones" label={t("hiring:proposal.milestones")} error={errors.milestones}>
            <label className="vy-select-box" style={{ fontSize: 14, color: "var(--text-secondary)" }}>
              <input type="checkbox" checked={useMilestones} onChange={(e) => setUseMilestones(e.target.checked)} />
              {t("hiring:proposal.splitMilestones")}
            </label>
            {useMilestones && (
              <div className="vy-milestones">
                {rows.map((r, i) => (
                  <div key={i} className="vy-milestone">
                    <div className="vy-milestone-fields">
                      <input
                        className="vy-input"
                        value={r.title}
                        maxLength={120}
                        placeholder={t("hiring:proposal.milestoneTitle", { n: i + 1 })}
                        aria-label={t("hiring:proposal.milestoneTitle", { n: i + 1 })}
                        onChange={(e) => setRows(rows.map((x, j) => (j === i ? { ...x, title: e.target.value } : x)))}
                      />
                      <MoneyInput
                        value={r.amount}
                        onChange={(v) => {
                          setRows(rows.map((x, j) => (j === i ? { ...x, amount: v } : x)));
                          clearError("milestones");
                        }}
                        placeholder={t("hiring:proposal.amount")}
                        ariaLabel={t("hiring:proposal.amount")}
                      />
                      <div className="vy-unit">
                        <span>{t("hiring:proposal.dayPrefix")}</span>
                        <input
                          className="vy-input"
                          inputMode="numeric"
                          value={r.days}
                          placeholder={t("hiring:proposal.dueInDays")}
                          aria-label={t("hiring:proposal.dueInDays")}
                          onChange={(e) => setRows(rows.map((x, j) => (j === i ? { ...x, days: e.target.value.replace(/[^\d]/g, "").slice(0, 4) } : x)))}
                        />
                      </div>
                    </div>
                    <button
                      type="button"
                      className="vy-icon-btn"
                      aria-label={t("hiring:proposal.removeMilestone", { n: i + 1 })}
                      disabled={rows.length === 1}
                      onClick={() => setRows(rows.filter((_, j) => j !== i))}
                    >
                      ×
                    </button>
                  </div>
                ))}
                <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                  {rows.length < MAX_MILESTONES && (
                    <button type="button" className="vy-btn vy-btn-ghost" style={{ paddingLeft: 0 }} onClick={() => setRows([...rows, { title: "", amount: remaining > 0 ? paiseToRupeeInput(remaining) : "", days: "" }])}>
                      + {t("hiring:proposal.addMilestone")}
                    </button>
                  )}
                  {bidPaise ? (
                    <span className={`vy-msleft${remaining === 0 ? " vy-msleft-ok" : remaining < 0 ? " vy-error" : ""}`} aria-live="polite">
                      {remaining === 0
                        ? t("hiring:proposal.allAssigned")
                        : remaining > 0
                          ? t("hiring:proposal.leftToAssign", { amount: formatRupees(remaining, lang) })
                          : t("hiring:proposal.overBy", { amount: formatRupees(-remaining, lang) })}
                    </span>
                  ) : (
                    <span className="vy-field-hint">{t("hiring:proposal.setPriceFirst")}</span>
                  )}
                </div>
              </div>
            )}
          </FieldBlock>
        </div>
      )}

      {questions.length > 0 && (
        <div id="vy-field-p-answers" className="vy-stack" style={{ gap: 12 }}>
          <span className="vy-label" style={{ marginBottom: 0 }}>{t("hiring:proposal.questionsTitle")}</span>
          {questions.map((q, i) => (
            <div key={q.id} className="vy-field">
              <label className="vy-label" htmlFor={`vy-ans-${q.id}`} style={{ color: "var(--text-primary)", fontSize: 14 }}>
                {i + 1}. {q.text}
              </label>
              <VoiceInput fieldLabel={q.text} compact onConfirm={(text) => setAnswers((a) => ({ ...a, [q.id as string]: appendSpoken(a[q.id as string] ?? "", text) }))}>
                <textarea
                  id={`vy-ans-${q.id}`}
                  className="vy-textarea"
                  rows={2}
                  maxLength={1000}
                  value={answers[q.id as string] ?? ""}
                  onChange={(e) => {
                    setAnswers((a) => ({ ...a, [q.id as string]: e.target.value }));
                    clearError("answers");
                  }}
                />
              </VoiceInput>
            </div>
          ))}
          {errors.answers && <span className="vy-error" role="alert">{errors.answers}</span>}
        </div>
      )}

      <div>
        <FieldBlock code="p-cover" label={t("hiring:proposal.cover")} error={errors.cover}>
          <VoiceInput fieldLabel={t("hiring:proposal.cover")} onConfirm={(text) => setCover((v) => appendSpoken(v, text))}>
            <textarea
              className="vy-textarea"
              rows={6}
              maxLength={1000}
              value={cover}
              onChange={(e) => {
                setCover(e.target.value);
                clearError("cover");
              }}
              placeholder={t("hiring:proposal.coverPlaceholder")}
            />
          </VoiceInput>
          <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
            <span className={cover.trim().length >= MIN_COVER ? "vy-field-hint" : "vy-field-hint"}>
              {t("hiring:proposal.counter", { count: cover.length, max: 1000, min: MIN_COVER })}
            </span>
            <button type="button" className="vy-btn vy-btn-secondary" style={{ padding: "8px 16px", fontSize: 14 }} disabled={helpBusy} onClick={improve}>
              {helpBusy ? t("hiring:proposal.improving") : cover.trim() ? t("hiring:proposal.improve") : t("hiring:proposal.writeForMe")}
            </button>
          </div>
        </FieldBlock>

        {help && (
          <div className="vy-ai-card" style={{ marginTop: 12 }} aria-live="polite">
            <span className="vy-fact-label">{t("hiring:proposal.suggestedText")}</span>
            <blockquote>{help.cover_text}</blockquote>
            <div className="vy-row" style={{ flexWrap: "wrap", gap: 8 }}>
              <button
                type="button"
                className="vy-btn vy-btn-secondary"
                style={{ padding: "8px 16px", fontSize: 14 }}
                onClick={() => {
                  setCover(help.cover_text);
                  clearError("cover");
                }}
              >
                {t("hiring:proposal.useText")}
              </button>
              <button type="button" className="vy-btn vy-btn-ghost" onClick={() => setHelp(null)}>
                {t("hiring:proposal.keepMine")}
              </button>
            </div>
            {improvements.length > 0 && (
              <>
                <span className="vy-fact-label">{t("hiring:proposal.stillWorth")}</span>
                <ul>
                  {improvements.map((i) => (
                    <li key={i.code}>{i.text}</li>
                  ))}
                </ul>
              </>
            )}
            {help.bid.median_paise != null && basisKey !== "none" && (
              <div className="vy-stack" style={{ gap: 6 }}>
                <span className="vy-fact-label">{t("hiring:proposal.suggestedBid")}</span>
                <p style={{ color: "var(--text-primary)", fontSize: 14 }}>
                  {formatRupeeRange(help.bid.min_paise, help.bid.max_paise, lang)} · {t(`hiring:proposal.basis.${basisKey}`, { count: help.bid.sample_size })}
                </p>
                {belowBudget && budgetLine && <p className="vy-field-hint">{t("hiring:proposal.belowBudget", { range: budgetLine })}</p>}
                <button type="button" className="vy-chip" style={{ alignSelf: "flex-start", cursor: "pointer" }} onClick={() => setBid(paiseToRupeeInput(help.bid.median_paise))}>
                  {t("hiring:proposal.useBid", { amount: formatRupees(help.bid.median_paise, lang) })}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <FieldBlock code="p-sample" label={t("hiring:proposal.sample")}>
        <FileUpload value={attachment} onChange={setAttachment} />
      </FieldBlock>

      {needsAccept && (
        <AcceptancePrompt
          kind={needsAccept}
          onAccepted={() => {
            setNeedsAccept(null);
            void send();
          }}
        />
      )}
      {errors.form && (
        <div className="vy-stack" style={{ gap: 6 }}>
          <p className="vy-error" role="alert">{errors.form}</p>
          {existing && (
            <a className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start", textDecoration: "none" }} href={`/enquiries/${existing}`}>
              {t("hiring:apply.openConversation")}
            </a>
          )}
        </div>
      )}
      <button type="button" className="vy-btn vy-btn-primary vy-submit" disabled={sending} onClick={send}>
        {sending ? t("hiring:apply.sending") : t("hiring:proposal.send")}
      </button>
      <p className="vy-field-hint">🔒 {t("hiring:apply.privacy")}</p>
    </div>
  );
}
