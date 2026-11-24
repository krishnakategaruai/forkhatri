/* [D12, 2026-10-06] The profile being made is saved on this device at every
 * step — answers, chosen photos and an attached biodata — and resumed on the
 * next visit. Nothing reaches the server until the family publishes, so a
 * child's details are never stored by Mangalya before then (critique C3).
 *
 * IndexedDB, because photos are Blobs (localStorage holds only strings and
 * a few megabytes). One draft per signed-in member, so two people sharing a
 * phone never see each other's draft. Every call fails soft: a browser with
 * storage switched off simply keeps the answers in memory, as before. */

const DB_NAME = "mangalya-drafts";
const STORE = "profile";

export type DraftFile = { blob: Blob; name: string; type: string };

export type ProfileDraft = {
  forWhom: string;
  step: number;
  name: string;
  dobDay: string;
  dobMonth: string;
  dobYear: string;
  gender: string;
  lookingFor: string;
  cityLocality: string;
  educationLevel: string;
  educationOther: string;
  occupation: string;
  maritalStatus: string;
  relocation: string;
  childPhone: string;
  relation: string | null;
  photos: DraftFile[];
  biodata: DraftFile | null;
  attachBiodata: boolean;
  /** Extra facts read from a biodata, saved to the profile after publish. */
  extras: Record<string, string | number>;
  savedAt: number;
};

function open(): Promise<IDBDatabase | null> {
  return new Promise((resolve) => {
    try {
      if (typeof indexedDB === "undefined") return resolve(null);
      const req = indexedDB.open(DB_NAME, 1);
      req.onupgradeneeded = () => {
        if (!req.result.objectStoreNames.contains(STORE)) req.result.createObjectStore(STORE);
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(null);
      req.onblocked = () => resolve(null);
    } catch {
      resolve(null);
    }
  });
}

async function run<T>(mode: IDBTransactionMode, fn: (s: IDBObjectStore) => IDBRequest<T>): Promise<T | null> {
  const db = await open();
  if (!db) return null;
  return new Promise((resolve) => {
    try {
      const tx = db.transaction(STORE, mode);
      const req = fn(tx.objectStore(STORE));
      req.onsuccess = () => resolve(req.result ?? null);
      req.onerror = () => resolve(null);
      tx.oncomplete = () => db.close();
    } catch {
      resolve(null);
    }
  });
}

/* A member can keep several drafts at once (a brother's, a daughter's, their
 * own). The first keeps the plain member key; later ones add "#<id>". */
export function newDraftKey(memberKey: string): string {
  return `${memberKey}#${Date.now().toString(36)}`;
}

export async function listDrafts(memberKey: string): Promise<{ key: string; draft: ProfileDraft }[]> {
  const db = await open();
  if (!db) return [];
  return new Promise((resolve) => {
    const out: { key: string; draft: ProfileDraft }[] = [];
    try {
      const tx = db.transaction(STORE, "readonly");
      const req = tx.objectStore(STORE).openCursor();
      req.onsuccess = () => {
        const cur = req.result;
        if (!cur) return;
        const key = String(cur.key);
        const d = cur.value as ProfileDraft;
        if ((key === memberKey || key.startsWith(`${memberKey}#`)) && d && typeof d === "object" && "forWhom" in d) {
          out.push({ key, draft: d });
        }
        cur.continue();
      };
      req.onerror = () => resolve([]);
      tx.oncomplete = () => {
        db.close();
        resolve(out.sort((a, b) => b.draft.savedAt - a.draft.savedAt));
      };
    } catch {
      resolve([]);
    }
  });
}

export async function loadDraft(memberKey: string): Promise<ProfileDraft | null> {
  const d = await run<ProfileDraft>("readonly", (s) => s.get(memberKey) as IDBRequest<ProfileDraft>);
  return d && typeof d === "object" && "forWhom" in d ? d : null;
}

export async function saveDraft(memberKey: string, draft: ProfileDraft): Promise<boolean> {
  return (await run("readwrite", (s) => s.put(draft, memberKey))) !== null;
}

export async function clearDraft(memberKey: string): Promise<void> {
  await run("readwrite", (s) => s.delete(memberKey));
}

/** Clear every locally saved profile draft after the member deletes their data. */
export async function clearAllDrafts(): Promise<void> {
  await run("readwrite", (s) => s.clear());
}
