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
  const elements = Object.fromEntries(["#count-view", "#count-value", "#count-increment", "#count-run", "#count-truename", "#count-object", "#count-message"].map((i) => [i, {
    value: i === "#count-increment" ? "1" : "0", hidden: false, checked: false,
    validity: { valid: true },
    addEventListener(event, callback) { this[event] = callback; },
    setAttribute() {},
    setCustomValidity(message) { this.validity.valid = !message; },
  }]));
  const request = (action, payload) => {
    calls.push({ action, payload });
    return Promise.resolve({ truename: "the", browsed: { type: "int", value: payload.value } });
  };
  vm.runInNewContext(runnerSource + "\n" + source, {
    document: { querySelector: (i) => elements[i] },
    window: {
      location: { get href() { return url.href; } },
      history: { replaceState(state, title, next) { url = new URL(next); } },
      addEventListener: (event, callback) => { listeners[event] = callback; },
    },
    URL, URLSearchParams, configured: Promise.resolve(), request,
    setTimeout() { assert.equal(this, undefined, "Browser timers cannot be called on CountRunner"); },
    clearTimeout() { assert.equal(this, undefined, "Browser timers cannot be called on CountRunner"); },
    describeObject: (i) => `${i.type}: ${i.value}`,
    TunePlayer: class {}, console,
  });
  return {
    calls, elements,
    get url() { return url; },
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
