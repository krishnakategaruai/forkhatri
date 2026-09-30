"use client";

// [Owner, 2026-09-30: "each user will get one profile"] There is no list of
// profiles any more: the member's one profile (and its optional business
// section) lives on /profile. Old links to "My profiles" (Businesses,
// promotions, apply) land there.
// Traces to: FR01, FR03, FR04
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";

export default function MyListingsPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/profile");
  }, [router]);
  return (
    <Screen>
      <SkeletonGrid count={2} grid={false} />
    </Screen>
  );
}
