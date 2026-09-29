"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import AccountButton from "@/components/AccountButton";
import { NumberPrivacy, ReportUnwanted } from "@/components/ContactSafety";
import ForKhatriHubLink from "@/components/ForKhatriHubLink";
import { getDashboard, setAgentsMaySeeContact, type Dashboard } from "@/lib/agents";

import "../../agent/agent.css";

/* [DEC-V1-034] "Who saw your number": for every family, whether or not they
 * work with an agent — Discover profiles are open to verified agents unless
 * the family closes them, so every family needs to see each look and be
 * able to report an unwanted call. Notifications about a report link here. */

function ContactSafetyPage() {
  const { t } = useTranslation(["agents", "common"]);
  const forCandidate = useSearchParams().get("for") ?? undefined;
  const [dash, setDash] = useState<Dashboard | null | undefined>(undefined);

  useEffect(() => {
    let alive = true;
    getDashboard(forCandidate).then((d) => alive && setDash(d));
    return () => {
      alive = false;
    };
  }, [forCandidate]);

  const toggle = async (open: boolean) => {
    if (!dash) return;
    const before = dash;
    setDash({ ...dash, agents_may_see_contact: open });
    const out = await setAgentsMaySeeContact(open, forCandidate);
    if (!out.ok) setDash(before);
  };

  return (
    <>
      <header className="topbar">
        <h1 className="topbar__title">{t("agents:safety.title")}</h1>
        <div className="topbar__actions">
          <ForKhatriHubLink />
          <AccountButton />
        </div>
      </header>
      <main className="screen ag-screen">
        <p className="ag-lede">{t("agents:safety.lede")}</p>
        {dash === undefined ? (
          <p className="caption">{t("common:state.loading")}</p>
        ) : dash === null ? (
          <p className="caption">{t("common:state.empty")}</p>
        ) : (
          <div className="card ag-form ag-safety">
            <NumberPrivacy dash={dash} onToggle={toggle} showTitle={false} />
            <ReportUnwanted
              forCandidate={forCandidate}
              numberOpen={dash.agents_may_see_contact !== false}
              mayDecide={dash.may_decide}
              onCloseNumber={() => toggle(false)}
            />
          </div>
        )}
      </main>
    </>
  );
}

export default function Page() {
  return (
    <Suspense fallback={null}>
      <ContactSafetyPage />
    </Suspense>
  );
}
