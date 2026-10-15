/* Run against a built site: node test/browser_smoke.cjs http://127.0.0.1:8765 */
const assert = require("node:assert/strict");
const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({ headless: true, channel: process.env.NMR_BROWSER_CHANNEL || "chrome" });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    const started = Date.now();
    await page.goto(process.argv[2] || "http://127.0.0.1:8765");
    await page.waitForFunction(() => document.getElementById("engine-status").textContent.startsWith("Ready"), null, { timeout: 120000 });
    console.log(`Local engine ready in ${Date.now() - started}ms`);
    const requests = [];
    page.on("request", (request) => requests.push(request.url()));
    await page.locator("#example").click();
    await page.waitForFunction(() => document.getElementById("value").value.includes(":"));
    await page.locator("#convert").click();
    await page.locator("#result").waitFor({ state: "visible" });
    assert.equal(await page.locator("#result-value").inputValue(), "2/4");
    await page.locator('[data-mode="encode"]').click();
    await page.locator("#type").selectOption("virtual:text");
    const secret = " personal 001 # é ";
    await page.locator("#value").fill(secret);
    await page.locator("#convert").click();
    await page.locator("#result").waitFor({ state: "visible" });
    const name = await page.locator("#result-name").inputValue();
    assert.equal(await page.locator("#result-value").inputValue(), secret);
    await page.locator('[data-mode="decode"]').click();
    await page.locator("#value").fill(name);
    await page.locator("#convert").click();
    await page.locator("#result").waitFor({ state: "visible" });
    assert.equal(await page.locator("#result-value").inputValue(), secret);
    await page.locator("details").evaluate((element) => element.open = true);
    await page.locator("#word-list").fill("é\nred\nblue\ngreen\ngold\nwhite\nblack\n");
    await page.locator("#apply-words").click();
    await page.waitForFunction(() => document.getElementById("vocabulary-count").textContent.startsWith("7 "));
    await page.locator('[data-mode="encode"]').click();
    await page.locator("#type").selectOption("universal:math:int");
    await page.locator("#value").fill("-2");
    await page.locator("#convert").click();
    await page.locator("#result").waitFor({ state: "visible" });
    const customName = await page.locator("#result-name").inputValue();
    await page.locator('[data-mode="decode"]').click();
    await page.locator("#value").fill(customName);
    await page.locator("#convert").click();
    await page.locator("#result").waitFor({ state: "visible" });
    assert.equal(await page.locator("#result-value").inputValue(), "-2");
    await page.locator("#value").fill("universal:green");
    await page.locator("#convert").click();
    await page.waitForFunction(() => document.getElementById("message").classList.contains("error"));
    assert.equal(await page.locator("#result").isVisible(), false);
    await page.locator('[data-mode="browse"]').click();
    await page.locator("#convert").click();
    await page.locator("#result").waitFor({ state: "visible" });
    assert.match(await page.locator("#result-note").textContent(), /not canonical/);
    assert.deepEqual(requests, [], "Conversions must not make network requests");
    assert.deepEqual(errors, []);
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
    await page.screenshot({ path: "/tmp/nmr-browser-mobile.png", fullPage: true });
    console.log("Browser round trips, custom vocabulary, canonical rejection, browsing, privacy, and mobile layout passed");
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
