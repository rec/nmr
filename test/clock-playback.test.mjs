import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = fs.readFileSync(new URL("../nmr/web/clock.js", import.meta.url), "utf8").replace(/^import .*;\n/gm, "");
const flush = () => new Promise(setImmediate);

function page(hidden = false) {
  const elements = Object.fromEntries(["clock-view", "clock-time", "clock-date", "clock-hours", "clock-truename", "clock-playing", "clock-on", "clock-interval", "clock-time-only", "clock-short-name", "clock-display-utc"].map((i) => ["#" + i, {
    checked: false, hidden: i === "clock-view" && hidden, value: "5", textContent: "",
    addEventListener(event, callback) { this[event] = callback; },
  }]));
  const calls = [];
  const pending = [];
  const listeners = {};
  const audio = { plays: 0, stops: 0 };
  let timer;
  const app = { hold: null, calls, audio, pending,
    tick() { timer(); },
    switch(hidden) { elements["#clock-view"].hidden = hidden; listeners.viewchange(); },
    enable() { elements["#clock-on"].checked = true; elements["#clock-on"].change(); },
  };
  vm.runInNewContext(source, {
    document: { querySelector: (i) => elements[i] },
    window: { addEventListener: (name, callback) => { listeners[name] = callback; } },
    configured: Promise.resolve(),
    clockReading: () => ({ second: 1, due: true, type: "time", value: "00:00:01", displayDate: "2027-01-01", displayTime: "00:00:01" }),
    presentation: { root: 53, bpm: 180, position: "middle" },
    Date: class extends Date { static now() { return 1000; } },
    setTimeout: (callback) => { timer = callback; }, console,
    request: (operation) => {
      calls.push(operation);
      const result = operation === "convert" ? { truename: "the" } : { playback: [{ pitch: 53, onset: 0, duration: 1 }] };
      return app.hold === operation ? new Promise((resolve) => pending.push(() => resolve(result))) : Promise.resolve(result);
    },
    TunePlayer: class {
      constructor(onEnded) { this.onEnded = onEnded; }
      setVolume() {}
      unlock() { return Promise.resolve(); }
      play() { this.playing = true; audio.plays++; }
      stop() { this.playing = false; audio.stops++; this.onEnded(); }
    },
  });
  return app;
}

test("leaving Clock stops its current tune and prevents subsequent hidden ticks", () => {
  const app = page();
  return flush().then(() => {
    app.enable();
    app.tick();
    return flush();
  }).then(() => {
    assert.equal(app.audio.plays, 1);
    app.switch(true);
    assert.equal(app.audio.stops, 1);
    const calls = app.calls.length;
    app.tick();
    return flush().then(() => {
      assert.equal(app.calls.length, calls);
      assert.equal(app.audio.plays, 1);
      app.switch(false);
      app.tick();
      return flush();
    });
  }).then(() => assert.equal(app.audio.plays, 2));
});

for (const operation of ["convert", "preview_truename"]) {
  test(`a pending ${operation} response cannot restart Clock after navigation`, () => {
    const app = page();
    return flush().then(() => {
      app.enable();
      app.hold = operation;
      app.tick();
      return flush();
    }).then(() => {
      assert.ok(app.pending.length);
      app.switch(true);
      for (const resolve of app.pending) resolve();
      return flush();
    }).then(() => assert.equal(app.audio.plays, 0));
  });
}

test("opening another page does not start Clock requests or audio", () => {
  const app = page(true);
  return flush().then(() => {
    app.tick();
    return flush();
  }).then(() => {
    assert.deepEqual(app.calls, []);
    assert.equal(app.audio.plays, 0);
  });
});
