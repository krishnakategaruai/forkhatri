# Research for the platform critique: sign-in, DPDP, small-cell privacy (2026-10-06)

Written by a research helper of the platform critic, after that critic had already finished, so these findings are not in CRITIQUE-platform.md. Sources are secondary unless marked; "partial" means not confirmed against the primary text. WebSearch hit its cap during this research.

## 1. DPDP Act 2023 and Rules 2025
- Rules notified 13/14 Nov 2025 in three steps: Board and definitions live now; Consent Managers from 13 Nov 2026 (Rule 4); notice, consent, security, breach, erasure, rights and children's rules (Rules 3, 5-16) about 13 May 2027. MeitY floated cutting 18 months to 12; an Aug 2026 article still shows 13 May 2027, so treat compression as a pending possibility. https://www.dpdpa.com/dpdparules/rule1.html , https://www.mondaq.com/india/data-protection/1773554/meity-plans-to-cut-short-dpdp-compliance-timeline-and-notify-cross-border-restrictions-for-sdfs
- Breach (Rule 7): tell each affected person and the Board without delay, then a detailed report within 72 hours. Fines: up to Rs 250 crore for security failure, Rs 200 crore for failing to notify a breach, Rs 50 crore for other violations. https://www.dpdpa.com/dpdparules/rule7.html , https://www.dpdpa.com/dpdpa2023/chapter-2/section8.html
- Security (Rule 6): encryption/masking/tokens, access control, logs and monitoring, backups, processor contracts (email, SMS and hosting vendors are processors; the fiduciary stays responsible). https://www.dpdpa.com/dpdparules/rule6.html
- Erasure: the 3-year inactivity clock applies only to very large e-commerce, gaming and social platforms, not ForKhatri. Erasure on withdrawal of consent still applies, and logs must be kept at least 1 year (Rule 8), so deletion and the log floor must be designed together. https://www.dpdpa.com/dpdparules/rule8.html
- Children are under 18; verifiable parental consent is needed, with no tracking or targeted advertising (s.9, Rule 10). Adults with disabilities need a court- or authority-appointed guardian (Rule 11), so a relative is not enough. https://www.dpdpa.com/dpdparules/rule10.html , https://www.dpdpa.com/dpdparules/rule11.html
- Parent pre-creating an adult child's account by phone number: strongest legal angle. Data supplied by a third party needs consent under s.6; the "voluntarily provided" basis in s.7 requires the person themself to provide it. Partial, not checked against the Gazette. https://www.dpdpa.com/dpdpa2023/chapter-2/section7.html
- A community body or app is likely a data fiduciary: "person" includes an association of persons or body of individuals, incorporated or not. The only carve-out is an individual's personal or domestic use. Startup relief (s.17(3)) has no notification, so full duties apply. https://www.dpdpa.com/dpdpa2023/chapter-1/section2.html
- Dashboards: the research/statistical exemption is not blanket and security duties still apply; whether private entities can use it is unclear.

## 2. SMS and OTP in India
- TRAI traceability (message chain from sender to operator) enforced from 11 Dec 2024; sending needs a DLT-registered entity, header and template. https://www.storyboard18.com/how-it-works/trai-issues-directives-to-access-providers-to-curb-misuse-of-messaging-services-40075.htm
- Costs (vendor blog, May 2026, indicative): SMS OTP Rs 0.10-0.45; DLT setup about Rs 5,900 per entity and per header. https://www.messagecentral.com/blog/sms-otp-pricing-india
- Delivery risk: in the March 2021 DLT rollout about 40% of roughly 1 billion daily SMS failed (partial). No 2025 India benchmark found.
- WhatsApp authentication messages: per-delivered-message billing since 1 Jul 2025; India about Rs 0.115-0.13 domestic (third-party), similar to SMS. Official rate card not opened. https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing
- SMS pumping (fraud via scripted OTP requests to numbers the attacker profits from): rate limits per number, IP and country, CAPTCHA and spend alerts needed before SMS is re-enabled. https://www.twilio.com/en-us/blog/sms-pumping-fraud-solutions
- RBI's 2025 authentication directions (effective 1 Apr 2026) do not ban SMS OTP. They govern payments, not ForKhatri's login. https://rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=61282

## 3. Phone number recycling and pre-hijacking
- India: a deactivated number is not reissued for at least 90 days (TRAI told the Supreme Court; the Court on 7 Nov 2023 declined to bar reissuing). An account tied to a phone number can pass to a stranger. https://telecomtalk.info/?p=894092
- Princeton (Lee and Narayanan, 2021): of 259 recycled US numbers, 66% were linked to accounts on major platforms. https://recyclednumbers.cs.princeton.edu/ No India study found.
- Pre-hijacking (Sudhodanan and Paverd, USENIX Security 2022): at least 35 of 75 popular services vulnerable. A parent-created account on a child's number fits the "trojan identifier" shape; the creator's access must end when the real owner claims it. https://arxiv.org/abs/2205.10174
- Suggested mitigations (synthesis, no single source): re-verify after inactivity, a recovery route that is not the phone, alerts when the phone or email is changed.

## 4. Passkeys and Aadhaar
- Passkey momentum in India (payments): Mastercard 2024, Visa Jul 2026; barriers: no device lock, unfamiliar word, shared phones, OTP habit. No study found on low-literacy or shared-phone users. https://www.corbado.com/blog/passkeys-india-overview (vendor blog)
- Aadhaar authentication by private entities needs a government ministry sponsor and fits only listed purposes (Jan 2025 rules); a community app confirming membership or age does not fit. Private entities may not store full Aadhaar numbers or photocopies; offline verification rules took effect 9 Dec 2025. https://www.khaitanco.com/thought-leadership/Aadhaar-authentication-for-private-entities
- DigiLocker "requester" route exists with user consent; whether a community platform would be approved is unverified. https://www.digilocker.gov.in/web/partners/requesters

## 5. Small counts and re-identification (the Insights page)
- Sweeney: 87% of Americans unique by ZIP, gender and birth date (later estimates about 61-63%). https://dataprivacylab.org/projects/identifiability/paper1.pdf
- US Census reconstruction (Abowd et al., HDSR 2025): published tables alone were not sufficient protection (figures not verified). https://hdsr.mitpress.mit.edu/pub/ntchx9im/release/4
- For ForKhatri (inference): gender-by-city counts in a small community have many cells of 0-2; changing counts over time reveal individuals. Remedies: minimum cell sizes, merge small cities into regions, delay and round. No Indian small-cell example or standard found.

## 6. Identifiers across modules
- OIDC pairwise subject identifiers stop modules correlating members by `sub`, but not by phone, email or name claims. Little use while all modules are first-party. https://openid.net/specs/openid-connect-core-1_0.html
- Contextual integrity (Nissenbaum): a parent acting in matrimony is normal, but not in a business or loans context; one id across contexts needs per-context norms. No applied work on a single cross-module identifier found.
