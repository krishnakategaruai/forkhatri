# Provider limitations and validation

Checked on 2026-09-27. Only what was actually tested is recorded here. A
README's claims are not treated as validation.

## What does what

| Part | Source | Validated against |
|---|---|---|
| Planet positions (ascendant, Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, mean Rahu/Ketu) | `@prisri/jyotish` 1.1.12, pinned exactly, through `PrisriJyotishProvider` (the only file that imports it) | Independent astronomy; Drik Panchang's Moon |
| Rashi, nakshatra, pada, Moon sign half | Mangaly (`domain/zodiac.ts`), from the provider's longitudes | The same checks |
| Guna Milan: all eight kootas and the total | **Mangaly's own tables** (`domain/ashtakootaRules.ts`, rules v3) | **AstroSage, 205 pairs, all equal** |
| Mangal Dosha: presence and level | **Mangaly's rule** (`MANGAL_ASTROSAGE_V1`) | **AstroSage, 40 people, all equal** |
| South Indian 10 poruthams | **Mangaly's own rules** (`domain/poruthamRules.ts`, rules v4) | **ProKerala, every bride star × groom star (2,916 pairs): 9 poruthams equal on all; Rajju classical (below)** |

The library's own koota tables, total, "Good Match" verdict and Mangal rule
are **not used**. Its predictions, gemstones and remedies are never called.

## Why AstroSage is the reference

The owner's goal: every customer gets the correct number, the one they see when they check.
- **Most used:** AstroSage is the most-installed kundli service in India (70M+ app downloads; it states 80% of online matching runs on it).
- **Allowed to check:** its robots.txt allows automated access, so its tables could be read completely.
- **Drik Panchang:** it has the largest website audience. It was checked by hand (11 pairs), and its robots.txt asks automated agents to keep off its calculator.

## Validation

1. **Positions against independent astronomy:** 200 synthetic charts (1940–2008, 17 cities, 9 time zones), using Meeus lunar and solar series, JPL approximate elements and Meeus sidereal time.
   - **Largest difference:** Moon 0.011°, ascendant 0.006°, Sun 0.012°, Mars 0.036°, Venus 0.021°, Mercury 0.021°, Jupiter 0.12°, Saturn 0.18° (the last two limited by the reference itself).
   - **Placements:** rashi, nakshatra and pada agree in all 1,888 decisive comparisons.
2. **Moon against Drik Panchang:** within 0.02° for 10 births.
3. **Guna Milan against AstroSage:**
   - **What was checked:** 197 pairs covering every ordered Yoni animal pairing (all 196 cells read in both directions), 5 pairs completing the Vashya table, and 3 hand checks. Every koota and every total is equal (`test/reference/referenceSites.test.ts`).
   - **A real couple, end to end:** Kunal × Ananya scores 15.5 on both AstroSage and Mangaly, with every koota equal.
4. **Mangal Dosha against AstroSage:** 40 random synthetic people, with the level (none, low or high) equal for all (`test/reference/astrosageMangal.test.ts`).
   - **The rule found:** Mars in house 1, 4, 7, 8 or 12 counted from the ascendant and from the Moon. High when both, low when one.
   - **Not counted:** Venus, the 2nd house, and own-sign cancellation.

## Where the library differed (why its tables are not used)

Across 200 random pairs, the library's totals differ from AstroSage's rules in most pairs:

| Koota | Library | AstroSage (= Mangaly) |
|---|---|---|
| Yoni | Simplified table | AstroSage's 14×14 table; 6 animal pairs depend on who is the groom |
| Vashya | Whole signs; Manava–Keeta 1; Chatushpada–Vanachara 0.5 both ways | Sagittarius and Capricorn split at 15°; Manava groom with Keeta bride 0; Vanachara groom with Chatushpada bride 0.5, reverse 0 |
| Gana | Rakshasa groom with Deva bride 0 | 1 |
| Bhakoot | Same sign lord restores 7 | 0 |
| Nadi | Same sign with a different star keeps 8 | 0 |
| Mangal | Lagna, Moon and Venus; houses 1, 2, 4, 7, 8, 12; own-sign cancellation; no level | Lagna and Moon; houses 1, 4, 7, 8, 12; no cancellation; high or low |

`docs/differential-report.json` lists every difference, with its inputs.

## Porutham against ProKerala

- **Why ProKerala:** it is the most-visited site offering South Indian matching, and its robots.txt allows automated checks. Its star form was read for all 54 × 54 bride and groom star options, with stars that span two signs split by pada (`test/fixtures/prokerala-porutham.json`).
- **Nine poruthams match exactly on all 2,916 pairs:** Dina, Gana, Mahendra, Stree Deergha, Yoni, Vedha, Rasi, Rasi Adhipathi and Vasya (`test/reference/prokeralaPorutham.test.ts`).
- **Where ProKerala differs from common textbook forms** (Mangaly follows ProKerala):
  - Dina also agrees for the same star and for counts of 10 and 19.
  - Stree Deergha agrees from a count of 10.
  - Yoni is decided by whether the bride's star is a "female" star.
  - Rasi, Vasya and Rasi Adhipathi use ProKerala's own sign and lord tables.
  - Vedha leaves out the Mrigashira–Chitra–Dhanishta group.
- **Rajju is the exception, and it is deliberate.** ProKerala's Rajju contradicts itself. It gives a star a different Rajju group depending on the partner, and its detailed form calls "Nabhi | Nabhi" a Good match although the rule is that the same group does not agree. Rajju is one of the two poruthams treated as essential, so Mangaly uses the classical definition every Tamil and Kerala text gives: five groups by star, and the same group does not agree. It therefore differs from ProKerala's star form on 792 of 2,916 pairs. The test pins that number.
- **System label:** ProKerala's detailed form reports "Dashakoot (Kerala)" whichever system is selected, and on one checked pair it gave Stree Deergha a half point where its star form gives a full point. Mangaly follows the star form, which is internally consistent.

## Where Drik Panchang differs from AstroSage

Recorded in `test/fixtures/reference-site-checks.json`:
- **Yoni:** some cells differ, e.g. Horse–Serpent is Drik 1, AstroSage 2.
- **Nadi:** for the same sign with a different star, Drik keeps 8.
- **Vashya:** Vanachara groom with Chatushpada bride is Drik 0.
- **Totals:** Drik's headline rounds half points down.

Where a Nadi case applies, Mangaly's profile screen says that some panchangs keep the 8 points.

## Known limitations

- **Ayanamsha:** the Lahiri value at J2000 is shared by the library and our reference, so it is not independently proven. A nutation inconsistency of up to about 0.005° could flip a result only within about 20 seconds of clock time of a boundary.
- **Porutham variants:** Tamil and Kerala traditions differ on a few poruthams. Mangaly follows ProKerala (Kerala Dashakoota) for nine, and the classical definition for Rajju.
- **Supported range:** births 1900–2100. Time zones come from the IANA database, and wartime India, daylight saving, skipped and repeated hours, and +05:45 are all tested.
- **Places:** a village not in the list means choosing the nearest town, which moves the ascendant by a fraction of a degree.

## Before production

1. **Licence:** get the library's licence file or written ISC confirmation (see LICENSES.md).
2. **Rules maintenance:** re-run `scripts/astrosage-calibrate.ts` and `scripts/astrosage-mangal.ts` periodically, and before any rules change. If AstroSage changes its tables, the replay tests fail.
3. **Ayanamsha:** check the anchor against a published ephemeris for a few dates.
