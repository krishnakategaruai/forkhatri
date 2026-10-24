// [FE2 — imp-backend-b §4] Tiered service packages on a listing: at most
// one Basic, one Standard and one Premium. Requesting a package is an
// ordinary enquiry (every enquiry rule, cap and block still applies) that
// carries the package id and a system note.
import { seg, type VyaparClient } from "../client";
import type { EnquiryDetail } from "../types";

export type PackageTier = "basic" | "standard" | "premium";

export interface ServicePackage {
  id: string;
  listing_id: string;
  tier: PackageTier;
  /** Localized tier name ("Basic"). */
  tier_label: string;
  /** Resolved to the viewer's language when the owner gave a variant. */
  name: string;
  description: string | null;
  price_paise: number;
  /** Server-formatted, e.g. "₹1,499". */
  price_label: string;
  delivery_days: number | null;
  revisions: number | null;
  includes: string[];
  sort: number;
  name_hi?: string | null;
  name_te?: string | null;
  description_hi?: string | null;
  description_te?: string | null;
  name_mr?: string | null;
  name_kn?: string | null;
  description_mr?: string | null;
  description_kn?: string | null;
}

export interface ServicePackageInput {
  tier: PackageTier;
  name: string;
  name_hi?: string | null;
  name_te?: string | null;
  description?: string | null;
  description_hi?: string | null;
  description_te?: string | null;
  name_mr?: string | null;
  name_kn?: string | null;
  description_mr?: string | null;
  description_kn?: string | null;
  price_paise: number;
  delivery_days?: number | null;
  revisions?: number | null;
  includes?: string[];
  sort?: number | null;
}

export interface PackageRequestResult {
  enquiry: EnquiryDetail & { id: string };
  package: ServicePackage;
}

export function packagesApi(c: VyaparClient) {
  const base = (listingId: string) => `/v1/listings/${seg(listingId)}/packages`;
  return {
    /** listListingPackages */
    list: (listingId: string) => c.get<ServicePackage[]>(base(listingId)),
    /** upsertListingPackages — upsert by tier; tiers not sent are kept */
    upsert: (listingId: string, packages: ServicePackageInput[]) => c.put<ServicePackage[]>(base(listingId), { packages }),
    /** deleteListingPackage */
    remove: (listingId: string, packageId: string) => c.delete<unknown>(`${base(listingId)}/${seg(packageId)}`),
    /** requestListingPackage — creates the enquiry; send an Idempotency-Key so a double tap sends one */
    request: (listingId: string, packageId: string, message: string, idempotencyKey?: string) =>
      c.post<PackageRequestResult>(`${base(listingId)}/${seg(packageId)}/request`, { message }, { idempotencyKey }),
  };
}

export type PackagesApi = ReturnType<typeof packagesApi>;
