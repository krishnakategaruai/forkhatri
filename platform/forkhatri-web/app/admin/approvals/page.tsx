import { Suspense } from "react";
import Approvals from "@/components/admin/Approvals";

export default function Page() {
  return (
    <Suspense>
      <Approvals />
    </Suspense>
  );
}
