# Mangaly horoscope matching engine (V1)

A deterministic, explainable calculation service for Mangaly's **optional**
traditional horoscope layer:
- **Ashtakoota / Guna Milan:** 8 kootas, out of 36.
- **Porutham (South Indian):** 10 poruthams; Rajju and Vedha are marked essential.
- **Mangal (Kuja) Dosha:** calculated separately, never part of the 36.

It is **not** Mangaly's compatibility model. It never combines with the
personality, lifestyle or practical scores. It never gives a verdict ("good
match", "not recommended") or a recommendation. It never ranks people, hides
them or rejects them. It calculates the traditional result, and the family
decides what it means to them.

## Architecture

```
Mangaly (mangaly-service)
   │  internal HTTP (service token, x-mangaly-viewer)
   ▼
src/api/http.ts ── HoroscopeService (opt-in, AccessPolicy, audit, append-only store)
                        │
                        ▼
                   HoroscopeEngine (normalise → sample → canonical chart → match)
                        │                         │
                        ▼                         ▼
        HoroscopeProvider interface     domain/ashtakootaRules.ts (Mangaly's koota tables)
                        │               domain/mangalRules.ts     (structured Mangal rule)
                        ▼
        provider/prisri/PrisriJyotishProvider.ts  ← the only file that imports @prisri/jyotish
                        │
                        ▼
                 @prisri/jyotish → astronomy-engine
```

- **`src/domain/`:** Mangaly's own types, configuration, zodiac arithmetic, birth-time handling, koota and Mangal rules, and explanation codes. It is provider-independent.
- **`src/provider/HoroscopeProvider.ts`:** the replaceable boundary. A future `CommercialHoroscopeProvider` or `MangalyHoroscopeProvider` implements this interface; nothing else changes.
- **The provider's role:** it supplies **planetary positions only**. Koota scores and Mangal Dosha come from Mangaly's rules (rules v3), which equal AstroSage's on all 205 checked pairs and 40 checked people. See `docs/PROVIDER-LIMITATIONS.md`.
- **Configuration (`src/domain/config.ts`):** the values below are stated explicitly and appear in every result. None of them is a provider default.
  - zodiac: sidereal
  - ayanamsha: Lahiri
  - houses: whole sign
  - matching: Ashtakoota
  - rules version: `mangaly-ashtakoota-rules/4`
  - pipeline version: `mangaly-horoscope/1.0.0`
  - Mangal rule set: `MANGAL_ASTROSAGE_V1`

### Birth time
- **Time zone:** local time at the birthplace becomes UTC through the birthplace's IANA zone, including historical offsets (India's 1942–45 war time, daylight saving abroad). The server's zone is never used, and IST is never assumed.
- **Clock changes:** a time that a clock change skipped is refused. A time it repeated needs `utcOffsetSeconds`.
- **Precision `EXACT`:** one instant.
- **Precision `APPROXIMATE`:** requires `birthTimeUncertaintyMinutes`. The window is sampled at 25 instants, and a field (rashi, nakshatra, pada, ascendant, the Moon's sign half) is reported only if it is the same at every instant. Otherwise it is `null`, with a warning.
- **Precision `UNKNOWN`:** the same method over the whole local day. Nothing is guessed. If the Moon's rashi and nakshatra hold all day, Ashtakoota is still calculated. Otherwise it is `NOT_DETERMINABLE`.

### Privacy
- **Owner decision (2026-09-27):** in Mangaly, birth time and place of birth are part of the public biodata.
- **This service still:** logs no birth details, returns none in errors, and gives the full chart (with inputs) only to its owner. A match result contains no birth inputs.
- **Authorisation:** it goes through an `AccessPolicy`. The default is owners-only. Mangaly supplies its circle-aware policy.

### Determinism and versions
- **Ids:** chart and match ids are hashes of the normalised input, configuration, provider name and version, pipeline version and rules version. The same inputs always give the same ids and results.
- **No overwriting:** stored results are append-only. A different result under an existing id is refused.
- **No mixing versions:** charts from another provider, rules version or configuration are refused for matching (`PROVIDER_VERSION_MISMATCH`), never silently mixed.
- **Version pin:** the adapter refuses any `@prisri/jyotish` version other than the validated 1.1.12.

## Local setup

Requires Node 24 or newer. TypeScript runs directly; there is no build step.

```bash
cd modules/MOD03-mangaly/horoscope-service
npm install
npm test                      # unit, integration, golden, differential, reference-site tests
npm run typecheck
npm run differential:report   # writes docs/differential-report.json (every mismatch, with inputs)
npm run golden:update         # ONLY when a change in results is intended and reviewed
HOROSCOPE_SERVICE_TOKEN=<24+ chars> HOROSCOPE_PORT=8013 npm start
```

The server listens on 127.0.0.1 only. Storage is in memory (see "Persistence").

## API

All routes except `/health` need `Authorization: Bearer $HOROSCOPE_SERVICE_TOKEN`
and `x-mangaly-viewer: <account id>`.

| Route | What |
|---|---|
| `POST /horoscope/chart` | `{ownerAccountId, optedIn, birthDetails}` → summary (no birth inputs). 409 if not opted in. |
| `GET /horoscope/chart/{chartId}` | The owner's full chart. 403 for anyone else. |
| `POST /horoscope/match` | `{groomChartId, brideChartId}` → match. 201 new, 200 existing. |
| `GET /horoscope/match/{matchId}` | A stored match. 403 unless the policy allows. |
| `POST /horoscope/calculate/chart` | Stateless, for mangaly-service: `{birthDetails}` → canonical chart (with this person's Mangal result). |
| `POST /horoscope/calculate/match` | Stateless: `{groom, bride}` canonical charts → match. 409 if a chart is from another rules or provider version. |
| `POST /horoscope/calculate/scores` | Stateless: up to 500 `{groom, bride}` Moon placements → totals, for the Discover filter. |

Errors are `{error: {code, message, fields}}`. The message names the field, never the value.

### Example

```http
POST /horoscope/chart
{ "ownerAccountId": "arjun", "optedIn": true,
  "birthDetails": { "birthDate": "1995-01-09", "birthTime": "22:30", "birthTimePrecision": "EXACT",
                    "birthLocation": "Hyderabad", "latitude": 17.3842, "longitude": 78.4564,
                    "timezone": "Asia/Kolkata" } }
→ 201 { "chartId": "chart_…", "calculationId": "hc_94c2…", "rulesVersion": "mangaly-ashtakoota-rules/2",
        "configuration": {"zodiacSystem":"SIDEREAL","ayanamsha":"LAHIRI","houseSystem":"WHOLE_SIGN"},
        "rashi": 1, "nakshatra": 1, "nakshatraPada": 3, "warnings": [] }

POST /horoscope/match   { "groomChartId": "chart_…", "brideChartId": "chart_…" }
→ 201 { "matchId": "hm_0949…", "traditionalSystem": "ASHTAKOOTA",
        "ashtakoota": { "status": "CALCULATED", "totalScore": 23.5, "maxScore": 36,
                        "kootas": [ { "koota": "VARNA", "score": 1, "maxScore": 1,
                                      "groomClass": "KSHATRIYA", "brideClass": "VAISHYA",
                                      "explanation": { "code": "KOOTA.VARNA.FULL", "params": { "basis": "RASHI_VARNA_CLASS", … } } },
                                    … 7 more ] },
        "mangal": { "groom": { "status": "PRESENT", "relevantPlacements": [ { "reference": "LAGNA", "house": 1 } ], … },
                    "bride": { "status": "PRESENT", … }, "pairing": "BOTH_PRESENT" },
        "presentation": { "layer": "TRADITIONAL_OPTIONAL",
                          "headline": { "code": "ASHTAKOOTA_SCORE", "score": 23.5, "outOf": 36 },
                          "noticeCodes": [ "HOROSCOPE.NOTICE.NOT_SCIENTIFIC_NOT_A_PREDICTION", … ] } }
```

AstroSage shows 23.5 for this pair, the same as Mangaly now does (rules v3).
Drik Panchang shows 22 (Horse–Serpent Yoni 1 instead of 2, and a total
rounded down).

## Tests

| Suite | What it proves |
|---|---|
| `test/unit/*` | Birth-time conversion (hand-computed instants, server-zone independence); validation; zodiac arithmetic; Mangal structure; sampling for imprecise times; determinism; caching; version refusal; that the Prisri adapter leaks no library types; that no file outside the adapter imports the library |
| `test/integration/*` | Service opt-in, authorisation, audit, append-only store; the HTTP API end to end; logs free of birth data |
| `test/golden/*` | 69 charts and 69 pairs (60 synthetic plus 9 edge cases) locked to fixtures; any change in results fails |
| `test/differential/*` | 200 charts against independent astronomy; 200 pairs, all 1,296 Moon-placement pairs and all 20,736 Mangal inputs, provider against Mangaly's rules; every mismatch categorised, none unexplained |
| `test/reference/referenceSites.test.ts` | 205 AstroSage pairs: every koota and total equal. 11 Drik Panchang pairs: equal except the documented Drik/AstroSage differences |
| `test/reference/astrosageMangal.test.ts` | 40 AstroSage Mangal Dosha levels: all equal |
| `test/reference/prokeralaPorutham.test.ts` | 2,916 ProKerala Porutham results: 9 poruthams equal on all; Rajju classical, with its differences pinned |

## Persistence

Mangaly keeps charts and matches in its own Postgres (migration 056,
`mangaly_horoscope.chart` and `.match`, append-only), through the stateless
routes: mangaly-service calculates a person's chart when they save their
horoscope section, and a match when a profile is opened. Who may read whose
chart is decided in SQL: the same people who may read the biodata.
`InMemoryHoroscopeStore` backs only the stateful routes (tests, local use).
The earlier in-process Python engine (migration 049, never applied) was
removed.

## Documents

- `docs/PROVIDER-LIMITATIONS.md`: what was validated, discrepancies, recommendation.
- `docs/LICENSES.md`: dependency and data licence inventory and notices.
- `docs/differential-report.json`: the full differential output.
