"use client";

// [Design direction / coordinator's "fewer taps" refinement] A single Post
// entry point that asks the one real ambiguity once: a post (a job, project,
// local service need, training or event — FR11) or a profile (a business
// profile or a work profile — FR01/FR04). Not its own FR; a navigation-
// clarity step in front of /opportunities/new and /listings/new.
// [Design language 2026-09-29] Two chooser cards with tinted icon tiles
// under a page header, the post first because it is the hub's primary
// action. Words per GLOSSARY.md ("post", "profile"; never "listing" or
// "opportunity" on screen).
import { useTranslation } from "react-i18next";
import { Megaphone, Store } from "lucide-react";
import Screen from "@/app/components/Screen";
import PageHeader from "@/app/components/account/PageHeader";
import ChoiceCard from "@/app/components/account/ChoiceCard";
import { useRoutes } from "@/app/host/HostProvider";
import "@/app/styles/account-2026.css";

export default function PostChooserPage() {
  const { t } = useTranslation("discover");
  const routes = useRoutes();
  return (
    <Screen>
      <PageHeader title={t("post.title")} purpose={t("post.subtitle")} />
      <div className="vy-acct-choices">
        <ChoiceCard icon={Megaphone} tint="brand" title={t("post.opportunityTitle")} hint={t("post.opportunityDesc")} href="/opportunities/new" />
        <ChoiceCard icon={Store} tint="indigo" title={t("post.listingTitle")} hint={t("post.listingDesc")} href={routes.newListing} />
      </div>
    </Screen>
  );
}
