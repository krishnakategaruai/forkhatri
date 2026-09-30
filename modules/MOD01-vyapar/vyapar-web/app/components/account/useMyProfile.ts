"use client";

// [Owner, 2026-09-30: "each user will get one profile"; "i already logged in
// as user, but still it is asking me this"] One data hook for "who am I on
// Vyapar", so no account screen asks for what the app already knows.
//
// Sources, in order:
//   1. GET /v1/me/profile — the one-profile contract backend A is adding
//      (one profile created from the ForKhatri identity, with an optional
//      `business` section). Read defensively: until its shape is published
//      in references/imp-backend-a.md only the fields named below are used.
//   2. Fallback while that endpoint returns 404: GET /v1/members/me (name,
//      language, the member's profile rows) + GET /v1/first-run/state
//      (locality, lat/lng, skills, work mode captured at first run).
// Presentational screens take the normalised value; nothing here renders.
import { useCallback, useEffect, useState } from "react";
import type { Me, ProfessionVerdict, ProfileBrief } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { api } from "@/lib/api";

/** A profile section with the per-section flags (imp-backend-a §11b). */
export type MyBrief = ProfileBrief & {
  /** draft | submitted | active | suspended | archived */
  profile_status?: string;
  /** This section's own verification: a credential for the person, a business document for the business. */
  verified?: boolean;
};

export interface MyProfile {
  name: string;
  language: string;
  locality: string | null;
  lat: number | null;
  lng: number | null;
  phone: string | null;
  /** Skill slugs captured at first run, used to prefill the work profile. */
  skills: string[];
  workMode: "on_site" | "remote" | "both" | null;
  /** The member's own work profile (the ONE profile), when it has been set up. */
  work: MyBrief | null;
  /** The optional business section. */
  business: MyBrief | null;
  operatorPermissions: string[];
  /** [Trust pack §4] The council rule that applies to the profile (advocate, architect…), or null. */
  profession: ProfessionVerdict | null;
  /** The one profile exists (GET /v1/me/profile `exists`). */
  exists: boolean;
  /** What the API says it still needs to create the profile (e.g. ["locality"]). */
  missing: string[];
  /** Where the data came from: the one-profile endpoint, or the fallback. */
  source: "me-profile" | "legacy";
}

interface FirstRunState {
  display_name: string;
  language: string;
  locality: string | null;
  lat: number | null;
  lng: number | null;
  capabilities: string[];
  work_mode: string | null;
}

function asBrief(v: unknown): ProfileBrief | null {
  if (!v || typeof v !== "object") return null;
  const o = v as Record<string, unknown>;
  if (typeof o.id !== "string" || typeof o.name !== "string") return null;
  return {
    id: o.id,
    kind: (o.kind as ProfileBrief["kind"]) ?? "professional",
    name: o.name,
    headline: (o.headline as string | null) ?? null,
    locality: (o.locality as string) ?? "",
    state: (o.state as string) ?? "draft",
    verification_state: (o.verification_state as string) ?? "not_started",
    capability_labels: Array.isArray(o.capability_labels) ? (o.capability_labels as string[]) : [],
  };
}

function mode(v: unknown): MyProfile["workMode"] {
  return v === "on_site" || v === "remote" || v === "both" ? v : null;
}

export function useMyProfile() {
  const sdk = useSdk();
  const [data, setData] = useState<MyProfile | null>(null);
  const [error, setError] = useState(false);

  const load = useCallback(() => {
    return Promise.all([
      api.get<Record<string, unknown>>("/v1/me/profile").catch(() => null),
      sdk.members.me().catch((): Me | null => null),
      api.get<FirstRunState>("/v1/first-run/state").catch((): FirstRunState | null => null),
    ]).then(([mine, me, fr]) => {
      if (!me && !mine) {
        setError(true);
        return;
      }
      // GET /v1/me/profile (imp-backend-a §getMyProfile):
      // {exists, profile: ListingOut + has_business/business_*, prefill, missing}
      const one = mine && typeof mine === "object" && "exists" in mine ? mine : null;
      const p = (one?.profile ?? null) as Record<string, unknown> | null;
      const pre = (one?.prefill ?? {}) as Record<string, unknown>;
      let work: MyBrief | null;
      let business: MyBrief | null;
      if (one) {
        const base = asBrief(p);
        // §11b: each section carries its own verification; the person's card
        // never borrows the shop's document check ("Active", not "Active · Verified").
        const status = typeof p?.profile_status === "string" ? (p.profile_status as string) : undefined;
        const credentialVerified =
          typeof p?.credential_verified === "boolean" ? (p.credential_verified as boolean) : p?.verification_document === "credential" && base?.verification_state === "verified";
        const businessVerified = typeof p?.business_verified === "boolean" ? (p.business_verified as boolean) : undefined;
        work = base ? { ...base, kind: "professional", profile_status: status, verified: !!credentialVerified } : null;
        business =
          base && p?.has_business
            ? {
                ...base,
                kind: "business",
                name: (p.business_name as string) || base.name,
                headline: (p.business_headline as string | null) ?? null,
                capability_labels: [],
                profile_status: status,
                verified: businessVerified,
              }
            : null;
      } else {
        work = me?.profiles?.professional ?? null;
        business = me?.profiles?.business ?? null;
      }
      setData({
        name: (pre.name as string) || (p?.name as string) || me?.display_name || fr?.display_name || "",
        language: (pre.language as string) || me?.language || fr?.language || "en",
        locality: (pre.locality as string) || (p?.locality as string) || fr?.locality || work?.locality || business?.locality || null,
        lat: (pre.lat as number) ?? fr?.lat ?? null,
        lng: (pre.lng as number) ?? fr?.lng ?? null,
        phone: (pre.phone as string) || (p?.primary_phone as string) || null,
        skills: Array.isArray(p?.capabilities) ? (p?.capabilities as string[]) : (fr?.capabilities ?? []),
        workMode: mode(p?.service_mode) ?? mode(fr?.work_mode),
        work,
        business,
        operatorPermissions: me?.operator_permissions ?? [],
        profession: (p?.profession as ProfessionVerdict | null | undefined) ?? null,
        exists: one ? !!one.exists : !!(work || business),
        missing: Array.isArray(one?.missing) ? (one?.missing as string[]) : [],
        source: one ? "me-profile" : "legacy",
      });
    });
  }, [sdk]);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, error, refresh: load };
}

/**
 * "Use my current location": the browser's position, turned into a locality
 * Vyapar knows. Asks POST /v1/me/profile/locate first (backend A); while that
 * is not live, returns the coordinates alone so the screen can offer the
 * known areas as one-tap choices and still send lat/lng with the profile.
 */
export function locateMe(): Promise<{ lat: number; lng: number; locality: string | null }> {
  return new Promise((resolve, reject) => {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      reject(new Error("unavailable"));
      return;
    }
    // An unanswered permission prompt never calls back; stop waiting after
    // 15 s so the screen falls back to typing instead of spinning forever.
    let done = false;
    const guard = setTimeout(() => {
      if (!done) reject(new Error("timeout"));
    }, 15000);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        done = true;
        clearTimeout(guard);
        const lat = Math.round(pos.coords.latitude * 1e5) / 1e5;
        const lng = Math.round(pos.coords.longitude * 1e5) / 1e5;
        api
          .post<{ locality?: string | null }>("/v1/me/profile/locate", { lat, lng })
          .then((r) => resolve({ lat, lng, locality: r?.locality ?? null }))
          .catch(() => resolve({ lat, lng, locality: null }));
      },
      (err) => {
        done = true;
        clearTimeout(guard);
        reject(err);
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 },
    );
  });
}
