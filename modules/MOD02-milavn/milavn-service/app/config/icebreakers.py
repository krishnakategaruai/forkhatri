"""[FR118] Conversation cards — something to say when nobody knows anyone yet.

Timeleft puts printed prompt cards on every table and 222 texts a written "colour" before the
event, both for the same reason: the hardest part of meeting strangers is the first two minutes,
and a shared prompt beats small talk because nobody has to invent it. These are written for this
community: warm, specific, answerable by an eighteen-year-old and by a grandmother, never about
money, marriage, caste or politics, and never a question a stranger would find intrusive.

They are content, not data — there is nothing to store and nothing to moderate, so they live here
rather than in a table. Each activity gets a few, chosen by its category, in a stable order per
activity so everyone at the same activity sees the same cards.
"""

from __future__ import annotations

ANYONE: tuple[str, ...] = (
    "What made you say yes to this one?",
    "What is something you have started doing recently?",
    "Which part of the city do you know best?",
    "What did you eat today that was worth it?",
    "Who taught you something useful this year?",
    "What is a small thing that made this week better?",
)

BY_CATEGORY: dict[str, tuple[str, ...]] = {
    "play": (
        "How long have you been playing?",
        "Who got you started?",
        "Best game you have ever watched?",
    ),
    "meet": (
        "What brought you to this part of town?",
        "What do you do when you have a free Sunday?",
        "Which meet-up have you enjoyed most so far?",
    ),
    "eat": (
        "What is your order when you cannot decide?",
        "Which dish does your family make better than any restaurant?",
        "Sweet first or last?",
    ),
    "learn": (
        "What are you trying to get better at?",
        "What is something you learned the hard way?",
        "Who would you like to learn from?",
    ),
    "work": (
        "What does a good day at work look like for you?",
        "What did you want to be at fifteen?",
        "What is worth doing slowly?",
    ),
    "explore": (
        "Where do you go when you want quiet?",
        "Which walk in this city should everyone do once?",
        "Morning person or evening person, honestly?",
    ),
    "celebrate": (
        "Which festival does your family do best?",
        "What is a tradition you would keep forever?",
        "What song has to be played?",
    ),
    "help": (
        "What made you want to help with this?",
        "What is a small change you would like to see here?",
        "Who in your life gives without being asked?",
    ),
}

PER_ACTIVITY = 3


def cards_for(*, intent_category: str, seed: str, count: int = PER_ACTIVITY) -> list[str]:
    """A few prompts for one activity: its own category first, then the ones anyone can answer.

    `seed` (the activity id) makes the choice stable — everyone at the same activity sees the same
    cards in the same order, so they can be read aloud, and a reload does not reshuffle them.
    """
    pool = list(BY_CATEGORY.get(intent_category, ())) + list(ANYONE)
    if not pool:
        return []
    start = sum(ord(ch) for ch in seed) % len(pool)
    return [pool[(start + i) % len(pool)] for i in range(min(count, len(pool)))]
