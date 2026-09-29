"use client";

// [Design language 2026-09-29, §7–8] Trade visuals: every category and
// specialty of GET /v1/taxonomy/tree has its own icon (lucide-react, ISC
// licence; original line icons, no photos of people), placed on a tile
// tinted by its FAMILY of work. The tint carries meaning (hands-on, on the
// move, food and care, office and money, tech and media, learning and
// wellbeing), so the same plug the Electricians tile shows is the icon on
// every electrician card: a person who cannot read "Electrician" still
// matches the card to the tile. An unknown specialty falls back to its
// category's icon, and an unknown category to a briefcase — a tile is
// never empty.
import type { LucideIcon } from "lucide-react";
import {
  AirVent, Aperture, BookOpen, Box, Briefcase, BrickWall, Brush, Cake, Calculator, Camera, Car, CarFront, ChefHat,
  Clapperboard, CodeXml, Cog, Construction, DraftingCompass, Flame, FlaskConical, Flower2, Gavel, GraduationCap,
  Grid3x3, Hammer, HardHat, Headset, House, IndianRupee, Keyboard, Landmark, Megaphone, Newspaper, Package,
  PaintRoller, Palette, PartyPopper, PenTool, Printer, Receipt, Rocket, Scale, Scissors, Shield, Shirt, ShoppingBag,
  Sigma, Sparkles, SprayCan, Sprout, Stethoscope, Store, Syringe, Truck, UserRound, UtensilsCrossed, Wrench, Zap,
  Plug, Layers, Boxes, Presentation, PhoneCall, ConciergeBell, Leaf,
} from "lucide-react";

export type Family = "amber" | "sky" | "green" | "indigo" | "plum" | "teal";

interface Visual {
  icon: LucideIcon;
  family: Family;
}

/** Category slug → icon and family. */
const CATEGORY: Record<string, Visual> = {
  accounting_tax: { icon: Calculator, family: "indigo" },
  automotive: { icon: Car, family: "amber" },
  beauty_personal_care: { icon: Sparkles, family: "teal" },
  design_architecture: { icon: DraftingCompass, family: "plum" },
  logistics: { icon: Truck, family: "sky" },
  education: { icon: GraduationCap, family: "teal" },
  events: { icon: PartyPopper, family: "teal" },
  food_catering: { icon: UtensilsCrossed, family: "green" },
  handicraft: { icon: Palette, family: "amber" },
  health_wellness: { icon: Leaf, family: "teal" },
  healthcare: { icon: Stethoscope, family: "green" },
  home_repair: { icon: Wrench, family: "amber" },
  hospitality_housekeeping: { icon: ConciergeBell, family: "green" },
  legal: { icon: Gavel, family: "indigo" },
  manufacturing_labour: { icon: HardHat, family: "amber" },
  marketing: { icon: Megaphone, family: "plum" },
  office_admin: { icon: Briefcase, family: "indigo" },
  media_photo: { icon: Camera, family: "plum" },
  printing: { icon: Printer, family: "amber" },
  sales_telecalling: { icon: Headset, family: "indigo" },
  software_it: { icon: CodeXml, family: "plum" },
  textiles_retail: { icon: Shirt, family: "teal" },
};

/** Specialty slug → [icon, category]. The family always comes from the category. */
const SPECIALTY: Record<string, [LucideIcon, string]> = {
  accountant: [Calculator, "accounting_tax"],
  accounting: [Sigma, "accounting_tax"],
  gst_filing: [Receipt, "accounting_tax"],
  tax: [IndianRupee, "accounting_tax"],
  car_repair: [CarFront, "automotive"],
  mechanic: [Cog, "automotive"],
  beautician: [Sparkles, "beauty_personal_care"],
  architecture: [DraftingCompass, "design_architecture"],
  interior_design: [House, "design_architecture"],
  delivery: [Package, "logistics"],
  driver: [Car, "logistics"],
  packer: [Boxes, "logistics"],
  mathematics: [Sigma, "education"],
  teacher: [Presentation, "education"],
  tutoring: [BookOpen, "education"],
  events: [PartyPopper, "events"],
  bakery: [Cake, "food_catering"],
  catering: [UtensilsCrossed, "food_catering"],
  cakes: [Cake, "food_catering"],
  handicraft: [Palette, "handicraft"],
  yoga: [Flower2, "health_wellness"],
  lab_technician: [FlaskConical, "healthcare"],
  nurse: [Syringe, "healthcare"],
  ac_technician: [AirVent, "home_repair"],
  carpenter: [Hammer, "home_repair"],
  electrical: [Plug, "home_repair"],
  mason: [BrickWall, "home_repair"],
  painter: [PaintRoller, "home_repair"],
  plumbing: [Wrench, "home_repair"],
  tile_fitter: [Grid3x3, "home_repair"],
  cook: [ChefHat, "hospitality_housekeeping"],
  maid: [SprayCan, "hospitality_housekeeping"],
  gardener: [Sprout, "hospitality_housekeeping"],
  housekeeping: [Brush, "hospitality_housekeeping"],
  security_guard: [Shield, "hospitality_housekeeping"],
  legal: [Scale, "legal"],
  property_law: [Landmark, "legal"],
  labourer: [Construction, "manufacturing_labour"],
  machine_operator: [Cog, "manufacturing_labour"],
  welder: [Flame, "manufacturing_labour"],
  content_writing: [Newspaper, "marketing"],
  digital_marketer: [Megaphone, "marketing"],
  social_media: [Layers, "marketing"],
  data_entry: [Keyboard, "office_admin"],
  office_assistant: [Briefcase, "office_admin"],
  receptionist: [UserRound, "office_admin"],
  graphic_designer: [PenTool, "media_photo"],
  photography: [Aperture, "media_photo"],
  video_editing: [Clapperboard, "media_photo"],
  printing: [Printer, "printing"],
  counter_sales: [Store, "sales_telecalling"],
  field_sales: [ShoppingBag, "sales_telecalling"],
  sales: [ShoppingBag, "sales_telecalling"],
  telecaller: [PhoneCall, "sales_telecalling"],
  product_management: [Layers, "software_it"],
  python: [CodeXml, "software_it"],
  react: [CodeXml, "software_it"],
  software: [CodeXml, "software_it"],
  startup: [Rocket, "software_it"],
  tailoring: [Scissors, "textiles_retail"],
  textiles: [Shirt, "textiles_retail"],
  wholesale: [Box, "textiles_retail"],
};

const FALLBACK: Visual = { icon: Briefcase, family: "indigo" };

export function categoryVisual(slug: string | null | undefined): Visual {
  return (slug && CATEGORY[slug]) || FALLBACK;
}

export function specialtyVisual(slug: string | null | undefined): Visual {
  const hit = slug ? SPECIALTY[slug] : undefined;
  if (!hit) return FALLBACK;
  return { icon: hit[0], family: categoryVisual(hit[1]).family };
}

/** The visual for a card: its first known skill, else a type-based default. */
export function cardVisual(skills: readonly string[] | undefined, type: string): Visual {
  for (const s of skills ?? []) if (SPECIALTY[s]) return specialtyVisual(s);
  if (type === "freelance") return { icon: CodeXml, family: "plum" };
  if (type === "training") return { icon: GraduationCap, family: "teal" };
  if (type === "community") return { icon: Zap, family: "teal" };
  if (type === "local_service") return { icon: Wrench, family: "amber" };
  return FALLBACK;
}

/**
 * The trade rail on Discover: the trades people look for most, as people
 * name them ("Electricians", "CA & tax"), each one a skill filter — a
 * specialty, or a whole category (every specialty in it). Labels are
 * explore:trades.<key> in en/hi/te.
 */
export interface RailTrade {
  key: string;
  icon: LucideIcon;
  family: Family;
  /** A specialty slug, or `cat:<category slug>` for the whole category. */
  target: string;
}

const t = (key: string, target: string): RailTrade => {
  const v = target.startsWith("cat:") ? categoryVisual(target.slice(4)) : specialtyVisual(target);
  return { key, icon: v.icon, family: v.family, target };
};

export const RAIL_TRADES: RailTrade[] = [
  t("electricians", "electrical"),
  t("plumbers", "plumbing"),
  t("delivery", "delivery"),
  t("drivers", "driver"),
  t("cooks", "cook"),
  t("housekeeping", "cat:hospitality_housekeeping"),
  t("security", "security_guard"),
  t("sales", "cat:sales_telecalling"),
  t("tailors", "tailoring"),
  t("beauticians", "beautician"),
  t("tutors", "cat:education"),
  t("caTax", "cat:accounting_tax"),
  t("developers", "cat:software_it"),
  t("designers", "cat:design_architecture"),
  t("media", "cat:media_photo"),
  t("office", "cat:office_admin"),
  t("carpenters", "carpenter"),
  t("painters", "painter"),
];
