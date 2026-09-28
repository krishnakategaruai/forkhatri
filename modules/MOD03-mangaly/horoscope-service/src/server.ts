import { readFileSync } from 'node:fs';
import { createServer } from 'node:http';

import { createHandler } from './api/http.ts';
import { HoroscopeService } from './application/HoroscopeService.ts';
import { InMemoryHoroscopeStore, OwnersOnlyAccessPolicy } from './application/memory.ts';
import { createDefaultEngine } from './index.ts';

/* Local entry point. Listens on loopback only; mangaly-service is the only
 * intended caller. Storage is in memory (see README.md, "Persistence"). */

// Local settings from ./.env (gitignored) when present; real environment variables win.
try {
  const text = readFileSync(new URL('../.env', import.meta.url), 'utf8');
  for (const line of text.split(/\r?\n/)) {
    const m = /^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/.exec(line);
    if (m && process.env[m[1] as string] === undefined) process.env[m[1] as string] = m[2];
  }
} catch {
  // No .env: configuration comes from the environment only.
}

const token = process.env.HOROSCOPE_SERVICE_TOKEN;
if (!token || token.length < 24) {
  console.error('HOROSCOPE_SERVICE_TOKEN must be set (at least 24 characters). Refusing to start.');
  process.exit(1);
}
const port = Number(process.env.HOROSCOPE_PORT ?? 8013);

const log = (entry: Record<string, string | number>) => console.log(JSON.stringify({ at: new Date().toISOString(), ...entry }));

const engine = createDefaultEngine();
const service = new HoroscopeService({
  engine,
  store: new InMemoryHoroscopeStore(),
  policy: new OwnersOnlyAccessPolicy(),
  audit: { record: (e) => log({ audit: e.action, viewer: e.viewerAccountId, subjects: e.subjectIds.join(','), outcome: e.outcome }) },
});

createServer(createHandler(service, token, log, engine)).listen(port, '127.0.0.1', () => {
  log({ event: 'listening', port });
});
