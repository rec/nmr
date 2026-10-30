import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = fs.readFileSync(new URL("../nmr/web/count.js", import.meta.url), "utf8").replace(/^import .*;\n/gm, "");
const runnerSource = fs.readFileSync(new URL("../nmr/web/count-runner.mjs", import.meta.url), "utf8").replace("export class", "class");
const flush = () => new Promise(setImmediate);

function page(address) {
  let url = new URL(address);
  const listeners = {};
  const calls = [];
  let display;
  const elements = Object.fromEntries(["#count-view", "#count-value", "#count-increment", "#count-run", "#count-truename", "#count-object", "#count-message", "#count-value-display", "#score-top", "#score-bottom", "#score-highlight-color", "#tune-root", "#tune-position"].map((i) => [i, {
    value: i.startsWith("#score-") ? "4" : i === "#count-increment" ? "1" : "0", hidden: false, checked: false,
    validity: { valid: true },
    addEventListener(event, callback) { this[event] = callback; },
    setAttribute() {},
    setCustomValidity(message) { this.validity.valid = !message; },
  }]));
  const request = (action, payload) => {
    calls.push({ action, payload });
    if (action === "count_action") return Promise.resolve({ index: "123" });
    return Promise.resolve({ truename: "the", browsed: { type: "int", value: payload.value }, display: { kind: "text", type: "int", value: payload.value } });
  };
  vm.runInNewContext(runnerSource + "\n" + source, {
    document: { querySelector: (i) => elements[i] },
    window: {
      location: { get href() { return url.href; } },
      history: {
        replaceState(state, title, next) { url = new URL(next); },
        pushState(state, title, next) { url = new URL(next); },
      },
      addEventListener: (event, callback) => { listeners[event] = callback; },
    },
    URL, URLSearchParams, configured: Promise.resolve(), request,
    presentation: { root: 53, bpm: 180, position: "middle" },
    ValueDisplay: class {
      constructor(container, onAction) { this.container = container; this.onAction = onAction; display = this; }
      clear() { this.value = null; this.container.inert = false; }
      show(value) { this.value = value; }
    },
    setTimeout() { assert.equal(this, undefined, "Browser timers cannot be called on CountRunner"); },
    clearTimeout() { assert.equal(this, undefined, "Browser timers cannot be called on CountRunner"); },
    describeObject: (i) => `${i.type}: ${i.value}`,
    TunePlayer: class {}, console,
  });
  return {
    calls, elements,
    get url() { return url; },
    get display() { return display; },
    input(selector, value) {
      const input = elements[selector];
      let prevented = false;
      input.beforeinput({ data: value, preventDefault() { prevented = true; } });
      if (!prevented) { input.value = value; input.input(); }
      return prevented;
    },
    load(next) { url = new URL(next); listeners.viewchange(); },
  };
}

test("Count loads URL values exactly and defaults invalid increments to one", () => {
  for (const inc of ["-2", "0", "abc", ""]) {
    const app = page(`https://ax.to/nmr?count=9007199254740993&inc=${inc}`);
    assert.equal(app.elements["#count-value"].value, "9007199254740993");
    assert.equal(app.elements["#count-increment"].value, "1");
    assert.equal(app.elements["#count-run"].checked, false);
    assert.equal(app.url.search, "?count=9007199254740993&inc=1");
  }
  return flush();
});

test("Count sends meter and pitch settings and refreshes notation when they change", () => {
  const app = page("https://ax.to/nmr?count=72&inc=1");
  return flush().then(() => {
    const payload = app.calls.at(-1).payload;
    assert.equal(payload.root, 53);
    assert.equal(payload.position, "middle");
    assert.equal(payload.time_signature.top, "4");
    assert.equal(payload.time_signature.bottom, 4);
    assert.equal(app.input("#score-top", "7x"), true);
    app.input("#score-top", "7");
    app.elements["#score-bottom"].value = "12";
    app.elements["#score-bottom"].input();
    return flush();
  }).then(() => {
    const payload = app.calls.at(-1).payload;
    assert.equal(payload.time_signature.top, "7");
    assert.equal(payload.time_signature.bottom, 12);
    const before = app.calls.length;
    app.elements["#tune-root"].change();
    return flush().then(() => assert.equal(app.calls.length, before + 1));
  });
});

test("value actions navigate to the canonical count without losing the increment", () => {
  const app = page("https://ax.to/nmr?count=3&inc=7");
  return flush().then(() => {
    app.display.onAction({ action: "move", move: "e2e4" });
    return flush();
  }).then(() => {
    assert.equal(app.url.search, "?count=123&inc=7");
    assert.equal(app.elements["#count-value"].value, "123");
    assert.equal(app.elements["#count-run"].checked, false);
    assert.equal(app.display.value.value, "123");
  });
});

test("a pending board action cannot navigate away from another view", () => {
  const app = page("https://ax.to/nmr?count=3&inc=7");
  return flush().then(() => {
    app.display.onAction({ action: "move", move: "e2e4" });
    app.elements["#count-view"].hidden = true;
    app.load("https://ax.to/nmr?type=clock");
    return flush();
  }).then(() => {
    assert.equal(app.url.search, "?type=clock");
    assert.equal(app.display.value, null);
  });
});

test("component rendering errors are shown instead of leaving an unexplained empty area", () => {
  const app = page("https://ax.to/nmr?count=3&inc=1");
  app.display.show = () => { throw new Error("Could not render the value"); };
  return flush().then(() => {
    assert.equal(app.elements["#count-message"].textContent, "Could not render the value");
    assert.equal(app.elements["#count-run"].disabled, true);
  });
});

test("Count names the exact index, displays its object, and only accepts digits", () => {
  const app = page("https://ax.to/nmr?count=0&inc=3");
  assert.equal(app.elements["#count-truename"].hidden, false);
  assert.equal(app.elements["#count-truename"].textContent, "Loading truename…");
  assert.equal(app.elements["#count-truename"].disabled, true);
  return flush().then(() => {
    assert.equal(app.elements["#count-truename"].textContent, "the");
    assert.equal(app.elements["#count-object"].textContent, "int: 0");
    assert.equal(app.input("#count-value", "12x"), true);
    assert.equal(app.elements["#count-value"].value, "0");
    app.input("#count-value", "9007199254740993");
    return flush();
  }).then(() => {
    assert.equal(app.calls.at(-1).payload.value, "9007199254740993");
    assert.equal(app.url.search, "?count=9007199254740993&inc=3");
    app.input("#count-increment", "0");
    assert.equal(app.elements["#count-run"].disabled, true);
    app.input("#count-increment", "7");
    assert.equal(app.elements["#count-run"].disabled, false);
    app.input("#count-value", "");
    assert.equal(app.elements["#count-run"].disabled, true);
    assert.equal(app.elements["#count-truename"].hidden, true);
  });
});

test("Count restores bookmarks on Back and Forward without enabling Run", () => {
  const app = page("https://ax.to/nmr?count=1&inc=2");
  app.load("https://ax.to/nmr?count=42&inc=5");
  assert.equal(app.elements["#count-value"].value, "42");
  assert.equal(app.elements["#count-increment"].value, "5");
  assert.equal(app.elements["#count-run"].checked, false);
  app.load("https://ax.to/nmr?count=-1&inc=1");
  assert.equal(app.elements["#count-value"].value, "0");
  return flush();
});
