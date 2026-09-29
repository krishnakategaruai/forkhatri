// [FE2 — research §5] Outcome landing pages: what a person wants done, in
// their own words, mapped onto the real taxonomy. Each outcome names the
// specialties that do it (slugs from GET /v1/taxonomy/tree), the category
// to search profiles in, and the kind of post "Post this" should start
// (the composer reads ?type=&skills=). Copy lives in locales/*/explore.json
// under outcome.<slug>.
export interface Outcome {
  slug: string;
  /** Opportunity type the "Post this" button starts. */
  type: "employment" | "freelance" | "local_service";
  category: string;
  skills: string[];
}

export const OUTCOMES: Outcome[] = [
  { slug: "hire-shop-staff", type: "employment", category: "sales_telecalling", skills: ["counter_sales", "sales", "housekeeping", "security_guard", "data_entry"] },
  { slug: "home-repair", type: "local_service", category: "home_repair", skills: ["electrical", "plumbing", "carpenter", "painter", "ac_technician"] },
  { slug: "build-website", type: "freelance", category: "software_it", skills: ["software", "react", "python", "graphic_designer"] },
  { slug: "cater-event", type: "local_service", category: "food_catering", skills: ["catering", "cook", "cakes", "bakery", "events"] },
  { slug: "gst-accounts", type: "freelance", category: "accounting_tax", skills: ["gst_filing", "accounting", "accountant", "tax"] },
  { slug: "market-business", type: "freelance", category: "marketing", skills: ["digital_marketer", "social_media", "content_writing", "graphic_designer", "photography"] },
];

export function outcomeBySlug(slug: string): Outcome | undefined {
  return OUTCOMES.find((o) => o.slug === slug);
}

export function postHref(o: Outcome): string {
  return `/opportunities/new?type=${o.type}&skills=${o.skills.join(",")}`;
}
