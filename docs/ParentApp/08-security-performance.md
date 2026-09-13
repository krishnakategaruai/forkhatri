---
project: ForKhatri
artifact: Parent Application Security and Performance
step: 8
status: Ready for Review
---

# Parent Application Security and Performance

## Security requirements

- Do not place credentials, API keys, or personal secrets in the static files.
- Treat demo member state as non-production data.
- Escape or text-render dynamic member/module content to prevent XSS.
- Use the parent identity/session contract for production authentication.
- Enforce authorization server-side; hiding a module card is not authorization.
- Do not surface sensitive Mangaly or financial information in generic parent summaries without an explicit contract.
- Add CSP, HTTPS, secure cookies, CSRF protection, and dependency scanning when a backend is connected.

## Performance baseline

- First meaningful parent content should be visible without waiting for module data.
- Avoid blocking third-party fonts or scripts in the first slice.
- Keep the initial page lightweight and dependency-free.
- Lazy-load future module data and module-specific bundles.
- Preserve usable rendering when a module request times out.

## Accessibility baseline

- Keyboard access for all actions.
- Visible focus state.
- Semantic landmarks and heading order.
- Sufficient contrast for text and status labels.
- Reduced-motion support.
- No information conveyed by color alone.

