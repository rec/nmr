import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = fs.readFileSync(new URL("../nmr/web/tune.js", import.meta.url), "utf8").replaceAll("export ", "");

class Parameter {
  constructor(value = 0) { this.value = value; this.events = []; }
  cancelScheduledValues(time) { this.events.push(["cancel", time]); }
  setValueAtTime(value, time) { this.value = value; this.events.push(["set", value, time]); }
  linearRampToValueAtTime(value, time) { this.value = value; this.events.push(["ramp", value, time]); }
}

class AudioNode {
  constructor(kind) { this.kind = kind; this.connections = []; }
  connect(target) { this.connections.push(target); return target; }
  disconnect() { this.connections = []; }
}

class AudioContext {
  currentTime = 10;
  nodes = [];
  addEventListener() {}
  node(kind) { const node = new AudioNode(kind); this.nodes.push(node); return node; }
  createGain() { const node = this.node("gain"); node.gain = new Parameter(1); return node; }
  createStereoPanner() { const node = this.node("pan"); node.pan = new Parameter(); return node; }
  createDelay() { const node = this.node("delay"); node.delayTime = new Parameter(); return node; }
  createWaveShaper() { return this.node("shape"); }
  createPeriodicWave(real, imag, options) { return { real, imag, options }; }
  createOscillator() {
    const node = this.node("oscillator");
    node.frequency = new Parameter();
    node.start = (time = 0) => { node.started = time; };
    node.stop = (time) => { node.stopped = time; };
    node.setPeriodicWave = (wave) => { node.wave = wave; };
    return node;
  }
}

function synth(onPosition = null) {
  const frames = new Map();
  let nextFrame = 0;
  const context = vm.createContext({
    AudioContext, onPosition,
    requestAnimationFrame(callback) { frames.set(++nextFrame, callback); return nextFrame; },
    cancelAnimationFrame(id) { frames.delete(id); },
  });
  const player = vm.runInContext(source + "\nnew TunePlayer(() => {}, onPosition);", context);
  return { player, frames, context };
}

function voices(player) {
  return player.context.nodes.filter((i) => i.kind === "oscillator" && i.frequency.value > 1);
}

test("playback positions follow the audio clock through rests and clear on stop or completion", () => {
  const positions = [];
  const { player, frames } = synth((seconds) => positions.push(seconds));
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
  voices(player)[0].onended();
  assert.equal(frames.size, 1);
  for (const voice of voices(player).slice(1)) voice.onended();
  assert.equal(positions.at(-1), null);
  assert.equal(frames.size, 0);
  player.play([{ pitch: 53, onset: 0, duration: 1 }]);
  player.stop();
  assert.equal(positions.at(-1), null);
  assert.equal(frames.size, 0);
});

test("volume uses decibel spacing with unity at 120 and tune envelopes reach full amplitude", () => {
  const { player, context } = synth();
  const master = player.context.nodes[0].gain;
  assert.ok(Math.abs(master.value - 10 ** (-20 / 20)) < 1e-12, "Default volume is 100");
  for (const level of [0, 90, 100, 120]) {
    vm.runInContext(`setMasterVolume(${level});`, context);
    assert.equal(master.value, level === 0 ? 0 : 10 ** ((level - 120) / 20));
  }
  player.play([{ pitch: 53, onset: 0, duration: 1 }]);
  const envelope = voices(player)[0].connections[0].gain;
  assert.deepEqual(envelope.events.filter((i) => i[0] === "ramp").map((i) => i[1]), [1, 0]);
});

test("both timbres preserve note pitches, times and envelopes in either Evolve state", () => {
  const { player } = synth();
  const event = { pitch: 60, onset: 0.25, duration: 1 };
  player.play([event]);
  const first = voices(player).slice();
  assert.deepEqual(first.map(i => i.type), ["triangle", "sawtooth"]);
  for (const voice of first) {
    assert.equal(voice.started, 10.3);
    assert.equal(voice.stopped, 11.3);
    assert.deepEqual(voice.connections[0].gain.events, [
      ["set", 0, 10.3], ["ramp", 1, 10.3 + 0.005],
      ["set", 1, 11.295], ["ramp", 0, 11.3],
    ]);
  }
  player.setEvolution(false);
  player.context.currentTime = 100;
  player.play([event]);
  for (const voice of voices(player).slice(-2)) {
    assert.equal(voice.stopped - voice.started, 1);
    assert.equal(voice.frequency.value, first[0].frequency.value);
  }
});

test("shared modulation survives tune boundaries and switching evolution does not unmute effects", () => {
  const { player } = synth();
  const shared = player.context.nodes.slice();
  const modulators = shared.filter((i) => i.kind === "oscillator");
  assert.equal(modulators.length, 3);
  player.setVolume(0, 0);
  player.play([{ pitch: 53, onset: 0, duration: 1 }]);
  player.stop();
  player.setEvolution(false);
  assert.equal(player.output.gain.value, 0);
  assert.equal(player.dry.gain.value, 1);
  assert.equal(player.evolved.gain.value, 0);
  assert.ok(modulators.every((i) => i.stopped === undefined));
  player.play([{ pitch: 53, onset: 0, duration: 1 }]);
  assert.deepEqual(voices(player).slice(-2).map(i => i.type), ["triangle", "sawtooth"]);
  const held = voices(player).slice(-2);
  player.setEvolution(true);
  assert.equal(player.output.gain.value, 0);
  assert.equal(player.dry.gain.value, 0);
  assert.equal(player.evolved.gain.value, Math.SQRT2);
  assert.deepEqual(voices(player).slice(-2), held);
  assert.ok(held.every(i => i.stopped === 11.05));
  assert.equal(player.context.nodes.filter((i) => i.kind === "delay").length, 1);
  assert.equal(player.context.nodes.filter((i) => i.kind === "shape").length, 2);
  assert.equal(player.context.nodes.filter((i) => i.kind === "pan").length, 1);
  const echo = shared.find((i) => i.kind === "delay");
  assert.equal(echo.delayTime.value, 0.19);
  assert.ok(echo.connections.every((i) => i.gain.value < 1));
});
