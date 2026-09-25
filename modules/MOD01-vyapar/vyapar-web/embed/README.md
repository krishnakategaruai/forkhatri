# Vyapar embeddable surfaces

These are self-contained Vyapar components that another React app can mount.

- **Needs:** an SDK instance and, optionally, a host config.
- **Contains:** no ForKhatri code.
- **Loads data:** through the SDK you pass in.
- **Languages:** English, Hindi and Telugu, from Vyapar's own translations.

## Components

| Export | What it shows |
|---|---|
| `OpportunityDetailPanel` | The full opportunity detail, with the same view and behaviour as the `/opportunities/[id]` route but without the page frame. It covers facts, fit, the poster, similar opportunities and every member action: save, share, apply or enquire, not interested, "Why this?", and the poster's lifecycle actions. |
| `OpportunityCard` | One opportunity card. The `variant` is `"feed"`, `"sponsored"` or `"similar"`. |
| `ProfileRecommendations` | A block of recommended business or professional profiles for any loader, for example `() => sdk.listings.similar(id)`. It renders nothing when there are no profiles. |
| `ProfileRecommendationsView` | Presentational only: you pass the `cards`. |

Building blocks are exported as well:
- `OpportunityDetailView` and `useOpportunityDetailController`;
- the data hooks (`useOpportunity`, `useFeed`, `useListing`…);
- `HostProvider` and `useSdk`.

## Usage

```tsx
import {
  VyaparEmbedProvider,
  OpportunityDetailPanel,
  createVyaparSdk,
  bearerTokenAuth,
} from "vyapar-web/embed";

const sdk = createVyaparSdk({
  baseUrl: "https://vyapar-api.example.com",
  auth: bearerTokenAuth(() => session.vyaparToken), // or cookieSessionAuth()
  language: () => currentLanguage,                   // sent as X-Vyapar-Language
});

export function OpportunityDrawer({ id, language }: { id: string; language: "en" | "hi" | "te" }) {
  return (
    <VyaparEmbedProvider sdk={sdk} language={language}>
      <OpportunityDetailPanel opportunityId={id} />
    </VyaparEmbedProvider>
  );
}
```

### Language

When the `language` prop changes:
- every label switches live;
- the data hooks re-fetch, so text translated on the server (skill names, labels) follows the new language.

The SDK's `language` provider should return the same value.

### Host config

`host` defaults to the standalone host: neutral brand, no development tools, and Vyapar's own URLs. To link into your own routes, pass a config with your own `routes`:

```tsx
import { standaloneHost, defaultRoutes } from "vyapar-web/embed";

const myHost = {
  ...standaloneHost,
  routes: {
    ...defaultRoutes,
    opportunity: (id) => `/jobs/${id}`,
    listing: (id) => `/providers/${id}`,
  },
};

<VyaparEmbedProvider sdk={sdk} host={myHost}>…</VyaparEmbedProvider>
```

### Authentication

Pick the auth strategy that matches the backend's identity providers:

| Strategy | Sends | When |
|---|---|---|
| `bearerTokenAuth(token)` | `Authorization: Bearer …` | Personal access or agent tokens |
| `cookieSessionAuth()` | `credentials: "include"` | The host's session cookie |
| `devHeaderAuth()` | `X-Dev-Member-Id` | Development only |

Never put a token in `NEXT_PUBLIC_*` environment variables.

## Requirements and limits

- **React 19 and Next.js App Router.** The cards use `next/link` and view transitions, as the rest of Vyapar does. A non-Next host needs a `next/link` / `next/navigation` shim.
- **Styles.** Import Vyapar's `app/globals.css`, or provide the same `vy-*` classes and design tokens.
- **Every call uses your SDK.** Every block these components render, including the report sheet, the performance report, reviews and the verification panel, calls through the SDK instance you pass in.
