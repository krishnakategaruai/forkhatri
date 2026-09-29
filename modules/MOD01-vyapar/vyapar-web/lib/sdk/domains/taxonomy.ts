// [FE2 — imp-backend-a §4] The two-level taxonomy (category → specialty),
// each with a one-line plain-language description, localized by the server.
// Shared: FE1's hiring screens (useTaxonomyTree) and FE2's desktop
// Hire / Find work menu and outcome pages read the same domain.
import type { VyaparClient } from "../client";

export interface TaxonomySpecialty {
  slug: string;
  label: string;
  description?: string | null;
}

export interface TaxonomyCategory {
  slug: string;
  label: string;
  description?: string | null;
  icon?: string | null;
  children?: TaxonomySpecialty[];
}

export interface TaxonomyTree {
  language?: string;
  categories: TaxonomyCategory[];
}

export function taxonomyApi(c: VyaparClient) {
  return {
    /** getTaxonomyTree */
    tree: () => c.get<TaxonomyTree>("/v1/taxonomy/tree"),
  };
}

export type TaxonomyApi = ReturnType<typeof taxonomyApi>;
