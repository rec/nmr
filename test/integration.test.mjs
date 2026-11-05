import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import vm from "node:vm";
import { TruenameEditor } from "../nmr/web/truename-editor.mjs";
import { clockReading } from "../nmr/web/clock-time.mjs";
const source = fs.readFileSync(new URL("../nmr/web/app.js", import.meta.url), "utf8").replace(/^import .*;\n/gm, "");
const runnerSource = fs.readFileSync(new URL("../nmr/web/count-runner.mjs", import.meta.url), "utf8").replace("export class", "class");
const flush = () => new Promise(setImmediate);
function page(address = "http://localhost/?mode=count&index=42&inc=1", duration = 0.1, configuration = Promise.resolve({ types: { int: "Integer", cards: "Cards" }, words: ["the", "of", "and"] })) {
  let url = new URL(address);
  const elements = new Map();
  const radios = ["name", "count", "clock"].map((value) => ({ value, addEventListener(event, fn) { this[event] = fn; } }));
  const element = (id) => {
    if (!elements.has(id)) elements.set(id, {
      value: id === "#count-increment" ? "1" : id === "#score-top" || id === "#score-bottom" ? "4" : id === "#playback-delay" ? "2" : "",
      checked: ["#retain-playback", "#evolve"].includes(id), textContent: "", dataset: {}, validity: { valid: true }, style: { setProperty() {} },
      hidden: id === "#clock-count",
      attributes: {},
      addEventListener(event, fn) { this[event] = fn; }, setAttribute(name, value) { this.attributes[name] = String(value); },
      querySelector(selector) { return selector === ".value-text" ? null : element(id + " " + selector); },
      append() {}, querySelectorAll() { return []; }, replaceChildren() { this.textContent = ""; }, setCustomValidity(value) { this.validity.valid = !value; },
    });
    return elements.get(id);
  };
  const calls = [];
  const timers = [];
  let now = 0;
  let wallTime = Date.now();
  class ClockDate extends Date {
    constructor(...args) { super(...(args.length ? args : [wallTime])); }
    static now() { return wallTime; }
  }
  const listeners = {};
  let player;
  let hold;
  const app = { element, calls, radios, timers, listeners,
    get player() { return player; },
    get url() { return url; },
    elapse(milliseconds) { wallTime += milliseconds; },
    get date() { return new Date(wallTime); },
    tick() { timers.filter(i => i.name === "tick").at(-1).fn(); },
    switch(mode) { radios.find((i) => i.value === mode).change(); },
    hold(action) { hold = action; },
    load(address) { url = new URL(address); listeners.popstate(); },
  };
  vm.runInNewContext(runnerSource + "\n" + source, {
    document: { querySelector: element, querySelectorAll: () => radios, createElement: () => ({}) },
    window: { location: { get href() { return url.href; } }, history: {
      replaceState(a, b, next) { url = new URL(next); }, pushState(a, b, next) { url = new URL(next); },
    }, addEventListener(event, fn) { listeners[event] = fn; } },
    URL, URLSearchParams, Date: ClockDate, console, TruenameEditor, clockReading,
    ResizeObserver: class { observe() {} },
    requestAnimationFrame(fn) { fn(); },
    presentation: { root: 53, bpm: 180, position: "middle" },
    configured: configuration,
    request(action, payload) {
      calls.push({ action, payload });
      const result = action === "preview_truename" ? { playback: [{ onset: 0, duration }], score: { value: payload.value } }
        : { index: payload.source_type ? "123" : payload.value, truename: "the", browsed: { type: "int", value: "42" }, display: { kind: "text" } };
      if (hold === action) return new Promise((resolve) => { app.release = () => resolve(result); });
      return Promise.resolve(result);
    },
    ValueDisplay: class {
      constructor(container) { this.container = container; }
      clear() { this.container.textContent = ""; }
      show(value) { this.container.textContent = value?.kind || ""; }
    },
    TunePlayer: class {
      constructor(onEnded) { player = this; this.onEnded = onEnded; this.plays = 0; this.playing = false; this.context = { state: "suspended", suspend() { this.state = "suspended"; return Promise.resolve(); } }; }
      unlock() { this.context.state = "running"; return Promise.resolve(); }
      setVolume(value) { this.volume = value; }
      setEvolution(value) { this.evolving = value; }
      play() { this.onEnded(); this.playing = true; this.plays++; }
      finish() { this.playing = false; this.onEnded(); }
    },
    drawScore(container, value) { container.textContent = value.value; }, highlightScore() {},
    performance: { now: () => now },
    setTimeout(fn, delay) { timers.push({ name: fn.name, fn() { now += delay; fn(); }, delay }); return timers.length; }, clearTimeout() {},
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
  app.element("#type").value = "play:game:cards";
  app.element("#type").change(); await flush();
  assert.ok(app.element("#typed").textContent.startsWith("cards: "));
  app.load("http://localhost/?mode=count&type=cards&index=999999999999999999999&inc=7"); await flush();
  assert.equal(app.element("#count-value").value, "999999999999999999999");
  assert.equal(app.element("#count-increment").value, "7");
  assert.equal(app.element("#workspace h1").textContent, "Count");
  assert.equal(app.element("#source-name").textContent, "the");
});

test("Count advances before audio is unlocked and mute only changes the volume", async () => {
  const app = page(); await flush();
  assert.equal(app.player.volume, 0);
  assert.equal(app.player.evolving, true);
  app.element("#evolve").checked = false;
  app.element("#evolve").change();
  assert.equal(app.player.evolving, false);
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

test("muted Count waits for a long tune without overflowing browser timers", async () => {
  const duration = 40 * 24 * 60 * 60;
  const app = page(undefined, duration); await flush();
  const first = app.timers.find((i) => i.delay === 2147483647);
  assert.ok(first);
  first.fn(); await flush();
  assert.equal(app.element("#count-value").value, "42");
  assert.equal(app.timers.some((i) => i.delay === 2000), false);
  const remainder = app.timers.at(-1);
  assert.equal(remainder.delay, (duration + 0.05) * 1000 - first.delay);
  remainder.fn(); await flush();
  app.timers.find((i) => i.delay === 2000).fn(); await flush();
  assert.equal(app.element("#count-value").value, "43");
  assert.ok(app.timers.every((i) => i.delay <= 2147483647));
});

test("entering Clock defaults to All types and toggles between date/time and its live count", async () => {
  const app = page("http://localhost/?mode=count&type=int"); await flush();
  app.switch("clock"); await flush();
  assert.equal(app.element("#type").value, "");
  assert.equal(app.calls.filter((i) => i.action === "count").at(-1).payload.type_name, "");
  assert.equal(app.element("#count-value").hidden, true);
  assert.equal(app.element("#clock-reading").hidden, false);
  assert.equal(app.element("#count-value").value, "123");
  assert.equal(app.element("#clock-count").textContent, "123");
  assert.match(app.element("#clock-date").textContent, /^\d{4}-\d{2}-\d{2}$/);
  assert.match(app.element("#clock-hours").textContent, /^\d{2}:\d{2}:\d{2}$/);
  app.element("#clock-reading").click();
  assert.equal(app.element("#clock-time").hidden, true);
  assert.equal(app.element("#clock-count").hidden, false);
  app.timers.find((i) => i.delay <= 1000).fn(); await flush();
  assert.equal(app.element("#clock-count").hidden, false);
  app.element("#clock-reading").click();
  assert.equal(app.element("#clock-time").hidden, false);
  assert.equal(app.element("#clock-count").hidden, true);
  app.element("#type").value = "cards";
  app.element("#type").change(); await flush();
  assert.equal(app.calls.filter((i) => i.action === "count").at(-1).payload.type_name, "cards");
  app.switch("count"); await flush();
  assert.equal(app.element("#count-value").hidden, false);
});

test("a pending clock tick retains the complete previous reading", async () => {
  const app = page("http://localhost/?mode=clock"); await flush();
  const snapshot = () => [
    app.element("#count-value").value,
    ...["#clock-date", "#clock-hours", "#source-name", "#value-display"].map((i) => app.element(i).textContent),
  ];
  const before = snapshot();
  assert.equal(before.at(-1), "text");
  app.hold("count");
  app.timers.find((i) => i.delay <= 1000).fn(); await flush();
  assert.deepEqual(snapshot(), before);
  app.release(); await flush();
  assert.equal(app.element("#value-display").textContent, "text");
});

test("pause freezes Count, preserves mute and resumes at its next number", async () => {
  const app = page(); await flush();
  const pause = app.element("#pause-toggle");
  assert.equal(pause.hidden, false);
  pause.click(); await flush();
  assert.equal(pause.attributes["aria-pressed"], "true");
  assert.equal(app.player.context.state, "suspended");
  app.timers.find(i => Math.abs(i.delay - 150) < 1).fn(); await flush();
  app.timers.find(i => i.delay === 2000).fn(); await flush();
  assert.equal(app.element("#count-value").value, "42");
  app.element("#sound-toggle").click();
  assert.equal(app.player.context.state, "suspended", "Unmuting cannot resume transport");
  app.element("#sound-toggle").click();
  pause.click(); await flush();
  assert.equal(app.element("#count-value").value, "43");
  assert.equal(app.player.volume, 0);
  assert.equal(app.player.context.state, "running");
});

test("Clock freezes pending and periodic updates and catches up on resume", async () => {
  const app = page("http://localhost/?mode=clock"); await flush();
  const snapshot = ["#clock-date", "#clock-hours", "#clock-count", "#source-name"].map(i => app.element(i).textContent);
  app.hold("count");
  app.timers.find(i => i.delay <= 1000).fn(); await flush();
  app.element("#pause-toggle").click();
  const requests = app.calls.length;
  app.release(); await flush();
  app.elapse(60000);
  app.tick(); await flush();
  assert.equal(app.calls.length, requests);
  assert.deepEqual(["#clock-date", "#clock-hours", "#clock-count", "#source-name"].map(i => app.element(i).textContent), snapshot);
  app.hold(null);
  app.element("#pause-toggle").click(); await flush();
  assert.equal(app.calls.length, requests);
  assert.equal(app.player.context.state, "suspended");
  app.elapse(1000 - app.date.getTime() % 1000);
  app.tick(); await flush();
  assert.ok(app.calls.length > requests);
  assert.equal(app.calls.filter(i => i.action === "count").at(-1).payload.source_type, "datetime");
  assert.equal(app.calls.filter(i => i.action === "count").at(-1).payload.source_value, clockReading(app.date, false, false).value);
  assert.equal(app.player.context.state, "running");
});

for (const milliseconds of [0, 1, 500, 999]) test(`Clock resumes on the next second when Play is clicked at ${milliseconds}ms`, async () => {
  const app = page("http://localhost/?mode=clock"); await flush();
  app.element("#pause-toggle").click();
  const before = app.element("#clock-hours").textContent;
  app.elapse(5000 - app.date.getTime() % 1000 + milliseconds);
  const start = app.date.getTime();
  const calls = app.calls.length;
  app.element("#pause-toggle").click(); await flush();
  app.element("#sound-toggle").click();
  assert.equal(app.player.context.state, "suspended");
  assert.equal(app.calls.length, calls);
  assert.equal(app.element("#clock-hours").textContent, before);
  app.elapse(999 - milliseconds);
  app.tick(); await flush();
  assert.equal(app.calls.length, calls, "No update just before the boundary");
  app.elapse(1);
  app.tick(); await flush();
  assert.equal(app.player.context.state, "running");
  const reading = app.calls.filter(i => i.action === "count").at(-1);
  assert.equal(reading.payload.source_value, clockReading(new Date(start + 1000 - milliseconds)).value);
});

test("pausing again cancels a Clock restart waiting for the next second", async () => {
  const app = page("http://localhost/?mode=clock"); await flush();
  app.element("#pause-toggle").click();
  app.element("#pause-toggle").click();
  app.element("#pause-toggle").click();
  const calls = app.calls.length;
  app.elapse(2000);
  app.tick(); await flush();
  assert.equal(app.calls.length, calls);
  assert.equal(app.player.context.state, "suspended");
});

for (const mode of ["name", "count"]) test(`switching to ${mode} cancels a pending Clock resume without leaving audio suspended`, async () => {
  const app = page("http://localhost/?mode=clock"); await flush();
  app.element("#pause-toggle").click();
  app.element("#pause-toggle").click();
  assert.equal(app.player.context.state, "suspended");
  app.switch(mode); await flush();
  assert.equal(app.player.context.state, "running");
  assert.equal(app.element("#workspace").dataset.mode, mode);
  assert.equal(app.player.volume, 0, "Changing mode preserves mute");
});

test("pause is hidden in Name and retained when returning to Count or Clock", async () => {
  const app = page(); await flush();
  app.element("#pause-toggle").click();
  app.switch("name"); await flush();
  assert.equal(app.element("#pause-toggle").hidden, true);
  assert.equal(app.player.context.state, "running");
  app.switch("clock"); await flush();
  assert.equal(app.element("#pause-toggle").hidden, false);
  assert.equal(app.element("#pause-toggle").attributes["aria-pressed"], "true");
  assert.equal(app.player.context.state, "suspended");
  app.switch("count"); await flush();
  const calls = app.calls.length;
  app.tick(); await flush();
  assert.equal(app.calls.length, calls);
  assert.equal(app.element("#count-value").value, "123");
});

for (const mode of ["clock", "count", "name"]) test(`${mode} URL applies its layout before runtime configuration`, async () => {
  let configure;
  const configuration = new Promise(resolve => { configure = resolve; });
  const address = `http://localhost/?mode=${mode}&type=int&index=42&inc=7&value=the`;
  const app = page(address, 0.1, configuration);
  assert.equal(app.element("#workspace h1").textContent, mode[0].toUpperCase() + mode.slice(1));
  assert.equal(app.element("#workspace").dataset.mode, mode);
  assert.equal(app.radios.find(i => i.checked).value, mode);
  assert.equal(app.element("#name-editor").hidden, mode !== "name");
  assert.equal(app.element("#count-value").hidden, mode !== "count");
  assert.equal(app.element("#clock-reading").hidden, mode !== "clock");
  assert.equal(app.element("#pause-toggle").hidden, mode === "name");
  await flush();
  assert.equal(app.url.href, address, "Startup must preserve values until options and editor exist");
  assert.equal(app.calls.length, 0, "No codec requests before configuration");
  configure({ types: { int: "Integer" }, words: ["the", "of", "and"] });
  await flush();
  assert.equal(app.element("#type").value, "int");
  assert.equal(app.element("#count-increment").value, "7");
  if (mode === "name") assert.equal(app.element("#typed").textContent.trim(), "the");
  assert.ok(app.calls.length > 0);
});

for (const seconds of [0, 0.627, 2.5]) test(`Clock finishes a tune, waits ${seconds}s, then selects the next whole second`, async () => {
  const app = page("http://localhost/?mode=clock", 10);
  app.elapse(250 - app.date.getMilliseconds());
  app.element("#playback-delay").value = String(seconds);
  app.element("#playback-delay").change();
  await flush();
  const previews = () => app.calls.filter(i => i.action === "preview_truename").length;
  assert.equal(previews(), 1, "First tune starts without waiting for a boundary");
  for (let i = 0; i < 3; i++) { app.elapse(1000); app.tick(); await flush(); }
  assert.equal(previews(), 1, "Second ticks cannot interrupt a long tune");
  app.elapse(123);
  app.timers.find(i => i.name === "finish").fn(); await flush();
  const next = Math.floor((app.date.getTime() + seconds * 1000) / 1000) * 1000 + 1000;
  app.elapse(next - 1 - app.date.getTime());
  app.tick(); await flush();
  assert.equal(previews(), 1, "No playback before the next new second after the delay");
  app.elapse(1);
  app.tick(); await flush();
  assert.equal(previews(), 2);
  assert.equal(app.calls.filter(i => i.action === "count").at(-1).payload.source_value, clockReading(new Date(next)).value);
});

test("Count uses the same configurable delay after completion", async () => {
  const app = page(); await flush();
  app.element("#playback-delay").value = "3.5";
  app.element("#playback-delay").change();
  app.timers.find(i => i.name === "finish").fn(); await flush();
  assert.ok(app.timers.some(i => i.delay === 3500));
  assert.equal(app.element("#count-value").value, "42");
  app.timers.find(i => i.delay === 3500).fn(); await flush();
  assert.equal(app.element("#count-value").value, "43");
});

test("entering Clock lets an existing tune finish before the shared delay", async () => {
  const app = page(); await flush();
  app.switch("clock"); await flush();
  assert.equal(app.calls.filter(i => i.action === "preview_truename").length, 1);
  app.timers.find(i => i.name === "finish").fn(); await flush();
  app.elapse(3000);
  app.tick(); await flush();
  assert.equal(app.calls.filter(i => i.action === "preview_truename").length, 2);
});
