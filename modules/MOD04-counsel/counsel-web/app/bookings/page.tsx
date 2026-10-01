"use client";

import { useTranslation } from "react-i18next";
import { useIdentity } from "@/lib/identity";
import { TimeRequests } from "@/components/TimeRequests";
import { MyPurchases } from "@/components/Offers";
import { BookingsBoard } from "@/components/BookingsBoard";

export default function BookingsPage() {
  const { t } = useTranslation();
  const { me } = useIdentity();

  return (
    <div className="wrap page stack-lg">
      <div className="stack" style={{ gap: 4 }}>
        <h1 style={{ fontSize: "clamp(1.7rem,3vw,2.3rem)" }}>{t("bookings.title")}</h1>
        <p className="small muted">{t("bookings.subtitle")}</p>
      </div>
      {me && (
        <BookingsBoard key={me.member_id} role="any" extra={
          <>
            <TimeRequests role="provider" pendingOnly />
            <TimeRequests role="seeker" />
            <MyPurchases role="buyer" />
          </>
        } />
      )}
    </div>
  );
}
