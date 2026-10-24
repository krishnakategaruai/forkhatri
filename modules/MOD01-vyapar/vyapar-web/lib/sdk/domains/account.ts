// [IMP38 — Refactor C] The caller's own account: identity, first run,
// privacy, preferences, workspace (team) membership, development tools.
import { seg, type VyaparClient } from "../client";
import type { DevMember, FirstRunState, LocateResult, Me, ProfileCompletion, StartInput, StartOut, TradeTile, WorkspaceInvite, WorkspaceRow } from "../types";

export function membersApi(c: VyaparClient) {
  return {
    /** getMe */
    me: () => c.get<Me>("/v1/members/me"),
    /** setMyLanguage — persists the language choice on the member's own row */
    setLanguage: (language: string) => c.patch<unknown>("/v1/members/me/language", { language }),
  };
}

export function firstRunApi(c: VyaparClient) {
  return {
    state: () => c.get<FirstRunState>("/v1/first-run/state"),
    step: (step: number, extra: Record<string, unknown> = {}) => c.post<unknown>("/v1/first-run/step", { step, ...extra }),
    categoryOptions: <T = unknown[]>() => c.get<T>("/v1/first-run/category-options"),
    capabilityOptions: <T = unknown[]>() => c.get<T>("/v1/first-run/capability-options"),
    scopedCapabilityOptions: <T = unknown[]>(categories?: readonly string[]) =>
      c.get<T>("/v1/first-run/scoped-capability-options", { categories }),
    /** [Start flow 2026-10] listTradeTiles — picture-tile trades for a goal */
    tradeTiles: (goal: "find_work" | "get_customers") => c.get<TradeTile[]>("/v1/first-run/trade-tiles", { goal }),
    /** completeStart — goal, trades and area in one call; goes live where the rules allow */
    start: (body: StartInput) => c.post<StartOut>("/v1/first-run/start", body),
  };
}

/** [Start flow 2026-10] The member's one profile: completion card and place lookup. */
export function myProfileApi(c: VyaparClient) {
  return {
    /** getMyProfileCompletion — percent done and the one next question (never blocking) */
    completion: () => c.get<ProfileCompletion>("/v1/me/profile/completion"),
    /** locateMyProfile — nearest known area for a position, with nearby areas for chips */
    locate: (lat: number, lng: number) => c.post<LocateResult>("/v1/me/profile/locate", { lat, lng }),
    /** updateMyProfile — any profile field; `publish: true` submits it so it goes live when allowed */
    update: <T = Record<string, unknown>>(patch: Record<string, unknown>) => c.patch<T>("/v1/me/profile", patch),
  };
}

export function privacyApi(c: VyaparClient) {
  return {
    get: <T = Record<string, unknown>>() => c.get<T>("/v1/privacy"),
    update: <T = Record<string, unknown>>(patch: Record<string, unknown>) => c.patch<T>("/v1/privacy", patch),
    requests: <T = unknown[]>() => c.get<T>("/v1/privacy/requests"),
    exportData: <T = { document: unknown }>() => c.post<T>("/v1/privacy/export", {}),
    deleteAccount: <T = { state: string; reason?: string }>() => c.post<T>("/v1/privacy/delete", {}),
  };
}

export function preferencesApi(c: VyaparClient) {
  return {
    mine: <T = unknown[]>() => c.get<T>("/v1/preferences/mine"),
    act: <T = unknown>(id: string, action: string) => c.post<T>(`/v1/preferences/${seg(id)}/${seg(action)}`, {}),
  };
}

export function workspaceApi(c: VyaparClient) {
  return {
    mine: () => c.get<WorkspaceRow[]>("/v1/workspace/mine"),
    invitesMine: () => c.get<WorkspaceInvite[]>("/v1/workspace/invites/mine"),
    answerInvite: (inviteId: string, accept: boolean) => c.post<unknown>(`/v1/workspace/invites/${seg(inviteId)}/answer`, { accept }),
    get: <T = unknown>(listingId: string) => c.get<T>(`/v1/workspace/${seg(listingId)}`),
    invite: <T = unknown>(listingId: string, body: Record<string, unknown>) => c.post<T>(`/v1/workspace/${seg(listingId)}/invite`, body),
    setRole: <T = unknown>(memberId: string, body: Record<string, unknown>) => c.post<T>(`/v1/workspace/members/${seg(memberId)}/role`, body),
  };
}

export function devApi(c: VyaparClient) {
  return {
    /** Development only: the seeded members a tester can act as. */
    members: () => c.get<DevMember[]>("/v1/dev/members"),
  };
}

export function eventsApi(c: VyaparClient) {
  return {
    /** submitEvents — operational/analytics events */
    submit: (events: { event: string; level?: string; props?: Record<string, unknown> }[]) => c.post<unknown>("/v1/events", { events }),
  };
}

export function uploadsApi(c: VyaparClient) {
  return {
    upload: (file: File) => c.upload<{ url: string; size: number }>("/v1/uploads", file),
    resolveUrl: (url: string) => c.resolveUrl(url),
  };
}
