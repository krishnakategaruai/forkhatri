# MOD01 Vyapar documentation coverage report (2026-11-22)

Method: inventory from the live OpenAPI, live database, migration files, config.py and web page routes; then string match in the documents.

| Item | Inventoried | Documented | Left out |
|---|---|---|---|
| API operations | 268 | 268 (API-REFERENCE.md) | 0 |
| Database tables | 63 | 63 (07a-er-model-as-built.md) | 0 |
| Migrations | 33 | 33 (07a-er-model-as-built.md) | 0 |
| Service settings | 58 | 58 (architecture.md) | 0 [] |
| Web page routes | 38 | 38 (03-ux.md addendum, grouped rows) | 0 [] |

Not inventoried (reason): individual web components (about 150 files, summarised by folder in the UX/UI addenda); per-column meaning (names, types, constraints are listed; meaning is in 07a-er-model.md); per-endpoint request field lists (schema names only; fetch /openapi.json for fields); SECURITY DEFINER function bodies (names only); the MCP tool list (about 73 tools, see vyapar-mcp/vyapar_mcp/server.py). The Auth column in API-REFERENCE is a heuristic from route dependencies. Screens were derived mainly from code per the owner instruction, with a short live pass at 390 px.
