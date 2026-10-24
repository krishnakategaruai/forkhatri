#!/usr/bin/env python3
"""Locale parity checker for every ForKhatri web app and API.

For each `locales/` folder (web and server) it compares every language with
English, namespace by namespace, and reports:
  - invalid JSON
  - missing keys (in English, not in the language) and extra keys
  - placeholder mismatches ({{name}} in i18next files, {name} in server files)
  - values still identical to English (likely untranslated) for mr/kn
  - mr values with no Devanagari and kn values with no Kannada script

Usage (from the repo root):
  python scripts/check_locale_parity.py            # all locale folders, all languages
  python scripts/check_locale_parity.py mr kn      # only these languages
  python scripts/check_locale_parity.py --quiet    # counts only
Exit code 0 = no missing/extra keys, bad JSON or placeholder mismatches.
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKIP_DIRS = {"node_modules", ".next", ".venv", "AgentOutputs", "__pycache__", ".git"}
PLACEHOLDER = re.compile(r"\{\{\s*[\w.]+\s*\}\}|\{[a-zA-Z_][\w]*\}")
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
KANNADA = re.compile(r"[ಀ-೿]")
LATIN_WORD = re.compile(r"[A-Za-z]{2,}")
SCRIPT = {"mr": DEVANAGARI, "kn": KANNADA}
# Values that may legitimately stay identical to English.
KEEP_AS_IS = re.compile(
    r"^(ForKhatri|Vyapar|Milavn|Mangalya|Mangaly|Counsel|WhatsApp|English|हिन्दी|తెలుగు|मराठी|ಕನ್ನಡ|OK|UPI|PAN|GST|OTP|ID|URL|PDF|AI|₹.*|[\W\d_]*)$"
)


def leaves(obj, prefix=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from leaves(value, f"{prefix}.{key}" if prefix else key)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from leaves(value, f"{prefix}[{index}]")
    else:
        yield prefix, obj


def locale_dirs():
    for base in ("platform", "modules"):
        for dirpath, dirnames, _ in os.walk(os.path.join(ROOT, base)):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".next")]
            if os.path.basename(dirpath) == "locales" and os.path.isdir(os.path.join(dirpath, "en")):
                yield dirpath


def load(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle), None
    except Exception as error:  # noqa: BLE001
        return None, str(error)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    quiet = "--quiet" in sys.argv
    problems = 0
    grand = {}
    for loc in locale_dirs():
        rel = os.path.relpath(loc, ROOT)
        langs = sorted(d for d in os.listdir(loc) if os.path.isdir(os.path.join(loc, d)) and d != "en")
        if args:
            langs = [lang for lang in args if lang in langs or lang in args]
        print(f"\n== {rel}")
        for namespace in sorted(f for f in os.listdir(os.path.join(loc, "en")) if f.endswith(".json")):
            en, err = load(os.path.join(loc, "en", namespace))
            if err:
                print(f"  BAD JSON en/{namespace}: {err}")
                problems += 1
                continue
            en_leaves = dict(leaves(en))
            for lang in langs:
                path = os.path.join(loc, lang, namespace)
                stats = grand.setdefault((rel, lang), [0, 0, 0, 0])
                stats[0] += len(en_leaves)
                if not os.path.exists(path):
                    print(f"  {lang}/{namespace}: MISSING FILE ({len(en_leaves)} keys)")
                    stats[1] += len(en_leaves)
                    problems += 1
                    continue
                data, err = load(path)
                if err:
                    print(f"  BAD JSON {lang}/{namespace}: {err}")
                    problems += 1
                    continue
                other = dict(leaves(data))
                missing = [k for k in en_leaves if k not in other]
                extra = [k for k in other if k not in en_leaves]
                ph_bad = [
                    k for k in en_leaves
                    if k in other and sorted(PLACEHOLDER.findall(str(en_leaves[k]))) != sorted(PLACEHOLDER.findall(str(other[k])))
                ]
                same = []
                wrong_script = []
                if lang in SCRIPT:
                    for k, v in en_leaves.items():
                        if k not in other or not isinstance(v, str):
                            continue
                        stripped = PLACEHOLDER.sub("", v).strip()
                        if not LATIN_WORD.search(stripped) or KEEP_AS_IS.match(stripped):
                            continue
                        if other[k] == v:
                            same.append(k)
                        elif not SCRIPT[lang].search(str(other[k])):
                            wrong_script.append(k)
                stats[1] += len(missing)
                stats[2] += len(same) + len(wrong_script)
                stats[3] += len(ph_bad)
                if missing or extra or ph_bad:
                    problems += 1
                if not quiet and (missing or extra or ph_bad or same or wrong_script):
                    print(
                        f"  {lang}/{namespace}: en={len(en_leaves)} {lang}={len(other)} missing={len(missing)} "
                        f"extra={len(extra)} placeholders={len(ph_bad)} same-as-en={len(same)} no-{lang}-script={len(wrong_script)}"
                    )
                    for label, keys in (("missing", missing), ("extra", extra), ("placeholder", ph_bad), ("same", same), ("script", wrong_script)):
                        for k in keys[:8]:
                            print(f"      {label}: {k}")
                        if len(keys) > 8:
                            print(f"      {label}: … {len(keys) - 8} more")
    print("\nSUMMARY (keys in English / missing / untranslated-looking / placeholder mismatches)")
    for (rel, lang), (total, missing, same, ph) in sorted(grand.items()):
        print(f"  {lang}  {total:6d} {missing:5d} {same:5d} {ph:4d}  {rel}")
    print("RESULT", "OK" if problems == 0 else f"{problems} problem namespace(s)")
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
