import { Suspense } from "react";
import Today from "@/components/admin/Today";

export default function Page() {
  return (
    <Suspense>
      <Today />
    </Suspense>
  );
}
