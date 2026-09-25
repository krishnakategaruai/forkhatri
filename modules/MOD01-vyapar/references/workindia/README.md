# Real WorkIndia app screenshots — product owner reference (2026-09-17)

Real phone screenshots the product owner shared directly. Read the files as ground truth, not
descriptions.

- `01-job-details-1.jpg`, `03-job-details-2.jpg`, `04-company-details.jpg` — a job's detail page,
  split into two tabs at the top: **Job Details** and **Company Details**. Job Details holds
  `Candidate Requirement` (Qualification, Skills required — as plain comma-separated text, not
  chips) and `Additional Information` (Job Timings, Job Type, Department, Role, Incentive, Job
  Address — each a bold label + value on one line). Company Details holds `Company Details`
  (Organisation Size, Industry Type, Perks and Benefits — the only one rendered as a chip, with an
  icon) and `Interview Details` (Contact Person: name + role). Every section is visually a distinct
  card. Below both tabs' content: a row of three secondary actions — **Share** (WhatsApp icon,
  green), **Report** (warning icon, red), **Tips** (bulb icon, blue) — then a sticky bottom bar with
  **two primary actions side by side**: an outlined "Apply" (paper-plane icon) and a filled "Click
  to call HR" (phone icon, brand blue). Two calls to action, not one — apply in-app OR call
  directly, member's choice.
- `02-similar-jobs.jpg` — below the detail page, a "Similar Jobs" section (heading + one sentence
  of framing) with a scrollable list of cards: role title (bold, brand blue), salary **range**
  (Rs. 22000 - Rs. 29000, not a single number), locality + distance in km, company name, and a
  pill badge for applicant count (e.g. "30") plus a separate "New" pill when applicable. A chevron
  circle on the right of each row opens it.
- `05-onboarding-jobtype.jpg`, `07-onboarding-jobtype-2.jpg` — onboarding step 3 of 4
  (**Education → Experience → Preference → See Jobs**, shown as a top stepper with checkmarks on
  done steps and a rocket icon on the final step — a small gamified progress bar). "Select the Job
  Type you want": a search box, then multi-select job-type cards — each a small representative
  photo, a bold title, one-line description, and a checkbox — not a plain text list or dropdown.
- `06-onboarding-skills.jpg` — the following sub-step: "Skills" with a search-and-add box, then
  "Or Select from Suggested Skills" grouped into cards by the job type just chosen (e.g. a
  "Travel / Tourism Services" card full of relevant skill chips, a separate "Security / Fire /
  Safety" card, etc.) — the suggestions are scoped to what the member actually selected one step
  earlier, not a flat global list.

## What this is useful for in Vyapar

- **Opportunity detail's primary action, for Employment/local-service types specifically**: WorkIndia
  offers Apply AND a direct call, side by side, not just one path — worth comparing against FR22's
  single "Enquire Now"/"Apply" action. If a listing/opportunity has a public phone number available
  (FR02 "After accepted enquiry" doesn't block a number already marked Public), consider a second,
  equally-weighted "Click to call" style action alongside the in-app Apply/Enquire button for
  Employment and local-service types — this is a real, cited precedent, not an invented addition.
  Flag as a discussion point for the product owner/critique agent rather than building unprompted,
  since FR24 governs when contact is revealed and this shouldn't bypass it for unverified numbers.
- **Job/opportunity detail's two-tab structure** (core details vs. poster/company details) is a
  cleaner precedent than a single long scroll for a data-dense Employment posting — compare against
  FR55's current single-scroll detail layout.
- **The onboarding "job type" step's picture-card multi-select**, scoped skill suggestions per
  selected type, and the small step-progress-with-icons treatment are all directly relevant to
  FR44's first-run capability capture (currently structured choices + free text) — a concrete,
  cited upgrade path if the product owner wants first-run to feel more guided.
- **"Similar Jobs" salary shown as a range with distance-in-km on every card** reinforces the
  distance-sort work already shipped (2026-09-17) — the exact "X km" wording/placement pattern here
  is worth matching on Vyapar's own opportunity cards.
