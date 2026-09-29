"use client";

/** Find a person: by name, mobile number or email. Contact details stay masked here. */
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { admin, type MemberRow } from "@/lib/admin-api";
import { Avatar, Badge, Chips, Empty, errorMessage, ErrorLine, formatDate, formatNumber, Loading, PageHead, relative, useConsole } from "./kit";

export default function Members() {
  const { t, lang, version } = useConsole();
  const router = useRouter();
  const params = useSearchParams();
  const [query, setQuery] = useState(params.get("q") ?? "");
  const [status, setStatus] = useState(params.get("status") ?? "");
  const [rows, setRows] = useState<MemberRow[] | null>(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    const timer = setTimeout(() => {
      admin
        .members({ q: query.trim(), status })
        .then((page) => {
          if (!live) return;
          setRows(page.members);
          setTotal(page.total);
          setError(null);
        })
        .catch((e) => live && setError(errorMessage(t, e)));
      const search = new URLSearchParams();
      if (query.trim()) search.set("q", query.trim());
      if (status) search.set("status", status);
      router.replace(`/admin/members${search.size ? `?${search}` : ""}`, { scroll: false });
    }, 220);
    return () => {
      live = false;
      clearTimeout(timer);
    };
  }, [query, status, t, router, version]);

  async function more() {
    const page = await admin.members({ q: query.trim(), status, offset: rows?.length ?? 0 });
    setRows((prev) => [...(prev ?? []), ...page.members]);
  }

  return (
    <div className="adm-page">
      <PageHead title={t("membersTitle")} sub={t("membersSub")} />
      <div className="adm-search">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
          <circle cx="11" cy="11" r="6.5" />
          <path d="M20 20l-4.2-4.2" />
        </svg>
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t("searchPlaceholder")}
          aria-label={t("searchPlaceholder")}
          autoComplete="off"
          enterKeyHint="search"
        />
      </div>
      <div className="adm-toolbar">
        <Chips
          label={t("membersTitle")}
          value={status}
          onChange={setStatus}
          options={[
            { value: "", label: t("filterAllMembers") },
            { value: "active", label: t("status_active") },
            { value: "suspended", label: t("status_suspended") },
            { value: "not_joined", label: t("status_not_joined") },
          ]}
        />
        {rows && <span className="adm-muted">{t("peopleCount", { n: formatNumber(total, lang) })}</span>}
      </div>
      <ErrorLine error={error} />
      {!rows ? (
        <Loading />
      ) : rows.length === 0 ? (
        <Empty>{t("noPeople")}</Empty>
      ) : (
        <ul className="adm-list adm-card">
          {rows.map((m) => (
            <li key={m.member_id}>
              <Link className="adm-row" href={`/admin/members/${m.member_id}`}>
                <Avatar person={m} />
                <span className="adm-row-main">
                  <span className="adm-row-title">
                    {m.display_name}
                    {m.is_staff && <Badge tone="accent">{t("staff")}</Badge>}
                  </span>
                  <span className="adm-row-sub">
                    <span dir="ltr">{m.phone_hint ?? m.email_hint}</span> · {t("joinedOn", { date: formatDate(m.created_at, lang) })} ·{" "}
                    {m.last_seen_at ? t("lastSeen", { when: relative(m.last_seen_at, lang, t) }) : t("neverSignedIn")}
                  </span>
                </span>
                {m.status !== "active" ? (
                  <Badge tone="danger">{t(m.status === "suspended" ? "status_suspended" : "status_deleted")}</Badge>
                ) : !m.joined ? (
                  <Badge>{t("status_not_joined")}</Badge>
                ) : null}
              </Link>
            </li>
          ))}
        </ul>
      )}
      {rows && rows.length < total && (
        <button type="button" className="adm-btn" onClick={() => void more()}>
          {t("loadMore")}
        </button>
      )}
    </div>
  );
}
