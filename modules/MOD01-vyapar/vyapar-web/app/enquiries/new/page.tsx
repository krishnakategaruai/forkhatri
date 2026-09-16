"use client";

// [TR022] Submit an Enquiry or Opportunity Response (FR22). The compose
// step every "Enquire Now"/"Apply"/"Submit a Proposal"/"Contact"/
// "Register" primary action routes through — one form, action_type
// resolved server-side from the target, never chosen here.
// Traces to: FR22, TR022
import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";

function ComposeInner() {
  const { t } = useTranslation(["enquiries", "common"]);
  const router = useRouter();
  const params = useSearchParams();
  const listingId = params.get("listing_id");
  const opportunityId = params.get("opportunity_id");
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  async function send() {
    setSending(true);
    setError(null);
    try {
      const enquiry = await api.post<{ id: string }>("/v1/enquiries", {
        listing_id: listingId || undefined,
        opportunity_id: opportunityId || undefined,
        message,
      });
      router.push(`/enquiries/${enquiry.id}`);
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("common:state.somethingWentWrong"));
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="vy-shell">
      <h1>{t("enquiries:compose.title")}</h1>
      <p>{t("enquiries:compose.help")}</p>
      <div className="vy-stack">
        <textarea
          className="vy-textarea"
          rows={6}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={t("enquiries:compose.placeholder")}
        />
        {error && <p className="vy-error">{error}</p>}
        <button className="vy-btn vy-btn-primary" disabled={message.length < 20 || sending} onClick={send}>
          {sending ? t("common:state.saving") : t("enquiries:compose.send")}
        </button>
      </div>
    </main>
  );
}

export default function NewEnquiryPage() {
  return (
    <Suspense fallback={null}>
      <ComposeInner />
    </Suspense>
  );
}
