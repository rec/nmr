/* Native Web Audio regression: node test/tune-audio.cjs [Chrome executable]. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawn } = require("node:child_process");

const directory = fs.mkdtempSync(path.join(os.tmpdir(), "nmr-tune-audio-"));
const source = fs.readFileSync(path.join(__dirname, "../nmr/web/tune.js"), "utf8").replaceAll("export ", "");
async function render() {
  const results = [];
  for (const pitch of [53, 60, 84]) {
    for (const evolving of [false, true, "switch"]) {
      const context = new OfflineAudioContext(2, 25 * 48000, 48000);
      globalThis.AudioContext = class { constructor() { return context; } };
      const player = new TunePlayer();
      player.setEvolution(evolving === true);
      player.play([{ pitch, onset: 0, duration: 24 }]);
      if (evolving === "switch") {
        context.suspend(8).then(() => { player.setEvolution(true); context.resume(); });
        context.suspend(16).then(() => { player.setEvolution(false); context.resume(); });
      }
      const audio = await context.startRendering();
      const channels = [audio.getChannelData(0), audio.getChannelData(1)];
      const rms = [];
      const colour = [];
      const fundamental = [];
      const harmonics = [];
      for (let second = 1; second < 23; second++) {
        const start = second * 48000;
        let power = 0;
        for (let i = start; i < start + 48000; i++) {
          power += channels[0][i] ** 2 + channels[1][i] ** 2;
        }
        rms.push(Math.sqrt(power / 96000));
        const frequency = 440 * 2 ** ((pitch - 69) / 12);
        const energy = (harmonic) => {
          const omega = 2 * Math.PI * frequency * harmonic / 48000;
          const factor = 2 * Math.cos(omega);
          let previous = 0;
          let before = 0;
          for (let i = start; i < start + 48000; i++) {
            const sample = channels[0][i] + channels[1][i];
            const current = sample + factor * previous - before;
            before = previous;
            previous = current;
          }
          return previous ** 2 + before ** 2 - factor * previous * before;
        };
        // Fit and subtract the fundamental, retaining harmonic sidebands from
        // continuous modulation and from switching Evolve during a held note.
        let cc = 0, ss = 0, cs = 0, xc = 0, xs = 0, monoPower = 0;
        for (let i = start; i < start + 48000; i++) {
          const phase = 2 * Math.PI * frequency * i / 48000;
          const c = Math.cos(phase), s = Math.sin(phase);
          const x = channels[0][i] + channels[1][i];
          cc += c * c; ss += s * s; cs += c * s;
          xc += x * c; xs += x * s; monoPower += x * x;
        }
        const determinant = cc * ss - cs * cs;
        const a = (xc * ss - xs * cs) / determinant;
        const b = (xs * cc - xc * cs) / determinant;
        fundamental.push(10 * Math.log10((a * a + b * b) / 2));
        harmonics.push(10 * Math.log10((monoPower - a * xc - b * xs) / 48000));
        colour.push(10 * Math.log10(energy(2) / energy(3)));
      }
      const bytes = new Uint8Array(channels[0].length * 4);
      const view = new DataView(bytes.buffer);
      for (let i = 0; i < channels[0].length; i++) {
        for (let channel = 0; channel < 2; channel++) {
          const sample = Math.max(-1, Math.min(1, channels[channel][i]));
          view.setInt16(i * 4 + channel * 2, Math.round(sample * 32767), true);
        }
      }
      let binary = "";
      for (let offset = 0; offset < bytes.length; offset += 32768) {
        binary += String.fromCharCode(...bytes.subarray(offset, offset + 32768));
      }
      results.push({ pitch, evolving, rms, colour, fundamental, harmonics, pcm: btoa(binary) });
    }
  }
  return results;
}
const chrome = process.argv[2] || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const browser = spawn(chrome, ["--headless", "--disable-gpu", "--remote-debugging-pipe", "--no-first-run", `--user-data-dir=${path.join(directory, "chrome")}`], { stdio: ["ignore", "ignore", "inherit", "pipe", "pipe"] });
let sequence = 0;
let incoming = "";
const pending = new Map();
browser.stdio[4].on("data", chunk => {
  incoming += chunk.toString();
  let end;
  while ((end = incoming.indexOf("\0")) !== -1) {
    const message = JSON.parse(incoming.slice(0, end));
    incoming = incoming.slice(end + 1);
    const response = pending.get(message.id);
    if (response) {
      pending.delete(message.id);
      if (message.error) response.reject(new Error(JSON.stringify(message.error)));
      else response.resolve(message.result);
    }
  }
});
function request(method, params = {}, sessionId) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    pending.set(id, { resolve, reject });
    browser.stdio[3].write(JSON.stringify({ id, method, params, sessionId }) + "\0");
  });
}
browser.on("exit", code => {
  for (const response of pending.values()) response.reject(new Error(`Chrome exited: ${code}`));
});
const timeout = setTimeout(() => { browser.kill(); }, 60000);
request("Target.createTarget", { url: "about:blank" }).then(({ targetId }) =>
  request("Target.attachToTarget", { targetId, flatten: true })
).then(({ sessionId }) => request("Runtime.evaluate", {
  expression: source + `\n(${render.toString()})()`, awaitPromise: true, returnByValue: true,
}, sessionId)).then(response => {
  if (response.exceptionDetails) throw new Error(JSON.stringify(response.exceptionDetails));
  check(response.result.value);
}).finally(() => {
  clearTimeout(timeout);
  browser.kill();
});

function check(results) {
  for (const result of results) {
    const pcm = Buffer.from(result.pcm, "base64");
    const header = Buffer.alloc(44);
    header.write("RIFF"); header.writeUInt32LE(36 + pcm.length, 4); header.write("WAVEfmt ", 8);
    header.writeUInt32LE(16, 16); header.writeUInt16LE(1, 20); header.writeUInt16LE(2, 22);
    header.writeUInt32LE(48000, 24); header.writeUInt32LE(192000, 28);
    header.writeUInt16LE(4, 32); header.writeUInt16LE(16, 34);
    header.write("data", 36); header.writeUInt32LE(pcm.length, 40);
    const mode = result.evolving === "switch" ? "switch" : result.evolving ? "evolve" : "plain";
    fs.writeFileSync(path.join(directory, `${result.pitch}-${mode}.wav`), Buffer.concat([header, pcm]));
    delete result.pcm;
  }
  fs.writeFileSync(path.join(directory, "measurements.json"), JSON.stringify(results, null, 2));
  console.log(`48 kHz WAV files and measurements: ${directory}`);
  for (const plain of results.filter(i => !i.evolving)) {
    for (const evolved of results.filter(i => i.pitch === plain.pitch && i.evolving)) {
      const differences = evolved.rms.map((value, i) => 20 * Math.log10(value / plain.rms[i]));
      console.log(`MIDI ${plain.pitch}, ${evolved.evolving}: level differences ${differences.map(i => i.toFixed(2)).join(", ")} dB; harmonic mix range ${(Math.max(...evolved.colour) - Math.min(...evolved.colour)).toFixed(2)} dB`);
      assert.ok(differences.every(i => Math.abs(i) < 0.5), "Evolve stays within 0.5 dB of plain playback");
      assert.ok(Math.max(...evolved.colour) - Math.min(...evolved.colour) > 12, "A held note changes its harmonic mix by more than 12 dB");
      const fundamentalRange = Math.max(...evolved.fundamental) - Math.min(...evolved.fundamental);
      const harmonicRange = Math.max(...evolved.harmonics) - Math.min(...evolved.harmonics);
      console.log(`Fundamental range ${fundamentalRange.toFixed(3)} dB; combined harmonic range ${harmonicRange.toFixed(3)} dB`);
      assert.ok(fundamentalRange < 0.5, "The fundamental stays steady through the blend");
      assert.ok(harmonicRange < 0.5, "Combined harmonic energy stays steady through the blend");
    }
  }
}
