import assert from "node:assert/strict";
import test from "node:test";
import { CountRunner } from "../nmr/web/count-runner.mjs";

const flush = () => new Promise(setImmediate);

function counting() {
  let value = 0n;
  let finish;
  let timer = null;
  const played = [];
  const errors = [];
  const runner = new CountRunner(() => {
    played.push(value);
    return new Promise((resolve) => { finish = resolve; });
  }, () => { value += 3n; }, (error) => errors.push(error), () => 2000, (callback, delay) => {
    assert.equal(delay, 2000);
    timer = callback;
    return callback;
  }, () => { timer = null; });
  return {
    runner, played, errors,
    finish() { finish(); },
    get timer() { return timer; },
  };
}

test("Run plays, waits two seconds after completion, then increments and plays", () => {
  const app = counting();
  app.runner.start();
  return flush().then(() => {
    assert.deepEqual(app.played, [0n]);
    assert.equal(app.timer, null);
    app.finish();
    return flush();
  }).then(() => {
    assert.deepEqual(app.played, [0n]);
    app.timer();
    return flush();
  }).then(() => {
    assert.deepEqual(app.played, [0n, 3n]);
    app.runner.stop();
    app.finish();
  });
});

test("turning Run off during playback waits for the tune without incrementing", () => {
  const app = counting();
  app.runner.start();
  return flush().then(() => {
    app.runner.stop();
    assert.ok(app.runner.playing);
    app.finish();
    return flush();
  }).then(() => {
    assert.equal(app.timer, null);
    assert.equal(app.runner.playing, null);
    assert.deepEqual(app.played, [0n]);
  });
});

test("turning Run off during silence cancels the next increment", () => {
  const app = counting();
  app.runner.start();
  return flush().then(() => {
    app.finish();
    return flush();
  }).then(() => {
    assert.ok(app.timer);
    app.runner.stop();
    assert.equal(app.timer, null);
    assert.deepEqual(app.played, [0n]);
  });
});

test("restarting during playback uses the current tune instead of playing twice", () => {
  const app = counting();
  app.runner.start();
  return flush().then(() => {
    app.runner.stop();
    app.runner.start();
    assert.deepEqual(app.played, [0n]);
    app.finish();
    return flush();
  }).then(() => {
    assert.ok(app.timer);
    app.timer();
    return flush();
  }).then(() => {
    assert.deepEqual(app.played, [0n, 0n]);
    app.runner.stop();
    app.finish();
  });
});

test("a playback failure stops Run and reports the error", () => {
  const error = new Error("No playable tune");
  const errors = [];
  const runner = new CountRunner(() => Promise.reject(error), () => assert.fail(), (e) => errors.push(e));
  runner.start();
  return flush().then(() => {
    assert.equal(runner.running, false);
    assert.deepEqual(errors, [error]);
  });
});

test("transport pause retains the next increment instead of replaying the same count", async () => {
  const app = counting();
  app.runner.start(); await flush();
  app.runner.pause();
  app.finish(); await flush();
  app.timer(); await flush();
  assert.deepEqual(app.played, [0n]);
  app.runner.resume(); await flush();
  assert.deepEqual(app.played, [0n, 3n]);
  app.runner.stop(); app.finish();
});

test("resuming a paused playing tune does not restart it", async () => {
  const app = counting();
  app.runner.start(); await flush();
  app.runner.pause();
  app.runner.resume(); await flush();
  assert.deepEqual(app.played, [0n]);
  app.finish(); await flush();
  app.timer(); await flush();
  assert.deepEqual(app.played, [0n, 3n]);
  app.runner.stop(); app.finish();
});

test("the current delay setting is read after each tune completes", async () => {
  let delay = 500;
  const timers = [];
  const runner = new CountRunner(() => Promise.resolve(), () => {}, assert.fail, () => delay, (fn, milliseconds) => {
    timers.push({ fn, milliseconds });
  }, () => {});
  runner.start(); await flush();
  assert.equal(timers[0].milliseconds, 500);
  delay = 1250;
  timers[0].fn(); await flush();
  assert.equal(timers[1].milliseconds, 1250);
  runner.stop();
});
