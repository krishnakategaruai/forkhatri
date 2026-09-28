# Dependency and data licence inventory

Checked on 2026-09-27 against each package's `package.json`, its source
repository and the files actually shipped in `node_modules`.

## Runtime dependencies (`npm ls --all --omit=dev`)

| Package | Version | Declared licence | Where verified | Licence file shipped? | Commercial use |
|---|---|---|---|---|---|
| `@prisri/jyotish` | 1.1.12 (pinned exactly) | ISC | `package.json` `"license": "ISC"`; README badge on github.com/prisriorg/jyotish | **No.** Neither the npm package nor the GitHub repository contains a LICENSE file (GitHub API: no licence detected). | Permitted by ISC. See the open issue below. |
| `astronomy-engine` (transitive) | 2.1.19 | MIT | LICENSE in github.com/cosinekitty/astronomy | No, not in the npm package. The full text is reproduced below. | Permitted by MIT, with the notice kept. |

There are no other runtime dependencies. The development dependencies are
`typescript` (Apache-2.0) and `@types/node` (MIT). They are not shipped.

### Open issue: `@prisri/jyotish` has no licence text

- **What exists:** ISC is declared in `package.json` and in the README badge. That is normally taken as a grant.
- **What's missing:** ISC's condition is that the copyright and permission notice appear in copies, and the author has not published that text. So there is no exact notice to reproduce.
- **Before production:** ask the author (Priyansh Srivastava, github.com/prisriorg) to add a LICENSE file, or get written confirmation of ISC for version 1.1.12. Until then, the notice below is kept on the basis of the declaration.

## Data

| Data | Licence | Attribution |
|---|---|---|
| GeoNames places (`mangaly-service/app/components/places/data/places.tsv`) | CC BY 4.0 | "Places: GeoNames (CC BY 4.0)" is shown under the place search. See that folder's ATTRIBUTION.md. |
| Indian district town names (`indian_district_towns.csv`) | Mangaly's own list | None needed. |

- **Koota tables:** the tables in `src/domain/ashtakootaRules.ts` are traditional Jyotish rules, which are facts and not anyone's code.
- **Yoni table:** it is the one printed by most references. The same values appear in the Maitreya program's documentation (Saravali, CC BY-SA). No code or text was copied from either.
- **Drik Panchang and AstroSage:** they were used only to read results, by hand, for 14 synthetic pairs. Nothing from them is included.

Not used, deliberately:
- **Swiss Ephemeris:** it is AGPL or commercial.
- **Astropy:** it is not needed.
- **A JPL ephemeris:** it belongs to the unused Python component.

## Notices

### @prisri/jyotish (declared ISC)

    ISC License
    Copyright (c) Priyansh Srivastava
    (Licence text not published by the author; see "Open issue" above.)

### astronomy-engine (MIT)

    MIT License

    Copyright (c) 2019-2025 Don Cross <cosinekitty@gmail.com>

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
