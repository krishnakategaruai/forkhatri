# Milavn QA users

20 development members for Milavn QA (10 women, 10 men). Development only; never create them in production.
Each has a ForKhatri member, a development password, and a Milavn profile made through the product API
(live place search, onboarding, the one-time woman/man answer, a short bio). No profile photo.

Seed or refresh: `platform\identity-service\.venv\Scripts\python modules\MOD02-milavn\scripts\seed_qa_members.py`
Remove exactly these 20 and their Milavn data: add `--remove`.
Needs the identity service (8100) and Milavn API (8001) running.

| # | Name | Member uuid | Phone | Place (live search) | Answer | Language | Profession | Interests |
|---|---|---|---|---|---|---|---|---|
| 1 | Ananya Iyer | `c2000000-0000-4000-8000-000000000001` | +919800020001 | Banjara Hills, Hyderabad, Telangana | woman | en | Chartered accountant | book-club, networking, yoga |
| 2 | Rohan Deshmukh | `c2000000-0000-4000-8000-000000000002` | +919800020002 | Hadapsar, Pune, Maharashtra | man | en | Doctor | cycling, running, trekking, volunteering |
| 3 | Sneha Reddy | `c2000000-0000-4000-8000-000000000003` | +919800020003 | Hanamkonda, Telangana | woman | te | Lawyer | book-club, festivals, poetry |
| 4 | Vikram Chowdary | `c2000000-0000-4000-8000-000000000004` | +919800020004 | Vijayawada, Andhra Pradesh | man | te | Software engineer | badminton, coding, startups |
| 5 | Priya Nair | `c2000000-0000-4000-8000-000000000005` | +919800020005 | Indiranagar, Bengaluru, Karnataka | woman | en | Teacher | book-club, kids-activities, language-exchange, music |
| 6 | Arjun Mehra | `c2000000-0000-4000-8000-000000000006` | +919800020006 | Karol Bagh, Delhi, Delhi | man | hi | Shop owner | cricket, festivals, street-food |
| 7 | Kavita Joshi | `c2000000-0000-4000-8000-000000000007` | +919800020007 | Bandra West, Mumbai, Maharashtra | woman | hi | Chef | dance, potluck, street-food, workshops |
| 8 | Suresh Babu | `c2000000-0000-4000-8000-000000000008` | +919800020008 | Zone 13 Adyar, Chennai, Tamil Nadu | man | te | Photographer | coffee-meetups, music, photography-walks, trekking |
| 9 | Meera Kulkarni | `c2000000-0000-4000-8000-000000000009` | +919800020009 | Dharampeth, Nagpur, Maharashtra | woman | hi | Homemaker | cleanup-drives, festivals, parenting |
| 10 | Aditya Sharma | `c2000000-0000-4000-8000-000000000010` | +919800020010 | Jaipur, Rajasthan | man | en | Student | board-games, coding, football |
| 11 | Divya Menon | `c2000000-0000-4000-8000-000000000011` | +919800020011 | Whitefield, Bengaluru, Karnataka | woman | en | Software engineer | coding, coffee-meetups, cycling |
| 12 | Karthik Raman | `c2000000-0000-4000-8000-000000000012` | +919800020012 | Thiyagaraya Nagar, Chennai, Tamil Nadu | man | en | Chartered accountant | career, cricket, networking |
| 13 | Pooja Agarwal | `c2000000-0000-4000-8000-000000000013` | +919800020013 | Vaishali Nagar, Jaipur, Rajasthan | woman | hi | Doctor | swimming, volunteering, yoga |
| 14 | Imran Qureshi | `c2000000-0000-4000-8000-000000000014` | +919800020014 | Madhapur, Hyderabad, Telangana | man | hi | Chef | cricket, festivals, potluck, street-food |
| 15 | Lakshmi Prasad | `c2000000-0000-4000-8000-000000000015` | +919800020015 | Kakinada, Andhra Pradesh | woman | te | Teacher | book-club, dance, music |
| 16 | Nitin Bhosale | `c2000000-0000-4000-8000-000000000016` | +919800020016 | Shivajinagar, Pune, Maharashtra | man | hi | Lawyer | networking, running, workshops |
| 17 | Farah Khan | `c2000000-0000-4000-8000-000000000017` | +919800020017 | Powai, Mumbai, Maharashtra | woman | en | Photographer | coffee-meetups, photography-walks, theatre |
| 18 | Gaurav Malhotra | `c2000000-0000-4000-8000-000000000018` | +919800020018 | Lajpat Nagar, Delhi, Delhi | man | hi | Shop owner | badminton, networking, street-food |
| 19 | Shalini Rao | `c2000000-0000-4000-8000-000000000019` | +919800020019 | Gachibowli, Hyderabad, Telangana | woman | en | Student | board-games, language-exchange, poetry, theatre |
| 20 | Manoj Patil | `c2000000-0000-4000-8000-000000000020` | +919800020020 | Nagpur, Maharashtra | man | hi | Homemaker | kids-activities, parenting, volunteering |

The "Answer" column is each member's own truthful answer to the one-time woman/man question.
Emails are `first.last@qa.forkhatri.test`; the phones run +919800020001 to +919800020020.

## Signing in

The entrance's "Act as (development)" list shows only the built-in personas, so these 20 are not in it.
Use the member uuid instead (from `platform\identity-service`):

- Playwright: `.venv\Scripts\python scripts\dev_session.py <uuid> --storage-state ..\..\modules\MOD02-milavn\.logs\<name>.json`
- curl: `.venv\Scripts\python scripts\dev_session.py <uuid> --cookie-header` (prints `Cookie: fk_session=...`)
- Password sign-in (end-to-end checks only): the phone above with `ForKhatri-dev-2026`.

Use normal sign-out, never "Sign out on all devices". Never use the OTP screens.
