import type { Metadata } from "next";
import Insights from "@/components/insights/Insights";
import "./insights.css";

// Members dashboard: open to every signed-in member (owner, 2026-09-27).
export const metadata: Metadata = { title: "Members · ForKhatri" };

export default function InsightsPage() {
  return <Insights />;
}
