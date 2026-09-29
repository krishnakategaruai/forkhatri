"use client";

/** Two-person rule (maker-checker): one office bearer asks, a different one decides. */
import Link from "next/link";
import { useState } from "react";
import { admin, type Approval } from "@/lib/admin-api";
import { Avatar, Badge, Chips, Dialog, Empty, errorMessage, ErrorLine, Field, formatDate, Loading, PageHead, reasonName, relative, roleName, useConsole, useLoad } from "./kit";

export default function Approvals() {
  const { t, lang, me, changed, version } = useConsole();
  const [tab, setTab] = useState<"pending" | "decided">("pending");
  const list = useLoad(
    () => admin.approvals(tab === "pending" ? "pending" : null).then((all) => (tab === "pending" ? all : all.filter((a) => a.status !== "pending"))),
    [tab, version],
  );
  const rows = list.data;
  const [actionError, setError] = useState<string | null>(null);
  const error = actionError ?? (list.error ? errorMessage(t, list.error) : null);
  const [declining, setDeclining] = useState<Approval | null>(null);
  const [note, setNote] = useState("");

  async function decide(a: Approval, decision: "approved" | "declined" | "withdrawn", text = "") {
    setError(null);
    try {
      await admin.decide(a.id, decision, text);
      setDeclining(null);
      setNote("");
      changed();
    } catch (e) {
      setError(errorMessage(t, e));
    }
  }

  function title(a: Approval) {
    const name = a.target.display_name ?? "";
    return a.kind === "ban" ? t("kindBan", { name }) : t("kindGrant", { name, role: roleName(t, a.payload.role ?? "") });
  }

  return (
    <div className="adm-page">
      <PageHead title={t("approvalsTitle")} sub={t("approvalsSub")} />
      <Chips
        label={t("approvalsTitle")}
        value={tab}
        onChange={setTab}
        options={[
          { value: "pending", label: t("tabPending") },
          { value: "decided", label: t("tabDecided") },
        ]}
      />
      <ErrorLine error={error} />
      {!rows ? (
        <Loading />
      ) : rows.length === 0 ? (
        <Empty>{tab === "pending" ? t("noApprovals") : t("noDecided")}</Empty>
      ) : (
        <ul className="adm-cards">
          {rows.map((a) => {
            const mine = a.requested_by.member_id === me.member.member_id;
            return (
              <li key={a.id} className="adm-card adm-approval">
                <div className="adm-approval-head">
                  <Avatar person={a.target} size={40} />
                  <div>
                    <Link href={`/admin/members/${a.target.member_id}`} className="adm-plain-link">
                      <h3>{title(a)}</h3>
                    </Link>
                    <p className="adm-muted">{t("askedBy", { name: a.requested_by.display_name ?? "", when: relative(a.requested_at, lang, t) })}</p>
                  </div>
                  {a.kind === "ban" ? <Badge tone="danger">{t("kind_ban")}</Badge> : <Badge tone="accent">{roleName(t, a.payload.role ?? "")}</Badge>}
                </div>
                <p className="adm-approval-note">
                  {a.kind === "ban" && <strong>{reasonName(t, a.reason_code)} · </strong>}
                  {a.note}
                  {a.kind === "grant_role" && a.payload.ends_at && <span className="adm-muted"> · {t("untilDate", { date: formatDate(a.payload.ends_at, lang) })}</span>}
                </p>
                {a.status === "pending" ? (
                  mine ? (
                    <div className="adm-actions">
                      <span className="adm-muted">{t("youAsked")}</span>
                      <button type="button" className="adm-btn" onClick={() => void decide(a, "withdrawn")}>
                        {t("withdraw")}
                      </button>
                    </div>
                  ) : a.can_decide ? (
                    <div className="adm-actions">
                      <button type="button" className="adm-btn" onClick={() => setDeclining(a)}>
                        {t("decline")}
                      </button>
                      <button type="button" className={`adm-btn ${a.kind === "ban" ? "danger" : "primary"}`} onClick={() => void decide(a, "approved")}>
                        {t("approve")}
                      </button>
                    </div>
                  ) : (
                    <p className="adm-muted">{t("cannotDecide")}</p>
                  )
                ) : (
                  <p className="adm-muted">
                    {a.status === "withdrawn" ? t("approvalStatus_withdrawn") : t(a.status === "approved" ? "approvalStatus_approved" : "approvalStatus_declined", { name: a.decided_by?.display_name ?? "" })}
                    {a.decided_at && ` · ${formatDate(a.decided_at, lang)}`}
                    {a.decision_note && ` · ${a.decision_note}`}
                  </p>
                )}
              </li>
            );
          })}
        </ul>
      )}
      <Dialog open={!!declining} onClose={() => setDeclining(null)} title={declining ? title(declining) : ""}>
        <Field label={t("declineReason")}>
          <textarea className="adm-input" rows={3} value={note} onChange={(e) => setNote(e.target.value)} />
        </Field>
        <div className="adm-actions end">
          <button type="button" className="adm-btn" onClick={() => setDeclining(null)}>
            {t("cancel")}
          </button>
          <button type="button" className="adm-btn primary" disabled={note.trim().length < 3} onClick={() => declining && void decide(declining, "declined", note)}>
            {t("decline")}
          </button>
        </div>
      </Dialog>
    </div>
  );
}
