import type { Metadata } from "next";
import AdminShell from "@/components/admin/AdminShell";
import "./admin.css";

// The Admin & Governance Console (ARCHITECTURE.md ADR-012): one console for the whole of
// ForKhatri, shown only to people the samaj has appointed. Never indexed.
export const metadata: Metadata = { title: "Admin · ForKhatri", robots: { index: false, follow: false } };

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <AdminShell>{children}</AdminShell>;
}
