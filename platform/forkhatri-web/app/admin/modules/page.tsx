import { Suspense } from "react";
import Modules from "@/components/admin/Modules";

export default function Page() {
  return (
    <Suspense>
      <Modules />
    </Suspense>
  );
}
