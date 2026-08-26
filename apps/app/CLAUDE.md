# apps/app — React + Vite

The customer's whole experience: new project → wizard → review → involvement →
design window → build → reveal. Seven steps, documented in `docs/UX-FLOW.md`.

## The design system is not optional

`docs/DESIGN.md` holds the tokens and it is the single source of truth: the
drafting-table direction from ADR-0003, teal `#0B5563`, cool draft paper rather
than cream, semantic `verified` / `attention` / `error`, 7px card and 5px button
radii, structure through 1px lines rather than shadows, a 4px spacing grid.
Motion is minimal — things land, they do not bounce.

Take colours and type from the tokens. Do not introduce a hex value here.

## Say only what is true

This screen set makes promises about someone's money and someone's app, so the
copy is load-bearing:

- A preview is **not** a delivered app. A project that has only been through the
  design window says "This is your preview — nothing has been built yet" and
  offers **Build it**, never **Get the code**.
- Honest status is honest: "4 of 5 parts work" beats a green tick, and
  `unjudged` is a real state that must not be rendered as either pass or fail.
- Never say "nothing yet" before the answer is known — show that it is loading.

## What in-process tests cannot see

Every real bug found in this app was found by a browser, not by a test:
project cards that looked clickable and had no handler, a wizard that looped on
the free path, a build stream aborted by StrictMode, a preview presented as a
delivered app.

So: render under `StrictMode` in tests, give every control an `aria-label` and a
real `<button>` rather than a `<div>` with `cursor-pointer`, announce state
changes in a live region — and click the thing before saying it works.

## Talking to the api

Types come from `packages/shared`; do not restate a contract here. `VITE_API_URL`
points at the api, and the browser calls it directly — which is why a forwarded
Codespace needs port 3000 public, and why CORS breaks are an app-visible bug.

`npx vitest run` from this directory.
