"""Live checks for FR002/FR003/FR005 (TR002/TR003/TR005) against RUNNING services.

Signs in through ForKhatri as the automated-test member, creates a profile,
exercises per-category attributes (set, decline, overwrite), the
discoverability gate and three-tier completeness, then deletes everything it
created.

Run the Mangaly API and the ForKhatri identity service first, then:
    python -m scripts.check_profile_categories
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

PROFILE = {
    "name": "Kavya Menon",
    "date_of_birth": "1994-06-20",
    "gender": "female",
    "looking_for": "groom",
    "city_locality": "Bengaluru, Karnataka",
}


def main() -> int:
    print("\nMangaly profile categories — live checks (FR002/FR003/FR005)\n")
    if not services_up():
        print("  The Mangaly API (8000) or the ForKhatri identity service (8100) is not running.")
        return 2

    client, account_id = sign_in_test_member()
    refuse_if_profile_exists(account_id)
    results = Results()

    def patch(category: str, body: dict) -> int:
        status, _ = client.json("PATCH", f"{API}/profile/{category}", body)
        return status

    def completeness() -> dict:
        status, body = client.json("GET", f"{API}/profile/completeness")
        return body if status == 200 and isinstance(body, dict) else {}

    try:
        s, b = client.multipart(f"{API}/profile", PROFILE, "photo.jpg", portrait(), "image/jpeg")
        results.check("Prerequisite: the profile saves (201)", s == 201, s)

        results.check(
            "Education can be set (204)",
            patch("education", {"highest_education_level": {"state": "value", "value": "masters"}})
            == 204,
        )
        results.check(
            "Profession can be set (204)",
            patch("profession", {"occupation": {"state": "value", "value": "Software Engineer"}})
            == 204,
        )

        report = completeness()
        results.check(
            "Completeness shows three discoverability items still missing",
            report.get("discoverability_complete") is False
            and len(report.get("discoverability_missing", [])) == 3,
            report,
        )
        results.check("The existence tier is complete", report.get("existence_complete") is True)

        results.check(
            "A field can be declined (204)",
            patch("marital_history", {"marital_status": {"state": "declined"}}) == 204,
        )
        missing = completeness().get("discoverability_missing", [])
        results.check(
            "A declined field still counts as missing for discoverability",
            "marital_history.marital_status" in missing,
            missing,
        )

        results.check(
            "Relocation can be set (204)",
            patch("relocation", {"relocation_willingness": {"state": "value", "value": "yes"}})
            == 204,
        )
        results.check(
            "A declined field can be overwritten with a value (204)",
            patch(
                "marital_history", {"marital_status": {"state": "value", "value": "never_married"}}
            )
            == 204,
        )
        results.check(
            "A partner age range satisfies the partner-preference requirement (204)",
            patch(
                "partner_preference",
                {"age_range": {"state": "value", "value": {"min": 28, "max": 36}}},
            )
            == 204,
        )

        report = completeness()
        results.check(
            "The discoverability tier is now complete",
            report.get("discoverability_complete") is True
            and report.get("discoverability_missing") == [],
            report,
        )

        results.check(
            "An enhanced-tier category can be set (204)",
            patch("lifestyle", {"diet": {"state": "value", "value": "vegetarian"}}) == 204,
        )
        report = completeness()
        results.check(
            "The enhanced tier counts it without gating anything",
            report.get("enhanced_filled_categories") == 1
            and report.get("discoverability_complete") is True,
            report,
        )
    finally:
        remove_profile(account_id)
        print("  cleanup: removed the profile, attributes, photos and Discovery row it created")

    return results.finish()


if __name__ == "__main__":
    sys.exit(main())
