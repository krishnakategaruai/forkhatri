import { writeFileSync } from 'node:fs';

import { runDifferential } from '../test/differential/harness.ts';

/* Runs the differential harness and writes the full report (every mismatch,
 * with input, provider output and reference output) for review. The inputs
 * are synthetic; the report contains no real person's data. */

const report = runDifferential();
const out = new URL('../docs/differential-report.json', import.meta.url);
writeFileSync(out, `${JSON.stringify(report, null, 2)}\n`);

console.log(JSON.stringify({ ...report, mismatches: `${report.mismatches.length} (see docs/differential-report.json)` }, null, 2));
