"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { Session } from "@/lib/auth";
import { entranceUrl } from "@/lib/platform";
import { claimProfile, disownProfile } from "@/lib/profile";

/**
 * [DEC-V1-019] A profile a parent made with this person's number, not yet
 * taken over: "Rajesh (Father) created this profile for you" with Make it
 * mine / This isn't me.
 *
 * [Owner walkthrough, 2026-09-30] This lived only on "My profile", so a son
 * signing in for the first time landed on Home as if the profile had always
 * been his and never learned his father made it. It now shows first on Home
 * too, and on My profile as before.
 */
export default function ClaimProfileNote({ session }: { session: Session }) {
  const { t } = useTranslation(["profile", "circle"]);
  const [busy, setBusy] = useState(false);
  const [disowning, setDisowning] = useState(false);
  const own = session.own_profile;
  if (!own?.created_by_name || own.claimed !== false) return null;

  return (
    <div className="managed-note managed-note--claim" role="status">
      <strong>
        {t("profile:managed.claimTitle", {
          name: own.created_by_name,
          relation: own.created_by_relation
            ? t(`circle:relation.${own.created_by_relation}`)
            : t(`circle:invite.relationshipOption.${own.created_by_role ?? "relative"}`),
        })}
      </strong>
      <span>{t("profile:managed.claimBody")}</span>
      <button
        type="button"
        className="btn btn--primary"
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          if (await claimProfile()) window.location.reload();
          setBusy(false);
        }}
      >
        {t("profile:managed.claimCta")}
      </button>
      {/* The number's owner did not ask for this profile: remove it,
          confirmed in place rather than on another screen. */}
      {disowning ? (
        <div className="managed-note__confirm">
          <span>{t("profile:managed.disownConfirm")}</span>
          <button
            type="button"
            className="btn btn--ghost"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              if (await disownProfile()) window.location.assign(entranceUrl());
              setBusy(false);
            }}
          >
            {t("profile:managed.disownYes")}
          </button>
          <button type="button" className="link link--button" onClick={() => setDisowning(false)}>
            {t("profile:managed.disownNo")}
          </button>
        </div>
      ) : (
        <button type="button" className="link link--button" onClick={() => setDisowning(true)}>
          {t("profile:managed.disownCta")}
        </button>
      )}
    </div>
  );
}
