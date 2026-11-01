import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import vm from "node:vm";
import { TruenameEditor } from "../nmr/web/truename-editor.mjs";
import { clockReading } from "../nmr/web/clock-time.mjs";
const source = fs.readFileSync(new URL("../nmr/web/app.js", import.meta.url), "utf8").replace(/^import .*;\n/gm, "");
const runnerSource = fs.readFileSync(new URL("../nmr/web/count-runner.mjs", import.meta.url), "utf8").replace("export class", "class");
const flush = () => new Promise(setImmediate);
function page(address = "http://localhost/?mode=count&index=42&inc=1") {
  let url = new URL(address);
  const elements = new Map();
  const radios = ["name", "count", "clock"].map((value) => ({ value, addEventListener(event, fn) { this[event] = fn; } }));
  const element = (id) => {
    if (!elements.has(id)) elements.set(id, {
      value: id === "#count-increment" ? "1" : id === "#score-top" || id === "#score-bottom" ? "4" : id === "#clock-interval" ? "5" : "",
      checked: id === "#retain-playback", textContent: "", dataset: {}, validity: { valid: true }, style: { setProperty() {} },
      attributes: {},
      addEventListener(event, fn) { this[event] = fn; }, setAttribute(name, value) { this.attributes[name] = String(value); },
      querySelector(selector) { return selector === ".value-text" ? null : element(id + " " + selector); },
      append() {}, querySelectorAll() { return []; }, replaceChildren() { this.textContent = ""; }, setCustomValidity(value) { this.validity.valid = !value; },
    });
    return elements.get(id);
  };
  const calls = [];
  const timers = [];
  const listeners = {};
  let player;
  let hold;
  const app = { element, calls, radios, timers, listeners,
    get player() { return player; },
    get url() { return url; },
    switch(mode) { radios.find((i) => i.value === mode).change(); },
    hold(action) { hold = action; },
    load(address) { url = new URL(address); listeners.popstate(); },
  };
  vm.runInNewContext(runnerSource + "\n" + source, {
    document: { querySelector: element, querySelectorAll: () => radios, createElement: () => ({}) },
    window: { location: { get href() { return url.href; } }, history: {
      replaceState(a, b, next) { url = new URL(next); }, pushState(a, b, next) { url = new URL(next); },
    }, addEventListener(event, fn) { listeners[event] = fn; } },
    URL, URLSearchParams, Date, console, TruenameEditor, clockReading,
    ResizeObserver: class { observe() {} },
    requestAnimationFrame(fn) { fn(); },
    presentation: { root: 53, bpm: 180, position: "middle" },
    configured: Promise.resolve({ types: { int: "Integer", cards: "Cards" }, words: ["the", "of", "and"] }),
    request(action, payload) {
      calls.push({ action, payload });
      const result = action === "preview_truename" ? { playback: [{ onset: 0, duration: 0.1 }], score: { value: payload.value } }
        : { index: payload.source_type ? "123" : payload.value, truename: "the", browsed: { type: "int", value: "42" }, display: { kind: "text" } };
      if (hold === action) return new Promise((resolve) => { app.release = () => resolve(result); });
      return Promise.resolve(result);
    },
    ValueDisplay: class { constructor(container) { this.container = container; } clear() {} show() {} },
    TunePlayer: class {
      constructor(onEnded) { player = this; this.onEnded = onEnded; this.plays = 0; this.playing = false; this.context = { state: "suspended" }; }
      unlock() { this.context.state = "running"; return Promise.resolve(); }
      setVolume(value) { this.volume = value; }
      play() { this.onEnded(); this.playing = true; this.plays++; }
      finish() { this.playing = false; this.onEnded(); }
    },
    drawScore(container, value) { container.textContent = value.value; }, highlightScore() {},
    setTimeout(fn, delay) { timers.push({ fn, delay }); return timers.length; }, clearTimeout() {},
  });
  return app;
}
test("Type changes preserve the exact count and pending requests cannot start stale music", async () => {
  const app = page("http://localhost/?mode=count&index=123456789012345678901234567890");
  app.hold("preview_truename");
  await flush();
  app.element("#type").value = "cards";
  app.element("#type").change();
  app.release();
  await flush();
  assert.equal(app.player.plays, 0);
  assert.equal(app.element("#count-value").value, "123456789012345678901234567890");
  assert.equal(app.calls.filter((i) => i.action === "count").at(-1).payload.type_name, "cards");
});
test("mode changes let audio finish and retain or clear its snapshot according to Settings", async () => {
  const app = page("http://localhost/?mode=name"); await flush();
  app.element("#sound-toggle").click();
  app.switch("count"); await flush();
  assert.equal(app.player.plays, 1);
  const name = app.element("#playing-name").textContent;
  app.switch("clock"); await flush();
  assert.equal(app.player.playing, true);
  assert.equal(app.element("#playing-name").textContent, name);
  assert.equal(app.calls.at(-1).payload.source_type, "datetime");
  app.switch("name"); await flush();
  app.player.finish(); await flush();
  assert.equal(app.element("#playing-name").textContent, name);
  app.element("#retain-playback").checked = false;
  app.element("#retain-playback").change();
  assert.equal(app.element("#playing-name").textContent, "");
});
test("Count resumes on return without overlapping the finishing tune", async () => {
  const app = page("http://localhost/?mode=name"); await flush();
  app.element("#sound-toggle").click();
  app.switch("count"); await flush();
  app.switch("name"); await flush();
  app.switch("count"); await flush();
  assert.equal(app.player.plays, 1);
  app.player.finish(); await flush();
  assert.ok(app.timers.some((i) => i.delay === 2000));
});
test("Name accepts truenames and Back restores mode, type and exact index", async () => {
  const app = page("http://localhost/?mode=name&type=int&edit=truename&value=the"); await flush();
  assert.equal(app.element("#typed").textContent.trim(), "the");
  const recognition = app.calls.find((i) => i.action === "recognize");
  assert.equal(recognition.payload.mode, "truename");
  assert.equal(recognition.payload.type_name, "int");
  app.load("http://localhost/?mode=count&type=cards&index=999999999999999999999&inc=7"); await flush();
  assert.equal(app.element("#count-value").value, "999999999999999999999");
  assert.equal(app.element("#count-increment").value, "7");
  assert.equal(app.element("#workspace h1").textContent, "Count");
  assert.equal(app.element("#source-name").textContent, "the");
});

test("Count advances before audio is unlocked and mute only changes the volume", async () => {
  const app = page(); await flush();
  assert.equal(app.player.volume, 0);
  assert.equal(app.player.plays, 0);
  app.timers.find((i) => Math.abs(i.delay - 150) < 1).fn(); await flush();
  app.timers.find((i) => i.delay === 2000).fn(); await flush();
  assert.equal(app.element("#count-value").value, "43");
  app.element("#sound-toggle").click();
  assert.equal(app.player.volume, 1);
  assert.equal(app.element("#sound-toggle").attributes["aria-pressed"], "false");
  app.element("#sound-toggle").click();
  assert.equal(app.player.volume, 0);
  assert.equal(app.element("#sound-toggle").attributes["aria-pressed"], "true");
  assert.equal(app.element("#count-value").value, "43");
});
