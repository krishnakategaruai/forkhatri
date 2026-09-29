import { Suspense } from "react";
import Queues from "@/components/admin/Queues";

export default function Page() {
  return (
    <Suspense>
      <Queues />
    </Suspense>
  );
}
