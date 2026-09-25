// [IMP38 — Refactor C] Host-dependent document metadata. A plain module (no
// React, no "use client") so the server-rendered root layout can read it.
export const HOST_ID = process.env.NEXT_PUBLIC_VYAPAR_HOST === "standalone" ? "standalone" : "forkhatri";

export const hostMetadata =
  HOST_ID === "standalone"
    ? {
        title: "Vyapar",
        description: "Business, professional and opportunity discovery.",
      }
    : {
        title: "Vyapar — ForKhatri",
        description: "Business, professional and opportunity discovery for the Khatri community.",
      };
