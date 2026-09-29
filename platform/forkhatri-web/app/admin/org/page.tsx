import { Suspense } from "react";
import Organisation from "@/components/admin/Organisation";

export default function Page() {
  return (
    <Suspense>
      <Organisation />
    </Suspense>
  );
}
