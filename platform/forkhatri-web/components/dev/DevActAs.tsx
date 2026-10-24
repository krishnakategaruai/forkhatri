"use client";

/**
 * DEVELOPMENT ONLY: "Act as" member switcher (docs/ParentApp/07-tech-reqs.md
 * "Development tools"). Loaded by Entrance.tsx through a guarded dynamic import
 * that the production build compiles out (NODE_ENV === "production"), and only
 * when NEXT_PUBLIC_DEV_TOOLS=true. Its text and styles live here, not in
 * lib/i18n.ts or the global CSS, so none of it reaches a production bundle.
 *
 * One tap: POST /dev/v1/sessions (sets the normal session cookie) and reload.
 * Renders nothing when the identity service has not mounted /dev/v1.
 */
import { useEffect, useId, useState } from "react";
import { IDENTITY_API, type Lang } from "@/lib/api";
import styles from "./DevActAs.module.css";

type Persona = {
  key: string;
  member_id: string;
  display_name: string;
  description: string;
  for_automated_tests: boolean;
};

const TEXT = {
  en: {
    heading: "Act as (development)",
    link: "Development: act as…",
    hide: "Hide",
    current: "Current",
    switching: "Switching…",
    failed: "Couldn't switch. Check that the identity service runs with DEV_TOOLS_ENABLED=true.",
    note: "Signs this browser in as a development member, without a password. Automated tests never use Krishna.",
    "p:krishna": "Owner's account. Not for automated tests.",
    "p:asha": "Data in Mangalya and Milavn",
    "p:new-member": "Fresh, no module data",
    "p:mangaly-family": "Home Circle family member in Mangalya",
    "p:mangaly-parent": "Ananya's mother, family member in Mangalya (not a candidate)",
    "p:milavn-moderator": "Moderator in Milavn",
  },
  hi: {
    heading: "इस सदस्य के रूप में (डेवलपमेंट)",
    link: "डेवलपमेंट: इस सदस्य के रूप में…",
    hide: "छिपाएँ",
    current: "अभी",
    switching: "बदल रहे हैं…",
    failed: "सदस्य नहीं बदल सका। जाँचें कि पहचान सेवा DEV_TOOLS_ENABLED=true के साथ चल रही है।",
    note: "बिना पासवर्ड इस ब्राउज़र को एक डेवलपमेंट सदस्य के रूप में साइन इन करता है। स्वचालित टेस्ट कभी Krishna का उपयोग नहीं करते।",
    "p:krishna": "मालिक का खाता। स्वचालित टेस्ट के लिए नहीं।",
    "p:asha": "Mangalya और Milavn में डेटा",
    "p:new-member": "नया सदस्य, किसी मॉड्यूल में डेटा नहीं",
    "p:mangaly-family": "Mangalya में होम सर्कल का परिवार सदस्य",
    "p:mangaly-parent": "अनन्या की माँ, Mangalya में परिवार सदस्य (उम्मीदवार नहीं)",
    "p:milavn-moderator": "Milavn में मॉडरेटर",
  },
  te: {
    heading: "ఈ సభ్యుడిగా (డెవలప్‌మెంట్)",
    link: "డెవలప్‌మెంట్: ఈ సభ్యుడిగా…",
    hide: "దాచండి",
    current: "ప్రస్తుతం",
    switching: "మారుస్తోంది…",
    failed: "సభ్యుడిని మార్చలేకపోయాం. గుర్తింపు సేవ DEV_TOOLS_ENABLED=true తో నడుస్తోందో చూడండి.",
    note: "పాస్‌వర్డ్ లేకుండా ఈ బ్రౌజర్‌ను డెవలప్‌మెంట్ సభ్యుడిగా సైన్ ఇన్ చేస్తుంది. ఆటోమేటెడ్ టెస్టులు Krishna ను ఎప్పుడూ వాడవు.",
    "p:krishna": "యజమాని ఖాతా. ఆటోమేటెడ్ టెస్టులకు కాదు.",
    "p:asha": "Mangalya, Milavn లో డేటా",
    "p:new-member": "కొత్త సభ్యుడు, మాడ్యూల్ డేటా లేదు",
    "p:mangaly-family": "Mangalya లో హోమ్ సర్కిల్ కుటుంబ సభ్యుడు",
    "p:mangaly-parent": "అనన్య తల్లి, Mangalya లో కుటుంబ సభ్యురాలు (అభ్యర్థి కాదు)",
    "p:milavn-moderator": "Milavn లో మోడరేటర్",
  },
  mr: {
    heading: "या सदस्याच्या रूपात (डेव्हलपमेंट)",
    link: "डेव्हलपमेंट: या सदस्याच्या रूपात…",
    hide: "लपवा",
    current: "सध्या",
    switching: "बदलत आहोत…",
    failed: "सदस्य बदलता आला नाही. ओळख सेवा DEV_TOOLS_ENABLED=true सह चालू आहे का ते तपासा.",
    note: "पासवर्डशिवाय हा ब्राउझर एका डेव्हलपमेंट सदस्याच्या रूपात साइन इन करतो. स्वयंचलित चाचण्या Krishna यांचे खाते कधीच वापरत नाहीत.",
    "p:krishna": "मालकांचे खाते. स्वयंचलित चाचण्यांसाठी नाही.",
    "p:asha": "Mangalya आणि Milavn मध्ये डेटा",
    "p:new-member": "नवीन सदस्य, कोणत्याही मॉड्यूलमध्ये डेटा नाही",
    "p:mangaly-family": "Mangalya मध्ये होम सर्कलमधील कुटुंब सदस्य",
    "p:mangaly-parent": "अनन्याची आई, Mangalya मध्ये कुटुंब सदस्य (उमेदवार नाही)",
    "p:milavn-moderator": "Milavn मध्ये मॉडरेटर",
  },
  kn: {
    heading: "ಈ ಸದಸ್ಯರಾಗಿ (ಡೆವಲಪ್‌ಮೆಂಟ್)",
    link: "ಡೆವಲಪ್‌ಮೆಂಟ್: ಈ ಸದಸ್ಯರಾಗಿ…",
    hide: "ಮರೆಮಾಡಿ",
    current: "ಪ್ರಸ್ತುತ",
    switching: "ಬದಲಾಯಿಸಲಾಗುತ್ತಿದೆ…",
    failed: "ಸದಸ್ಯರನ್ನು ಬದಲಾಯಿಸಲು ಆಗಲಿಲ್ಲ. ಗುರುತಿನ ಸೇವೆ DEV_TOOLS_ENABLED=true ಜೊತೆ ನಡೆಯುತ್ತಿದೆಯೇ ಎಂದು ಪರಿಶೀಲಿಸಿ.",
    note: "ಪಾಸ್‌ವರ್ಡ್ ಇಲ್ಲದೆ ಈ ಬ್ರೌಸರ್ ಅನ್ನು ಡೆವಲಪ್‌ಮೆಂಟ್ ಸದಸ್ಯರಾಗಿ ಸೈನ್ ಇನ್ ಮಾಡುತ್ತದೆ. ಸ್ವಯಂಚಾಲಿತ ಪರೀಕ್ಷೆಗಳು Krishna ಅವರ ಖಾತೆಯನ್ನು ಎಂದಿಗೂ ಬಳಸುವುದಿಲ್ಲ.",
    "p:krishna": "ಮಾಲೀಕರ ಖಾತೆ. ಸ್ವಯಂಚಾಲಿತ ಪರೀಕ್ಷೆಗಳಿಗೆ ಅಲ್ಲ.",
    "p:asha": "Mangalya ಮತ್ತು Milavn ನಲ್ಲಿ ಡೇಟಾ",
    "p:new-member": "ಹೊಸ ಸದಸ್ಯರು, ಯಾವುದೇ ಮಾಡ್ಯೂಲ್ ಡೇಟಾ ಇಲ್ಲ",
    "p:mangaly-family": "Mangalya ದಲ್ಲಿ ಹೋಮ್ ಸರ್ಕಲ್‌ನ ಕುಟುಂಬ ಸದಸ್ಯರು",
    "p:mangaly-parent": "ಅನನ್ಯ ಅವರ ತಾಯಿ, Mangalya ದಲ್ಲಿ ಕುಟುಂಬ ಸದಸ್ಯರು (ಅಭ್ಯರ್ಥಿ ಅಲ್ಲ)",
    "p:milavn-moderator": "Milavn ನಲ್ಲಿ ಮಾಡರೇಟರ್",
  },
} satisfies Record<Lang, Record<string, string>>;

type DevActAsProps = {
  lang: Lang;
  /** The signed-in member, or null on the signed-out arrival screen. */
  currentMemberId: string | null;
  variant: "sheet" | "arrival";
};

export default function DevActAs({ lang, currentMemberId, variant }: DevActAsProps) {
  const text = TEXT[lang] ?? TEXT.en;
  const headingId = useId();
  const [personas, setPersonas] = useState<Persona[] | null>(null);
  const [open, setOpen] = useState(variant === "sheet");
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${IDENTITY_API}/dev/v1/personas`, { credentials: "include", cache: "no-store", signal: controller.signal })
      .then((response) => (response.ok ? (response.json() as Promise<Persona[]>) : null))
      .then((list) => setPersonas(list && list.length ? list : null))
      .catch(() => setPersonas(null));
    return () => controller.abort();
  }, []);

  if (!personas) return null;

  async function actAs(persona: Persona) {
    if (busyKey || persona.member_id === currentMemberId) return;
    setBusyKey(persona.key);
    setFailed(false);
    try {
      const response = await fetch(`${IDENTITY_API}/dev/v1/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ persona: persona.key }),
        credentials: "include",
        cache: "no-store",
      });
      if (!response.ok) throw new Error(`dev session ${response.status}`);
      window.location.reload();
    } catch {
      setBusyKey(null);
      setFailed(true);
    }
  }

  const describe = (persona: Persona) => (text as Record<string, string>)[`p:${persona.key}`] ?? persona.description;

  const panel = (
    <section className={variant === "sheet" ? styles.section : styles.panel} aria-labelledby={headingId} data-dev-act-as={variant}>
      <p id={headingId} className={styles.heading}>
        {text.heading}
      </p>
      <div className={styles.grid} role="group" aria-labelledby={headingId}>
        {personas.map((persona) => {
          const current = persona.member_id === currentMemberId;
          return (
            <button
              key={persona.key}
              type="button"
              className={styles.persona}
              aria-pressed={current}
              data-persona={persona.key}
              disabled={busyKey !== null}
              onClick={() => void actAs(persona)}
            >
              <span className={styles.name}>
                {persona.display_name}
                {current && <span className={styles.current}> · {text.current}</span>}
              </span>
              <span className={styles.desc}>{busyKey === persona.key ? text.switching : describe(persona)}</span>
            </button>
          );
        })}
      </div>
      <p className={failed ? styles.error : styles.note} role={failed ? "alert" : undefined}>
        {failed ? text.failed : text.note}
      </p>
    </section>
  );

  if (variant === "sheet") return panel;

  return (
    <div className={styles.dock}>
      {open && panel}
      <button type="button" className={styles.link} aria-expanded={open} onClick={() => setOpen((value) => !value)}>
        {open ? text.hide : text.link}
      </button>
    </div>
  );
}
