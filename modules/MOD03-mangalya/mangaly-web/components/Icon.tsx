"use client";

/* Mangalya's one icon language (DEC-V1-030, critique agent + owner,
 * 2026-09-25). Every icon comes from a single set — Phosphor, "light"
 * weight (a 1.5px stroke on a 24px grid, round caps and joins) — so glyphs
 * never mix weights or styles. Icons inherit their colour from the text
 * beside them; "fill" is used only for an active navigation item or a
 * toggled state (a saved bookmark). Sizes: 16 inline, 20 for navigation,
 * headers and actions, 28+ only for empty states. No containers: a circle
 * of colour behind an icon is never used at rest. */

import {
  ArrowLeft,
  Briefcase,
  Handshake,
  ArrowsLeftRight,
  BookmarkSimple,
  BookOpenText,
  FlowerLotus,
  Globe,
  MapPin,
  Phone,
  PlayCircle,
  Tag,
  Camera,
  CaretRight,
  ChatCircle,
  ChatsCircle,
  DotsThree,
  Eye,
  GearSix,
  Heart,
  House,
  List,
  Lock,
  MagnifyingGlass,
  NotePencil,
  PencilSimple,
  Plus,
  SealCheck,
  SquaresFour,
  User,
  UserPlus,
  UsersThree,
  X,
} from "@phosphor-icons/react";

const SET = {
  back: ArrowLeft,
  briefcase: Briefcase,
  handshake: Handshake,
  bookmark: BookmarkSimple,
  camera: Camera,
  caretRight: CaretRight,
  swap: ArrowsLeftRight,
  eye: Eye,
  edit: PencilSimple,
  chat: ChatCircle,
  chats: ChatsCircle,
  more: DotsThree,
  settings: GearSix,
  heart: Heart,
  home: House,
  menu: List,
  lock: Lock,
  search: MagnifyingGlass,
  compose: NotePencil,
  plus: Plus,
  verified: SealCheck,
  hub: SquaresFour,
  me: User,
  invite: UserPlus,
  family: UsersThree,
  close: X,
  wedding: FlowerLotus,
  guides: BookOpenText,
  pin: MapPin,
  phone: Phone,
  web: Globe,
  play: PlayCircle,
  offer: Tag,
} as const;

export type IconName = keyof typeof SET;

export default function Icon({
  name,
  size = 20,
  filled = false,
  className,
  label,
}: {
  name: IconName;
  size?: 16 | 20 | 28 | 40;
  filled?: boolean;
  className?: string;
  /** Only when the icon carries meaning on its own; otherwise decorative. */
  label?: string;
}) {
  const Glyph = SET[name];
  return (
    <Glyph
      size={size}
      weight={filled ? "fill" : "light"}
      className={`icon${className ? ` ${className}` : ""}`}
      aria-hidden={label ? undefined : true}
      aria-label={label}
      role={label ? "img" : undefined}
    />
  );
}
