/**
 * The spike's actual question: does a booking made through the UI persist?
 *
 * Not "does the page render" — the earlier sandbox spike already proved that.
 * This fills the real form, submits it through the app's own server action, then
 * reloads a DIFFERENT page and asserts the row is there, in the UI and in the
 * database. Nothing is seeded: the app creates the row.
 */

import { chromium } from "playwright";

const BASE = process.env.SPIKE_BASE ?? "http://127.0.0.1:45001";
const GUEST = `Ada ${Date.now()}`;

function check(label, ok, detail = "") {
  console.log(`${ok ? "  PASS" : "  FAIL"}  ${label}${detail ? ` — ${detail}` : ""}`);
  if (!ok) process.exitCode = 1;
  return ok;
}

// The sandbox ships a Chromium that this Playwright build did not download.
// Pointing at it beats fetching a second copy of the same browser.
const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
const page = await browser.newPage();
// The message TEXT of a 404 names nothing — "Failed to load resource: ... 404"
// is the same string for a missing favicon and a broken API route. Only the URL
// tells them apart, which is the whole reason the engine's console classifier
// keys on origin (core/console.py). The harness has to do the same or it fails
// every run on the favicon nobody wrote.
const errors = [];
page.on("console", (m) => {
  if (m.type() !== "error") return;
  errors.push(`${m.text()} (${m.location()?.url ?? "unknown"})`);
});
page.on("pageerror", (e) => errors.push(String(e)));

try {
  console.log("1. the list starts empty (nothing seeded)");
  await page.goto(`${BASE}/booking`, { waitUntil: "networkidle" });
  const before = await page.locator('[data-scio-id="booking-list"] li').count();
  console.log(`     rows before: ${before}`);

  console.log("2. fill the real form and submit it");
  await page.goto(`${BASE}/booking/new`, { waitUntil: "networkidle" });
  await page.fill('[data-scio-id="booking-form-name"]', GUEST);
  await page.fill('[data-scio-id="booking-form-phone"]', "+46 70 123 45 67");
  await page.fill('[data-scio-id="booking-form-when"]', "2026-09-01T19:00");
  await page.fill('[data-scio-id="booking-form-size"]', "4");
  await page.click('[data-scio-id="booking-form-submit"]');

  await page.waitForSelector('[data-scio-id="booking-form-message"]', { timeout: 20000 });
  const message = await page.textContent('[data-scio-id="booking-form-message"]');
  check("the app confirms the booking", /confirmed/i.test(message ?? ""), message?.trim());

  console.log("3. RELOAD a different page — is it still there?");
  await page.goto(`${BASE}/booking`, { waitUntil: "networkidle" });
  const after = await page.locator('[data-scio-id="booking-list"] li').count();
  const shown = await page.textContent('[data-scio-id="booking-list"]').catch(() => "");

  check("the list grew by one", after === before + 1, `${before} -> ${after}`);
  check("the booking is visible after reload", (shown ?? "").includes(GUEST));

  console.log("4. is it actually in the DATABASE, not just the page?");
  const res = await fetch(`${BASE}/api/spike/rows`);
  const rows = await res.json();
  const match = rows.find((r) => r.guest_name === GUEST);
  check("the row exists in Postgres", Boolean(match), match ? `id=${match.id}` : "not found");
  check("the values round-tripped", match?.party_size === 4, `party_size=${match?.party_size}`);

  const appErrors = errors.filter((e) => !/favicon|apple-touch-icon/.test(e));
  check("no console errors from the app", appErrors.length === 0, appErrors[0] ?? "");
} finally {
  await browser.close();
}

console.log(process.exitCode ? "\nVERDICT: something failed" : "\nVERDICT: persistence verified");
