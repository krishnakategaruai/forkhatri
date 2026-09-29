"""Live checks for FR001/TR001/SP001 profile creation against RUNNING services.

Signs in through ForKhatri as the automated-test member, exercises profile
creation (validation, "looking for", the marriageable-age gate, photo rules,
the duplicate guard, read-back and an authorized photo fetch), then deletes
everything it created.

Run the Mangaly API and the ForKhatri identity service first, then:
    python -m scripts.check_profile
"""

from __future__ import annotations

import sys

from scripts._check_support import (
    API,
    Results,
    portrait,
    refuse_if_profile_exists,
    remove_profile,
    services_up,
    sign_in_test_member,
)

VALID = {
    "name": "Meera Kulkarni",
    "date_of_birth": "1996-04-12",
    "gender": "female",
    "looking_for": "groom",
    "city_locality": "Pune, Maharashtra",
}


def main() -> int:
    print("\nMangaly profile creation — live checks (FR001/TR001/SP001)\n")
    if not services_up():
        print("  The Mangaly API (8000) or the ForKhatri identity service (8100) is not running.")
        return 2

    client, account_id = sign_in_test_member()
    refuse_if_profile_exists(account_id)
    results = Results()
    photo = portrait()

    try:
        s, b = client.multipart(
            f"{API}/profile", {**VALID, "name": ""}, "photo.jpg", photo, "image/jpeg"
        )
        results.check("A missing name is rejected (422)", s == 422, s)

        fields = {k: v for k, v in VALID.items() if k != "looking_for"}
        s, b = client.multipart(f"{API}/profile", fields, "photo.jpg", photo, "image/jpeg")
        results.check("A missing 'looking for' is rejected (422)", s == 422, s)

        s, b = client.multipart(
            f"{API}/profile",
            {**VALID, "date_of_birth": "2015-01-01"},
            "photo.jpg",
            photo,
            "image/jpeg",
        )
        results.check("An under-age profile is rejected (422)", s == 422, s)

        s, b = client.multipart(f"{API}/profile", VALID, "photo.txt", b"not a photo", "text/plain")
        results.check("A non-image photo is rejected (422)", s == 422, s)

        s, b = client.multipart(f"{API}/profile", VALID, "photo.jpg", photo, "image/jpeg")
        results.check("A valid profile saves (201)", s == 201, s)
        results.check(
            "The saved profile has a photo URL", isinstance(b, dict) and bool(b.get("photo_url")), b
        )

        s, _ = client.multipart(f"{API}/profile", VALID, "photo.jpg", photo, "image/jpeg")
        results.check("A second profile for the same member is rejected (409)", s == 409, s)

        s, me = client.json("GET", f"{API}/profile/me")
        results.check(
            "GET /profile/me returns the saved profile",
            s == 200 and isinstance(me, dict) and me.get("name") == VALID["name"],
            s,
        )

        s, values = client.json("GET", f"{API}/profile/attributes/full")
        looking_for = (values or {}).get("partner_preference", {}).get("looking_for", {})
        results.check(
            "'Looking for' is stored with the profile",
            looking_for.get("value") == "groom",
            looking_for,
        )

        photo_url = me.get("photo_url") if isinstance(me, dict) else None
        if photo_url:
            results.check(
                "The owner can load the saved photo", client.raw_status(f"{API}{photo_url}") == 200
            )
    finally:
        remove_profile(account_id)
        print("  cleanup: removed the profile, attributes, photos and Discovery row it created")

    return results.finish()


if __name__ == "__main__":
    sys.exit(main())
