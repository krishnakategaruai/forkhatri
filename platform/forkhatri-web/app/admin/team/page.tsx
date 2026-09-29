import { Suspense } from "react";
import Team from "@/components/admin/Team";

export default function Page() {
  return (
    <Suspense>
      <Team />
    </Suspense>
  );
}
