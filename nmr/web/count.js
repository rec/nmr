import { configured, request } from "./runtime.js";
import { describeObject } from "./description.mjs";
import { CountRunner } from "./count-runner.mjs";
import { TunePlayer } from "./tune.js";
import { presentation } from "./presentation.mjs";

const view = document.querySelector("#count-view");
const field = document.querySelector("#count-value");
const increment = document.querySelector("#count-increment");
const run = document.querySelector("#count-run");
const truename = document.querySelector("#count-truename");
const object = document.querySelector("#count-object");
const message = document.querySelector("#count-message");
let revision = 0;
let named = null;
let playback = null;
let playingValue = null;
let finished = null;
let player;
try {
  player = new TunePlayer(() => {
    truename.setAttribute("aria-pressed", "false");
    const resolve = finished;
    finished = null;
    resolve?.();
  });
} catch (error) {
  console.error("Audio is unavailable in this browser.", error);
}

function report(error) {
  run.checked = false;
  message.textContent = error.message;
  console.error(error);
}
function pause() {
  run.checked = false;
  runner.stop();
}
function writeURL() {
  if (view.hidden) return;
  const url = new URL(window.location.href);
  url.search = new URLSearchParams({ count: field.value || "0", inc: increment.validity.valid && increment.value ? increment.value : "1" });
  if (url.pathname !== "/") url.pathname = url.pathname.replace(/\/$/, "");
  window.history.replaceState(window.history.state, "", url);
}
function refresh() {
  const current = ++revision;
  named = null;
  truename.hidden = !field.value;
  truename.disabled = true;
  truename.textContent = field.value ? "Loading truename…" : "";
  object.textContent = "";
  message.textContent = "";
  run.disabled = !player || !field.value || !increment.value || !increment.validity.valid;
  writeURL();
  if (!field.value) return Promise.resolve(null);
  const value = field.value;
  const result = configured.then(() => request("count", { value }));
  named = result;
  result.then((result) => {
    if (revision !== current) return;
    truename.textContent = result.truename;
    truename.hidden = false;
    truename.disabled = !player;
    object.textContent = result.browsed ? describeObject(result.browsed) : "";
  }, (error) => {
    if (revision !== current) return;
    pause();
    run.disabled = true;
    truename.hidden = true;
    message.textContent = error.message;
  });
  return result;
}
function play() {
  if (playback) return playingValue === field.value ? playback : playback.then(play);
  if (!player || !named) return Promise.reject(new Error("Enter a count to play."));
  const unlocked = player.unlock();
  playingValue = field.value;
  playback = Promise.all([named, unlocked]).then(([result]) => request("preview_truename", {
    value: result.truename, absolute: true, ...presentation,
  })).then((music) => {
    if (music.playback_error) throw new Error(music.playback_error);
    return new Promise((resolve) => {
      player.play(music.playback);
      truename.setAttribute("aria-pressed", "true");
      if (player.playing) finished = resolve;
      else resolve();
    });
  }).finally(() => { playback = null; });
  return playback;
}
const runner = new CountRunner(play, () => {
  field.value = String(BigInt(field.value) + BigInt(increment.value));
  refresh();
}, report);

for (const input of [field, increment]) {
  let accepted = input.value;
  input.addEventListener("beforeinput", (event) => {
    accepted = input.value;
    if (event.data && /[^0-9]/.test(event.data)) event.preventDefault();
  });
  input.addEventListener("input", () => {
    if (/[^0-9]/.test(input.value)) input.value = accepted;
    accepted = input.value;
    pause();
    increment.setCustomValidity(increment.value && BigInt(increment.value) === 0n ? "Increment must be positive." : "");
    refresh();
  });
}
run.addEventListener("change", () => {
  if (run.checked) runner.start();
  else runner.stop();
});
truename.addEventListener("click", () => {
  if (window.getSelection()?.toString()) return;
  pause();
  play().catch(report);
});
function load() {
  pause();
  if (view.hidden) return;
  const parameters = new URL(window.location.href).searchParams;
  const count = parameters.get("count") || "0";
  const inc = parameters.get("inc") || "1";
  field.value = /^[0-9]+$/.test(count) ? count : "0";
  increment.value = /^[0-9]+$/.test(inc) && BigInt(inc) > 0n ? inc : "1";
  increment.setCustomValidity("");
  refresh();
}
window.addEventListener("viewchange", load);
load();
