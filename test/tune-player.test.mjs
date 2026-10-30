import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = fs.readFileSync(new URL("../nmr/web/tune.js", import.meta.url), "utf8").replaceAll("export ", "");

test("playback positions follow the audio clock through rests and clear on stop or completion", () => {
  const frames = new Map();
  const positions = [];
  const oscillators = [];
  let nextFrame = 0;
  const parameter = () => ({ value: 0, setValueAtTime() {}, linearRampToValueAtTime() {} });
  class AudioContext {
    currentTime = 10;
    createGain() { return { gain: parameter(), connect() {}, disconnect() {} }; }
    createOscillator() {
      const voice = { frequency: parameter(), connect: (gain) => gain, disconnect() {}, start() {}, stop() {} };
      oscillators.push(voice);
      return voice;
    }
    addEventListener() {}
  }
  const player = vm.runInNewContext(source + "\nnew TunePlayer(() => {}, (seconds) => positions.push(seconds));", {
    AudioContext, positions,
    requestAnimationFrame(callback) { frames.set(++nextFrame, callback); return nextFrame; },
    cancelAnimationFrame(id) { frames.delete(id); },
  });
  const frame = () => {
    const [id, callback] = frames.entries().next().value;
    frames.delete(id);
    callback();
  };
  player.play([{ pitch: 53, onset: 0, duration: 0.5 }, { pitch: 55, onset: 1, duration: 0.5 }]);
  player.context.currentTime = 10.8;
  frame();
  assert.ok(Math.abs(positions.at(-1) - 0.75) < 1e-9, "Position advances during the rest");
  frame();
  assert.ok(Math.abs(positions.at(-1) - 0.75) < 1e-9, "A paused audio clock does not advance the highlight");
  oscillators[0].onended();
  assert.equal(frames.size, 1);
  oscillators[1].onended();
  assert.equal(positions.at(-1), null);
  assert.equal(frames.size, 0);
  player.play([{ pitch: 53, onset: 0, duration: 1 }]);
  player.stop();
  assert.equal(positions.at(-1), null);
  assert.equal(frames.size, 0);
});

test("volume uses decibel spacing with unity at 120 and tune envelopes reach full amplitude", () => {
  const gains = [];
  class AudioContext {
    currentTime = 0;
    addEventListener() {}
    createGain() {
      const gain = { value: 0, cancelScheduledValues() {}, setValueAtTime(value) { this.value = value; }, linearRampToValueAtTime(value) { this.value = value; } };
      gains.push(gain);
      return { gain, connect() {}, disconnect() {} };
    }
    createOscillator() { return { frequency: {}, connect: (gain) => gain, start() {}, stop() {} }; }
  }
  const context = vm.createContext({ AudioContext, cancelAnimationFrame() {} });
  const player = vm.runInContext(source + "\nnew TunePlayer();", context);
  assert.ok(Math.abs(gains[0].value - 10 ** (-20 / 20)) < 1e-12, "Default volume is 100");
  for (const level of [0, 90, 100, 120]) {
    vm.runInContext(`setMasterVolume(${level});`, context);
    assert.equal(gains[0].value, level === 0 ? 0 : 10 ** ((level - 120) / 20));
  }
  const peaks = [];
  const createGain = player.context.createGain.bind(player.context);
  player.context.createGain = () => {
    const node = createGain();
    node.gain.linearRampToValueAtTime = (value) => peaks.push(value);
    return node;
  };
  player.play([{ pitch: 53, onset: 0, duration: 1 }]);
  assert.deepEqual(peaks, [1, 0]);
});
