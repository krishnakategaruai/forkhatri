import { writeFileSync } from 'node:fs';

import { computeGolden } from '../test/golden/golden.ts';

/* Rewrites the golden fixtures from the engine as it is now. Run only when a
 * change in results is intended, and review the diff before committing. */

const file = computeGolden();
writeFileSync(new URL('../test/golden/fixtures.json', import.meta.url), `${JSON.stringify(file, null, 2)}\n`);
console.log(`wrote ${file.charts.length} charts and ${file.pairs.length} pairs`);
