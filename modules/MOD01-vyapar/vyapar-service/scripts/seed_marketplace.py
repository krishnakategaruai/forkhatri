"""Seed a living Vyapar marketplace for development, through the public API.

Owner, 2026-09-30: "Vyapar looks like working app, but all the real
functionality is actually created as dummy." The dev database had about 20
posts, most of them expired, so every screen looked empty or wrong. This
script creates a believable Hyderabad marketplace the way members would:

  * ~20 new members (shop owners, a clinic, a BPO, a builder, tradespeople,
    a CA, a photographer...) are created through the normal member path:
    first request (just-in-time member), first run (name, language,
    locality, skills), privacy + terms acceptance, their one profile
    (GET/PATCH /v1/me/profile, business section where they have a shop),
    contact OTP verification and submit;
  * ~110 active posts across every trade category and 20+ Hyderabad
    localities, from those members and the existing dev personas: real pay
    ranges per trade (monthly salary for jobs, a budget per visit or project
    for local work and projects), deadlines 7 to 30 days out, Hinglish /
    Telugu-English titles as people actually write them;
  * priced service packages on the tradespeople's and professionals' profiles;
  * a handful of real reviews through the real flow (enquiry -> accept ->
    both reply -> resolve -> both review).

Everything goes through the API as the member (X-Dev-Member-Id). Two things
are written directly, as the owner role, because no API does them: the
`seed_batch` marker on every member, profile and post it creates (migration
026), and a staggered `published_at` (0-9 days ago) so "New today" isn't the
whole feed. The owner's own account (m_krishna) is never used or touched.

Idempotent: a member, profile, post, package or review that already exists is
left as it is. `--clean` removes everything carrying the marker (and the
enquiries, reviews, notifications and events hanging off it).

    .venv/Scripts/python scripts/seed_marketplace.py --api http://127.0.0.1:8011
    .venv/Scripts/python scripts/seed_marketplace.py --clean
"""
from __future__ import annotations

import argparse
import asyncio
import os
import random
import sys
from datetime import datetime, timedelta, timezone

import asyncpg
import httpx

SEED = "marketplace-v1"
OWNER_ACCOUNT = "m_krishna"  # never used as a persona, never touched
OWNER_DSN = os.environ.get("VYAPAR_OWNER_DSN", "postgres://vyapar_owner:vyapar_owner_dev_password@localhost:5433/vyapar")

# ---------------------------------------------------------------------------
# New members. id, name, language, locality, kind, skills, categories,
# business (name, headline) or None, headline, phone suffix, packages
# ---------------------------------------------------------------------------
P = lambda tier, name, price, days, rev, inc, desc="": dict(tier=tier, name=name, price_paise=price * 100, delivery_days=days,  # noqa: E731
                                                            revisions=rev, includes=inc, description=desc or None)
MEMBERS = [
    ("m_seed_srisai", "Srinivas Goud", "te", "Kukatpally", ["cook", "catering", "delivery"], ["food_catering"],
     ("Sri Sai Cloud Kitchen", "Home-style Andhra meals, 400 orders a day"), "Runs a cloud kitchen in KPHB", "001", []),
    ("m_seed_greenleaf", "Farhana Begum", "hi", "Gachibowli", ["security_guard", "housekeeping"], ["hospitality_housekeeping"],
     ("Green Leaf Residency Association", "320-flat gated community, Gachibowli"), "Secretary, Green Leaf Residency", "002", []),
    ("m_seed_quickmove", "Rajesh Yadav", "hi", "LB Nagar", ["delivery", "driver", "packer"], ["logistics"],
     ("QuickMove Logistics", "Last-mile delivery for e-commerce, LB Nagar hub"), "Operations head, QuickMove", "003", []),
    ("m_seed_lakshmi", "Lakshmi Prasanna", "te", "Dilsukhnagar", ["tailoring", "counter_sales"], ["textiles_retail"],
     ("Lakshmi Silks & Tailoring", "Sarees, blouses and alterations since 2009"), "Owner, Lakshmi Silks", "004", []),
    ("m_seed_vistara", "Mohammed Irfan", "hi", "Himayatnagar", ["nurse", "lab_technician", "receptionist"], ["healthcare"],
     ("Vistara Clinic & Diagnostics", "Family clinic with a NABL-partner lab"), "Administrator, Vistara Clinic", "005", []),
    ("m_seed_brightminds", "Padmaja Rao", "te", "Miyapur", ["teacher", "tutoring", "mathematics"], ["education"],
     ("Bright Minds Tuition Centre", "Classes 6-10, State and CBSE"), "Runs Bright Minds Tuition Centre", "006", []),
    ("m_seed_codecraft", "Arvind Menon", "en", "Madhapur", ["software", "react", "python"], ["software_it"],
     ("CodeCraft Labs", "Web and mobile apps for small businesses"), "Founder, CodeCraft Labs", "007", []),
    ("m_seed_callpoint", "Sneha Varma", "en", "Ameerpet", ["telecaller", "sales", "field_sales"], ["sales_telecalling"],
     ("CallPoint Services", "Telugu, Hindi and English customer support"), "Team lead, CallPoint Services", "008", []),
    ("m_seed_buildwell", "Venkat Reddy", "te", "Kondapur", ["mason", "electrical", "plumbing", "tile_fitter"], ["home_repair"],
     ("BuildWell Constructions", "Independent houses and interiors, west Hyderabad"), "Site engineer, BuildWell", "009", []),
    ("m_seed_glamour", "Ayesha Siddiqui", "hi", "Banjara Hills", ["beautician"], ["beauty_personal_care"],
     ("Glamour Unisex Salon", "Hair, skin and bridal makeup"), "Owner, Glamour Salon", "010", []),
    ("m_seed_autofix", "Naresh Kumar", "te", "Uppal", ["mechanic", "car_repair"], ["automotive"],
     ("AutoFix Garage", "Multi-brand car and bike service"), "Owner, AutoFix Garage", "011", []),
    ("m_seed_printhub", "Suresh Babu", "te", "Abids", ["printing", "graphic_designer", "machine_operator"], ["printing"],
     ("PrintHub Offset", "Wedding cards, flex and offset printing"), "Owner, PrintHub Offset", "012", []),
    # Tradespeople and professionals (profiles with packages)
    ("m_seed_krishnarao", "Krishna Rao", "te", "Ameerpet", ["plumbing"], ["home_repair"],
     ("Krishna Rao Plumbing Works", "Leak repair, bathroom fitting, motor installation"), "Plumber, 12 years in Ameerpet and SR Nagar", "013",
     [P("basic", "Leak or tap repair (per visit)", 500, 0, 0, ["Visit and inspection", "Minor leak fix", "Tap or washer change"]),
      P("standard", "Bathroom fitting", 3500, 1, 1, ["Shower, taps and flush fitting", "Concealed pipe check", "Materials extra"]),
      P("premium", "Full bathroom plumbing", 18000, 4, 2, ["New concealed lines", "Geyser and motor point", "6-month repair warranty"])]),
    ("m_seed_ramesh", "Ramesh Naidu", "te", "Kukatpally", ["electrical", "ac_technician"], ["home_repair"], None,
     "Electrician and AC technician, KPHB and Nizampet", "014",
     [P("basic", "Switch, fan or light fitting (per visit)", 400, 0, 0, ["Visit", "Up to 3 points", "Testing"]),
      P("standard", "Split AC service", 700, 0, 0, ["Jet wash of indoor unit", "Gas pressure check", "Drain cleaning"]),
      P("premium", "2BHK rewiring", 22000, 5, 1, ["Copper wiring", "MCB board", "Earthing check", "Materials quoted separately"])]),
    ("m_seed_salma", "Salma Khatoon", "hi", "Charminar", ["tailoring"], ["textiles_retail"], None,
     "Ladies tailor, blouses and salwar suits", "015",
     [P("basic", "Blouse stitching", 450, 5, 1, ["Measurement", "Lining", "Hooks"]),
      P("standard", "Designer blouse", 1200, 7, 2, ["Padded", "Back design", "Piping"]),
      P("premium", "Bridal blouse with maggam work", 6500, 14, 2, ["Hand maggam work", "Two trials", "Delivery at home"])]),
    ("m_seed_divya", "Divya Sharma", "en", "Gachibowli", ["graphic_designer", "social_media"], ["media_photo"], None,
     "Graphic designer for small brands: logos, menus, Instagram posts", "016",
     [P("basic", "Logo design", 4000, 3, 2, ["2 concepts", "PNG + PDF", "Colour and black versions"]),
      P("standard", "Logo + visiting card + menu", 9000, 6, 3, ["Logo", "Visiting card", "One-page menu", "Print-ready files"]),
      P("premium", "Monthly Instagram (20 posts)", 15000, 30, 4, ["20 designed posts", "Captions in English and Telugu", "Posting calendar"])]),
    ("m_seed_kiran", "Kiran Kumar", "te", "Secunderabad", ["photography", "video_editing"], ["media_photo"], None,
     "Wedding and event photographer", "017",
     [P("basic", "Birthday or small event (3 hours)", 6000, 3, 0, ["150 edited photos", "Online gallery"]),
      P("standard", "Engagement or haldi (full day)", 18000, 7, 1, ["400 edited photos", "Short highlight reel"]),
      P("premium", "Wedding (2 days, photo + video)", 65000, 21, 2, ["Candid + traditional", "Full video", "Album of 40 sheets"])]),
    ("m_seed_harsha", "Harsha Vardhan", "en", "Begumpet", ["accounting", "gst_filing", "tax"], ["accounting_tax"],
     ("Harsha & Co., Chartered Accountants", "GST, income tax and bookkeeping for small businesses"), "Chartered accountant, 8 years", "018",
     [P("basic", "Monthly GST return (up to 100 invoices)", 1500, 5, 1, ["GSTR-1", "GSTR-3B", "Challan"]),
      P("standard", "Income tax return (salaried + business)", 3000, 7, 1, ["ITR filing", "Tax computation", "Advance-tax plan"]),
      P("premium", "Monthly bookkeeping + GST", 6000, 30, 2, ["Tally entries", "GST returns", "Monthly P&L"])]),
    ("m_seed_mahesh", "Mahesh Yadav", "hi", "Miyapur", ["driver"], ["logistics"], None, "Car driver, LMV + badge, 9 years", "019", []),
    ("m_seed_anjali", "Anjali Reddy", "te", "Kondapur", ["tutoring", "mathematics"], ["education"], None,
     "Maths and science home tutor, classes 6-10", "020",
     [P("basic", "Home tuition, 3 days a week (monthly)", 3500, 30, 0, ["12 sessions", "Weekly test"]),
      P("standard", "Home tuition, 5 days a week (monthly)", 5500, 30, 0, ["20 sessions", "Weekly test", "Parent update"])]),
    ("m_seed_prakash", "Prakash Chary", "te", "LB Nagar", ["carpenter"], ["home_repair"], None, "Carpenter: modular kitchens, wardrobes, repairs", "021",
     [P("basic", "Door or furniture repair (per visit)", 600, 0, 0, ["Visit", "Hinge / lock / channel fix"]),
      P("standard", "Wardrobe (per sq ft)", 1400, 12, 1, ["Plywood + laminate", "Soft-close hinges"]),
      P("premium", "Modular kitchen (10 ft)", 85000, 21, 2, ["BWP ply", "Tandem drawers", "1-year warranty"])]),
    ("m_seed_sunitha", "Sunitha Devi", "te", "Tarnaka", ["cook"], ["hospitality_housekeeping"], None, "Home cook: Andhra and North Indian meals", "022", []),
]

LOCALITIES = ["Kukatpally", "Ameerpet", "Madhapur", "Dilsukhnagar", "Himayatnagar", "Secunderabad", "Gachibowli",
              "Banjara Hills", "Uppal", "LB Nagar", "Miyapur", "Begumpet", "Charminar", "Kondapur", "Abids",
              "Koti", "Mehdipatnam", "Tarnaka", "Manikonda", "Nizampet", "Kompally", "ECIL", "Hitech City", "Attapur", "Malakpet"]

# ---------------------------------------------------------------------------
# Posts. poster, type, skills, title ({loc}), description, pay (lo, hi) in rupees,
# work_mode, timing, localities to post in
# ---------------------------------------------------------------------------
J = "employment"
L = "local_service"
F = "freelance"
POSTS = [
    ("m_seed_srisai", J, ["delivery"], "Delivery boy kavali — {loc} cloud kitchen",
     "Lunch and dinner shifts, own bike with licence. Petrol allowance ₹2,000 extra, orders within 5 km.", (15000, 21000), "on_site", "Immediate joining", ["Kukatpally", "Nizampet", "Miyapur"]),
    ("m_seed_srisai", J, ["cook"], "South Indian cook needed — {loc}",
     "Tiffins and meals for a cloud kitchen, 400 orders a day. Stay available. 1 day off a week.", (16000, 24000), "on_site", "Join this week", ["Kukatpally", "Ameerpet"]),
    ("m_seed_srisai", J, ["packer"], "Kitchen helper cum packer — {loc}",
     "Packing, cleaning and prep. Freshers welcome, food provided.", (11000, 14000), "on_site", "Immediate joining", ["Kukatpally"]),
    ("m_seed_greenleaf", J, ["security_guard"], "Security guard (night shift) — {loc} apartment",
     "12-hour night shift, 320-flat community. PF and ESI, uniform provided. Ex-servicemen preferred.", (13000, 17000), "on_site", "From 1st of next month", ["Gachibowli", "Manikonda", "Kondapur"]),
    ("m_seed_greenleaf", J, ["housekeeping"], "Housekeeping staff for gated community — {loc}",
     "Common-area cleaning, 8-hour shift, weekly off. Female and male both.", (11000, 14000), "on_site", "Immediate joining", ["Gachibowli", "Hitech City"]),
    ("m_seed_quickmove", J, ["delivery"], "E-commerce delivery executive — {loc} hub",
     "Two-wheeler with RC and licence. Per-parcel incentive over fixed pay. Weekly payout.", (16000, 24000), "on_site", "Join tomorrow", ["LB Nagar", "Dilsukhnagar", "Uppal", "Malakpet", "ECIL"]),
    ("m_seed_quickmove", J, ["driver"], "Tata Ace driver — {loc} to city routes",
     "LMV licence with badge. Fixed routes, 10-hour day, overtime paid.", (18000, 24000), "on_site", "Join this week", ["LB Nagar", "Uppal"]),
    ("m_seed_quickmove", J, ["packer"], "Warehouse packer / loader — {loc}",
     "Sorting and loading parcels. Day and night shifts, PF and ESI.", (12000, 15000), "on_site", "Immediate joining", ["LB Nagar", "Kompally"]),
    ("m_seed_lakshmi", J, ["tailoring"], "Ladies tailor kavali — {loc} boutique",
     "Blouse and salwar stitching, maggam work a plus. Piece-rate bonus over salary.", (13000, 18000), "on_site", "Join this week", ["Dilsukhnagar", "Kothapet"]),
    ("m_seed_lakshmi", J, ["counter_sales"], "Saree showroom sales girl — {loc}",
     "Telugu and Hindi speaking, 10am-9pm with lunch break. Incentive on sales.", (12000, 16000), "on_site", "Immediate joining", ["Dilsukhnagar", "Koti"]),
    ("m_seed_vistara", J, ["nurse"], "Staff nurse (GNM/BSc) — {loc} clinic",
     "Day shift, OPD and minor procedures. 1 year experience preferred.", (20000, 28000), "on_site", "Join within 2 weeks", ["Himayatnagar", "Abids"]),
    ("m_seed_vistara", J, ["lab_technician"], "Lab technician (DMLT) — {loc}",
     "Sample collection and basic tests, home-collection visits in the area.", (18000, 24000), "on_site", "Join this week", ["Himayatnagar"]),
    ("m_seed_vistara", J, ["receptionist"], "Clinic receptionist — {loc}",
     "Front desk, appointments, billing. Telugu, Hindi and basic English.", (14000, 18000), "on_site", "Immediate joining", ["Himayatnagar", "Mehdipatnam"]),
    ("m_seed_brightminds", J, ["teacher"], "Maths teacher for classes 8-10 — {loc}",
     "Evening batches 4-8 pm, State and CBSE syllabus. B.Sc/B.Ed preferred.", (15000, 22000), "on_site", "From next week", ["Miyapur", "Chanda Nagar", "Nizampet"]),
    ("m_seed_brightminds", L, ["tutoring"], "Home tutor for class 7 student — {loc}",
     "Maths and science, 5 days a week, 1 hour, near the Metro station.", (3500, 5000), "on_site", "Start this week", ["Miyapur", "Kukatpally"]),
    ("m_seed_codecraft", J, ["react"], "React developer (2+ yrs) — {loc}",
     "Build web apps for small-business clients. Hybrid: 3 days office.", (45000, 80000), "both", "Join within a month", ["Madhapur", "Hitech City"]),
    ("m_seed_codecraft", J, ["python"], "Python / Django developer — {loc}",
     "APIs and dashboards. PostgreSQL experience needed.", (40000, 75000), "both", "Join within a month", ["Madhapur"]),
    ("m_seed_codecraft", F, ["software"], "Website for a restaurant — fixed budget",
     "5-page site with menu, online table booking and WhatsApp order button.", (25000, 45000), "remote", "Deliver in 3 weeks", ["Madhapur"]),
    ("m_seed_callpoint", J, ["telecaller"], "Telecaller (Telugu + Hindi) — {loc}",
     "Inbound customer support, no sales targets. Freshers welcome, training given.", (13000, 18000), "on_site", "Immediate joining", ["Ameerpet", "Begumpet", "Secunderabad"]),
    ("m_seed_callpoint", J, ["field_sales"], "Field sales executive with bike — {loc}",
     "Visit shops for a payments app. Fixed plus ₹8,000 average incentive.", (15000, 22000), "on_site", "Join this week", ["Ameerpet", "Uppal", "Kompally"]),
    ("m_seed_buildwell", J, ["mason"], "Mason (raj mistri) for villa project — {loc}",
     "Brickwork and plastering. Daily wage option also available.", (18000, 24000), "on_site", "Immediate joining", ["Kondapur", "Manikonda"]),
    ("m_seed_buildwell", J, ["electrical"], "Site electrician — {loc}",
     "Concealed wiring for independent houses. ITI electrician preferred.", (18000, 26000), "on_site", "Join this week", ["Kondapur", "Gachibowli", "Attapur"]),
    ("m_seed_buildwell", J, ["plumbing"], "Plumber for construction site — {loc}",
     "CPVC and UPVC lines, bathroom fittings. 2 years experience.", (16000, 22000), "on_site", "Immediate joining", ["Kondapur", "Madhapur"]),
    ("m_seed_buildwell", L, ["tile_fitter"], "Tile fitting for 2BHK flat — {loc}",
     "Floor and bathroom tiles, around 1,100 sq ft. Tiles supplied.", (22000, 30000), "on_site", "Start next week", ["Kondapur"]),
    ("m_seed_glamour", J, ["beautician"], "Beautician (hair + skin) — {loc} salon",
     "Facials, threading, hair spa. Commission on services over fixed pay.", (14000, 22000), "on_site", "Join this week", ["Banjara Hills", "Jubilee Hills"]),
    ("m_seed_autofix", J, ["mechanic"], "Two-wheeler mechanic — {loc} garage",
     "Honda / Hero / Bajaj servicing. Tools provided.", (15000, 22000), "on_site", "Immediate joining", ["Uppal", "Tarnaka", "ECIL"]),
    ("m_seed_autofix", J, ["car_repair"], "Car mechanic (multi-brand) — {loc}",
     "General service, brakes and suspension. 3 years experience.", (18000, 26000), "on_site", "Join within 2 weeks", ["Uppal"]),
    ("m_seed_printhub", J, ["machine_operator"], "Offset machine operator — {loc}",
     "Heidelberg single-colour, day shift, overtime in wedding season.", (15000, 20000), "on_site", "Immediate joining", ["Abids", "Koti"]),
    ("m_seed_printhub", F, ["graphic_designer"], "Wedding card designs in Telugu and English",
     "30 new card designs for the season in CorelDraw, editable files.", (12000, 20000), "remote", "Deliver in 2 weeks", ["Abids"]),
    # households and small businesses (existing dev personas) — local work
    ("m_anita", L, ["plumbing"], "Plumber needed urgently — bathroom leak, {loc}",
     "Leak under the washbasin and a running flush. Today or tomorrow morning.", (600, 1200), "on_site", "Today", ["Banjara Hills"]),
    ("m_meena", L, ["electrical"], "Electrician for inverter wiring — {loc}",
     "Inverter point and 4 fan regulators to replace in a bakery.", (1500, 2500), "on_site", "This week", ["Himayatnagar"]),
    ("m_sunita", J, ["cook"], "Cooks and helpers for wedding season catering — {loc}",
     "North and South Indian. Per-event bonus. Stay provided.", (16000, 22000), "on_site", "Immediate joining", ["Secunderabad"]),
    ("m_sunita", L, ["catering"], "Service boys for a 400-guest reception — {loc}",
     "Saturday evening, 6 pm to midnight, uniform provided. ₹900 per person.", (900, 900), "on_site", "This Saturday", ["Secunderabad", "Begumpet"]),
    ("m_vikram", J, ["counter_sales"], "Counter salesman for textile wholesale — {loc}",
     "Hindi and Telugu, knowledge of sarees and dress material.", (13000, 17000), "on_site", "Join this week", ["Charminar"]),
    ("m_vikram", J, ["accountant"], "Accounts assistant (Tally + GST) — {loc}",
     "Billing, stock entries and monthly GST. B.Com preferred.", (18000, 26000), "on_site", "Join within 2 weeks", ["Charminar", "Koti"]),
    ("m_deepak", F, ["interior_design"], "Interior design for a 3BHK — {loc}",
     "Concept, 3D views and working drawings for living, kitchen and 3 bedrooms.", (35000, 60000), "both", "Deliver in 4 weeks", ["Jubilee Hills"]),
    ("m_deepak", L, ["painter"], "Painters for 3BHK interior repaint — {loc}",
     "Asian Paints Tractor Emulsion, putty where needed. Around 1,800 sq ft.", (25000, 38000), "on_site", "Start next week", ["Jubilee Hills", "Banjara Hills"]),
    ("m_gaurav", J, ["car_repair"], "Denter and painter for car workshop — {loc}",
     "Body shop work, 2 years experience.", (18000, 25000), "on_site", "Immediate joining", ["Uppal"]),
    ("m_shreya", F, ["content_writing"], "Content writer — 8 blog posts on small-business finance",
     "1,000-word posts in simple English, SEO basics, 2 revisions each.", (8000, 16000), "remote", "Deliver in 3 weeks", ["Hitech City"]),
    ("m_shreya", F, ["social_media"], "Instagram manager for a startup (monthly)",
     "12 posts and 8 reels a month, captions in English and Telugu.", (12000, 22000), "remote", "Start this month", ["Hitech City"]),
    ("m_priya", F, ["video_editing"], "Video editor for YouTube cooking channel",
     "4 videos a month, 10-15 minutes each, Telugu subtitles.", (10000, 20000), "remote", "Start this week", ["Kondapur"]),
    ("m_kavita", F, ["legal"], "Rental agreement and property document check",
     "Review sale deed and draft a rental agreement for a shop.", (3000, 6000), "both", "This week", ["Abids"]),
    ("m_arjun", F, ["photography"], "Second shooter for weddings — November dates",
     "Candid photographer with own camera, 5 wedding dates in November.", (15000, 30000), "on_site", "November", ["Secunderabad", "Hitech City"]),
    ("m_rahul", L, ["tutoring"], "Spoken English tutor for 4 kids — {loc}",
     "Weekend batch at home, 2 hours each day.", (4000, 6000), "on_site", "From this weekend", ["Kukatpally"]),
    # more local needs from the new members
    ("m_seed_greenleaf", L, ["plumbing"], "Plumber for overhead tank line repair — {loc}",
     "Main line leak on the terrace, needs a same-day fix.", (1500, 3000), "on_site", "Today", ["Gachibowli"]),
    ("m_seed_greenleaf", L, ["electrical"], "Electrician for common-area lights — {loc}",
     "Replace 30 corridor lights with LED and fix 2 DB boards.", (4000, 7000), "on_site", "This week", ["Gachibowli"]),
    ("m_seed_greenleaf", L, ["ac_technician"], "AC service for clubhouse (6 split ACs) — {loc}",
     "Jet service and gas check before the event season.", (3500, 4500), "on_site", "This week", ["Gachibowli"]),
    ("m_seed_vistara", L, ["carpenter"], "Carpenter for clinic cabinets — {loc}",
     "2 medicine cabinets and a reception counter repair.", (12000, 18000), "on_site", "Start next week", ["Himayatnagar"]),
    ("m_seed_lakshmi", L, ["painter"], "Shop painting before Dasara — {loc}",
     "400 sq ft showroom, walls and shutters.", (9000, 14000), "on_site", "This week", ["Dilsukhnagar"]),
    ("m_seed_glamour", L, ["graphic_designer"], "Menu card and offer flyers for salon",
     "Rate card, festive offer flyer, Instagram post sizes.", (3000, 6000), "remote", "This week", ["Banjara Hills"]),
    ("m_seed_autofix", L, ["electrical"], "Garage wiring and 3-phase point — {loc}",
     "New 3-phase point for the compressor and 6 tube lights.", (6000, 9000), "on_site", "This week", ["Uppal"]),
    ("m_seed_codecraft", L, ["driver"], "Driver for office cab (monthly) — {loc}",
     "Company car, 9 am-7 pm, Monday to Saturday.", (18000, 22000), "on_site", "From 1st", ["Madhapur"]),
    ("m_seed_brightminds", L, ["housekeeping"], "Part-time cleaning for tuition centre — {loc}",
     "Daily 7-9 am, 4 rooms and washrooms.", (5000, 6500), "on_site", "Immediate", ["Miyapur"]),
    ("m_seed_callpoint", L, ["data_entry"], "Data entry for 3 weeks — {loc}",
     "Enter 12,000 customer forms into Excel. ₹1 per form plus daily bonus.", (12000, 15000), "on_site", "Start tomorrow", ["Ameerpet"]),
    ("m_seed_quickmove", F, ["graphic_designer"], "Logo and van branding for QuickMove",
     "Logo refresh and vinyl wrap design for 12 vans.", (15000, 25000), "remote", "Deliver in 2 weeks", ["LB Nagar"]),
    ("m_seed_srisai", F, ["photography"], "Food photography for 60 menu items",
     "Studio-style shots for Swiggy and Zomato listings.", (12000, 20000), "on_site", "Next week", ["Kukatpally"]),
    ("m_seed_harsha", J, ["accountant"], "Article assistant / junior accountant — {loc}",
     "GST and TDS returns, Tally. CA Inter or B.Com with 1 year.", (15000, 22000), "on_site", "Join within 2 weeks", ["Begumpet", "Secunderabad"]),
    ("m_seed_printhub", J, ["office_assistant"], "Office boy cum delivery — {loc}",
     "Deliver print orders on bike, assist in office. Freshers ok.", (11000, 14000), "on_site", "Immediate joining", ["Abids"]),
    ("m_seed_buildwell", J, ["labourer"], "Construction helpers (10 needed) — {loc}",
     "Daily-wage work on a villa site, weekly payment, stay possible.", (13000, 16000), "on_site", "Join tomorrow", ["Kondapur", "Kompally"]),
    ("m_seed_greenleaf", J, ["gardener"], "Gardener for community landscaping — {loc}",
     "Lawn, 200 plants, watering schedule. 6 days a week.", (12000, 15000), "on_site", "From next week", ["Gachibowli"]),
    ("m_seed_vistara", J, ["data_entry"], "Billing and data entry operator — {loc}",
     "Lab reports and billing software. Evening shift 2-10 pm.", (13000, 17000), "on_site", "Join this week", ["Himayatnagar"]),
    ("m_seed_callpoint", J, ["sales"], "Inside sales executive (English + Telugu) — {loc}",
     "Call warm leads for a coaching institute, fixed plus incentives.", (15000, 20000), "on_site", "Join this week", ["Ameerpet", "Secunderabad"]),
    ("m_seed_quickmove", J, ["driver"], "Bike taxi / delivery rider, flexible hours — {loc}",
     "Choose your hours, daily payout. Own bike and smartphone.", (14000, 22000), "on_site", "Start today", ["Mehdipatnam", "Attapur", "Tarnaka"]),
    ("m_seed_glamour", J, ["beautician"], "Makeup artist for bridal bookings — {loc}",
     "Bridal and party makeup, portfolio needed. Travel within the city.", (18000, 28000), "on_site", "Join this week", ["Banjara Hills"]),
    ("m_sunita", L, ["events"], "Event decor team for Bathukamma celebrations — {loc}",
     "Flower and stage decor for a community event, 2 days, 6 people.", (18000, 25000), "on_site", "Next weekend", ["Secunderabad"]),
    ("m_seed_lakshmi", F, ["handicraft"], "Handmade kalamkari potlis and gift bags (300 pieces)",
     "Return gifts for a wedding, fabric supplied, samples first.", (15000, 24000), "both", "Deliver in 3 weeks", ["Dilsukhnagar"]),
    ("m_seed_greenleaf", L, ["yoga"], "Morning yoga teacher for residents (monthly) — {loc}",
     "6-7 am, 5 days a week, clubhouse hall, around 25 residents.", (8000, 12000), "on_site", "From 1st", ["Gachibowli"]),
    ("m_seed_printhub", J, ["printing"], "Flex printing and lamination operator — {loc}",
     "Solvent flex machine and lamination, 1 year experience.", (14000, 19000), "on_site", "Immediate joining", ["Abids"]),
    ("m_seed_srisai", J, ["delivery"], "Part-time delivery (evenings 6-11 pm) — {loc}",
     "Students welcome. Per-order pay with a monthly guarantee.", (8000, 12000), "on_site", "Start today", ["Kukatpally", "Miyapur"]),
]

REVIEWS = [  # (sender, provider, provider's work, sender's words, provider's words)
    ("m_seed_greenleaf", "m_seed_krishnarao", "overhead tank line leak", True, True),
    ("m_seed_srisai", "m_seed_ramesh", "kitchen exhaust wiring and 2 AC services", True, True),
    ("m_seed_lakshmi", "m_seed_salma", "10 designer blouses for the shop", True, True),
    ("m_seed_codecraft", "m_seed_divya", "logo and launch posts", True, True),
    ("m_seed_vistara", "m_seed_harsha", "monthly GST and ITR for the clinic", True, True),
    ("m_seed_buildwell", "m_seed_prakash", "wardrobes for a villa", True, True),
]


class Api:
    def __init__(self, base: str) -> None:
        self.http = httpx.Client(base_url=base, timeout=60)

    def __call__(self, member: str, method: str, path: str, **kw):
        assert member != OWNER_ACCOUNT, "the owner's account is never used by the seed"
        lang = kw.pop("lang", "en")
        r = self.http.request(method, path, headers={"X-Dev-Member-Id": member, "X-Vyapar-Language": lang}, **kw)
        return r


def ok(r, what: str) -> dict | list | None:
    if r.status_code >= 400:
        print(f"  ! {what}: {r.status_code} {r.text[:200]}")
        return None
    return r.json() if r.content else {}


async def tag(owner, table: str, ids: list[str]) -> None:
    if ids:
        await owner.execute(f"UPDATE {table} SET seed_batch = $1 WHERE id::text = ANY($2::text[])", SEED, ids)


async def seed(api: Api, owner) -> None:
    from app.geo import resolve_place

    rnd = random.Random(20260930)
    phone_base = "+9190000"
    # ---- members and their one profile ---------------------------------------
    for mid, name, lang, loc, skills, cats, business, headline, phone, packages in MEMBERS:
        place = resolve_place(loc)
        api(mid, "POST", "/v1/first-run/step", json={
            "step": 5, "display_name": name, "language": lang, "locality": loc, "lat": place.lat, "lng": place.lng,
            "radius_km": 10, "work_mode": "on_site", "capabilities": skills, "help_with": ["find_work", "find_customers"]})
        await owner.execute("UPDATE vyapar_identity.members SET seed_batch = $1 WHERE id = $2 AND seed_batch IS DISTINCT FROM $1", SEED, mid)
        for kind in ("privacy", "terms"):
            api(mid, "POST", f"/v1/legal/{kind}/accept")
        prof = ok(api(mid, "GET", "/v1/me/profile"), f"profile {mid}")
        if not prof:
            continue
        pid = (prof.get("profile") or prof).get("id") if isinstance(prof, dict) else None
        if pid is None:
            pid = await owner.fetchval("SELECT id::text FROM vyapar_listings.listings WHERE owner_id = $1 AND state <> 'archived'", mid)
        patch = {"name": name, "headline": headline, "capabilities": skills, "categories": cats, "locality": loc,
                 "lat": place.lat, "lng": place.lng, "primary_phone": f"{phone_base}10{phone}",
                 "experience_years": rnd.randint(2, 14), "languages": ["te", "hi", "en"][: rnd.randint(1, 3)],
                 "availability": rnd.choice(["now", "this_week"])}
        if business:
            patch["business"] = {"name": business[0], "headline": business[1]}
        ok(api(mid, "PATCH", "/v1/me/profile", json=patch), f"profile patch {mid}")
        state = await owner.fetchval("SELECT state FROM vyapar_listings.listings WHERE id = $1::uuid", pid)
        if state == "draft":
            api(mid, "PATCH", f"/v1/listings/{pid}/contacts", json={"contacts": [
                {"channel": "phone", "value": f"{phone_base}10{phone}", "disclosure": "after_accept"},
                {"channel": "whatsapp", "value": f"{phone_base}10{phone}", "disclosure": "after_accept"}]})
            code = (ok(api(mid, "POST", f"/v1/listings/{pid}/otp/request", json={"phone": f"{phone_base}10{phone}"}), f"otp {mid}") or {}).get("dev_code")
            if code:
                ok(api(mid, "POST", f"/v1/listings/{pid}/otp/verify", json={"code": code}), f"verify {mid}")
            ok(api(mid, "POST", f"/v1/listings/{pid}/submit"), f"submit {mid}")
        await tag(owner, "vyapar_listings.listings", [pid])
        if packages:
            existing = ok(api(mid, "GET", f"/v1/listings/{pid}/packages"), f"packages {mid}") or []
            if not existing:
                ok(api(mid, "PUT", f"/v1/listings/{pid}/packages", json={"packages": packages}), f"put packages {mid}")
        print(f"  member {mid:22} {name:18} profile {state or 'new'} -> ready")

    # ---- existing dev personas who post: the same gates a member passes -----
    new_ids = {m[0] for m in MEMBERS}
    for poster in sorted({p[0] for p in POSTS} - new_ids):
        for kind in ("privacy", "terms"):
            api(poster, "POST", f"/v1/legal/{kind}/accept")

    # ---- posts --------------------------------------------------------------
    created = 0
    now = datetime.now(timezone.utc)
    for poster, type_, skills, title_t, desc, (lo, hi), mode, timing, locs in POSTS:
        for loc in locs:
            title = title_t.format(loc=loc)
            exists = await owner.fetchval(
                "SELECT id FROM vyapar_opportunities.opportunities WHERE poster_id = $1 AND title = $2 AND state = 'active'", poster, title)
            if exists:
                continue
            structured: dict = {}
            if type_ == J:
                structured = {"salary_min_paise": lo * 100, "salary_max_paise": hi * 100, "openings": rnd.randint(1, 6),
                              "shift": "night" if "night" in title.lower() else "day"}
            elif type_ == F:
                structured = {"budget_type": "fixed", "budget_min_paise": lo * 100, "budget_max_paise": hi * 100,
                              "duration": "1_4_weeks" if hi < 50000 else "1_3_months"}
            else:
                structured = {"budget_paise": hi * 100, "urgency": "today" if timing.lower().startswith("today") else "this_week"}
            deadline = (now + timedelta(days=rnd.randint(7, 30))).isoformat()
            body = {"entry_mode": "create", "type": type_, "source_segment": "community", "title": title, "description": desc,
                    "location": loc, "work_mode": mode, "timing": timing, "required_capabilities": skills,
                    "deadline": deadline, "structured": structured,
                    "allow_precall": type_ in (J, L) and rnd.random() < 0.35}
            r = ok(api(poster, "POST", "/v1/opportunities", json=body), f"post {title}")
            if not r:
                continue
            if r.get("unconfirmed_fields"):
                api(poster, "PATCH", f"/v1/opportunities/{r['id']}/confirm", json={"fields": r["unconfirmed_fields"]})
            if ok(api(poster, "POST", f"/v1/opportunities/{r['id']}/publish"), f"publish {title}") is None:
                continue
            await tag(owner, "vyapar_opportunities.opportunities", [r["id"]])
            # stagger freshness so "New today" is today's, not everything
            await owner.execute(
                "UPDATE vyapar_opportunities.opportunities SET published_at = now() - make_interval(hours => $2) WHERE id = $1::uuid",
                r["id"], rnd.choice([1, 3, 8, 20, 30, 50, 75, 100, 140, 200]),
            )
            created += 1
    print(f"  posts created this run: {created}")

    # ---- reviews through the real flow ---------------------------------------
    for sender, provider, work, s_rec, p_rec in REVIEWS:
        listing = await owner.fetchval("SELECT id::text FROM vyapar_listings.listings WHERE owner_id = $1 AND state LIKE 'active%'", provider)
        if not listing:
            continue
        done = await owner.fetchval(
            """SELECT EXISTS (SELECT 1 FROM vyapar_reviews.reviews r JOIN vyapar_enquiries.enquiries e ON e.id = r.interaction_id
                WHERE e.sender_id = $1 AND e.provider_id = $2)""", sender, provider)
        if done:
            continue
        e = ok(api(sender, "POST", "/v1/enquiries", json={"listing_id": listing, "message": f"Namaste, we need help with {work}. Can you visit this week?"}), f"enquiry {sender}->{provider}")
        if not e:
            continue
        api(provider, "POST", f"/v1/enquiries/{e['id']}/accept")
        api(provider, "POST", f"/v1/enquiries/{e['id']}/messages", json={"body": "Yes, I can come on Thursday at 10 am. I'll bring the materials list."})
        api(sender, "POST", f"/v1/enquiries/{e['id']}/messages", json={"body": "Thursday works. Thank you!"})
        api(provider, "POST", f"/v1/enquiries/{e['id']}/resolve")
        ok(api(sender, "POST", "/v1/reviews", json={"interaction_kind": "enquiry", "interaction_id": e["id"], "recommend": s_rec,
                                                   "tags": ["on_time", "quality", "fair_price"],
                                                   "comment": f"Did the {work} neatly and on time. Explained everything before starting."}), f"review by {sender}")
        ok(api(provider, "POST", "/v1/reviews", json={"interaction_kind": "enquiry", "interaction_id": e["id"], "recommend": p_rec,
                                                     "tags": ["clear_pricing", "good_communication"],
                                                     "comment": "Clear about the work and paid on the same day. Happy to work again."}), f"review by {provider}")
        print(f"  review {sender} <-> {provider}")

    await normalize(owner)
    n = await owner.fetchrow(
        """SELECT (SELECT count(*) FROM vyapar_opportunities.opportunities WHERE state = 'active' AND (deadline IS NULL OR deadline > now())) AS live,
                  (SELECT count(*) FROM vyapar_opportunities.opportunities WHERE seed_batch = $1) AS seeded_posts,
                  (SELECT count(*) FROM vyapar_listings.listings WHERE state LIKE 'active%') AS profiles,
                  (SELECT count(DISTINCT split_part(location, ',', 1)) FROM vyapar_opportunities.opportunities WHERE state = 'active') AS places""", SEED)
    print(f"done: {n['live']} live posts ({n['seeded_posts']} seeded), {n['profiles']} active profiles, {n['places']} localities")


def jitter(lat: float, lng: float, key: str) -> tuple[float, float]:
    """A point 0.3-1.5 km from the locality centre in a direction fixed by the
    row id: real-looking distances (no "0.0 km" between neighbours), and the
    same point on every run."""
    import hashlib
    import math

    h = hashlib.sha256(key.encode()).digest()
    bearing = int.from_bytes(h[:4], "big") / 2**32 * 2 * math.pi
    km = 0.3 + int.from_bytes(h[4:8], "big") / 2**32 * 1.2
    dlat = km * math.cos(bearing) / 111.32
    dlng = km * math.sin(bearing) / (111.32 * math.cos(math.radians(lat)))
    return round(lat + dlat, 6), round(lng + dlng, 6)


async def normalize(owner) -> None:
    """Seeded rows only: the location is the locality alone ("Madhapur", not
    "Madhapur, Hyderabad") and the pin sits inside the locality, not on its
    centroid. Idempotent: always recomputed from the locality centre."""
    from app.geo import resolve_place
    from app.place_label import location_label

    fixed = 0
    for r in await owner.fetch("SELECT id, location FROM vyapar_opportunities.opportunities WHERE seed_batch = $1", SEED):
        loc = location_label(r["location"])
        place = resolve_place(loc)
        if place is None:
            continue
        lat, lng = jitter(place.lat, place.lng, str(r["id"]))
        await owner.execute("UPDATE vyapar_opportunities.opportunities SET location = $2, lat = $3, lng = $4 WHERE id = $1", r["id"], loc, lat, lng)
        fixed += 1
    for r in await owner.fetch("SELECT id, locality FROM vyapar_listings.listings WHERE seed_batch = $1", SEED):
        place = resolve_place(r["locality"])
        if place is None:
            continue
        lat, lng = jitter(place.lat, place.lng, str(r["id"]))
        await owner.execute("UPDATE vyapar_listings.listings SET lat = $2, lng = $3 WHERE id = $1", r["id"], lat, lng)
        fixed += 1
    print(f"normalized {fixed} seeded posts and profiles (locality-only location, pins 0.3-1.5 km inside the locality)")


async def clean(owner) -> None:
    members = [r["id"] for r in await owner.fetch("SELECT id FROM vyapar_identity.members WHERE seed_batch = $1", SEED)]
    assert OWNER_ACCOUNT not in members
    opps = [r["id"] for r in await owner.fetch("SELECT id FROM vyapar_opportunities.opportunities WHERE seed_batch = $1", SEED)]
    listings = [r["id"] for r in await owner.fetch("SELECT id FROM vyapar_listings.listings WHERE seed_batch = $1", SEED)]
    async with owner.transaction():
        enq = [r["id"] for r in await owner.fetch(
            """SELECT id FROM vyapar_enquiries.enquiries WHERE opportunity_id = ANY($1::uuid[]) OR listing_id = ANY($2::uuid[])
                  OR sender_id = ANY($3::text[]) OR provider_id = ANY($3::text[])""", opps, listings, members)]
        await owner.execute("DELETE FROM vyapar_reviews.reviews WHERE interaction_id = ANY($1::uuid[])", enq)
        await owner.execute("DELETE FROM vyapar_reviews.review_invites WHERE interaction_id = ANY($1::uuid[])", enq)
        await owner.execute("DELETE FROM vyapar_enquiries.contact_attempts WHERE enquiry_id = ANY($1::uuid[]) OR opportunity_id = ANY($2::uuid[])", enq, opps)
        await owner.execute("DELETE FROM vyapar_enquiries.enquiries WHERE id = ANY($1::uuid[])", enq)
        await owner.execute("DELETE FROM vyapar_trust_safety.moderation_cases WHERE object_id = ANY($1::uuid[]) OR object_id = ANY($2::uuid[])", opps, listings)
        await owner.execute("DELETE FROM vyapar_commercial.impressions WHERE target_id = ANY($1::uuid[]) OR target_id = ANY($2::uuid[])", opps, listings)
        await owner.execute("DELETE FROM vyapar_opportunities.member_opportunity WHERE opportunity_id = ANY($1::uuid[]) OR member_id = ANY($2::text[])", opps, members)
        await owner.execute("DELETE FROM vyapar_listings.member_listing WHERE listing_id = ANY($1::uuid[]) OR member_id = ANY($2::text[])", listings, members)
        await owner.execute("DELETE FROM vyapar_integration.notifications WHERE member_id = ANY($1::text[])", members)
        for oid in opps:
            await owner.execute("DELETE FROM vyapar_integration.notifications WHERE params::text LIKE '%' || $1 || '%'", str(oid))
        await owner.execute("DELETE FROM vyapar_opportunities.saved_searches WHERE member_id = ANY($1::text[])", members)
        await owner.execute("DELETE FROM vyapar_opportunities.opportunities WHERE id = ANY($1::uuid[])", opps)
        await owner.execute("DELETE FROM vyapar_listings.listings WHERE id = ANY($1::uuid[])", listings)  # cascades packages, contacts, otp
        await owner.execute("DELETE FROM vyapar_privacy.acceptances WHERE member_id = ANY($1::text[])", members)
        await owner.execute("DELETE FROM vyapar_privacy.privacy_settings WHERE member_id = ANY($1::text[])", members)
        await owner.execute("DELETE FROM vyapar_platform.rate_limit_counter WHERE split_part(rate_limit_key, ':', 2) = ANY($1::text[])", members)
        await owner.execute("DELETE FROM vyapar_identity.members WHERE id = ANY($1::text[])", members)
    print(f"cleaned: {len(opps)} posts, {len(listings)} profiles, {len(members)} members, {len(enq)} enquiries")


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=os.environ.get("VYAPAR_API_URL", "http://127.0.0.1:8011"))
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--normalize", action="store_true", help="only fix locations/pins of already-seeded rows")
    args = ap.parse_args()
    owner = await asyncpg.connect(OWNER_DSN)
    try:
        if args.clean:
            await clean(owner)
        elif args.normalize:
            await normalize(owner)
        else:
            await seed(Api(args.api), owner)
    finally:
        await owner.close()


if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    asyncio.run(main())
