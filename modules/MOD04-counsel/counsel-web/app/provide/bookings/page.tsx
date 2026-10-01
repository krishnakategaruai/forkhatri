"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";
import { TimeRequests } from "@/components/TimeRequests";
import { MyPurchases } from "@/components/Offers";
import { BookingsBoard } from "@/components/BookingsBoard";

/** The consultant's consultations: today's schedule, what needs them, what's coming and what's done, with earnings per booking. */
export default function ProvideBookings() {
  const { t } = useTranslation();
  return (
    <BookingsBoard role="provider"
      extra={<><TimeRequests role="provider" pendingOnly /><MyPurchases role="provider" /></>}
      emptyAction={<Link href="/provide/availability" className="btn btn-secondary">{t("provide.tab.availability")}</Link>} />
  );
}
