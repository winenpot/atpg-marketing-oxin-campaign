# ADR-0007: A static PWA served by our nginx on the same origin as the API

**Status:** Accepted
**Date:** 2026-10-07
**Deciders:** Backend developer, Arman (frontend)

## Context

Players arrive by scanning a QR code with their phone camera. Every extra step (store
download, account creation in an app) loses people. Iranian users install apps from local
stores, and foreign app stores are inconsistently available. The frontend developer works
off-site.

## Decision

- Build a **Progressive Web App** as static files (for example Vite + React + TypeScript) and serve it from our nginx, with the API under `/api/` on the same domain.
- No Node.js server in production. No foreign CDNs, fonts, analytics or tag managers.
- Add "install to home screen" as a hint, not a requirement.

## Options considered

### Option A: static PWA, same origin (chosen)

**Pros:** QR → page in one step; no CORS; first-party cookie; strict CSP; one deploy target; works on any phone browser.
**Cons:** no native push on older iPhones; fewer device features (not needed).

### Option B: native app (Android + iOS)

Rejected: store friction and review delays; two codebases; the QR flow becomes "install first".

### Option C: Next.js with server-side rendering

Rejected: a Node server to run and secure for no SEO or performance need in a logged-in app.

## Trade-off analysis

Static files are the cheapest thing to host and the hardest thing to break.

## Consequences

- Easier: deploys are file copies; rollbacks are instant; caching is simple.
- Harder: no server-side rendering for link previews (posters link to the home page, which can have static meta tags).
- Revisit: a native shell (for example a WebView wrapper) only if push notifications become essential.

## Action items

1. [ ] Arman: A01–A03 in [TODO.md](../TODO.md#arman-frontend).
2. [ ] nginx serves `dist/` with long-cache fingerprinted assets and an uncached `index.html` (B12).
