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
    const started = Date.now();
    await page.goto(process.argv[2] || "http://127.0.0.1:8765");
    await page.waitForFunction(
      () =>
        document
          .getElementById("engine-status")
          .textContent.startsWith("Ready"),
      null,
      { timeout: 120000 },
    );
    console.log(`Local engine ready in ${Date.now() - started}ms`);
    const requests = [];
    page.on("request", (request) => requests.push(request.url()));
    await page.locator("#example").click();
    await page.waitForFunction(() =>
      document.getElementById("value").value.includes(":"),
    );
    await page.locator("#convert").click();
    await page.locator("#result").waitFor({ state: "visible" });
    assert.equal(await page.locator("#result-value").inputValue(), "2/4");
    await page.locator('[data-mode="encode"]').click();
    await page.locator("#type").selectOption("data:contact:phone");
    const secret = "+442079460958;ext=001";
    await page.locator("#value").fill("+44 (0)20 7946 0958 ext. 001");
    await page.locator("#convert").click();
    await page.locator("#result").waitFor({ state: "visible" });
    const name = await page.locator("#result-name").inputValue();
    assert.equal(await page.locator("#result-value").inputValue(), secret);
    assert.equal(await page.locator("#result-type").textContent(), "phone");
    assert.match(await page.locator("#type option:checked").textContent(), /^phone \/ /);
    await page.locator('[data-mode="decode"]').click();
    await page.locator("#value").fill(name);
    await page.locator("#convert").click();
    await page.locator("#result").waitFor({ state: "visible" });
    assert.equal(await page.locator("#result-value").inputValue(), secret);
    await page.locator('[data-mode="encode"]').click();
    await page.locator("#type").selectOption("pure:math:int");
    await page.locator("#value").fill("2");
    assert.equal(await page.locator("#tune-play").isVisible(), true);
    assert.equal(await page.locator("#tune-mapping").inputValue(), "relative");
    await page.locator("#tune-preview").click();
    await page.waitForFunction(() => document.getElementById("tune-phrase").textContent === "@1 -1@1");
    assert.equal(await page.locator("#value").inputValue(), "2");
    await page.locator("#tune-mapping").selectOption("absolute");
    await page.locator("#tune-preview").click();
    await page.waitForFunction(() => document.getElementById("tune-phrase").textContent && document.getElementById("tune-phrase").textContent !== "@1 -1@1");
    assert.equal(await page.locator("#value").inputValue(), "2");
    await page.locator("#tune-mapping").selectOption("relative");
    await page.locator('[data-mode="encode"]').click();
    await page.locator("#type").selectOption("play:music:tune");
    await page.locator("#tune-example").click();
    await page.waitForFunction(() => document.querySelectorAll(".tune-note").length === 5);
    assert.equal(await page.locator("#value").inputValue(), "@1 2@1/2 2@1/2 r@1/3 -1@2/3 @1");
    assert.match(await page.locator("#tune-pitches").textContent(), /58, 60, 62, 61, 61/);
    await page.locator("#convert").click();
    await page.locator("#result").waitFor({state: "visible"});
    const tuneName = await page.locator("#result-name").inputValue();
    await page.locator("#tune-root").fill("72");
    await page.locator("#tune-bpm").fill("60");
    await page.locator("#tune-play").click();
    await page.waitForFunction(() => document.getElementById("tune-status").textContent === "Playing…");
    assert.equal(await page.evaluate(() => voices.length), 5);
    assert.ok(Math.abs(await page.evaluate(() => voices[0].frequency.value) - 466.1638) < 0.01);
    await page.locator("#tune-stop").click();
    assert.equal(await page.evaluate(() => voices.length), 0);
    await page.locator("#convert").click();
    await page.locator("#result").waitFor({state: "visible"});
    assert.equal(await page.locator("#result-name").inputValue(), tuneName);
    await page.locator('[data-mode="decode"]').click();
    await page.locator("#value").fill(tuneName);
    await page.locator("#convert").click();
    await page.locator("#result").waitFor({state: "visible"});
    assert.equal(await page.locator("#tune-panel").isVisible(), true);
    assert.equal(await page.locator("#tune-editor").isVisible(), false);
    await page.locator('[data-mode="encode"]').click();
    await page.locator("#value").fill("@1 @1");
    await page.locator("#tune-preview").click();
    await page.waitForFunction(() => document.querySelectorAll(".tune-note").length === 2);
    await page.locator(".tune-note button").click();
    await page.waitForFunction(() => document.getElementById("value").value === "@2");
    await page.locator("#tune-add").click();
    await page.locator("#tune-use").click();
    await page.waitForFunction(() => document.getElementById("value").value === "@2 @1/2");
    await page.locator("#tune-remove").click();
    await page.locator("#tune-use").click();
    await page.waitForFunction(() => document.getElementById("value").value === "@2");
    await page.locator("#value").fill("@1/9");
    await page.locator("#tune-preview").click();
    await page.waitForFunction(() => document.getElementById("tune-status").textContent.includes("factor of three"));
    await page.locator("#value").fill("@1000");
    await page.locator("#tune-play").click();
    await page.waitForFunction(() => document.getElementById("tune-status").textContent.includes("Playback limit"));
    await page.locator("details").evaluate((element) => (element.open = true));
    await page
      .locator("#word-list")
      .fill("é\nred\nblue\ngreen\ngold\nwhite\nblack\n");
    await page.locator("#apply-words").click();
    await page.waitForFunction(() =>
      document.getElementById("vocabulary-count").textContent.startsWith("7 "),
    );
    await page.locator('[data-mode="encode"]').click();
    await page.locator("#type").selectOption("pure:math:int");
    await page.locator("#value").fill("-2");
    await page.locator("#convert").click();
    await page.locator("#result").waitFor({ state: "visible" });
    const customName = await page.locator("#result-name").inputValue();
    await page.locator('[data-mode="decode"]').click();
    await page.locator("#value").fill(customName);
    await page.locator("#convert").click();
    await page.locator("#result").waitFor({ state: "visible" });
    assert.equal(await page.locator("#result-value").inputValue(), "-2");
    await page.locator("#value").fill("pure:green");
    await page.locator("#convert").click();
    await page.waitForFunction(() =>
      document.getElementById("message").classList.contains("error"),
    );
    assert.equal(await page.locator("#result").isVisible(), false);
    await page.locator('[data-mode="browse"]').click();
    await page.locator("#convert").click();
    await page.locator("#result").waitFor({ state: "visible" });
    assert.match(
      await page.locator("#result-note").textContent(),
      /not canonical/,
    );
    assert.deepEqual(
      requests,
      [],
      "Conversions must not make network requests",
    );
    assert.deepEqual(errors, []);
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
      true,
    );
    await page.screenshot({
      path: "/tmp/nmr-browser-mobile.png",
      fullPage: true,
    });
    console.log(
      "Browser round trips, custom vocabulary, canonical rejection, browsing, privacy, and mobile layout passed",
    );
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
