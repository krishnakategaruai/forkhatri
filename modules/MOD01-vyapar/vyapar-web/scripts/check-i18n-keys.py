#!/usr/bin/env python3
"""i18n key checker for vyapar-web (CI).

Finds every literal t("namespace:key") in app/**/*.ts(x) and fails when the
key is missing from locales/en, hi or te (plural keys _one/_other count).
Keys built from template strings (${...}) are skipped: they cannot be read
statically. Usage (from vyapar-web): python scripts/check-i18n-keys.py [web-dir] [files...]
Exit code 0 = no missing keys, 1 = missing keys (listed).
"""
import json, os, re, sys, subprocess
web = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
files = sys.argv[2:] if len(sys.argv) > 2 else None
loc = os.path.join(web, "locales")
cat = {}
for lang in ("en", "hi", "te"):
    for f in os.listdir(os.path.join(loc, lang)):
        try: cat[(lang, f[:-5])] = json.load(open(os.path.join(loc, lang, f), encoding="utf-8"))
        except Exception as e: print("BAD JSON", lang, f, e)
def has(lang, ns, key):
    d = cat.get((lang, ns))
    if d is None: return False
    for part in key.split("."):
        if isinstance(d, dict) and part in d: d = d[part]
        elif isinstance(d, dict) and any(k.startswith(part + "_") for k in d): return True  # plurals
        else: return False
    return True
pat = re.compile(r"""\bt\(\s*["'`]([a-zA-Z]+):([a-zA-Z0-9_.]+)["'`]""")
if not files:
    files = [os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(web, "app")) for f in fs if f.endswith((".tsx", ".ts"))]
missing = {}
for path in files:
    src = open(path, encoding="utf-8").read()
    for m in pat.finditer(src):
        ns, key = m.group(1), m.group(2)
        if "${" in key or key.endswith("."): continue
        for lang in ("en", "hi", "te"):
            if not has(lang, ns, key):
                missing.setdefault((os.path.relpath(path, web), ns, key), []).append(lang)
for (p, ns, key), langs in sorted(missing.items()):
    print(f"{p}: {ns}:{key} missing in {','.join(langs)}")
print("TOTAL", len(missing))
sys.exit(1 if missing else 0)
