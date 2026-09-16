"use client";

// [TR023] Provider/sender enquiry list — the Activity screen's "Responded"
// group (deferred in IMP14) now has a real home: a dedicated Enquiries
// list, sent/received tabs.
// Traces to: FR23, TR023
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";

interface Enquiry {
  id: string;
  action_type: string;
  state: string;
  is_sender: boolean;
  last_activity_at: string;
}

export default function MyEnquiriesPage() {
  const { t } = useTranslation(["enquiries", "common"]);
  const [role, setRole] = useState<"sent" | "received">("sent");
  const [items, setItems] = useState<Enquiry[] | null>(null);

  useEffect(() => {
    api.get<Enquiry[]>(`/v1/enquiries/mine?role=${role}`).then(setItems);
  }, [role]);

  return (
    <main className="vy-shell">
      <h1>{t("enquiries:mine.title")}</h1>
      <div className="vy-row">
        <button className="vy-btn" style={{ background: role === "sent" ? "var(--accent)" : "var(--surface-overlay)", color: role === "sent" ? "var(--accent-ink)" : "var(--text-primary)" }} onClick={() => setRole("sent")}>
          {t("enquiries:mine.tabSent")}
        </button>
        <button className="vy-btn" style={{ background: role === "received" ? "var(--accent)" : "var(--surface-overlay)", color: role === "received" ? "var(--accent-ink)" : "var(--text-primary)" }} onClick={() => setRole("received")}>
          {t("enquiries:mine.tabReceived")}
        </button>
      </div>
      {items?.length === 0 && <p className="vy-muted">{t("enquiries:mine.empty")}</p>}
      <div className="vy-stack">
        {items?.map((e) => (
          <a key={e.id} className="vy-card" style={{ textDecoration: "none" }} href={`/enquiries/${e.id}`}>
            {e.action_type} · {e.state}
          </a>
        ))}
      </div>
    </main>
  );
}
