/* One line icon per activity category (intent_category enum: play, meet, eat,
 * learn, work, explore, celebrate, help, professional). Replaces the emoji that used to
 * stand in for icons — lucide at 20px / stroke 1.75 like the rest of the app. */

import { Activity, BookOpen, Briefcase, Coffee, HandHeart, Mountain, PartyPopper, Presentation, Sparkles, Utensils, type LucideIcon } from 'lucide-react';

export const CATEGORY_ICONS: Record<string, LucideIcon> = {
  play: Activity,
  meet: Coffee,
  eat: Utensils,
  learn: BookOpen,
  work: Briefcase,
  explore: Mountain,
  celebrate: PartyPopper,
  help: HandHeart,
  professional: Presentation,
};

export default function CategoryIcon({ category, size = 20, strokeWidth = 1.75, className }: { category: string | null | undefined; size?: number; strokeWidth?: number; className?: string }) {
  const Icon = (category && CATEGORY_ICONS[category]) || Sparkles;
  return <Icon size={size} strokeWidth={strokeWidth} className={className} aria-hidden="true" />;
}
