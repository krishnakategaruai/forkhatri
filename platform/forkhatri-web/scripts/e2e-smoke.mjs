// End-to-end smoke test for the ForKhatri web entrance.
// Requires: entrance on :3100 (npm run dev), Identity & Trust Service on :8100.
// Usage: node scripts/e2e-smoke.mjs [scenarioName ...]
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const PLAYWRIGHT =
  process.env.PLAYWRIGHT_PATH ?? "C:/Users/krish/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright";
const { chromium } = require(PLAYWRIGHT);

const BASE = process.env.BASE ?? "http://localhost:3100";
const IDENTITY = process.env.IDENTITY ?? "http://localhost:8100";
const MILAVN = "http://localhost:3001";
const PASSWORD = "ForKhatri-dev-2026";
const DEV_MEMBER = "9999900001";
const DATA_MEMBER = "+919800000001";

const here = path.dirname(fileURLToPath(import.meta.url));
const LOGS = path.resolve(here, "..", ".logs");
mkdirSync(LOGS, { recursive: true });

const PHONE = { width: 390, height: 844 };
const DESKTOP = { width: 1440, height: 900 };

const results = [];
function check(scenario, name, ok, detail = "") {
  results.push({ scenario, name, ok: !!ok, detail: String(detail).slice(0, 400) });
  console.log(`${ok ? "PASS" : "FAIL"}  [${scenario}] ${name}${detail ? ` — ${String(detail).slice(0, 200)}` : ""}`);
}

const settle = (page, ms = 800) => page.waitForTimeout(ms);
async function shot(page, name) {
  await settle(page, 700);
  const file = path.join(LOGS, `${name}.png`);
  await page.screenshot({ path: file });
  return file;
}

async function newPage(browser, { viewport = PHONE, colorScheme = "dark", locale = "en-US", reducedMotion = "no-preference" } = {}) {
  const context = await browser.newContext({ viewport, colorScheme, locale, reducedMotion, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(`pageerror: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });
  return { context, page, errors };
}

async function passwordSignIn(page, identifier) {
  await page.getByRole("button", { name: "Use a password instead" }).click();
  await page.locator(".field-plain input").fill(identifier);
  await page.locator('input[autocomplete="current-password"]').fill(PASSWORD);
  await page.locator('form button[type="submit"].btn-primary').click();
}

async function resetLanguage(page) {
  // Leave dev members in English so later runs start from the same state.
  await page.evaluate(async (api) => {
    await fetch(`${api}/v1/me`, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ preferred_language: "en" }),
    });
  }, IDENTITY);
}

const scenarios = {
  // Arrival -> wrong code -> right code -> name step -> hub; then intent chips and entering Milavn.
  async codeSignUp(browser) {
    const s = "codeSignUp";
    const { context, page, errors } = await newPage(browser);
    await page.goto(BASE);
    await page.locator(".question").waitFor();
    check(s, "arrival asks for identifier", (await page.locator(".question").textContent()).includes("mobile number or email"));
    await shot(page, "phone-dark-en-01-arrival");

    const number = `9${String(Math.floor(Math.random() * 1e9)).padStart(9, "0")}`;
    await page.locator("[data-step-field]").fill(number);
    await page.getByRole("button", { name: "Send code" }).click();
    await page.locator(".code-input").waitFor();
    const devCode = (await page.locator(".dev-code code").textContent())?.trim();
    check(s, "development code hint shown", /^\d{6}$/.test(devCode ?? ""), devCode);
    check(s, "identifier collapsed into a chip", await page.locator(".thread-chip").count() === 1);
    check(s, "resend countdown visible", await page.locator(".resend-wait").isVisible());
    await shot(page, "phone-dark-en-02-code");

    const wrong = devCode === "000000" ? "111111" : "000000";
    await page.locator(".code-input").fill(wrong);
    await page.locator(".error-text").waitFor({ timeout: 8000 });
    check(s, "wrong code shows friendly error", (await page.locator(".error-text").textContent()).includes("isn't right"));
    await shot(page, "phone-dark-en-03-code-error");

    await page.locator(".code-input").fill(devCode);
    await page.locator(".question", { hasText: "What should we call you?" }).waitFor({ timeout: 8000 });
    check(s, "new identifier reaches name step", true);
    await shot(page, "phone-dark-en-04-name");

    await page.locator("[data-step-field]").fill("Asha Khatri");
    await page.getByRole("button", { name: "Enter ForKhatri" }).last().click();
    await page.locator(".greeting").waitFor({ timeout: 10000 });
    const greeting = await page.locator(".greeting").textContent();
    check(s, "hub greets the new member", greeting.includes("Asha"), greeting);
    check(s, "all six modules rendered", (await page.locator(".module-list > li").count()) + (await page.locator(".coming-tile").count()) === 6);
    check(s, "not-yet-open modules are not buttons", (await page.locator(".coming-tile button, button.coming-tile").count()) === 0);
    check(s, "hub starts at the top after sign-in", (await page.evaluate(() => window.scrollY)) === 0, await page.evaluate(() => window.scrollY));
    check(s, "bell sits left of avatar, avatar right-most", await page.evaluate(() => {
      const actions = document.querySelector(".topbar-actions");
      const kids = [...actions.children];
      return kids.length === 2 && kids[0].getAttribute("aria-label") === "Notifications" && kids[1].classList.contains("avatar-btn");
    }));
    await shot(page, "phone-dark-en-05-hub");
    // The hub now fits one screen, so force a short viewport to prove content scrolls under an opaque header.
    await page.setViewportSize({ width: 390, height: 460 });
    await page.mouse.wheel(0, 260);
    await settle(page, 400);
    const header = await page.evaluate(() => ({
      bg: getComputedStyle(document.querySelector(".topbar")).backgroundColor,
      scrolled: document.querySelector(".app").dataset.scrolled,
      scrollY: window.scrollY,
    }));
    check(s, "header is opaque over scrolled content", !/rgba\(.*,\s*0\)|transparent/.test(header.bg) && header.scrolled === "true" && header.scrollY > 0, JSON.stringify(header));
    await shot(page, "phone-dark-en-06-hub-scrolled");
    await page.mouse.wheel(0, -260);
    await page.setViewportSize(PHONE);

    // Inline intent input (no dialog).
    await page.locator("#ask-input").fill("cricket this weekend near me");
    await settle(page, 900);
    const chips = await page.locator(".u-chip").allTextContents();
    check(s, "understanding chips for cricket phrase", JSON.stringify(chips) === JSON.stringify(["Milavn", "activity", "this weekend", "near you"]), JSON.stringify(chips));
    check(s, "Milavn row highlighted at the top", (await page.locator(".module-row").first().getAttribute("class")).includes("is-match") && (await page.locator(".module-row .module-name").first().textContent()) === "Milavn");
    await shot(page, "phone-dark-en-08-intent-cricket");

    await page.locator("#ask-input").fill("need a plumber near me");
    await settle(page, 600);
    const note = await page.locator(".ask-note").first().textContent().catch(() => "");
    check(s, "unavailable module said plainly", note.includes("Vyapar isn't open yet"), note);
    await shot(page, "phone-dark-en-09-intent-vyapar");

    await page.locator("#ask-input").fill("cricket this weekend near me");
    await settle(page, 400);
    // Hold the enter response briefly so the "Entering Milavn" veil can be seen and captured.
    await context.route(`${IDENTITY}/v1/modules/milavn/enter`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      await route.continue();
    });
    const enterRequest = page.waitForRequest((r) => r.url() === `${IDENTITY}/v1/modules/milavn/enter` && r.method() === "POST", { timeout: 8000 });
    const milavnNavigation = page.waitForRequest((r) => r.isNavigationRequest() && r.url().startsWith(MILAVN), { timeout: 15000 });
    await page.locator("#ask-input").press("Enter");
    const request = await enterRequest.catch(() => null);
    check(s, "enter endpoint called for Milavn", !!request);
    await page.waitForTimeout(600);
    const veil = await page.locator(".entering-name").textContent().catch(() => "");
    check(s, "entering veil shown while entering", veil.includes("Entering Milavn"), veil);
    await page.screenshot({ path: path.join(LOGS, "phone-dark-en-10-entering.png") }).catch(() => {});
    const navigation = await milavnNavigation.catch(() => null);
    check(s, "navigation to Milavn entry_url attempted", !!navigation, navigation?.url() ?? page.url());
    await settle(page, 2500);
    await page.screenshot({ path: path.join(LOGS, "phone-dark-en-11-milavn-landing.png") }).catch(() => {});
    check(s, "no page errors", errors.filter((e) => e.startsWith("pageerror")).length === 0, errors.join(" | "));
    await context.close();
  },

  // Password sign-in, account sheet, Hindi, sign out.
  async passwordAccountHindi(browser) {
    const s = "passwordAccountHindi";
    const { context, page, errors } = await newPage(browser);
    await page.goto(BASE);
    await page.locator(".question").waitFor();
    await passwordSignIn(page, DEV_MEMBER);
    await page.locator(".greeting").waitFor({ timeout: 10000 });
    check(s, "password sign-in reaches hub", true, await page.locator(".greeting").textContent());

    await page.locator(".avatar-btn").click();
    await page.locator(".sheet .account").waitFor();
    const hints = await page.locator(".account-hints").textContent();
    check(s, "masked identifier hint shown", hints.includes("•"), hints);
    await shot(page, "phone-dark-en-20-account-sheet");

    await page.locator('.sheet .segment[lang="hi"]').click();
    await settle(page, 1200);
    const title = await page.locator(".sheet-title").textContent();
    check(s, "interface switches to Hindi", title.includes("आपका खाता"), title);
    await page.keyboard.press("Escape");
    await settle(page, 500);
    const greeting = await page.locator(".greeting").textContent();
    check(s, "hub greeting in Hindi", /सुप्रभात|नमस्ते|शुभ संध्या/.test(greeting), greeting);
    const tagline = await page.locator(".module-tagline").first().textContent();
    check(s, "taglines follow member language", /[\u0900-\u097F]/.test(tagline), tagline);
    await shot(page, "phone-dark-hi-21-hub");
    await page.locator("#ask-input").fill("इस वीकेंड पास में क्रिकेट");
    await settle(page, 800);
    check(s, "Hindi intent understood", (await page.locator(".u-chip").allTextContents()).includes("Milavn"), JSON.stringify(await page.locator(".u-chip").allTextContents()));
    await shot(page, "phone-dark-hi-22-intent");
    await page.keyboard.press("Escape");

    await resetLanguage(page);
    await page.reload();
    await page.locator(".greeting").waitFor();
    check(s, "session survives reload", true);
    await page.locator(".avatar-btn").click();
    await page.locator(".sheet .btn-secondary").click();
    await page.locator(".question").waitFor({ timeout: 8000 });
    const notice = await page.locator(".notice").textContent().catch(() => "");
    check(s, "sign out returns to arrival with notice", notice.includes("signed out"), notice);
    const session = await page.evaluate(async (api) => (await fetch(`${api}/v1/session`, { credentials: "include" })).status, IDENTITY);
    check(s, "session is gone after sign out", session === 401, session);
    await shot(page, "phone-dark-en-23-signed-out");
    check(s, "no page errors", errors.filter((e) => e.startsWith("pageerror")).length === 0, errors.join(" | "));
    await context.close();
  },

  // Desktop light: composed hub, orb, notifications, account; sign out everywhere.
  async desktopLight(browser) {
    const s = "desktopLight";
    const { context, page, errors } = await newPage(browser, { viewport: DESKTOP, colorScheme: "light" });
    await page.goto(BASE);
    await page.locator(".question").waitFor();
    await shot(page, "desktop-light-en-30-arrival");
    await passwordSignIn(page, DATA_MEMBER);
    await page.locator(".greeting").waitFor({ timeout: 10000 });
    check(s, "no floating orb", (await page.locator("button.orb, .orb-dock").count()) === 0);
    check(s, "hero column offers intent starters", (await page.locator(".hero-suggestions .suggestion").count()) === 3);
    check(s, "taglines clamp to whole lines", await page.evaluate(() =>
      [...document.querySelectorAll(".module-tagline")].every((el) => {
        const lineHeight = parseFloat(getComputedStyle(el).lineHeight);
        return Math.abs(el.clientHeight / lineHeight - Math.round(el.clientHeight / lineHeight)) < 0.1;
      }),
    ));
    await shot(page, "desktop-light-en-31-hub");
    await page.locator(".hero-suggestions .suggestion").first().click();
    await settle(page, 700);
    check(s, "suggestion fills the hub input", (await page.locator("#ask-input").inputValue()) === "Yoga this weekend near me");
    check(s, "suggestion understood as Milavn", (await page.locator(".u-chip").allTextContents())[0] === "Milavn", JSON.stringify(await page.locator(".u-chip").allTextContents()));
    await shot(page, "desktop-light-en-31b-suggestion");
    await page.keyboard.press("Escape");
    await settle(page, 500);
    check(s, "Escape clears the input", (await page.locator("#ask-input").inputValue()) === "");
    check(s, "typing opens no dialog or sheet", (await page.locator(".sheet, [role='dialog']").count()) === 0);
    const firstPortal = page.locator("button.module-row").first();
    const box = await firstPortal.boundingBox();
    await page.mouse.move(box.x + box.width * 0.8, box.y + box.height * 0.3, { steps: 8 });
    await shot(page, "desktop-light-en-32-portal-hover");

    await page.mouse.click(8, 880);
    await page.keyboard.press("/");
    await settle(page, 200);
    check(s, "/ focuses the hub input", await page.evaluate(() => document.activeElement?.id === "ask-input"));
    await page.locator("#ask-input").fill("rishta for my brother in Hyderabad");
    await settle(page, 800);
    const chips = await page.locator(".u-chip").allTextContents();
    check(s, "Mangaly intent with place chip", chips[0] === "Mangaly" && chips.includes("in Hyderabad"), JSON.stringify(chips));
    await shot(page, "desktop-light-en-33-orb-mangaly");
    await page.keyboard.press("Escape");
    await settle(page, 400);

    await page.getByRole("button", { name: "Notifications" }).click();
    await page.locator(".empty-title").waitFor();
    check(s, "honest empty notifications", (await page.locator(".empty-title").textContent()).includes("all caught up"));
    await shot(page, "desktop-light-en-34-notifications");
    await page.keyboard.press("Escape");
    await settle(page, 300);

    await page.locator(".avatar-btn").click();
    await page.locator(".sheet .account").waitFor();
    await shot(page, "desktop-light-en-35-account");
    await page.getByRole("button", { name: "Sign out on all devices" }).click();
    await page.getByRole("button", { name: "Sign out everywhere" }).click();
    await page.locator(".question").waitFor({ timeout: 8000 });
    check(s, "sign out everywhere returns to arrival", true);
    check(s, "no page errors", errors.filter((e) => e.startsWith("pageerror")).length === 0, errors.join(" | "));
    await context.close();
  },

  // Desktop dark with a member who has entered modules before: "Continue in" card.
  async desktopDark(browser) {
    const s = "desktopDark";
    const { context, page, errors } = await newPage(browser, { viewport: DESKTOP, colorScheme: "dark" });
    await page.goto(BASE);
    await page.locator(".question").waitFor();
    await passwordSignIn(page, DEV_MEMBER);
    await page.locator(".greeting").waitFor({ timeout: 10000 });
    await settle(page, 1200);
    await shot(page, "desktop-dark-en-36-hub");
    const vtErrors = errors.filter((e) => /Transition was aborted|InvalidStateError/.test(e));
    check(s, "no view-transition rejections", vtErrors.length === 0, vtErrors.join(" | "));
    await page.evaluate(async (api) => fetch(`${api}/v1/auth/sign-out`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: '{"everywhere":false}' }), IDENTITY);
    await context.close();
  },

  // Owner rule: every module, the greeting and the ask field fit on the first phone screen.
  async firstScreen(browser) {
    const s = "firstScreen";
    const measurements = [];
    for (const [w, h] of [[390, 844], [360, 740]]) {
      for (const scheme of ["dark", "light"]) {
        const { context, page } = await newPage(browser, { viewport: { width: w, height: h }, colorScheme: scheme });
        await page.goto(BASE);
        await page.locator(".question").waitFor();
        // Asha has entered both open modules, so both rows carry a "Visited" line (tallest case).
        await passwordSignIn(page, DATA_MEMBER);
        await page.locator(".greeting").waitFor({ timeout: 10000 });
        for (const lang of ["en", "hi", "te"]) {
          if (scheme === "light" && lang !== "en") continue;
          await page.evaluate(async ([api, l]) => {
            await fetch(`${api}/v1/me`, { method: "PATCH", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ preferred_language: l }) });
          }, [IDENTITY, lang]);
          await page.reload();
          await page.locator(".coming-tile").last().waitFor({ timeout: 10000 });
          await settle(page, 900);
          const m = await page.evaluate(() => {
            const last = [...document.querySelectorAll(".module-list > li, .coming-tile")].pop();
            const ask = document.querySelector(".ask-field").getBoundingClientRect();
            const greeting = document.querySelector(".greeting");
            return {
              bottom: Math.round(last.getBoundingClientRect().bottom),
              docHeight: document.documentElement.scrollHeight,
              minTap: Math.round(Math.min(...[...document.querySelectorAll(".topbar button, .ask-field, button.module-row")].map((el) => el.getBoundingClientRect().height))),
              innerHeight: window.innerHeight,
              scrollY: window.scrollY,
              askVisible: ask.bottom <= window.innerHeight,
              greetingOneLine: greeting.scrollHeight <= parseFloat(getComputedStyle(greeting).lineHeight) * 1.5,
            };
          });
          const a11y = await page.evaluate(() => ({
            // Only the decorative icon (.coming-mark and its SVG) may be aria-hidden; the text must be exposed.
            hiddenText: [...document.querySelectorAll(".coming-tile [aria-hidden='true']")].filter((el) => !el.closest(".coming-mark")).length,
            labelledList: document.querySelector(".coming-grid").getAttribute("aria-labelledby") === "coming-label",
            spoken: [...document.querySelectorAll(".coming-tile .coming-text")].map((el) => el.textContent),
            focusable: document.querySelectorAll(".coming-tile button, .coming-tile a, .coming-tile [tabindex]").length,
            metaOwnLine: [...document.querySelectorAll(".module-row")].every((row) => {
              const meta = row.querySelector(".module-meta");
              return !meta || meta.getBoundingClientRect().top >= row.querySelector(".module-name").getBoundingClientRect().bottom - 1;
            }),
          }));
          check(s, `${w}x${h} ${scheme} ${lang}: coming list exposed to screen readers`, a11y.hiddenText === 0 && a11y.labelledList && a11y.focusable === 0 && a11y.spoken.length === 4, JSON.stringify(a11y));
          check(s, `${w}x${h} ${scheme} ${lang}: visited note on its own line in every row`, a11y.metaOwnLine, JSON.stringify(a11y));
          const label = `${w}x${h} ${scheme} ${lang}`;
          measurements.push({ label, ...m });
          check(s, `${label}: last module bottom ${m.bottom} <= ${m.innerHeight}`, m.bottom <= m.innerHeight && m.scrollY === 0 && m.askVisible, JSON.stringify(m));
          if (h === 740) check(s, `${label}: docHeight ${m.docHeight} <= ${m.innerHeight} (no scroll), min tap ${m.minTap}px`, m.docHeight <= m.innerHeight && m.minTap >= 48, JSON.stringify(m));
          await shot(page, `first-screen-${w}x${h}-${scheme}-${lang}`);
        }
        await resetLanguage(page);
        await context.close();
      }
    }
    writeFileSync(path.join(LOGS, "first-screen-measurements.json"), JSON.stringify(measurements, null, 2));
  },

  // Devotional emblem: signed-in hub only, gold mask of the ForKhatri SVG, not interactive, no photo anywhere.
  async devotional(browser) {
    const s = "devotional";
    const names = {
      en: "Bhagwan Kartavirya Sahasrarjun",
      hi: "भगवान कार्तवीर्य सहस्रार्जुन",
      te: "భగవాన్ కార్తవీర్య సహస్రార్జున",
    };
    for (const [label, viewport, scheme] of [["phone", PHONE, "dark"], ["desktop", DESKTOP, "dark"], ["phone", PHONE, "light"]]) {
      const { context, page, errors } = await newPage(browser, { viewport, colorScheme: scheme });
      const photoRequests = [];
      page.on("request", (r) => r.url().includes("bhagwan-kartavirya-sahasrarjun") && photoRequests.push(r.url()));
      await page.goto(BASE);
      await page.locator(".question").waitFor();
      check(s, `${label} ${scheme}: emblem absent on arrival`, (await page.locator(".deity-emblem").count()) === 0);
      await passwordSignIn(page, DEV_MEMBER);
      await page.locator(".deity-emblem").waitFor({ timeout: 10000 });
      for (const lang of scheme === "light" ? ["en"] : ["en", "hi"]) {
        await page.evaluate(async ([api, l]) => {
          await fetch(`${api}/v1/me`, { method: "PATCH", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ preferred_language: l }) });
        }, [IDENTITY, lang]);
        await page.reload();
        await page.locator(".deity-emblem").waitFor({ timeout: 10000 });
        await settle(page, 900);
        const m = await page.evaluate(() => {
          const el = document.querySelector(".deity-emblem");
          const css = getComputedStyle(el);
          const box = el.getBoundingClientRect();
          const last = [...document.querySelectorAll(".module-list > li, .coming-tile")].pop().getBoundingClientRect();
          return {
            size: `${Math.round(box.width)}x${Math.round(box.height)}`,
            role: el.getAttribute("role"),
            label: el.getAttribute("aria-label"),
            focusable: el.tabIndex >= 0 || el.matches("a,button,[tabindex]"),
            mask: css.maskImage || css.webkitMaskImage,
            color: css.backgroundColor,
            filter: css.filter,
            animation: css.animationName,
            deityLine: document.querySelector(".deity-line").textContent,
            lastBottom: Math.round(last.bottom),
            innerHeight: window.innerHeight,
          };
        });
        check(s, `${label} ${scheme} ${lang}: emblem is role=img with localized label`, m.role === "img" && m.label === names[lang] && m.deityLine === names[lang], JSON.stringify(m));
        check(s, `${label} ${scheme} ${lang}: not interactive, no filter/animation`, !m.focusable && m.filter === "none" && m.animation === "none", JSON.stringify(m));
        check(s, `${label} ${scheme} ${lang}: masks the ForKhatri emblem SVG`, m.mask.includes("sahasrarjun-emblem.svg"), m.mask);
        if (label === "phone") check(s, `${label} ${scheme} ${lang}: all modules visible without scrolling`, m.lastBottom <= m.innerHeight, JSON.stringify(m));
        await page.locator(".deity-emblem").click({ force: true });
        await settle(page, 400);
        check(s, `${label} ${scheme} ${lang}: tapping opens nothing`, (await page.locator(".sheet").count()) === 0);
        await shot(page, `devotional-${label}-${scheme}-${lang}-hub`);
      }
      check(s, `${label} ${scheme}: Commons photo never requested`, photoRequests.length === 0, photoRequests.join(" | "));
      await resetLanguage(page);
      check(s, `${label} ${scheme}: no page errors`, errors.filter((e) => e.startsWith("pageerror")).length === 0, errors.join(" | "));
      await context.close();
    }
  },

  // Owner rule: the ask box is a real input on the hub; results show in place and stay above a phone keyboard.
  async inlineIntent(browser) {
    const s = "inlineIntent";
    const phrases = [["cricket this weekend", "milavn"], ["rishta", "mangaly"], ["electrician", "vyapar"]];
    for (const [w, h] of [[360, 740], [390, 844]]) {
      const { context, page, errors } = await newPage(browser, { viewport: { width: w, height: h }, colorScheme: "dark" });
      await page.goto(BASE);
      await page.locator(".question").waitFor();
      await passwordSignIn(page, DATA_MEMBER);
      await page.locator("#ask-input").waitFor({ timeout: 10000 });
      await settle(page, 900);
      const before = await page.evaluate(() => ({
        header: document.querySelector(".topbar").getBoundingClientRect().top,
        order: [...document.querySelectorAll(".module-row .module-name")].map((e) => e.textContent),
      }));
      check(s, `${w}x${h}: ask box is a text input, no button/dialog`, await page.evaluate(() => document.querySelector("#ask-input")?.tagName === "INPUT" && !document.querySelector("button.ask-field")));
      for (const [phrase, key] of phrases) {
        await page.locator("#ask-input").click();
        await page.locator("#ask-input").fill(phrase);
        await settle(page, 800);
        const m = await page.evaluate((k) => {
          // Simulate a typical phone keyboard covering ~42% of the layout viewport.
          const keyboard = Math.round(window.innerHeight * 0.42);
          const vv = window.visualViewport;
          const limit = (vv ? vv.offsetTop + vv.height : window.innerHeight) - keyboard;
          const chips = document.querySelector(".understanding");
          const result = k === "vyapar" ? document.querySelector(".ask-note") : document.querySelector(".module-row.is-match");
          return {
            dialogs: document.querySelectorAll(".sheet, [role='dialog']").length,
            // Every control inside the field (clear, mic) must sit inside the field and the viewport.
            fieldOverflow: (() => {
              const field = document.querySelector(".ask-field").getBoundingClientRect();
              return [...document.querySelectorAll(".ask-field > *")].some((el) => {
                const r = el.getBoundingClientRect();
                return r.right > field.right + 0.5 || r.right > window.innerWidth;
              }) || field.right > window.innerWidth - 15;
            })(),
            scrollY: window.scrollY,
            header: document.querySelector(".topbar").getBoundingClientRect().top,
            focused: document.activeElement?.id,
            chips: [...document.querySelectorAll(".u-chip")].map((e) => e.textContent),
            note: document.querySelector(".ask-note")?.textContent ?? "",
            firstRow: document.querySelector(".module-row .module-name")?.textContent,
            matchName: (document.querySelector(".module-row.is-match .module-name") ?? document.querySelector(".coming-tile.is-match .coming-name"))?.textContent,
            dimmed: document.querySelectorAll(".is-dim").length,
            chipsBottom: chips ? Math.round(chips.getBoundingClientRect().bottom) : null,
            resultBottom: result ? Math.round(result.getBoundingClientRect().bottom) : null,
            aboveKeyboardLimit: limit,
            hasVisualViewport: !!vv,
          };
        }, key);
        const label = `${w}x${h} "${phrase}"`;
        check(s, `${label}: no dialog, no page jump, header fixed`, m.dialogs === 0 && m.scrollY === 0 && m.header === before.header && m.focused === "ask-input", JSON.stringify(m));
        check(s, `${label}: clear and mic fit inside the field`, !m.fieldOverflow, JSON.stringify(m));
        check(s, `${label}: chips and result stay above keyboard (${m.resultBottom} <= ${m.aboveKeyboardLimit})`, m.hasVisualViewport && m.chips.length > 0 && m.resultBottom !== null && m.chipsBottom <= m.aboveKeyboardLimit && m.resultBottom <= m.aboveKeyboardLimit, JSON.stringify(m));
        if (key === "vyapar") {
          check(s, `${label}: not-open module said inline, tile highlighted`, m.note.includes("Vyapar") && m.matchName === "Vyapar", JSON.stringify(m));
        } else {
          check(s, `${label}: matching row highlighted, moved to top, others dimmed`, m.firstRow?.toLowerCase() === key && m.matchName?.toLowerCase() === key && m.dimmed > 0, JSON.stringify(m));
        }
        await shot(page, `inline-intent-${w}x${h}-${key}`);
      }
      await page.locator("#ask-input").fill("cricket this weekend");
      await page.keyboard.press("Escape");
      await settle(page, 700);
      const after = await page.evaluate(() => ({
        value: document.querySelector("#ask-input").value,
        order: [...document.querySelectorAll(".module-row .module-name")].map((e) => e.textContent),
        states: document.querySelectorAll(".is-dim, .is-match").length,
        chips: document.querySelectorAll(".u-chip").length,
        docHeight: document.documentElement.scrollHeight,
        innerHeight: window.innerHeight,
      }));
      check(s, `${w}x${h}: Escape clears and restores the hub`, after.value === "" && after.states === 0 && after.chips === 0 && JSON.stringify(after.order) === JSON.stringify(before.order), JSON.stringify(after));
      if (h === 740) check(s, `${w}x${h}: resting hub fits (docHeight ${after.docHeight})`, after.docHeight <= after.innerHeight, JSON.stringify(after));
      await page.locator("#ask-input").fill("cricket this weekend");
      const enterRequest = page.waitForRequest((r) => r.url() === `${IDENTITY}/v1/modules/milavn/enter` && r.method() === "POST", { timeout: 8000 });
      await page.locator("#ask-input").press("Enter");
      check(s, `${w}x${h}: Enter opens the top match through the enter flow`, !!(await enterRequest.catch(() => null)));
      check(s, `${w}x${h}: no page errors`, errors.filter((e) => e.startsWith("pageerror")).length === 0, errors.join(" | "));
      await context.close();
    }
  },

  // Appearance: explicit System / Light / Dark on this device, applied before first paint.
  async appearance(browser) {
    const s = "appearance";
    const firstPaintProbe = () => {
      new MutationObserver((_, observer) => {
        if (document.body) {
          window.__firstBodyTheme = document.documentElement.getAttribute("data-theme") || "unset";
          observer.disconnect();
        }
      }).observe(document, { childList: true, subtree: true });
    };
    const contrastProbe = () => {
      const parse = (value) => (value.match(/[\d.]+/g) || []).slice(0, 3).map(Number);
      const lum = ([r, g, b]) => [r, g, b].map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }).reduce((sum, v, i) => sum + v * [0.2126, 0.7152, 0.0722][i], 0);
      const ratio = (a, b) => { const [x, y] = [lum(parse(a)), lum(parse(b))].sort((p, q) => q - p); return Number(((x + 0.05) / (y + 0.05)).toFixed(2)); };
      const css = getComputedStyle(document.querySelector(".app"));
      const bg = getComputedStyle(document.body).backgroundColor;
      const probe = document.createElement("span");
      document.body.append(probe);
      const color = (token) => { probe.style.color = `var(${token})`; return getComputedStyle(probe).color; };
      const out = {
        theme: document.documentElement.getAttribute("data-theme"),
        bg,
        accentInk: ratio(color("--accent-ink"), bg),
        accentInkOnSurface2: ratio(color("--accent-ink"), color("--surface-2")),
        muted: ratio(color("--ink-3"), bg),
        focusRing: ratio(color("--accent"), bg),
        gold: ratio(getComputedStyle(document.querySelector(".deity-emblem")).backgroundColor, bg),
        themeColor: [...document.querySelectorAll('meta[name="theme-color"]')].map((m) => m.content),
        colorScheme: css.colorScheme,
      };
      probe.remove();
      return out;
    };

    for (const [osScheme, pick, other] of [["dark", "light", "dark"], ["light", "dark", "light"]]) {
      const { context, page, errors } = await newPage(browser, { viewport: PHONE, colorScheme: osScheme });
      await context.addInitScript(firstPaintProbe);
      await page.goto(BASE);
      await page.locator(".question").waitFor();
      check(s, `OS ${osScheme}: System follows OS on sign-in screen`, (await page.getAttribute("html", "data-theme")) === osScheme);
      check(s, `OS ${osScheme}: no appearance control on sign-in screen`, (await page.locator("[data-theme-option]").count()) === 0);
      await passwordSignIn(page, DEV_MEMBER);
      await page.locator(".greeting").waitFor({ timeout: 10000 });
      await page.locator(".avatar-btn").click();
      await page.locator("[data-theme-option]").first().waitFor();
      check(s, `OS ${osScheme}: System is the default`, (await page.locator('[data-theme-option="system"]').getAttribute("aria-checked")) === "true");
      await page.locator(`[data-theme-option="${pick}"]`).click();
      await settle(page, 500);
      check(s, `OS ${osScheme}: choosing ${pick} applies immediately`, (await page.getAttribute("html", "data-theme")) === pick && (await page.locator(`[data-theme-option="${pick}"]`).getAttribute("aria-checked")) === "true");
      const stored = await page.evaluate(() => localStorage.getItem("fk.theme"));
      check(s, `OS ${osScheme}: stored on this device only`, stored === pick, stored);
      await shot(page, `appearance-os-${osScheme}-picked-${pick}-account`);
      await page.keyboard.press("Escape");
      await settle(page, 400);

      await page.locator("#ask-input").fill("cricket this weekend");
      await settle(page, 700);
      const c = await page.evaluate(contrastProbe);
      if (pick === "light") {
        check(s, `OS ${osScheme} + Light: AA contrast (accent text ${c.accentInk}/${c.accentInkOnSurface2}, muted ${c.muted}, gold ${c.gold}, focus ring ${c.focusRing})`, c.accentInk >= 4.5 && c.accentInkOnSurface2 >= 4.5 && c.muted >= 4.5 && c.gold >= 3 && c.focusRing >= 3, JSON.stringify(c));
      }
      check(s, `OS ${osScheme} + ${pick}: theme-color follows choice`, c.themeColor.length > 0 && c.themeColor.every((v) => v === (pick === "light" ? "#fafaf8" : "#0c0c0d")) && c.colorScheme === pick, JSON.stringify(c));
      await shot(page, `appearance-os-${osScheme}-picked-${pick}-typing`);
      await page.locator("#ask-input").fill("");

      await page.reload();
      await page.locator(".greeting").waitFor({ timeout: 10000 });
      const firstBody = await page.evaluate(() => window.__firstBodyTheme);
      check(s, `OS ${osScheme}: ${pick} persists on reload, set before first paint`, firstBody === pick && (await page.getAttribute("html", "data-theme")) === pick, firstBody);
      await shot(page, `appearance-os-${osScheme}-picked-${pick}-hub`);

      await page.setViewportSize({ width: 360, height: 740 });
      await page.reload();
      await page.locator(".coming-tile").last().waitFor({ timeout: 10000 });
      await settle(page, 800);
      const docHeight = await page.evaluate(() => document.documentElement.scrollHeight);
      check(s, `OS ${osScheme} + ${pick}: 360x740 docHeight ${docHeight}`, docHeight === 740, docHeight);
      await page.setViewportSize(PHONE);

      await context.route(`${IDENTITY}/**`, (route) => route.abort("connectionrefused"));
      await page.reload();
      await page.locator(".offline-title").waitFor({ timeout: 10000 });
      await settle(page, 600);
      const offline = await page.evaluate(() => ({ theme: document.documentElement.getAttribute("data-theme"), aurora: getComputedStyle(document.querySelector(".aurora")).backgroundColor }));
      check(s, `OS ${osScheme}: ${pick} applies to offline (sign-in look) too`, offline.theme === pick && offline.aurora === (pick === "light" ? "rgb(245, 241, 232)" : "rgb(5, 7, 15)"), JSON.stringify(offline));
      await shot(page, `appearance-os-${osScheme}-picked-${pick}-offline`);
      await context.unroute(`${IDENTITY}/**`);

      // Back to System follows the OS again.
      await page.reload();
      await page.locator(".greeting").waitFor({ timeout: 10000 });
      await page.locator(".avatar-btn").click();
      await page.locator('[data-theme-option="system"]').click();
      await settle(page, 400);
      check(s, `OS ${osScheme}: System returns to ${other}`, (await page.getAttribute("html", "data-theme")) === other && (await page.evaluate(() => localStorage.getItem("fk.theme"))) === null);
      await page.evaluate(async (api) => fetch(`${api}/v1/auth/sign-out`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: '{"everywhere":false}' }), IDENTITY);
      check(s, `OS ${osScheme}: no page errors`, errors.filter((e) => e.startsWith("pageerror")).length === 0, errors.join(" | "));
      await context.close();
    }
  },

  async returnToAllowed(browser) {
    const s = "returnToAllowed";
    const { context, page, errors } = await newPage(browser);
    const navigations = [];
    page.on("request", (r) => r.isNavigationRequest() && r.frame() === page.mainFrame() && navigations.push(r.url()));
    page.on("response", (r) => r.url().includes("/v1/auth/password") && navigations.push(`password -> ${r.status()}`));
    await page.goto(`${BASE}/?return_to=${encodeURIComponent(`${MILAVN}/`)}`);
    await page.locator(".question").waitFor();
    const kicker = await page.locator(".kicker").textContent();
    check(s, "arrival names the module to continue to", kicker.includes("Milavn"), kicker);
    await shot(page, "phone-dark-en-40-return-to-milavn");
    const milavnNavigation = page.waitForRequest((r) => r.isNavigationRequest() && r.url().startsWith(MILAVN), { timeout: 15000 });
    await passwordSignIn(page, DEV_MEMBER);
    const navigation = await milavnNavigation.catch(() => null);
    check(s, "signed in and navigation to Milavn attempted", !!navigation, `${page.url()} | ${navigations.join(" > ")} | ${errors.join(" | ")}`);
    await settle(page, 2500);
    await page.screenshot({ path: path.join(LOGS, "phone-dark-en-41-after-return.png") }).catch(() => {});
    check(s, "final location after return_to", true, `${page.url()} | ${navigations.join(" > ")}`);
    await context.close();
  },

  async returnToRejected(browser) {
    const s = "returnToRejected";
    const { context, page } = await newPage(browser);
    const navigations = [];
    page.on("framenavigated", (frame) => frame === page.mainFrame() && navigations.push(frame.url()));
    await page.goto(`${BASE}/?return_to=${encodeURIComponent("https://evil.example/")}`);
    await page.locator(".question").waitFor();
    check(s, "no module named for foreign return_to", !(await page.locator(".kicker").textContent()).includes("continue"));
    check(s, "foreign return_to removed from address bar", !page.url().includes("return_to"), page.url());
    await passwordSignIn(page, DEV_MEMBER);
    await page.locator(".greeting").waitFor({ timeout: 10000 });
    await settle(page, 1000);
    check(s, "stays on hub, never navigates to evil.example", !navigations.some((u) => new URL(u).hostname === "evil.example") && page.url().startsWith(BASE), `${page.url()} | ${navigations.join(" > ")}`);
    await context.close();
  },

  // Service down: calm offline state with cached registry, then recovery.
  async offline(browser) {
    const s = "offline";
    for (const [label, viewport, scheme] of [["phone-dark", PHONE, "dark"], ["desktop-light", DESKTOP, "light"]]) {
      const { context, page, errors } = await newPage(browser, { viewport, colorScheme: scheme });
      await page.goto(BASE);
      await page.locator(".question").waitFor();
      await context.route(`${IDENTITY}/**`, (route) => route.abort("connectionrefused"));
      await page.reload();
      await page.locator(".offline-title").waitFor({ timeout: 10000 });
      check(s, `${label}: offline state shown`, true);
      check(s, `${label}: cached registry shown dimmed`, (await page.locator(".offline-item").count()) === 6);
      await shot(page, `${label}-en-50-offline`);
      await context.unroute(`${IDENTITY}/**`);
      await page.locator(".offline-card .btn-primary").click();
      await page.locator(".question").waitFor({ timeout: 10000 });
      check(s, `${label}: retry recovers`, true);
      check(s, `${label}: no page errors`, errors.filter((e) => e.startsWith("pageerror")).length === 0, errors.join(" | "));
      await context.close();
    }
  },

  async hindiArrivalLight(browser) {
    const s = "hindiArrivalLight";
    const { context, page } = await newPage(browser, { colorScheme: "light", locale: "hi-IN" });
    await page.goto(BASE);
    await page.locator(".question").waitFor();
    const question = await page.locator(".question").textContent();
    check(s, "navigator Hindi selects Hindi", question.includes("मोबाइल"), question);
    check(s, "html lang is hi", (await page.getAttribute("html", "lang")) === "hi");
    await shot(page, "phone-light-hi-60-arrival");
    await page.locator('.lang-switch button[lang="te"]').click();
    await settle(page, 500);
    check(s, "switch to Telugu", (await page.locator(".question").textContent()).includes("మొబైల్"));
    await shot(page, "phone-light-te-61-arrival");
    await page.locator('.lang-switch button[lang="en"]').click();
    await context.close();
  },

  async reducedMotionPhoneLight(browser) {
    const s = "reducedMotionPhoneLight";
    const { context, page, errors } = await newPage(browser, { colorScheme: "light", reducedMotion: "reduce" });
    await page.goto(BASE);
    await page.locator(".question").waitFor();
    await passwordSignIn(page, DATA_MEMBER);
    await page.locator(".greeting").waitFor({ timeout: 10000 });
    await shot(page, "phone-light-en-70-hub-reduced-motion");
    await page.locator("#ask-input").fill("pay my electricity bill");
    await settle(page, 500);
    const note = await page.locator(".ask-note").first().textContent().catch(() => "");
    check(s, "payments planned said plainly", note.includes("Payment Services isn't open yet"), note);
    await shot(page, "phone-light-en-71-intent-payments");
    await page.keyboard.press("Escape");
    await page.evaluate(async (api) => fetch(`${api}/v1/auth/sign-out`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: '{"everywhere":false}' }), IDENTITY);
    check(s, "no page errors", errors.filter((e) => e.startsWith("pageerror")).length === 0, errors.join(" | "));
    await context.close();
  },
};

const selected = process.argv.slice(2);
const browser = await chromium.launch();
try {
  for (const [name, run] of Object.entries(scenarios)) {
    if (selected.length && !selected.includes(name)) continue;
    try {
      await run(browser);
    } catch (error) {
      check(name, "scenario completed", false, error.stack ?? error.message);
    }
  }
} finally {
  await browser.close();
}

writeFileSync(path.join(LOGS, "e2e-results.json"), JSON.stringify(results, null, 2));
const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} checks passed`);
process.exitCode = failed.length ? 1 : 0;
