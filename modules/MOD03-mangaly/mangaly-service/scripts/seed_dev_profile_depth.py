"""Development seed: fill the profile sections the screens can now collect.

`EDIT_LAYOUT` only ever rendered five of the eight sections in
`PROFILE_SECTIONS`, so `community`, `education_career` and `horoscope` had no
way to be filled and no seeded candidate had them. The profile screens now
render all eight, and the viewing screen splits by role — a candidate reads a
Hinge-style prompt-and-photo profile, a family member reads the conventional
biodata — so both layouts need real content to be judged honestly.

Prompts matter most here. Without them the candidate layout collapses into
exactly the label-value form dump it exists to avoid, which is what the
product owner saw on the profile screen. Answers are written the way people
actually write them: specific, a bit particular, not a CV line.

Deliberately uneven. Rahul is close to complete, Karthik is mid-way and Rohan
has almost nothing, because a profile screen that has only ever been seen full
has not been tested — and §25 requires a sparse profile to degrade gracefully
rather than be silently penalised.

Run: python -m scripts.seed_dev_profile_depth
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

# Owner connection for the same narrow reason `reindex_discovery.py` uses one:
# `mangaly_app` is RLS-constrained and an unscoped select over every profile
# returns nothing.
_OWNER_URL = (
    "postgresql+asyncpg://mangaly_owner:mangaly_owner_dev_password@localhost:5433/mangaly"
)

# name -> {category: {attribute_key: value}}
PROFILES: dict[str, dict[str, dict[str, object]]] = {
    "Rahul Varma": {
        "in_my_words": {
            "prompt_1": {
                "q": "living_with_family",
                "a": "My parents in the same city, not the same kitchen. I want them "
                "twenty minutes away and at our table most Sundays.",
            },
            "prompt_2": {
                "q": "work_after_marriage",
                "a": "Whatever she wants, and I mean that practically — if her work "
                "means moving cities, I can do my job from anywhere and she cannot.",
            },
            "prompt_3": {
                "q": "non_negotiable",
                "a": "Being able to disagree out loud. I grew up in a house where nobody "
                "sulked, and I do not think I could learn to.",
            },
        },
        "community": {"gotra": "Kaushal", "sub_community": "khatri", "native_place": "Amritsar, Punjab"},
        "education_career": {
            "income_band": "20_40",
            "employer": "Infosys",
            "college": "NIT Warangal",
        },
        "horoscope": {
            "matching_required": "open",
            "manglik": "no",
            "rashi": "vrishabh",
            "birth_place": "Bengaluru, Karnataka",
        },
        "family": {"family_type": "nuclear", "family_values": "moderate"},
    },
    "Karthik Iyer": {
        "in_my_words": {
            "prompt_1": {
                "q": "on_children",
                "a": "Yes, but not immediately. I would like a couple of years of just "
                "the two of us learning how to be a household first.",
            },
            "prompt_2": {
                "q": "about_money",
                "a": "I track everything in a spreadsheet my sister finds unhinged. "
                "Happy to be argued out of it, not happy to stop saving.",
            },
        },
        "community": {"sub_community": "other", "native_place": "Thanjavur, Tamil Nadu"},
        "education_career": {"income_band": "20_40", "employer": "Deloitte"},
        "horoscope": {"matching_required": "yes", "manglik": "dont_know"},
    },
    "Arjun Khanna": {
        # Already has prompts from the original seed; this adds the three
        # sections that previously had nowhere to live.
        "community": {"gotra": "Bhardwaj", "sub_community": "arora", "native_place": "Ludhiana, Punjab"},
        "education_career": {"income_band": "10_20", "employer": "Zoho", "college": "BITS Pilani"},
        "horoscope": {"matching_required": "no"},
    },
    # The reader's own side. Two of these deliberately answer the same
    # questions Rahul answered, so the profile screen's "You answered this"
    # comparison has something real to show.
    "Asha Reddy": {
        "in_my_words": {
            "prompt_1": {
                "q": "living_with_family",
                "a": "I would like his parents close by. I have watched my mother do "
                "everything alone since my grandmother passed and I do not want that.",
            },
            "prompt_2": {
                "q": "work_after_marriage",
                "a": "I am not giving up my work. I will move cities for the right "
                "person, and I can build software from anywhere, but I will keep "
                "building it.",
            },
            "prompt_3": {
                "q": "on_children",
                "a": "Two, eventually. I want to lead my own engineering team first, and "
                "I would rather say that plainly than discover we disagree later.",
            },
        },
    },
    # Rohan Bhatia is left sparse on purpose.
}

UPSERT = text(
    """
    INSERT INTO mangaly_profile.profile_attribute
        (id, profile_id, category, attribute_key, state, value, updated_at)
    VALUES
        (gen_random_uuid(), :profile_id, :category, :attribute_key,
         'value'::mangaly_profile.field_state, CAST(:value AS jsonb), now())
    ON CONFLICT (profile_id, category, attribute_key) DO UPDATE SET
        state = EXCLUDED.state,
        value = EXCLUDED.value,
        updated_at = now()
    """
)


async def main() -> None:
    engine = create_async_engine(_OWNER_URL)
    written = 0
    async with engine.begin() as conn:
        rows = (await conn.execute(text("SELECT id, name FROM mangaly_profile.profile"))).all()
        by_name = {name: pid for pid, name in rows}
        for name, categories in PROFILES.items():
            pid = by_name.get(name)
            if pid is None:
                print(f"  (skipped, profile absent: {name})")
                continue
            for category, fields in categories.items():
                for key, value in fields.items():
                    await conn.execute(
                        UPSERT,
                        {
                            "profile_id": pid,
                            "category": category,
                            "attribute_key": key,
                            "value": json.dumps(value),
                        },
                    )
                    written += 1
            print(f"  {name}: {', '.join(categories)}")
    await engine.dispose()
    print(f"\n{written} attribute(s) written.")


asyncio.run(main())
