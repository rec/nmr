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
    assert.equal(await page.locator("#truename").isVisible(), false);
    assert.equal(await page.locator("#full-truename").isVisible(), false);
    const requests = [];
    page.on("request", (request) => requests.push(request.url()));
    const enter = async (value, prefix) => {
      await page.keyboard.press("Escape");
      await page.keyboard.type(value);
      await page.waitForFunction((prefix) => {
        const button = document.querySelector("#truename");
        return !button.hidden && button.textContent.startsWith(prefix.replace(":", ": "));
      }, prefix);
    };
    for (const value of ["asdf", "asdfasdf", "Hello!", "dfasdfasdf", "iPhone"]) {
      await enter(value, "string:");
      assert.equal(await page.locator("#value").inputValue(), value);
      assert.equal(await page.locator("#full-truename").isVisible(), true);
    }
    await page.keyboard.press("Escape");
    for (const character of "Tom R") {
      await page.keyboard.type(character);
      await page.waitForFunction(() => !document.querySelector("#truename").hidden && !document.querySelector("#full-truename").hidden);
    }
    assert.equal(await page.locator("#value").inputValue(), "Tom R");
    await page.waitForFunction(() => !document.querySelector("#truename").hidden && document.querySelector("#truename").textContent.startsWith("string: "));
    await enter("xyzzy!", "string:");
    assert.equal(await page.locator("#full-truename").isVisible(), true);
    await page.keyboard.press("Escape");
    await page.keyboard.type("th");
    await page.waitForFunction(() => !document.querySelector("#truename").hidden && document.querySelector("#truename").textContent.startsWith("string: "));
    await enter("42", "int:");
    await page.keyboard.press("End");
    await page.locator("#value").click({ position: { x: 1, y: 15 } });
    await page.keyboard.type("1");
    assert.equal(await page.locator("#value").inputValue(), "142");
    const bounds = await page.locator("#value").boundingBox();
    const y = bounds.y + bounds.height / 2;
    await page.mouse.move(bounds.x + 1, y);
    await page.mouse.down();
    await page.mouse.move(bounds.x + bounds.width - 1, y, {steps: 10});
    await page.mouse.up();
    await page.keyboard.type("5678");
    assert.equal(await page.locator("#value").inputValue(), "5678");
    await page.locator("#value").dblclick({position: {x: 1, y: 15}});
    await page.keyboard.press("Backspace");
    assert.equal(await page.locator("#value").inputValue(), "");
    await page.keyboard.type("142");
    await page.keyboard.press("Home");
    await page.keyboard.press("ArrowRight");
    await page.locator("h1").click();
    await page.keyboard.type("3");
    assert.equal(await page.locator("#value").inputValue(), "1342");
    for (const [value, kind] of [
      ["+1", "phone:"], ["8/5", "frac:"], ["2000-02-29", "date:"],
      ["12:34", "clock:"], ["51.5, -0.12", "latlong:"], ["@1 2@1", "tune:"],
    ]) await enter(value, kind);
    await enter("Tom Ritchford", "string:");
    await page.locator("#swap").click();
    await page.waitForFunction(() => document.querySelector("#source-heading").textContent === "True Name" &&
      document.querySelector("#truename").textContent === 'string: "Tom Ritchford"');
    assert.equal(await page.locator("#full-truename").isVisible(), false);
    assert.deepEqual([...new URL(page.url()).searchParams.keys()], ["name"]);
    assert.equal(new URL(page.url()).searchParams.get("name"), await page.locator("#value").inputValue());
    await page.locator("#swap").click();
    await page.waitForFunction(() => document.querySelector("#source-heading").textContent === "Description");
    assert.equal(await page.locator("#value").inputValue(), 'string: "Tom Ritchford"');
    await page.keyboard.press("ControlOrMeta+A");
    await page.keyboard.type("0");
    await page.waitForFunction(() => document.querySelector("#truename").textContent === "int: the");
    await page.locator("#truename").click();
    await page.waitForFunction(() => document.querySelector("#truename").getAttribute("aria-pressed") === "true");
    await page.locator("#truename").click();
    assert.equal(await page.locator("#truename").getAttribute("aria-pressed"), "false");
    assert.equal(await page.locator("#status").count(), 0);
    await enter("+1", "phone:");
    await page.keyboard.type("abc");
    assert.equal(await page.locator("#value").inputValue(), "+1");
    await page.locator("#swap").click();
    await page.waitForFunction(() => document.querySelector("#source-heading").textContent === "True Name");
    await enter("date:mass soup", "date:2000-02-29");
    assert.equal(await page.locator("#full-truename").isVisible(), false);
    const nameBookmark = page.url();
    await page.reload();
    await page.waitForSelector('#value[data-ready="true"]', { timeout: 120000 });
    assert.equal(page.url(), nameBookmark);
    assert.equal(await page.locator("#source-heading").textContent(), "True Name");
    await page.waitForFunction(() => document.querySelector("#truename").textContent === "date: 2000-02-29");
    requests.length = 0;
    await page.keyboard.press("Escape");
    await page.keyboard.type("missingword");
    await page.waitForFunction(() => !document.querySelector("#truename").hidden);
    assert.equal(await page.locator("#truename").isEnabled(), false);
    await enter("tune:post were", "tune:@1");
    await page.locator("#truename").click();
    await page.waitForFunction(() => document.querySelector("#truename").getAttribute("aria-pressed") === "true");
    await page.locator("#truename").click();
    assert.equal(await page.locator("#truename").getAttribute("aria-pressed"), "false");
    await page.locator("#swap").click();
    await page.waitForFunction(() => document.querySelector("#source-heading").textContent === "Description");
    await page.keyboard.press("Escape");
    assert.equal(await page.locator("#value").inputValue(), "");
    assert.equal(await page.locator("#truename").isVisible(), false);
    assert.equal(await page.locator("#full-truename").isVisible(), false);
    assert.deepEqual(errors, []);
    assert.deepEqual(requests, [], "Typing must not send details over the network");
    const historyLength = await page.evaluate(() => history.length);
    const original = new URL(page.url());
    await page.keyboard.press("Escape");
    let query = "";
    for (const character of "Tom Ritchford + café & 🎵") {
      await page.keyboard.type(character);
      query += character;
      assert.equal(new URL(page.url()).searchParams.get("desc"), query);
      assert.deepEqual([...new URL(page.url()).searchParams.keys()], ["desc"]);
    }
    const bookmark = new URL(page.url());
    assert.ok(bookmark.search.includes("desc=Tom+Ritchford+%2B+caf%C3%A9+%26+"));
    assert.equal(bookmark.pathname, original.pathname);
    assert.equal(bookmark.hash, original.hash);
    assert.equal(await page.evaluate(() => history.length), historyLength);
    assert.deepEqual(requests, [], "Updating the bookmark must not send requests");
    await page.reload();
    assert.equal(await page.locator("#value").inputValue(), query);
    await page.waitForSelector('#value[data-ready="true"]', { timeout: 120000 });
    await page.waitForFunction(() => !document.querySelector("#truename").hidden &&
      document.querySelector("#truename").textContent.startsWith("string: "));
    await page.keyboard.press("Escape");
    assert.equal(new URL(page.url()).searchParams.get("desc"), "");
    await page.reload();
    assert.equal(await page.locator("#value").inputValue(), "");

    await page.setViewportSize({ width: 375, height: 812 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    console.log("Two-pane conversion, swapping, mouse selection, editing, playback, and local-only conversion passed");
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
