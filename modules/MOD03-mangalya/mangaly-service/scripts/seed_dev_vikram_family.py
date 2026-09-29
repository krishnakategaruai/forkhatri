"""Owner decision 2026-09-25: Vikram Rao (persona mangaly-family) becomes the father
in his daughter Kavya Rao's Home Circle. Built through the live API, as each person.
Step 1 (Vikram): member profile + photo, the photo check, then "create a profile for
my daughter" with her mobile number. Step 2 (Kavya, after she signs in): take the
profile over and complete it. KEPT as persona data.

Photos (Unsplash License): Kavya photo-1767607740661-05e668190cdc, Vikram
photo-1787100612805-1c1735206c2e. Run once against the live API (not idempotent:
the mobile number can be provisioned only once):
    python -m scripts.seed_dev_vikram_family
"""
import json
import subprocess
import sys
from pathlib import Path

import httpx

S = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
ROOT = Path(r"C:\Users\krish\Krishna2025\startup2026\ForKhatri")
ASSETS = ROOT / "modules/MOD03-mangaly/mangaly-service/scripts/assets"
API = "http://localhost:8000"
KAVYA_PHONE = "+919999900004"
ORIGIN = {"Origin": "http://localhost:3000"}


def cookie(target: str) -> dict:
    out = subprocess.run(
        [str(ROOT / "platform/identity-service/.venv/Scripts/python"),
         str(ROOT / "platform/identity-service/scripts/dev_session.py"), target, "--cookie-header"],
        capture_output=True, text=True, check=True,
    ).stdout
    line = next(l for l in out.splitlines() if l.startswith("Cookie:"))
    k, v = line.split(": ", 1)
    return {k: v, **ORIGIN}


def ok(r: httpx.Response, label: str):
    print(f"{label}: {r.status_code} {r.text[:160] if r.status_code >= 300 else ''}")
    r.raise_for_status()
    return r.json() if r.content else None


c = httpx.Client(base_url=API, timeout=60)
vikram = cookie("mangaly-family")

# --- Vikram --------------------------------------------------------------
ok(c.patch("/profile/member/me", headers=vikram, json={
    "about": "Retired civil engineer, thirty years with the Hyderabad Metropolitan Water Supply board. Kavya's father.",
    "city": "Hyderabad, Telangana", "occupation": "Retired civil engineer"}), "Vikram member profile")
with open(ASSETS / "member-photos/vikram-rao.jpg", "rb") as f:
    ok(c.post("/profile/member/photo", headers=vikram, files={"photo": ("vikram.jpg", f, "image/jpeg")}), "Vikram photo")
# What the browser posts after the one-minute camera check (the match itself runs on
# the device). A dev account has no camera, so the check's result is sent directly.
ok(c.post("/verification/face-match", headers=vikram, json={
    "consent": True, "distance": 0.38, "liveness_passed": True, "photos_compared": 1}), "Vikram photo check")
with open(ASSETS / "more-matches/portrait-kavya-rao.jpg", "rb") as f:
    made = ok(c.post("/profile/managed", headers=vikram, data={
        "child_phone": KAVYA_PHONE, "relation": "father", "name": "Kavya Rao",
        "date_of_birth": "1998-11-06", "gender": "female", "looking_for": "groom",
        "city_locality": "Hyderabad, Telangana"}, files={"photo": ("kavya.jpg", f, "image/jpeg")}),
        "Vikram creates Kavya's profile")
kavya_id = made["account_id"]
print("Kavya account:", kavya_id)

# --- Kavya signs in and takes her profile over ---------------------------
kavya = cookie(kavya_id)
ok(c.post("/profile/claim", headers=kavya), "Kavya takes the profile over")
for name in ("life-hampi-ruins.jpg", "life-book-tea.jpg"):
    with open(ASSETS / "more-matches" / name, "rb") as f:
        ok(c.post("/profile/photos", headers=kavya, files={"photo": (name, f, "image/jpeg")}), f"photo {name}")

V = lambda v: {"state": "value", "value": v}  # noqa: E731
categories = {
    "basics": {"about": V("Kavya is an architect at a Hyderabad practice that restores old buildings; her current project is a step-well in Gandipet. Her father Vikram retired from the city's water board and her mother Sudha teaches mathematics."),
               "height_cm": V(163), "mother_tongue": V("telugu"), "have_children": V("no")},
    "education": {"highest_education_level": V("masters")},
    "education_career": {"college": V("School of Planning and Architecture, Vijayawada"), "employer": V("Studio Deccan Conservation"), "income_band": V("10_20")},
    "profession": {"occupation": V("Architect")},
    "marital_history": {"marital_status": V("never_married")},
    "relocation": {"relocation_willingness": V("open_to_discussion")},
    "community": {"native_place": V("Warangal, Telangana")},
    "family": {"family_type": V("nuclear"), "family_values": V("moderate"), "father_occupation": V("Retired civil engineer"),
               "mother_occupation": V("Mathematics teacher"), "brothers": V(1), "sisters": V(0), "lives_with_parents": V("yes")},
    "family_involvement_expectations": {"level": V("moderate")},
    "lifestyle": {"diet": V("vegetarian")},
    "food_travel_hobbies": {"hobbies": V(["photography", "reading", "road_trips"])},
    "horoscope": {"matching_required": V("open"), "manglik": V("no")},
    "career_children_living_financial": {"wants_children": V("yes")},
    "partner_preference": {"age_range": V({"min": 27, "max": 33}), "locality": V("Hyderabad")},
    "in_my_words": {
        "prompt_1": V({"q": "my_work_means", "a": "I restore old buildings for a living. Measuring a 200-year-old step-well with a tape and a torch is my idea of a good Tuesday.", "public": True}),
        "prompt_2": V({"q": "work_after_marriage", "a": "I will keep working. Site visits start early, so I am the one who makes the morning coffee, and I would like that to be a shared job."}),
        "prompt_3": V({"q": "ideal_weekend", "a": "A long drive to Warangal fort with my camera, and an evening at home with my parents arguing about cricket."}),
    },
    "openly": {"first_name": V(True), "photos": V(True)},
}
for cat, attrs in categories.items():
    ok(c.patch(f"/profile/{cat}", headers=kavya, json=attrs), f"Kavya {cat}")

me = ok(c.get("/auth/me", headers=kavya), "Kavya /auth/me")
print("own_profile:", me.get("own_profile"))
print("Vikram contexts:", ok(c.get("/home-circle/contexts", headers=vikram), "Vikram contexts"))
json.dump({"kavya_account_id": kavya_id}, open(S / "vikram_family.json", "w"))
