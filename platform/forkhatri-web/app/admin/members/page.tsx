import { Suspense } from "react";
import Members from "@/components/admin/Members";

export default function Page() {
  return (
    <Suspense>
      <Members />
    </Suspense>
  );
}
