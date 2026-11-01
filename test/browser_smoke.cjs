/* Run against freshly built assets: node test/browser_smoke.cjs http://127.0.0.1:8765 */
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({ headless: true, channel: process.env.NMR_BROWSER_CHANNEL || "chrome" });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    const origin = process.argv[2] || "http://127.0.0.1:8765";
    for (const width of [1200, 390]) {
      await page.setViewportSize({ width, height: width === 1200 ? 768 : 844 });
      await page.goto(origin + "/?mode=name&type=pure%3Amath%3Aint&value=the");
      await page.waitForSelector('#name-editor[data-ready="true"]', { timeout: 120000 });
      await page.waitForSelector("#playing-score svg");
      assert.equal(await page.locator("h1").textContent(), "Name");
      assert.equal(await page.locator("#sound-toggle").getAttribute("aria-pressed"), "true");
      assert.equal(await page.locator("#description-region, #play, #automatic, #copy-link").count(), 0);
      assert.ok(await page.locator("#page-controls").evaluate((i) => i.getBoundingClientRect().bottom <= innerHeight));
      assert.equal(await page.locator('[name="mode"]').count(), 3);
      assert.equal(await page.locator("#swap").count(), 0);
      const boxes = () => page.locator("#source-region, #value-display, #playback-area").evaluateAll((items) => items.map((i) => {
        const r = i.getBoundingClientRect(); return [r.x, r.y, r.width, r.height];
      }));
      const before = await boxes();
      await page.getByRole("radio", { name: "Count", exact: true }).check();
      await page.locator("#count-value").fill("86401");
      await page.locator("#type").selectOption("real:time:time");
      await page.waitForFunction(() => document.querySelector("#value-display").textContent.includes("00:00:01"));
      await page.waitForFunction(() => {
        const text = document.querySelector(".value-text");
        return text && text.scrollHeight <= text.clientHeight && text.scrollWidth <= text.clientWidth;
      });
      assert.equal(await page.locator("#count-value").inputValue(), "86401");
      assert.deepEqual(await boxes(), before);
      assert.equal(await page.locator("h1").textContent(), "Count");
      await page.waitForFunction(() => document.querySelector("#playing-name").textContent.length > 0);
      await page.waitForSelector("#playing-score svg");
      await page.getByRole("button", { name: "Mute", exact: true }).click();
      assert.equal(await page.locator("#sound-toggle").getAttribute("aria-pressed"), "false");
      await page.getByRole("button", { name: "Mute", exact: true }).click();
      await page.getByRole("radio", { name: "Clock", exact: true }).check();
      assert.deepEqual(await boxes(), before);
      assert.equal(await page.locator("h1").textContent(), "Clock");
      assert.ok(await page.locator("#clock-time").evaluate((i) => i.getBoundingClientRect().bottom <= document.querySelector("#source-name").getBoundingClientRect().top));
      assert.ok(await page.locator("#playing-score svg").evaluate((i) => {
        const r = i.getBoundingClientRect();
        const frame = document.querySelector("#playing-score").getBoundingClientRect();
        return r.width <= frame.width + 1 && r.height <= frame.height + 1;
      }));
      await page.goBack();
      assert.equal(await page.getByRole("radio", { name: "Count", exact: true }).isChecked(), true);
      await page.getByRole("button", { name: "Settings", exact: true }).click();
      assert.equal(await page.locator("#retain-playback").isChecked(), true);
      assert.equal(await page.locator("#settings-panel #count-increment").count(), 1);
    }
    assert.deepEqual(errors, []);
    console.log("Unified page browser checks passed at desktop and mobile widths.");
  } finally { await browser.close(); }
})().catch((error) => { console.error(error); process.exitCode = 1; });
