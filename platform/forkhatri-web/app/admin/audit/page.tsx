import { Suspense } from "react";
import AuditLog from "@/components/admin/AuditLog";

export default function Page() {
  return (
    <Suspense>
      <AuditLog />
    </Suspense>
  );
}
