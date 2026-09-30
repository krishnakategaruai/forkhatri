"use client";

import "./profile-view.css";
import { useLoaderHold } from "@/lib/useLoaderHold";

import Link from "next/link";
import SacredLoader from "@/components/SacredLoader";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import FamilyNotes from "@/components/FamilyNotes";
import OutlookScene from "@/components/OutlookScene";
import VoiceIntroPlayer from "@/components/VoiceIntroPlayer";
import { useActiveContext } from "@/lib/activeContext";
import CompatibilityPanel from "@/components/CompatibilityPanel";
import SimilarProfiles from "@/components/SimilarProfiles";
import { resolveMediaUrl } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import {
  accept,
  decline,
  getSharing,
  listIncoming,
  listSent,
  requestFamilyContact,
  sendRequest,
  setShare,
  withdrawFamilyContact,
  type ShareCategory,
  type SharingOverview,
} from "@/lib/connections";
import {
  compareOutlook,
  readOutlook,
  type OutlookAnswers,
} from "@/lib/outlook";
import { listMembers, suggestProfile, type Member } from "@/lib/homeCircle";
import { listConversations, openFamilyConversation } from "@/lib/messages";
import {
  getSnippet,
  whyThisMatch,
  type CompatibilityReason,
  type Snippet,
  type VerifiedLayer,
} from "@/lib/discovery";
import {
  getAllAttributeValues,
  viewProfileFull,
  viewPublicProfile,
  type ProfileView,
  type PublicProfile,
} from "@/lib/profile";
import {
  findCategory,
  findField,
  type CategoryDef,
} from "@/lib/profileCategoryConfig";
import { formatFieldValue } from "@/lib/profileFormat";
import {
  PROFILE_SECTIONS,
  PROMPT_CATEGORY,
  isPromptValue,
  type PromptSlot,
  type SectionId,
} from "@/lib/profileSections";

/* FR020/FR021 · A connection's profile, laid out the way Hinge reads: photos
 * interleaved with prompts and biodata, everything permitted shown at once
 * with no second unlock step. Partner preferences never reach this screen.
 * FR016 · A Home Circle member acting for a candidate also keeps private
 * notes about this match here. */

type Block =
  | { kind: "photo"; index: number }
  | { kind: "identity" }
  | { kind: "prompt"; slot: PromptSlot }
  | { kind: "outlook" }
  | { kind: "section"; id: SectionId };

/* Two ways to read the same profile, because the two readers are doing
   different jobs — and the product owner set exactly this boundary: a
   candidate gets a Hinge-style prompt-and-photo profile, a parent or relative
   gets the conventional detailed one. Profile-viewing style and messaging are
   the only two things that vary by role; everything else is identical.

   CANDIDATE_LAYOUT is photos and prompts, and nothing else. A candidate is
   deciding whether they want to know this person, and the prompts now carry
   the matrimony agenda themselves — "On working after marriage, I think",
   "On living with family after marriage, I picture", "On children, where I
   stand today". Those answers say more, in the person's own voice, than the
   same facts would as a chip. The biodata chips that used to sit here were
   the parent's view leaking into the candidate's.

   FAMILY_LAYOUT carries no prompts at all. The product owner was explicit
   that the Hinge/Bumble treatment is for candidates only: a parent or
   relative is evaluating a match, not being courted by one, and what they
   need is the standard biodata they would otherwise be reading on paper —
   and only as much of it as the candidate has chosen to share. Someone's
   answer to "Family, to me, means" is written for the person they might
   marry, not for that person's mother.

   Partner preferences appear in neither: they are the viewer's own matching
   filters, never shown to the person being viewed (FR020). */
const CANDIDATE_LAYOUT: Block[] = [
  { kind: "photo", index: 0 },
  { kind: "identity" },
  /* [Owner scenario, 2026-09-21] Once both sides accept, the candidate sees
     ALL the formal information as well as the prompts — not prompts alone.
     The facts come first, as compact chips, then the person's own words
     interleaved with the photos the way Hinge reads. */
  { kind: "section", id: "basics" },
  { kind: "section", id: "education_career" },
  { kind: "prompt", slot: "prompt_1" },
  { kind: "photo", index: 1 },
  { kind: "section", id: "community" },
  { kind: "section", id: "family" },
  { kind: "prompt", slot: "prompt_2" },
  { kind: "photo", index: 2 },
  { kind: "section", id: "lifestyle" },
  { kind: "section", id: "horoscope" },
  { kind: "section", id: "future" },
  { kind: "prompt", slot: "prompt_3" },
  /* Their ten words beside the reader's own. Answers only, never a score
     (§3): a difference is rendered as "you said …", something to talk
     about, and an unanswered question renders nothing at all. */
  { kind: "outlook" },
  { kind: "photo", index: 3 },
  { kind: "photo", index: 4 },
  { kind: "photo", index: 5 },
];

const FAMILY_LAYOUT: Block[] = [
  { kind: "photo", index: 0 },
  { kind: "identity" },
  { kind: "section", id: "basics" },
  { kind: "section", id: "education_career" },
  { kind: "section", id: "community" },
  { kind: "section", id: "family" },
  { kind: "section", id: "horoscope" },
  { kind: "section", id: "lifestyle" },
  { kind: "section", id: "future" },
  { kind: "photo", index: 1 },
  { kind: "photo", index: 2 },
  { kind: "photo", index: 3 },
  { kind: "photo", index: 4 },
  { kind: "photo", index: 5 },
];

function ageFromDob(dob: string): number {
  const birth = new Date(dob);
  const now = new Date();
  let age = now.getFullYear() - birth.getFullYear();
  if (
    now.getMonth() < birth.getMonth() ||
    (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate())
  ) {
    age -= 1;
  }
  return age;
}

export default function MemberProfilePage() {
  // [owner 2026-09-25] The loader stays at least a second, never a flash.
  const loaderHold = useLoaderHold();
  const { t, i18n } = useTranslation(["common", "profile", "discover"]);
  const router = useRouter();
  const { accountId } = useParams<{ accountId: string }>();
  const [view, setView] = useState<ProfileView | null | undefined>(undefined);
  const [connectionId, setConnectionId] = useState<string | null>(null);
  const [sharing, setSharing] = useState<SharingOverview | null>(null);
  const [confirming, setConfirming] = useState<ShareCategory | null>(null);
  const [busy, setBusy] = useState<ShareCategory | null>(null);
  const [shareError, setShareError] = useState<string | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [snippet, setSnippet] = useState<Snippet | null>(null);
  const [reasons, setReasons] = useState<CompatibilityReason[]>([]);
  const [myPrompts, setMyPrompts] = useState<Record<string, string>>({});
  const [myOutlook, setMyOutlook] = useState<OutlookAnswers>({});
  /* Where the two of you stand before a connection exists. The page used to
     say "shared once you connect" and offer no way to connect — a reader
     had to go back to Discover to act on what they had just read. */
  const [link, setLink] = useState<
    | { kind: "none" }
    | { kind: "sent"; id: string }
    | { kind: "incoming"; id: string }
    | { kind: "connected"; id: string }
  >({ kind: "none" });
  const [linkBusy, setLinkBusy] = useState(false);
  const [suggested, setSuggested] = useState(false);
  const [linkError, setLinkError] = useState<string | null>(null);
  const [publicProfile, setPublicProfile] = useState<PublicProfile | null>(
    null,
  );
  const { active } = useActiveContext();
  const family = active?.kind === "family" ? active.circle : null;

  useEffect(() => {
    let active = true;
    (async () => {
      const session = await requireSession();
      if (!active || !session) return;
      const result = await viewProfileFull(accountId);
      if (!active) return;

      /* The reader's side of the screen. Both are optional: if either fails
         the profile still renders, just without the extra context. */
      void Promise.all([
        whyThisMatch(accountId, family?.candidate_account_id).catch(() => []),
        // Only a reader with a profile of their own has answers to compare.
        session.own_profile
          ? getAllAttributeValues().catch(
              () => ({}) as Awaited<ReturnType<typeof getAllAttributeValues>>,
            )
          : ({} as Awaited<ReturnType<typeof getAllAttributeValues>>),
      ]).then(([why, mine]) => {
        if (!active) return;
        setReasons(why);
        // `getAllAttributeValues` returns `{ state, value }` per attribute,
        // not the bare value.
        const answers: Record<string, string> = {};
        for (const entry of Object.values(mine?.[PROMPT_CATEGORY] ?? {})) {
          if (isPromptValue(entry?.value)) {
            answers[entry.value.q] = entry.value.a;
          }
        }
        setMyPrompts(answers);
        setMyOutlook(readOutlook(mine));
      });
      /* Which connection this profile belongs to. The link from the accept
         flow carries it; a profile opened from Home or Discover does not, so
         a connected person is found among the reader's conversations —
         otherwise the connected profile had no way to message them. */
      let connection = new URLSearchParams(window.location.search).get(
        "connection",
      );
      if (!connection && result) {
        const convos = await listConversations(
          family?.candidate_account_id,
        ).catch(() => []);
        const mine = convos.find(
          (c) =>
            c.kind !== "direct" &&
            (c.other_account_id === accountId ||
              (c.participants ?? []).some((p) => p.account_id === accountId)),
        );
        connection = mine?.connection_id ?? null;
      }
      const [overview, circle]: [SharingOverview | null, Member[]] =
        connection && result
          ? await Promise.all([getSharing(connection), listMembers()])
          : [null, []];
      if (!active) return;
      setConnectionId(connection);
      setSharing(overview);
      setMembers(circle);
      // Not connected: the matrimonial facts this candidate has published
      // (DEC-V1-020) — a family member evaluating a match needs the biodata,
      // not four fields. Identity still waits for acceptance.
      if (!result) {
        const forCandidate = family?.candidate_account_id;
        const [publicView, fallback, sent, incoming] = await Promise.all([
          viewPublicProfile(accountId),
          getSnippet(accountId),
          listSent(forCandidate).catch(() => []),
          listIncoming(forCandidate).catch(() => []),
        ]);
        if (!active) return;
        setPublicProfile(publicView);
        setSnippet(fallback);
        const out = sent.find(
          (c) => c.status === "pending" && c.target_account_id === accountId,
        );
        const inc = incoming.find(
          (c) => c.status === "pending" && c.subject_account_id === accountId,
        );
        // Already connected (a parent reads the match through the public
        // view, so "not connected yet" cannot be inferred from that alone).
        const joined =
          sent.find(
            (c) => c.status === "accepted" && c.target_account_id === accountId,
          ) ??
          incoming.find(
            (c) => c.status === "accepted" && c.subject_account_id === accountId,
          );
        setLink(
          out
            ? { kind: "sent", id: out.id }
            : inc
              ? { kind: "incoming", id: inc.id }
              : joined
                ? { kind: "connected", id: joined.id }
                : { kind: "none" },
        );
      }
      if (!active) return;
      setView(result);
    })();
    return () => {
      active = false;
    };
    // Switching whose search you are in changes the lens, the reasons and
    // the pending request shown here, so it reloads too.
  }, [accountId, family?.candidate_account_id]);

  async function connect() {
    setLinkBusy(true);
    setLinkError(null);
    const outcome = await sendRequest(accountId, family?.candidate_account_id);
    setLinkBusy(false);
    if (!outcome.ok) {
      setLinkError(outcome.message ?? t("profile:view.link.failed"));
      return;
    }
    setLink({ kind: "sent", id: outcome.data.id });
  }

  async function answer(decision: "accept" | "decline") {
    if (link.kind !== "incoming") return;
    setLinkBusy(true);
    setLinkError(null);
    const outcome =
      decision === "accept"
        ? await accept(link.id, family?.candidate_account_id)
        : await decline(link.id, family?.candidate_account_id);
    setLinkBusy(false);
    if (!outcome.ok) {
      setLinkError(outcome.message ?? t("profile:view.link.failed"));
      return;
    }
    if (decision === "accept") {
      // Accepting opens the full profile: reload into the connected lens.
      // A full load on purpose: accepting changes the session's counts and
      // this screen's whole lens, which a client-side push would not refetch.
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.assign(`/profile/${accountId}?connection=${link.id}`);
      return;
    }
    setLink({ kind: "none" });
  }

  /* One primary action, following the reader down the page on a phone and
     sitting in the reading column on desktop. */
  function linkActions() {
    const who = family ? family.candidate_name.split(" ")[0] : null;
    // [Owner, 2026-09-25] Only the candidate, a parent or a guardian sends a
    // request; a sibling or relative suggests instead (the Suggest action).
    const maySend =
      !family ||
      family.relationship_type === "parent" ||
      family.relationship_type === "guardian";
    // Answering is the same decision, so they do not get Accept / Not now either.
    if (!maySend && (link.kind === "none" || link.kind === "incoming")) return null;
    return (
      <div className="pview__actions" role="group">
        {link.kind === "sent" || link.kind === "connected" ? (
          <span className="pview__sent">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5 12.5l4.2 4.2L19 7"
              />
            </svg>
            {link.kind === "connected"
              ? who
                ? t("profile:view.link.connectedFor", { name: who })
                : t("profile:view.link.connected")
              : who
                ? t("profile:view.link.sentFor", { name: who })
                : t("profile:view.link.sent")}
          </span>
        ) : link.kind === "incoming" ? (
          <>
            <button
              type="button"
              className="btn btn--ghost"
              disabled={linkBusy}
              onClick={() => void answer("decline")}
            >
              {t("profile:view.link.decline")}
            </button>
            <button
              type="button"
              className="btn btn--primary"
              disabled={linkBusy}
              onClick={() => void answer("accept")}
            >
              {t("profile:view.link.accept")}
            </button>
          </>
        ) : (
          <button
            type="button"
            className="btn btn--primary"
            disabled={linkBusy}
            onClick={() => void connect()}
          >
            {who
              ? t("profile:view.link.connectFor", { name: who })
              : t("profile:view.link.connect")}
          </button>
        )}
        {linkError && (
          <p className="form-error" role="alert">
            {linkError}
          </p>
        )}
      </div>
    );
  }

  /* The sealed part of a profile, drawn as what it is: a card still in its
     envelope. Names exactly what opens on connection, so the reader is
     deciding about something concrete rather than a vague "more". */
  function sealed() {
    // Only what is actually still closed: a name, answers or photos this
    // person already shows openly are not listed as "opens later".
    const openAnswers = Object.values(
      (publicProfile?.attributes?.in_my_words ?? {}) as Record<string, unknown>,
    ).filter(
      (v) => !!v && typeof v === "object" && (v as { public?: unknown }).public === true,
    ).length;
    const allPhotosOpen = (publicProfile?.open_photo_urls?.length ?? 0) > 1;
    return (
      <div className="sealed">
        <div className="sealed__inner">
          <span className="sealed__eyebrow">
            {link.kind === "incoming"
              ? t("profile:view.sealed.askedEyebrow")
              : t("profile:view.sealed.eyebrow")}
          </span>
          <h3 className="sealed__title">
            {link.kind === "incoming"
              ? t("profile:view.sealed.askedTitle")
              : t("profile:view.sealed.title")}
          </h3>
          <ul className="sealed__list">
            {!publicProfile?.open_name && <li>{t("profile:view.sealed.name")}</li>}
            <li>
              {openAnswers > 0
                ? t("profile:view.sealed.promptsRest")
                : t("profile:view.sealed.prompts")}
            </li>
            <li>{t("profile:view.sealed.outlook")}</li>
            {!allPhotosOpen && <li>{t("profile:view.sealed.photos")}</li>}
          </ul>
          <p className="sealed__note">{t("profile:view.sealed.note")}</p>
        </div>
      </div>
    );
  }

  /* `overlay`: the bar floats in glass over the hero photo, and the title is
     for screen readers only — the name is already set large on the photo. */
  const header = (title: string, overlay = false) => (
    <header className={overlay ? "topbar pview__bar" : "topbar"}>
      <button
        type="button"
        className="icon-btn"
        onClick={() => router.back()}
        aria-label={t("common:action.back")}
      >
        ←
      </button>
      <h1 className={overlay ? "sr-only" : undefined}>{title}</h1>
      {connectionId && view && family ? (
        /* A family member's chat is the families' conversation, never the
           candidates' session (DEC-V1-024). A parent or guardian opens it
           if nobody has yet; everyone else joins the one already open. */
        <button
          type="button"
          className="icon-btn"
          aria-label={t("profile:view.familyChat")}
          title={t("profile:view.familyChat")}
          onClick={async () => {
            await openFamilyConversation(connectionId);
            router.push(`/messages/${connectionId}?kind=family`);
          }}
        >
          <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
            <path
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 6h12v8H8l-4 3V6z M18 9h3v8l-3-2.4h-6V17"
            />
          </svg>
        </button>
      ) : connectionId && view ? (
        <Link
          href={`/messages/${connectionId}`}
          className="icon-btn"
          aria-label={t("profile:view.message")}
        >
          <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
            <path
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M4 5h16v11H9l-5 4z"
            />
          </svg>
        </Link>
      ) : (
        <span style={{ width: 44 }} aria-hidden="true" />
      )}
    </header>
  );

  /* [DEC-V1-030] The candidate lens opens full-bleed, the way the reference
     apps do: the photo fills the top of the screen, the name is set large on
     it with the key facts as glass chips, and the back button floats over
     it. On a desktop the photo becomes a sticky column beside the words. */
  const immersiveHero = (
    photoUrl: string | null,
    alt: string,
    name: string,
    age: number | null,
    chips: string[],
    bar: React.ReactNode,
  ) => (
    <div className="pview__hero pview__hero--immersive">
      {bar}
      {photoUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={resolveMediaUrl(photoUrl) ?? ""} alt={alt} />
      ) : null}
      <div className="pview__over">
        <h2 className="pview__bigname">
          {name}
          {age ? <span className="pview__age"> {age}</span> : null}
        </h2>
        {chips.length > 0 && (
          <div className="pview__chips">
            {chips.map((c) => (
              <span key={c} className="pview__chip">
                {c}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  const familyNotes =
    family && family.candidate_account_id !== accountId ? (
      <FamilyNotes
        membershipId={family.membership_id}
        subjectAccountId={accountId}
        candidateName={family.candidate_name}
      />
    ) : null;

  // Birth time and place: always visible (owner, 2026-09-27).
  const horoscopeFacts = publicProfile?.attributes?.horoscope as Record<string, unknown> | undefined;
  const birthDetails = {
    time: typeof horoscopeFacts?.birth_time === "string" ? horoscopeFacts.birth_time : null,
    place: typeof horoscopeFacts?.birth_place === "string" ? horoscopeFacts.birth_place : null,
  };
  // After everything about this person: the next few worth reading.
  const similar = (
    <SimilarProfiles viewedId={accountId} forCandidate={family?.candidate_account_id} />
  );

  if (view === undefined || loaderHold) {
    return (
      <main className="screen screen--centered">
        <SacredLoader />
      </main>
    );
  }

  if (view === null) {
    /* Not connected yet. Shaadi.com shows a registered member another member's
       full biodata and gates only identity and contact; Mangalya does the same
       (DEC-V1-020) — the facts are here, the name and contact are not. A family
       member evaluating a match reads them as a biodata sheet, the way every
       matrimony service presents them; a candidate reads the same facts the
       Hinge way, led by the photo and the person's own words. */
    const facts = publicProfile?.attributes ?? {};
    const educationRaw =
      publicProfile?.education_level ?? snippet?.education_level ?? null;
    const educationKey = `profile:option.highest_education_level.${educationRaw}`;
    const education =
      educationRaw && t(educationKey) !== educationKey
        ? t(educationKey)
        : educationRaw;
    const age = publicProfile?.age ?? snippet?.age ?? null;
    const locality = publicProfile?.locality ?? snippet?.locality ?? null;
    const profession = publicProfile?.profession ?? snippet?.profession ?? null;
    const photoUrl = publicProfile?.photo_url ?? snippet?.photo_url ?? null;
    const headline = [age ? t("profile:hub.ageYears", { age }) : null, locality]
      .filter(Boolean)
      .join(" · ");
    const subline = [education, profession].filter(Boolean).join(" · ");

    // `partner` is excluded here as well as on the server (FR020: partner
    // preferences are the viewer's own matching filters and never reach the
    // person being viewed). Belt and braces on a privacy rule is cheap.
    const sections = PROFILE_SECTIONS.filter((s) => s.id !== "partner")
      .map((section) => ({
        id: section.id,
        rows: section.categories.flatMap((category) => {
          const def = findCategory(category);
          if (!def) return [];
          return def.fields
            .map((f) => ({
              key: `${category}.${f.key}`,
              // A reader's wording where the form's differs ("About them",
              // not "A few lines about you"; "Height", not "Height (cm)").
              label: i18n.exists(`profile:fieldView.${category}.${f.key}`)
                ? t(`profile:fieldView.${category}.${f.key}`)
                : t(`profile:field.${category}.${f.key}`),
              text:
                f.key === "height_cm" && facts[category]?.[f.key]
                  ? `${String(facts[category]?.[f.key])} cm`
                  : formatFieldValue(t, f, facts[category]?.[f.key]),
            }))
            .filter(
              (row): row is { key: string; label: string; text: string } =>
                !!row.text,
            );
        }),
      }))
      .filter((section) => section.rows.length > 0);

    const prompts = (["prompt_1", "prompt_2", "prompt_3"] as PromptSlot[])
      .map((slot) => facts[PROMPT_CATEGORY]?.[slot])
      .filter(isPromptValue);

    const hero = (
      <>
        {photoUrl && (
          <div className="preview-photo">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={resolveMediaUrl(photoUrl) ?? ""} alt="" />
          </div>
        )}
        <div className="preview-identity">
          {/* [Owner, 2026-09-25] After both sides accept, a parent or
              guardian sees the match's full name. */}
          {publicProfile?.name && (
            <span className="profile-hero__name">{publicProfile.name}</span>
          )}
          <span className={publicProfile?.name ? "caption" : "profile-hero__name"}>
            {headline}
          </span>
          {subline && <span className="caption">{subline}</span>}
          <span className="caption">
            🔒{" "}
            {family
              ? t(
                  link.kind === "connected"
                    ? "profile:view.familyHintConnected"
                    : "profile:view.familyHint",
                  { name: family.candidate_name.split(" ")[0] },
                )
              : t("profile:view.publicHint")}
          </span>
        </div>
      </>
    );

    if (!publicProfile && !snippet) {
      return (
        <>
          {header(t("profile:view.title"))}
          <main className="screen">
            <div className="card">
              <h2 className="h2">{t("profile:view.locked")}</h2>
              <p className="caption">{t("profile:view.lockedHint")}</p>
            </div>
            {familyNotes}
          </main>
        </>
      );
    }

    if (family) {
      return (
        <>
          {header(t("profile:view.title"))}
          <main className="screen preview-card">
            {hero}
            {/* [2026-09-29, critique] The biodata a family reads, grouped the
                way a printed biodata is (basics, community, education and
                work, family, lifestyle, horoscope), two columns on a desk,
                larger type — not one flat list of 27 rows. */}
            {sections.length > 0 && (
              <div className="biodata-sections">
                {sections.map((section) => (
                  <section key={section.id} className="card biodata-section" aria-label={t(`profile:hub.section.${section.id}`)}>
                    <h2 className="biodata-section__title">{t(`profile:hub.section.${section.id}`)}</h2>
                    <dl className="biodata biodata--family">
                      {section.rows.map((row) => (
                        <div key={row.key} className="biodata__row">
                          <dt>{row.label}</dt>
                          <dd>{row.text}</dd>
                        </div>
                      ))}
                    </dl>
                  </section>
                ))}
              </div>
            )}
            {/* [Owner, 2026-09-28] Everything the engine knows about this
                pair in one place: fit, what they share, and the horoscope. */}
            <CompatibilityPanel
              candidateId={accountId}
              forCandidate={{ accountId: family.candidate_account_id, name: family.candidate_name }}
              birth={birthDetails}
            />
            {(publicProfile?.open_photo_urls?.length ?? 0) > 1 && (
              <div
                className="pview__strip"
                aria-label={t("profile:openly.photosLabel")}
              >
                {publicProfile!.open_photo_urls!.slice(1).map((u) => (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    key={u}
                    src={resolveMediaUrl(u) ?? ""}
                    alt=""
                    loading="lazy"
                  />
                ))}
              </div>
            )}
            {linkActions()}
            {/* Suggest this person to the candidate — never a decision and
                never sent to the person (FR014). It used to live on the
                Discover card; Discover is a photo wall now, and the decision
                to suggest is made here, having read the profile. Not once
                a request exists or they are already connected. */}
            {link.kind === "none" && (
            <button
              type="button"
              className="btn btn--ghost"
              disabled={suggested}
              onClick={async () => {
                const outcome = await suggestProfile(
                  family.membership_id,
                  accountId,
                );
                if (outcome.ok) setSuggested(true);
              }}
            >
              {suggested
                ? t("discover:family.suggested", {
                    name: family.candidate_name.split(" ")[0],
                  })
                : t("discover:family.suggest", {
                    name: family.candidate_name.split(" ")[0],
                  })}
            </button>
            )}
            {familyNotes}
            {similar}
          </main>
        </>
      );
    }

    /* Photos and prompts, matching the connected candidate view. The fact
       chips that used to be interleaved here have moved to the parent lens:
       a candidate is deciding whether they want to know this person, and the
       prompts carry the matrimony agenda in the person's own words. */
    // [Migration 043] Their first name, only if they chose to show it;
    // otherwise they are introduced by age.
    const openFirst = publicProfile?.open_name?.trim().split(/\s+/)[0] ?? null;
    return (
      <>
        <main className="screen pview-screen">
          <div className="pview pview--immersive">
            {immersiveHero(
              photoUrl,
              "",
              openFirst ?? (age ? t("profile:hub.ageYears", { age }) : ""),
              openFirst ? age : null,
              [locality?.split(",")[0]?.trim(), profession, education].filter(
                (c): c is string => !!c,
              ),
              header(t("profile:view.title"), true),
            )}
            <div className="pview__body">
              <span className="pcard__locked">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.7"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M7 10V7.5a5 5 0 0 1 10 0V10M5.5 10h13v9.5h-13z"
                  />
                </svg>
                {/* The family case returned above, so this is always the
                    candidate-facing wording. */}
                <span>
                  {publicProfile?.open_name
                    ? t("profile:view.publicHintNamed")
                    : t("profile:view.publicHint")}
                </span>
              </span>

              {insight(snippet?.verification)}
              <CompatibilityPanel candidateId={accountId} birth={birthDetails} />

              {/* Only what they chose to publish (migration 039). No claim
                  is made about what they have or have not written. */}
              {prompts.map((value, i) => promptCard(value, i))}

              {/* [Migration 043] All their photos, when they opened them. */}
              {(publicProfile?.open_photo_urls?.length ?? 0) > 1 && (
                <div
                  className="pview__strip"
                  aria-label={t("profile:openly.photosLabel")}
                >
                  {publicProfile!.open_photo_urls!.slice(1).map((u) => (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      key={u}
                      src={resolveMediaUrl(u) ?? ""}
                      alt=""
                      loading="lazy"
                    />
                  ))}
                </div>
              )}

              {sealed()}
              {linkActions()}
            </div>
          </div>
            {similar}
        </main>
      </>
    );
  }

  const { profile, photos, attributes } = view;

  function formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString(i18n.language, {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  }

  async function changeShare(category: ShareCategory, shared: boolean) {
    if (!connectionId) return;
    setBusy(category);
    setShareError(null);
    const outcome =
      category === "family_contact" && !shared
        ? await withdrawFamilyContact(connectionId)
        : await setShare(connectionId, category, shared);
    setBusy(null);
    if (!outcome.ok) {
      setShareError(t("profile:view.share.error"));
      return;
    }
    setConfirming(null);
    setSharing((prev) =>
      prev
        ? {
            ...prev,
            mine: prev.mine.map((m) =>
              m.category === category ? outcome.data : m,
            ),
          }
        : prev,
    );
  }

  async function askFamily(membershipId: string) {
    if (!connectionId) return;
    setBusy("family_contact");
    setShareError(null);
    const outcome = await requestFamilyContact(connectionId, membershipId);
    setBusy(null);
    if (!outcome.ok) {
      setShareError(t("profile:view.share.error"));
      return;
    }
    setConfirming(null);
    setSharing((prev) =>
      prev
        ? {
            ...prev,
            mine: prev.mine.map((m) =>
              m.category === "family_contact" ? outcome.data : m,
            ),
          }
        : prev,
    );
  }

  function relationshipLabel(value: string | null | undefined): string {
    return value ? t(`profile:view.share.relationship.${value}`) : "";
  }

  /* The candidate lens, built to the pattern the reference apps share:
     vitals as one scannable line under the name, prompts as the loudest
     thing on the page, and facts as chips rather than a two-column table.
     The family lens below keeps its table on purpose — a table is the right
     form for comparing several matches, which is the job a parent is doing. */

  /* Evidence and reasons, rendered the same way on both candidate paths.
     Neither is a score: the reasons are sentences the engine can justify,
     and the evidence is a fact with a date. */
  function insight(layers: VerifiedLayer[] | undefined) {
    const hasAny = (layers?.length ?? 0) > 0 || reasons.length > 0;
    if (!hasAny) return null;
    return (
      <div className="insight">
        {reasons.length > 0 && (
          <div className="insight__reasons">
            <div className="insight__title">{t("profile:view.whyTitle")}</div>
            {reasons.slice(0, 3).map((r, i) => (
              <p key={i} className="insight__reason">
                {r.text}
              </p>
            ))}
          </div>
        )}
        {(layers?.length ?? 0) > 0 && (
          <ul className="verified">
            {layers!.map((v) => (
              <li key={v.layer} className="verified__item">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 3.2l6.5 2.4v5.2c0 4-2.7 7.4-6.5 8.6-3.8-1.2-6.5-4.6-6.5-8.6V5.6z M9 12l2.2 2.2L15.5 10"
                  />
                </svg>
                <span>
                  {v.verified_on
                    ? t("discover:verified.on", {
                        label: t(`discover:verified.layer.${v.layer}`),
                        date: new Intl.DateTimeFormat(`${i18n.language}-IN`, {
                          month: "short",
                          year: "numeric",
                        }).format(new Date(v.verified_on)),
                      })
                    : t(`discover:verified.layer.${v.layer}`)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }

  /* A prompt. The first one is the lead and gets the largest type on the
     screen; the rest settle down so the page has a rhythm instead of three
     identical blocks. When the reader has answered the same question, their
     own words sit underneath — which turns a profile into the beginning of
     a conversation rather than a page about someone else. */
  function promptCard(value: { q: string; a: string }, index: number) {
    const mine = myPrompts[value.q];
    return (
      <div
        key={`${value.q}-${index}`}
        className={`pview__prompt${index === 0 ? " pview__prompt--lead" : ""}`}
      >
        <span className="pview__prompt-q">
          {t(`profile:hub.prompts.q.${value.q}`)}
        </span>
        <p className="pview__prompt-a">{value.a}</p>
        {mine && (
          <div className="pview__mine">
            <span className="pview__mine-label">
              {t("profile:view.youAnswered")}
            </span>
            <p className="pview__mine-a">{mine}</p>
          </div>
        )}
      </div>
    );
  }

  function fact(category: string, key: string): string | null {
    const def = findField(category, key);
    return def ? formatFieldValue(t, def, attributes[category]?.[key]) : null;
  }

  function vitals(): string[] {
    return [
      t("profile:hub.ageYears", { age: ageFromDob(profile.date_of_birth) }),
      profile.city_locality?.split(",")[0]?.trim(),
      fact("profession", "occupation"),
      fact("education", "highest_education_level"),
    ].filter((v): v is string => !!v);
  }

  function renderCandidateBlock(block: Block, index: number) {
    if (block.kind === "photo") {
      // The first photo is the hero, rendered outside the flow.
      if (block.index === 0) return null;
      const photo = photos[block.index];
      if (!photo) return null;
      return (
        <div key={`photo-${index}`} className="pview__hero">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={resolveMediaUrl(photo.url) ?? ""}
            alt={t("profile:view.photoAlt", { name: profile.name })}
          />
        </div>
      );
    }

    if (block.kind === "identity") {
      return (
        // The name and vitals are on the hero photo; this block keeps the
        // reader-facing insight (why this person, what is verified).
        <div key="identity" className="pview__head">
          {insight(snippet?.verification)}
              <CompatibilityPanel candidateId={accountId} birth={birthDetails} />
        </div>
      );
    }

    if (block.kind === "prompt") {
      const value = attributes[PROMPT_CATEGORY]?.[block.slot];
      if (!isPromptValue(value)) return null;
      return promptCard(value, index);
    }

    if (block.kind === "outlook") {
      const rows = compareOutlook(readOutlook(attributes), myOutlook);
      if (rows.length === 0) return null;
      const iAnswered = Object.keys(myOutlook).length > 0;
      return (
        <div key="outlook" className="olook">
          <div className="olook__head">
            <span className="factgroup__title">
              {t("profile:view.outlookTitle", {
                name: profile.name.split(" ")[0],
              })}
            </span>
            <span className="caption">
              {iAnswered
                ? t("profile:outlook.disclaimer")
                : t("profile:outlook.nudge")}
            </span>
          </div>
          <ul className="olook__list">
            {rows.map((r) => (
              <li
                key={r.id}
                className={`olook__row${r.same ? " is-same" : ""}`}
              >
                <OutlookScene id={r.theirs} className="olook__scene" />
                <span className="olook__q">
                  {t(`profile:outlook.q.${r.id}`)}
                </span>
                <span className="olook__a">
                  {t(`profile:outlook.pole.${r.theirs}`)}
                </span>
                {r.mine && (
                  <span className="olook__tag">
                    {r.same
                      ? t("profile:outlook.sameAsYou")
                      : t("profile:outlook.differentFromYou", {
                          mine: t(`profile:outlook.pole.${r.mine}`),
                        })}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      );
    }

    const section = PROFILE_SECTIONS.find((sec) => sec.id === block.id);
    // One chip per field, not per category, so each fact stands on its own
    // and long categories stop collapsing into a dot-joined run-on.
    const chips = (section?.categories ?? [])
      .map((c) => findCategory(c))
      .filter((d): d is CategoryDef => !!d)
      .flatMap((d) =>
        d.fields
          .map((f) => ({
            key: `${d.category}.${f.key}`,
            label: t(`profile:field.${d.category}.${f.key}`),
            text: formatFieldValue(t, f, attributes[d.category]?.[f.key]),
            long: f.kind === "textarea",
          }))
          .filter(
            (
              c,
            ): c is {
              key: string;
              label: string;
              text: string;
              long: boolean;
            } => !!c.text,
          ),
      );
    if (chips.length === 0) return null;
    // Sentences ("About", "About the family") read as a paragraph; facts as chips.
    const paragraphs = chips.filter((c) => c.long);
    const facts = chips.filter((c) => !c.long);
    return (
      <div key={block.id} className="factgroup">
        <div className="factgroup__title">
          {t(`profile:hub.section.${block.id}`)}
        </div>
        {paragraphs.map((c) => (
          <p key={c.key} className="factgroup__text">
            {c.text}
          </p>
        ))}
        <div className="factchips">
          {facts.map((c) => (
            <span key={c.key} className="factchip">
              <span className="factchip__k">{c.label}</span>
              {c.text}
            </span>
          ))}
        </div>
      </div>
    );
  }

  function renderBlock(block: Block, index: number) {
    if (block.kind === "photo") {
      const photo = photos[block.index];
      if (!photo) return null;
      return (
        <div key={`photo-${index}`} className="preview-photo">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={resolveMediaUrl(photo.url) ?? ""}
            alt={t("profile:view.photoAlt", { name: profile.name })}
          />
        </div>
      );
    }
    if (block.kind === "identity") {
      return (
        <div key="identity" className="preview-identity">
          <span className="profile-hero__name">{profile.name}</span>
          <span className="caption">
            {[
              t("profile:hub.ageYears", {
                age: ageFromDob(profile.date_of_birth),
              }),
              profile.city_locality,
            ]
              .filter(Boolean)
              .join(" · ")}
          </span>
        </div>
      );
    }
    if (block.kind === "prompt") {
      const value = attributes[PROMPT_CATEGORY]?.[block.slot];
      if (!isPromptValue(value)) return null;
      return (
        <div key={block.slot} className="prompt-card prompt-card--elevated">
          <span className="prompt-card__q">
            {t(`profile:hub.prompts.q.${value.q}`)}
          </span>
          <span className="prompt-card__a">{value.a}</span>
        </div>
      );
    }
    // The family lens never shows the ten choices: they are written for the
    // person someone might marry, not for that person's parent.
    if (block.kind === "outlook") return null;
    const section = PROFILE_SECTIONS.find((s) => s.id === block.id);
    /* One row per field, under the field's own label — never the storage
       category's name ("Education", "Profession", "Education & career"). */
    const rows = (section?.categories ?? [])
      .map((c) => findCategory(c))
      .filter((d): d is CategoryDef => !!d)
      .flatMap((d) =>
        d.fields.map((f) => ({
          key: `${d.category}.${f.key}`,
          label:
            f.key === "about"
              ? t("profile:view.aboutName", {
                  name: profile.name.split(" ")[0],
                })
              : t(`profile:field.${d.category}.${f.key}`),
          text: formatFieldValue(t, f, attributes[d.category]?.[f.key]),
        })),
      )
      .filter(
        (r): r is { key: string; label: string; text: string } => !!r.text,
      );
    if (rows.length === 0) return null;
    return (
      <div key={block.id} className="card preview-section">
        <div className="label">{t(`profile:hub.section.${block.id}`)}</div>
        <dl className="biodata">
          {rows.map((r) => (
            <div key={r.key} className="biodata__row">
              <dt>{r.label}</dt>
              <dd>{r.text}</dd>
            </div>
          ))}
        </dl>
      </div>
    );
  }

  return (
    <>
      {family && header(profile.name)}
      <main className={`screen preview-card${family ? "" : " pview-screen"}`}>
        {family ? (
          FAMILY_LAYOUT.map(renderBlock)
        ) : (
          <div className="pview pview--immersive">
            {immersiveHero(
              photos[0]?.url ?? null,
              t("profile:view.photoAlt", { name: profile.name }),
              profile.name,
              // The age sits with the name, as on every other card.
              ageFromDob(profile.date_of_birth),
              vitals().slice(1),
              header(profile.name, true),
            )}
            <div className="pview__body">
              {CANDIDATE_LAYOUT.map(renderCandidateBlock)}
              <VoiceIntroPlayer
                url={view.voice_intro_url ?? null}
                name={profile.name}
              />
              {/* Connected: the one thing to do next is talk. Opens the two
                  candidates' private session. */}
              {connectionId && (
                <div className="pview__actions" role="group">
                  <Link
                    className="btn btn--primary"
                    href={`/messages/${connectionId}`}
                  >
                    {t("profile:view.message")} {profile.name.split(" ")[0]}
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}
        {family && (
          <VoiceIntroPlayer
            url={view.voice_intro_url ?? null}
            name={profile.name}
          />
        )}
        {familyNotes}
        {sharing && (
          <section
            className="card share-card"
            aria-label={t("profile:view.share.title", { name: profile.name })}
          >
            <div className="label">
              {t("profile:view.share.title", { name: profile.name })}
            </div>
            <p className="caption">{t("profile:view.share.intro")}</p>
            <ul className="share-list">
              {sharing.mine.map((s) => (
                <li key={s.category} className="share-row">
                  {confirming === s.category ? (
                    <div className="share-row__confirm">
                      <p>
                        {t(`profile:view.share.confirm.${s.category}`, {
                          name: profile.name,
                          value: s.value,
                        })}
                      </p>
                      {s.category === "family_contact" && (
                        <div className="quick-pick__chips">
                          {members
                            .filter((m) => m.member_account_id !== accountId)
                            .map((m) => (
                              <button
                                key={m.membership_id}
                                type="button"
                                className="quick-pick__chip quick-pick__chip--active"
                                disabled={busy === "family_contact"}
                                onClick={() => void askFamily(m.membership_id)}
                              >
                                {t("profile:view.share.askMember", {
                                  relationship: relationshipLabel(
                                    m.relationship_type,
                                  ),
                                })}
                              </button>
                            ))}
                        </div>
                      )}
                      <div className="sheet__row">
                        <button
                          type="button"
                          className="quick-pick__chip"
                          onClick={() => setConfirming(null)}
                        >
                          {t("profile:view.share.cancel")}
                        </button>
                        {s.category !== "family_contact" && (
                          <button
                            type="button"
                            className="cta"
                            disabled={busy === s.category}
                            onClick={() => void changeShare(s.category, true)}
                          >
                            {t("profile:view.share.confirmCta")}
                          </button>
                        )}
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="share-row__text">
                        <span className="share-row__name">
                          {t(`profile:view.share.category.${s.category}`)}
                        </span>
                        <span className="caption">
                          {s.shared_at
                            ? t("profile:view.share.sharedOn", {
                                date: formatDate(s.shared_at),
                              })
                            : s.pending
                              ? t("profile:view.share.waiting", {
                                  relationship: relationshipLabel(s.pending),
                                })
                              : s.available
                                ? t("profile:view.share.notShared")
                                : t(
                                    `profile:view.share.unavailable.${s.category}`,
                                  )}
                        </span>
                      </div>
                      {s.shared_at ? (
                        <button
                          type="button"
                          className="quick-pick__chip"
                          disabled={busy === s.category}
                          onClick={() => void changeShare(s.category, false)}
                        >
                          {t("profile:view.share.stop")}
                        </button>
                      ) : s.available && !s.pending ? (
                        <button
                          type="button"
                          className="quick-pick__chip quick-pick__chip--active"
                          disabled={busy === s.category}
                          onClick={() => setConfirming(s.category)}
                        >
                          {t("profile:view.share.share")}
                        </button>
                      ) : null}
                    </>
                  )}
                </li>
              ))}
            </ul>
            {shareError && (
              <p className="form__error" role="alert">
                {shareError}
              </p>
            )}
            <div className="label">
              {t("profile:view.share.theirsTitle", { name: profile.name })}
            </div>
            {sharing.theirs.length === 0 ? (
              <p className="caption">{t("profile:view.share.theirsEmpty")}</p>
            ) : (
              <ul className="share-list">
                {sharing.theirs.map((s) => (
                  <li key={s.category} className="share-row">
                    <div className="share-row__text">
                      <span className="share-row__name">
                        {t(`profile:view.share.category.${s.category}`)}
                      </span>
                      <span className="caption">
                        {s.shared_at
                          ? t("profile:view.share.sharedOn", {
                              date: formatDate(s.shared_at),
                            })
                          : ""}
                      </span>
                    </div>
                    {s.category === "phone" && s.value && (
                      <a className="quick-pick__chip" href={`tel:${s.value}`}>
                        {s.value}
                      </a>
                    )}
                    {s.category === "email" && s.value && (
                      <a
                        className="quick-pick__chip"
                        href={`mailto:${s.value}`}
                      >
                        {s.value}
                      </a>
                    )}
                    {s.category === "additional_photos" && (
                      <span className="caption">
                        {t("profile:view.share.photosShared")}
                      </span>
                    )}
                    {s.category === "family_contact" &&
                      s.value &&
                      (() => {
                        const contact = JSON.parse(s.value) as {
                          name: string | null;
                          relationship: string;
                          phone: string;
                        };
                        return (
                          <a
                            className="quick-pick__chip"
                            href={`tel:${contact.phone}`}
                          >
                            {`${contact.name ?? relationshipLabel(contact.relationship)} · ${contact.phone}`}
                          </a>
                        );
                      })()}
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}
            {similar}
      </main>
    </>
  );
}
