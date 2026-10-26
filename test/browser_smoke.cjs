/* Run against a built site: node test/browser_smoke.cjs http://127.0.0.1:8765 */
const assert = require("node:assert/strict");
const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({
    headless: true,
    channel: process.env.NMR_BROWSER_CHANNEL || "chrome",
  });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto(process.argv[2] || "http://127.0.0.1:8765");
    await page.waitForSelector('#value[data-ready="true"]', { timeout: 120000 });
    assert.equal(await page.locator("h1").textContent(), "nmr");
    assert.equal(await page.locator("input").count(), 1);
    assert.equal(await page.locator("#value").inputValue(), "");
    assert.equal(await page.locator("#name").isVisible(), false);
    assert.equal(await page.locator("#full-name").isVisible(), false);
    const requests = [];
    page.on("request", (request) => requests.push(request.url()));
    const enter = async (value, prefix) => {
      await page.keyboard.press("Escape");
      await page.keyboard.type(value);
      await page.waitForFunction((prefix) => {
        const button = document.querySelector("#name");
        return !button.hidden && button.textContent.startsWith(prefix.replace(":", ": "));
      }, prefix);
    };
    for (const value of ["asdf", "Hello!", "dfasdfasdf", "iPhone"]) {
      await enter(value, "string:");
      assert.equal(await page.locator("#value").inputValue(), value);
      assert.equal(await page.locator("#full-name").isVisible(), true);
    }
    await enter("xyzzy!", "string:");
    assert.equal(await page.locator("#full-name").isVisible(), true);
    await page.keyboard.press("Escape");
    await page.keyboard.type("th");
    await page.waitForFunction(() => document.querySelector("#name").hidden);
    await enter("42", "int:");
    await page.keyboard.press("Home");
    await page.locator("#value").click({ position: { x: 100, y: 15 } });
    await page.keyboard.type("1");
    assert.equal(await page.locator("#value").inputValue(), "142");
    await page.locator("h1").click();
    await page.keyboard.type("3");
    assert.equal(await page.locator("#value").inputValue(), "1342");
    for (const [value, kind] of [
      ["+1", "phone:"], ["8/5", "frac:"], ["2000-02-29", "date:"],
      ["12:34", "clock:"], ["51.5, -0.12", "latlong:"], ["@1 2@1", "tune:"],
    ]) await enter(value, kind);
    await enter("THE OF", "the of");
    assert.equal(await page.locator("#value").inputValue(), "the of");
    await page.keyboard.type(" qzx");
    await page.waitForFunction(() => document.querySelector("#name").hidden);
    await page.keyboard.press("ControlOrMeta+A");
    await page.keyboard.type("0");
    await page.waitForFunction(() => document.querySelector("#name").textContent === "int: the");
    await page.locator("#name").click();
    await page.waitForFunction(() => document.querySelector("#name").getAttribute("aria-pressed") === "true");
    await page.locator("#name").click();
    assert.equal(await page.locator("#name").getAttribute("aria-pressed"), "false");
    assert.equal(await page.locator("#status").count(), 0);
    await enter("+1", "phone:");
    await page.keyboard.type("abc");
    assert.equal(await page.locator("#value").inputValue(), "+1");
    await enter("tune:such like", "tune:such like");
    assert.equal(await page.locator("#full-name").isVisible(), true);
    assert.equal((await page.locator("#full-name").textContent()).includes(":"), false);
    await page.locator("#name").click();
    await page.waitForFunction(() => document.querySelector("#name").getAttribute("aria-pressed") === "true");
    await page.locator("#full-name").click();
    await page.waitForFunction(() => document.querySelector("#full-name").getAttribute("aria-pressed") === "true");
    assert.equal(await page.locator("#name").getAttribute("aria-pressed"), "false");
    await page.locator("#full-name").click();
    assert.equal(await page.locator("#full-name").getAttribute("aria-pressed"), "false");
    await enter(":play:music:tune:THE", "tune:the");
    await page.keyboard.press("Enter");
    await page.waitForFunction(() => document.querySelector("#name").getAttribute("aria-pressed") === "true");
    await page.keyboard.press("Escape");
    assert.equal(await page.locator("#value").inputValue(), "");
    assert.equal(await page.locator("#name").isVisible(), false);
    assert.equal(await page.locator("#full-name").isVisible(), false);
    assert.deepEqual(errors, []);
    assert.deepEqual(requests, [], "Typing must not send details over the network");
    await page.setViewportSize({ width: 375, height: 812 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    console.log("Single-field recognition, owned cursor, name mode, playback, and local-only conversion passed");
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
