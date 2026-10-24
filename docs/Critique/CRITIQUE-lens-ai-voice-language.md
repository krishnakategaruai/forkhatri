# Critique: AI, voice and language across ForKhatri

Lens author: critic-ai. Date: 2026-10-06. Read-only review. I read the AI code in every module, then tried the live screens and endpoints as Asha (never Krishna) and wrote nothing.

How I checked, and its limits. The web-search quota for the session was already used up by the team, so evidence comes from arXiv (its API), MDN, caniuse, Anthropic's pricing page, Sarvam's pricing page and Wikipedia. Reddit and other social sites were blocked. I therefore have **no quoted user opinions**; I will not invent any. Items marked "unverified" are things I know but could not confirm in this session.

## 1. Understanding (please correct me)

ForKhatri's AI today is four different things, not one. (a) The signed-in hub box "What would you like to do?" is a client-side keyword table (`platform/forkhatri-web/lib/intent.ts`); it says plainly "no network and no AI call". (b) Milavn's Ask bar and smart-fill (`discovery/nl.py`) are a deterministic grammar over English/Hindi/Telugu words, deliberately never AI. (c) Mangalya's matchmaker (`compatibility/understand.py`) sends the family's words to Claude (default `claude-opus-5`) and validates the answer against a closed vocabulary; the "AI match score" is then plain weighted arithmetic (importance-weighted fit, harmonic mean of both sides, hidden number, word label plus reasons). Counsel (`ai.py`) and Vyapar (`integrations/ai/*`, `voice_interview.py`) have Claude behind a keyword fallback; Vyapar adds a per-member daily cap, redaction and an audit row. Voice is the browser's Web Speech API for listening and speaking. Every API key in dev is a placeholder, so **everything I tried ran the fallback, not the AI**. The "premium tier gets AI" gating is not built (memory note, 2026-10-02): AI turns on only when a key is set.

## 2. Test record (live, Asha, rules mode)

| Where | Input | What came back |
|---|---|---|
| Hub | "my father needs a lawyer for property dispute", "bathukamma near me", "rishta chahiye" | Correct module |
| Hub | मुझे वकील चाहिए; నాకు లాయర్ కావాలి; नौकरी; ఉద్యోగం; दुकान; వరుడు కావాలి; वर चाहिए; అప్పు కావాలి | "Not sure yet. Try words like yoga, plumber or rishta." (every one) |
| Hub | "shaadi", "dulha", "plumbr", "lawer", "kirket", "Mangalya", "milavn" | Not understood (even module names) |
| Hub | "gst consultant near me this weekend" | Milavn activity (wrong; "weekend/near me" outvote GST) |
| Hub | "I want to die"; "my mother has cancer need doctor" | "Not sure yet" and no help offered |
| Milavn understand | రేపు సాయంత్రం బ్యాడ్మింటన్; "ladies only yoga"; "women only trek" | Telugu activity ignored; the women-only condition silently dropped |
| Milavn smart-fill | "Diwali get together ... on 20 october 7pm, 30 people" | Draft time = **today 19:00** (the date was ignored) |
| Milavn smart-fill | "kal shaam 6 baje cricket Gachibowli" | Time = today (kal is ambiguous), place not found, title is the raw sentence |
| Counsel understand | "I want to end my life" | Returns a CA and a lawyer |
| Counsel understand | "my son is depressed and talks about suicide" | A counsellor card, no helpline |
| Counsel understand | "my husband beats me, what legal options" | A lawyer only |
| Counsel understand | मेरे पिता को ज़मीन के झगड़े के लिए वकील चाहिए; mere papa ko vakil chahiye jameen ka jhagda | Area empty, no result |
| Mangalya understand | "Strict vegetarian, Hyderabad or Bengaluru..." | Importance 7 ("strict" not read as firm) |
| Mangalya understand | "sirf Khatri ... Hyderabad ya Bangalore"; హైదరాబాద్ alone | "Bangalore" and Telugu city names not resolved; "sirf" read as 7 not 10 |
| Mangalya understand | "own caste only, earning above 20 lakhs, no smoking, no drinking, own house, no dowry" | Only smoking and drinking kept; the rest vanished with no note |
| Vyapar search | प्लंబర / ప్లంబర్ / bijli wala / ameerpet | Works in all scripts; "plumbr" and "tiffin" find nothing |
| Voice | Windows Chrome | `SpeechRecognition` present; installed voices: **en-US and en-IN only**, no hi-IN or te-IN |

## 3. Critiques, ranked

### Critical

**1. Safety: a person in crisis gets a keyword shrug or a wrong referral.** Evidence: the rows above. Research: safeguards in eight LLMs "hold reliably only for suicide and self-harm" in the tested setting (arXiv 2606.23884, 2026-07-01); failing to discourage self-harm rises from 30.0% to 41.1% as conversation context lengthens (2608.05004, 2026-08-05); IndicSafe finds cross-language safety agreement of just 12.8% across 12 Indic languages (2603.17915, 2026-03-18). Why it matters: Counsel markets mental health and legal help; the hub is the front door. Do: one shared "sensitive-input" interceptor (suicide, abuse, violence, medical emergency) in en/hi/te that shows verified helplines (Tele-MANAS 14416, women's helpline 181, emergency 112; numbers unverified in this session, confirm before shipping) before any search result. Effort M.

**2. Silent wrong understanding is worse than "I didn't get it".** The Milavn draft with a wrong date, the dropped "women only", Mangalya wishes that vanish. Do: every module shows "We could not use: ..." and refuses to guess dates (explicit dates win; "kal" asks yesterday/tomorrow). Effort S-M.

### High

**3. Hindi and Telugu are second-class in the non-AI path, which is what most users will get.** Because AI is premium, the free tier IS the keyword tables. Native-script phrases for lawyer, job, shop, loan, groom all fail on the hub; Counsel's Hindi area hints stop at "कानून". Vyapar shows the fix already exists in-house (its vocab handles Devanagari and Telugu). Do: a shared multilingual lexicon in the integrations utility, used by hub, Counsel and Mangalya; plus fuzzy/phonetic matching for romanised input. Effort M.

**4. Premium-only AI collides with the owner's own Hindi/Telugu and voice rules.** Comprehension of one's own language is not a luxury feature for the Samaj's elders. Cheap models make "AI for everyone, depth for premium" affordable (see 8). Do: gate depth (explanations, bulk shortlisting, drafts), not basic understanding. Effort S (policy).

**5. Privacy and DPDP exposure is undocumented.** Evidence: Mangalya and Counsel send raw text with no redaction (Vyapar redacts phones/emails); Counsel's `summarise` sends up to 8,000 characters of consultation notes (legal, health) to Claude; the Mangalya voice code comment says "Nothing is uploaded", but MDN states that in Chrome audio "is sent to a web service for recognition" (developer.mozilla.org, SpeechRecognition, fetched 2026-10-06; `processLocally` exists as an option). I found no privacy copy naming an AI or speech processor. DPDP Rules were notified 14 Nov 2025 and cross-border provisions reportedly start 13 Nov 2026 (Wikipedia summary, secondary; read the primary text). Family wishes carry caste, religion, horoscope and health habits. Do: processor list in privacy notice (en/hi/te), consent line before first AI/voice use, shared redaction, remove the false code comment. Effort M.

**6. Voice is built on the weakest foundation.** (a) caniuse: recognition is partial on Chrome, Safari, Samsung; Firefox off by default (2026-10-06). The mic is hidden where unsupported, so low-end Android WebViews and in-app browsers (a WhatsApp link opens in one) silently lose the owner's flagship feature. (b) My Windows Chrome could not speak Hindi or Telugu at all; the code then shows text only, which is honest, but it defeats "the app asks aloud". (c) Accuracy is unmeasured: the best published Indian field benchmark I found reports Hindi 16.2% WER and much worse on noisy multi-speaker audio (arXiv 2602.03868, 2026-01-31); Telugu dialect effects I could not find (unverified). Do: measure WER on 50 real elder recordings in Telangana and Andhra accents; add a server speech option (Sarvam lists speech-to-text at ₹30/hour and text-to-speech at ₹3/1,000 characters, sarvam.ai/api-pricing, 2026-10-06, so a 3-minute interview costs about ₹1.5 to listen). Effort M-L.

**7. Caste bias will arrive the moment an LLM is allowed to judge, explain or rank.** Today the design is wise: Claude only parses, validated against a closed vocabulary, and "fair/slim" is dropped. But research shows LLMs rate same-caste matches up to 25% higher (Sima AIunty, arXiv 2603.29288, 2026-03-31) and implicit bias is over six times explicit bias (ImplicitBBQ 2604.01925, 2026-04-02). Also hobbies are free-text tags, and `sub_community` can be a hard "must". Do: write the rule "AI parses, never rates people", add a bias test set, and tell families visibly what is never used (colour, dowry). Effort S-M.

**8. Cost and abuse are unplanned.** Mangalya defaults to `claude-opus-5` ($5/$25 per million tokens; Sonnet 5 is $2/$10, Haiku 4.5 $1/$5; platform.claude.com pricing, 2026-10-06) for a task a small model does. My estimate (unverified, depends on prompt length): about $0.02 per call on Opus 5 versus under $0.01 on Sonnet 5 and cheaper with prompt caching (cache reads at 0.1x). The 40/day cap means a single member could cost about $24 a month. Counsel's `/understand` is public, unauthenticated and has no rate limit once AI is on (OWASP LLM10 "Unbounded Consumption"). Newer Claude tokenizers add about 30% tokens, and Indian scripts cost more again (a study measured an 8x average "tokenizer tax" for Indian languages on GPT's cl100k tokenizer, arXiv 2607.24276, 2026-07-27; Claude figures unverified). Do: Sonnet/Haiku, caching, auth and per-member budgets in one gateway. Effort S.

**9. No evaluation set for AI mode.** Nobody has seen Claude's output on Telugu or Hinglish wishes in this repo; MILU shows LLMs trail on low-resource Indic languages and on Law and Humanities (arXiv 2411.02538, 2024-11-04). Do: 200 golden phrases per language per module, run on every model change. Effort M.

### Medium

**10. Advice hallucination risk (Counsel).** On Indian Contract Act cases a leading model had a 31.7% high-confidence error rate (arXiv 2608.21089, 2026-08-21); hallucinated precedents persist (2605.14665, 2026-05-14). Counsel confines AI to routing and note-summary, which is right. Gaps: the summary has no "AI-written, check with your expert" label and no provider review before it is shared. Effort S.

**11. Five separate AI integrations, no shared policy.** Vyapar has a provider seam; Mangalya calls the SDK with a beta fallback header; Counsel uses raw HTTP with another API version; Milavn and the hub have none. This contradicts the owner's "shared capability over bespoke" rule. Do: one AI gateway (redaction, consent flag, tier, budget, audit, model routing, crisis check). Effort M-L.

**12. Prompt-injection posture is decent but untested in AI mode.** Good: closed schemas, "treat as data". Gaps: Counsel puts user text inside the instruction string, and its area slugs from the model are not validated against its list; Vyapar's shortlist reads applicant text that could say "rank me 10". I could not test with AI on. OWASP LLM01 and LLM09 apply. Effort S.

**13. Hindi/Telugu copy: complete but not proven respectful.** Mechanical check: 0 missing keys in Mangalya (2,285) and Vyapar (2,710), and no informal pronouns (तुम, నువ్వు) found. But Vyapar's Telugu transliterates English ("ప్రపోజల్స్", "రేటు రిక్వెస్ట్‌లు", "ప్రమోషన్") against the owner's rule, and a developer string ("build.foundationsBlurb") sits in a user locale. No evidence of a native-reader review loop. Do: glossary plus a paid reviewer. Effort S-M.

**14. Vyapar drafting gaps and bias.** With a stub vocabulary the rules drafter misread Devanagari digits (१५०००), took "चाहिए अमीरपेट" as the place and "పేట్" for a Telugu place (re-run against real vocab before trusting), and let "Female only receptionist, age below 25, good looking, unmarried" through unflagged. Salary and bid-range suggestions inherit LLM demographic skew: outputs differ by 20.2% on average when only caste, religion or region changes (RupeeBias, arXiv 2609.31245, 2026-09-25). Effort S-M.

**15. "AI" naming and explainability.** The 1-10 score is weighted arithmetic over parsed items; saying "AI matching" suggests learning that does not exist (popularity weight is 0 by design). "Intelligent matching" in plain words is fine, but avoid implying personalisation or accuracy. A hidden number driving order is opaque to anyone who asks "why am I never shown?". Do: a "Why this order" line, and a mutual-fairness check of who is never shown (reciprocal recommenders concentrate exposure; Nash-welfare methods cut inequality, arXiv 2601.13609, 2026-01-20; popularity feedback loops 2508.01867). Effort M.

**16. The audience's voice channel is probably WhatsApp, not a web page.** I could not verify market data (unverified), but WhatsApp voice notes are the likely habit of the target elders, and the owner already plans WhatsApp via the integrations utility. Do: design the guided interview so it can run as a WhatsApp or phone-call flow later. Effort L.

## 4. New in the world

- LLM caste audit of matchmaking: https://arxiv.org/abs/2603.29288 (2026-03-31), and "Redirected, Not Removed" https://arxiv.org/abs/2604.02669 (models refuse explicit caste decisions but stereotype implicitly).
- Reciprocal-recommender fairness: https://arxiv.org/abs/2601.13609, https://arxiv.org/abs/2508.01867.
- IndicSafe safety benchmark: https://arxiv.org/abs/2603.17915.
- Sarvam: Saaras V3 speech-to-text, 105B model (Feb 2026), pay-as-you-go APIs: https://www.sarvam.ai/api-pricing, https://en.wikipedia.org/wiki/Sarvam_AI. Bhashini: 300+ models via open APIs: https://en.wikipedia.org/wiki/Bhashini.
- Web Speech `processLocally` on-device option: https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition.
- Claude pricing: Sonnet 5.5 $2/$10, batch half price, caching 0.1x, US-only inference option at 1.1x (no India region listed): https://platform.claude.com/docs/en/about-claude/pricing.
- India: IT Rules amendment on synthetic content, effective 2026-02-20 (https://en.wikipedia.org/wiki/Regulation_of_artificial_intelligence); DPDP Rules notified 2025-11-14 (https://en.wikipedia.org/wiki/Digital_Personal_Data_Protection_Rules,_2025). Secondary sources; verify with MeitY texts.
- OWASP LLM Top 10 2025: https://genai.owasp.org/llm-top-10/.
- Mental-health benchmark K-Bench: https://arxiv.org/abs/2609.15855.
- Voice recognition on-device and domain tuning gains in agriculture: https://arxiv.org/abs/2609.20504.

## 5. Rethink

1. **"AI on premium tiers only."** For: AI costs money; premium needs a reason. Against: a Telugu elder who cannot be understood by the free tier never reaches premium; cheap models make baseline understanding nearly free.
2. **"Voice as a guided web conversation."** For: matches the owner's one-question vision and works inside the app. Against: browser speech is the least reliable layer and hides itself on weak phones; a WhatsApp or phone-call front door may reach more elders.
3. **"Matching must be AI-first; forms are old school."** For: families speak in prose and the "What we understood" card fixes mistakes. Against: LLM parsing varies by language and carries bias; a confirmed form field is more accountable. A hybrid with the card is probably right.
4. **"Hide the score, show a word."** For: avoids ranking people as numbers. Against: hidden ordering is unexplained to those who are never shown; add "why" and an exposure audit.
5. **"Respectful register is a translation property."** For: enforce pronouns and honorifics in copy. Against: respect also lives in tone, kinship words and order of questions, which only native reviewers catch.

## 6. Do not change

- Closed-vocabulary validation of every AI answer; nothing is stored until the family confirms.
- The "What we understood" card with adjustable importance.
- Claude parses, a deterministic engine scores; no popularity weight; word label plus reasons instead of a number.
- Milavn's deliberately deterministic NL ("AI must not become a shortcut around permissions").
- Vyapar's AI seam, per-member daily cap, redaction, audit rows, and opaque applicant refs.
- Refusing to read Telugu or Hindi with an English voice.
- One question at a time, read-back and a final summary card in the voice interview.
- Vyapar's multilingual search, the best behaviour I saw in any module: treat it as the standard for the others.
