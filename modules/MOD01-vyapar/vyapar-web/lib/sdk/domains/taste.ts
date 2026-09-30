// [Recommendations 2026-09-30] What Vyapar learned from what the member did
// (references/imp-recommendations.md): the learned preferences as readable
// items the member can remove one by one, or reset all at once.
import type { VyaparClient } from "../client";
import type { TasteResponse } from "../types";

export function tasteApi(c: VyaparClient) {
  return {
    /** getMyTaste */
    get: () => c.get<TasteResponse>("/v1/me/taste"),
    /** removeTasteItem — forget one learned item */
    remove: (id: string) => c.patch<TasteResponse>("/v1/me/taste", { remove: id }),
    /** resetMyTaste — forget everything learned */
    reset: () => c.delete<TasteResponse>("/v1/me/taste"),
  };
}

export type TasteApi = ReturnType<typeof tasteApi>;
