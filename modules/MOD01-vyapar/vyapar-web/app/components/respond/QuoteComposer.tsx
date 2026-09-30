"use client";

// ======================================================================
// [FE1 — 2026-09-28] Local-service response: "Send a quote" or "Ask a
// question", as quick chips plus an optional note (research §2, FR22
// DEC-002's two sub-choices). A quote is a price and when you can come; a
// question is one or more ready questions. The message the customer
// receives is written from those taps in the sender's language, so the
// 20-character minimum never becomes a typing chore.
// ======================================================================

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError, type Opportunity } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import AcceptancePrompt, { acceptanceKind, type LegalKind } from "@/app/components/respond/AcceptancePrompt";
import { formatRupees, rupeesToPaise } from "@/lib/money";
import VoiceInput, { appendSpoken } from "@/app/components/VoiceInput";
import { FieldBlock, MoneyInput, MultiChips, OptionChips, Segmented } from "@/app/components/composer/fields";
import DisabledReason from "@/app/components/DisabledReason";

const WHEN = ["today", "tomorrow", "this_week", "weekend"] as const;
const QUESTIONS = ["photo", "address", "time", "materials", "budget"] as const;

export default function QuoteComposer({ opportunity, onSent }: { opportunity: Opportunity; onSent: (enquiryId: string) => void }) {
  const { t, i18n } = useTranslation(["hiring", "common"]);
  const sdk = useSdk();
  const [mode, setMode] = useState<"request_quote" | "ask_question">("request_quote");
  const [price, setPrice] = useState("");
  const [when, setWhen] = useState<(typeof WHEN)[number] | null>(null);
  const [asks, setAsks] = useState<string[]>([]);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [existing, setExisting] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [needsAccept, setNeedsAccept] = useState<LegalKind | null>(null);
  const [idemKey] = useState(() => (typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `quote-${Date.now()}`));

  const pricePaise = rupeesToPaise(price);

  function message(): string {
    const parts: string[] = [];
    if (mode === "request_quote") {
      parts.push(t("hiring:quote.msgIntro", { title: opportunity.title }));
      if (pricePaise) parts.push(t("hiring:quote.msgPrice", { amount: formatRupees(pricePaise, i18n.language) }));
      if (when) parts.push(t(`hiring:quote.msgWhen.${when}`));
    } else {
      parts.push(t("hiring:quote.msgAskIntro", { title: opportunity.title }));
      for (const a of asks) parts.push(t(`hiring:quote.ask.${a}`));
    }
    if (note.trim()) parts.push(note.trim());
    return parts.join(" ");
  }

  const ready = mode === "request_quote" ? !!pricePaise || !!when || note.trim().length > 0 : asks.length > 0 || note.trim().length > 0;

  async function send() {
    setSending(true);
    setError(null);
    setExisting(null);
    try {
      const r = await sdk.responses.create({ opportunity_id: opportunity.id, message: message(), sub_choice: mode, applied_via: "form" }, idemKey);
      onSent(r.id);
    } catch (e) {
      const legal = acceptanceKind(e);
      if (legal) {
        setNeedsAccept(legal);
        return;
      }
      if (e instanceof ApiError && e.status === 409 && e.detail && typeof e.detail === "object") {
        setExisting((e.detail as { existing_enquiry_id?: string }).existing_enquiry_id ?? null);
        setError(t("hiring:apply.alreadyApplied"));
      } else if (e instanceof ApiError && e.status === 429) {
        setError(t("hiring:apply.dailyCap"));
      } else {
        setError(e instanceof ApiError && e.code ? t(`hiring:errors.${e.code}`, { defaultValue: String(e.detail) }) : t("common:state.somethingWentWrong"));
      }
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="vy-stack" style={{ gap: 20 }}>
      <Segmented
        options={["request_quote", "ask_question"] as const}
        value={mode}
        onChange={setMode}
        label={(v) => t(`hiring:quote.mode.${v}`)}
        ariaLabel={t("hiring:quote.modeLabel")}
      />

      {mode === "request_quote" ? (
        <>
          <FieldBlock code="q-price" label={t("hiring:quote.price")}>
            <MoneyInput value={price} onChange={setPrice} placeholder={t("hiring:quote.pricePlaceholder")} ariaLabel={t("hiring:quote.price")} />
          </FieldBlock>
          <FieldBlock code="q-when" label={t("hiring:quote.when")}>
            <OptionChips options={WHEN} value={when} onChange={setWhen} label={(v) => t(`hiring:quote.whenOption.${v}`)} />
          </FieldBlock>
        </>
      ) : (
        <FieldBlock code="q-asks" label={t("hiring:quote.whatToAsk")}>
          <MultiChips options={QUESTIONS} value={asks} onChange={setAsks} label={(v) => t(`hiring:quote.askShort.${v}`)} />
        </FieldBlock>
      )}

      <FieldBlock code="q-note" label={t("hiring:quote.note")}>
        <VoiceInput fieldLabel={t("hiring:quote.note")} onConfirm={(text) => setNote((v) => appendSpoken(v, text))}>
          <textarea className="vy-textarea" rows={3} maxLength={600} value={note} onChange={(e) => setNote(e.target.value)} placeholder={t("hiring:quote.notePlaceholder")} />
        </VoiceInput>
      </FieldBlock>

      {ready && (
        <div className="vy-card vy-card-nested vy-stack" style={{ gap: 6, padding: 14 }}>
          <span className="vy-fact-label">{t("hiring:quote.theyWillRead")}</span>
          <p style={{ fontSize: 14, color: "var(--text-primary)", whiteSpace: "pre-wrap" }}>{message()}</p>
        </div>
      )}

      {needsAccept && (
        <AcceptancePrompt
          kind={needsAccept}
          onAccepted={() => {
            setNeedsAccept(null);
            void send();
          }}
        />
      )}
      {error && (
        <div className="vy-stack" style={{ gap: 6 }}>
          <p className="vy-error" role="alert">{error}</p>
          {existing && (
            <a className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start", textDecoration: "none" }} href={`/enquiries/${existing}`}>
              {t("hiring:apply.openConversation")}
            </a>
          )}
        </div>
      )}
      <button type="button" className="vy-btn vy-btn-primary vy-submit" aria-describedby={!ready ? "why-quote" : undefined} disabled={!ready || sending} onClick={send}>
        {sending ? t("hiring:apply.sending") : mode === "request_quote" ? t("hiring:quote.sendQuote") : t("hiring:quote.sendQuestion")}
      </button>
      <DisabledReason id={"why-quote"} show={!ready}>{t("common:disabled.quote")}</DisabledReason>
      <p className="vy-field-hint">🔒 {t("hiring:apply.privacy")}</p>
    </div>
  );
}
