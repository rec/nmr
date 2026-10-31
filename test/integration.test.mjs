import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import vm from "node:vm";
import { TruenameEditor } from "../nmr/web/truename-editor.mjs";
import { Editor } from "../nmr/web/editor.mjs";
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
      addEventListener(event, fn) { this[event] = fn; }, setAttribute() {},
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
    URL, URLSearchParams, Date, console, Editor, TruenameEditor, clockReading,
    presentation: { root: 53, bpm: 180, position: "middle" },
    configured: Promise.resolve({ types: { int: "Integer", cards: "Cards" }, words: ["the", "of", "and"] }),
    request(action, payload) {
      calls.push({ action, payload });
      const result = action === "preview_truename" ? { playback: [1], score: { value: payload.value } }
        : { index: payload.source_type ? "123" : payload.value, truename: "the", browsed: { type: "int", value: "42" }, display: { kind: "text" } };
      if (hold === action) return new Promise((resolve) => { app.release = () => resolve(result); });
      return Promise.resolve(result);
    },
    ValueDisplay: class { constructor(container) { this.container = container; } clear() {} show() {} },
    TunePlayer: class {
      constructor(onEnded) { player = this; this.onEnded = onEnded; this.plays = 0; this.playing = false; }
      unlock() { return Promise.resolve(); }
      play() { this.onEnded(); this.playing = true; this.plays++; }
      finish() { this.playing = false; this.onEnded(); }
    },
    drawScore(container, value) { container.textContent = value.value; }, highlightScore() {},
    describeObject: (i) => `${i.type}: ${i.value}`,
    setTimeout(fn, delay) { timers.push({ fn, delay }); return timers.length; }, clearTimeout() {},
  });
  return app;
}
test("Type changes preserve the exact count and pending requests cannot start stale music", async () => {
  const app = page("http://localhost/?mode=count&index=123456789012345678901234567890");
  await flush();
  app.hold("preview_truename");
  app.element("#play").click();
  await flush();
  app.element("#type").value = "cards";
  app.element("#type").change();
  app.release();
  await flush();
  assert.equal(app.player.plays, 0);
  assert.equal(app.element("#count-value").value, "123456789012345678901234567890");
  assert.equal(app.calls.at(-1).payload.type_name, "cards");
});
test("mode changes let audio finish and retain or clear its snapshot according to Settings", async () => {
  const app = page(); await flush();
  app.element("#play").click(); await flush();
  assert.equal(app.player.plays, 1);
  const name = app.element("#playing-name").textContent;
  app.switch("clock"); await flush();
  assert.equal(app.player.playing, true);
  assert.equal(app.element("#playing-name").textContent, name);
  assert.equal(app.calls.at(-1).payload.source_type, "datetime");
  app.player.finish(); await flush();
  assert.equal(app.element("#playing-name").textContent, name);
  app.element("#retain-playback").checked = false;
  app.element("#retain-playback").change();
  assert.equal(app.element("#playing-name").textContent, "");
});
test("automatic Count resumes on return without overlapping the finishing tune", async () => {
  const app = page(); await flush();
  app.element("#automatic").checked = true; app.element("#automatic").change(); await flush();
  app.switch("name"); await flush();
  app.switch("count"); await flush();
  assert.equal(app.element("#automatic").checked, true);
  assert.equal(app.player.plays, 1);
  app.player.finish(); await flush();
  assert.ok(app.timers.some((i) => i.delay === 2000));
});
test("Name fields update each other and Back restores mode, type and exact index", async () => {
  const app = page("http://localhost/?mode=name&type=int&edit=truename&value=the"); await flush();
  assert.equal(app.element("#value").value, "42");
  app.element("#value").value = "43"; app.element("#value").input();
  app.timers.find((i) => i.delay === 120).fn(); await flush();
  assert.equal(app.calls.at(-1).payload.mode, "description");
  assert.equal(app.calls.at(-1).payload.type_name, "int");
  app.load("http://localhost/?mode=count&type=cards&index=999999999999999999999&inc=7"); await flush();
  assert.equal(app.element("#count-value").value, "999999999999999999999");
  assert.equal(app.element("#count-increment").value, "7");
  assert.equal(app.element("#description-region").inert, true);
});
