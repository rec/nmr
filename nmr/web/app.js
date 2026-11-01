import "./volume.js";
import "./help.js";
import { configured, request } from "./runtime.js";
import { TruenameEditor } from "./truename-editor.mjs";
import { TunePlayer } from "./tune.js";
import { presentation } from "./presentation.mjs";
import { CountRunner } from "./count-runner.mjs";
import { clockReading } from "./clock-time.mjs";
import { ValueDisplay } from "./value-display.mjs";
import { drawScore, highlightScore } from "./music-notation.mjs";

const workspace = document.querySelector("#workspace");
const heading = workspace.querySelector("h1");
const modes = document.querySelectorAll('[name="mode"]');
const type = document.querySelector("#type");
const field = document.querySelector("#count-value");
const nameField = document.querySelector("#name-editor");
const typed = document.querySelector("#typed");
const guessed = document.querySelector("#guessed");
const time = document.querySelector("#clock-time");
const clockDate = document.querySelector("#clock-date");
const clockHours = document.querySelector("#clock-hours");
const clockReadingButton = document.querySelector("#clock-reading");
const clockCount = document.querySelector("#clock-count");
const sourceName = document.querySelector("#source-name");
const sound = document.querySelector("#sound-toggle");
const increment = document.querySelector("#count-increment");
const interval = document.querySelector("#clock-interval");
const timeOnly = document.querySelector("#clock-time-only");
const displayUTC = document.querySelector("#clock-display-utc");
const retain = document.querySelector("#retain-playback");
const playingName = document.querySelector("#playing-name");
const score = document.querySelector("#playing-score");
const scoreTop = document.querySelector("#score-top");
const scoreBottom = document.querySelector("#score-bottom");
const color = document.querySelector("#score-highlight-color");
const message = document.querySelector("#message");
let muted = true;
let mode = "name";
let editor;
let version = 0;
let current = null;
let loading = Promise.resolve(null);
let playback = null;
let ended = null;
let playingBpm = presentation.bpm;
let ready = false;
let player;
try {
  player = new TunePlayer(() => {
    highlightScore(score, null, playingBpm);
    const resolve = ended;
    ended = null;
    resolve?.();
    if (!retain.checked) clearPlayback();
  }, (seconds) => highlightScore(score, seconds, playingBpm));
} catch (error) {
  console.error("Audio is unavailable in this browser.", error);
}
const display = new ValueDisplay(document.querySelector("#value-display"), (action) => {
  if (mode === "clock" || !current) return;
  const revision = version;
  const object = current.browsed;
  const pending = mode === "count"
    ? request("count_action", { value: field.value, type_name: type.value, ...action })
    : request("value_action", { type_name: object.type, value: object.value, scope: type.value, ...action });
  pending.then((result) => {
    if (revision !== version) return;
    if (mode === "count") field.value = result.index;
    else editor.load(result.truename);
    refresh();
  }).catch(report);
});
new ResizeObserver(fitValueText).observe(display.container);
const runner = new CountRunner(playCurrent, () => {
  if (mode !== "count") return;
  field.value = String(BigInt(field.value) + BigInt(increment.value));
  refresh();
}, report);
player?.setVolume(0, 0);

function report(error) { message.textContent = error.message; console.error(error); }
function clearPlayback() { playingName.textContent = ""; score.replaceChildren(); }
function renderName() { typed.textContent = editor?.text || ""; guessed.textContent = editor?.guessed || ""; }
function fitValueText() {
  const text = display.container.querySelector(".value-text");
  if (!text) return;
  let low = 8;
  let high = Math.floor(Math.min(display.container.clientWidth, display.container.clientHeight, parseFloat(getComputedStyle(heading).fontSize) * 0.8));
  const height = display.container.clientHeight;
  const width = display.container.clientWidth;
  while (low < high) {
    const size = Math.ceil((low + high) / 2);
    text.style.fontSize = `${size}px`;
    if (text.scrollHeight > height || text.scrollWidth > width) high = size - 1;
    else low = size;
  }
  text.style.fontSize = `${low}px`;
}
function settings() {
  return { ...presentation, time_signature: { top: scoreTop.value || "4", bottom: Number(scoreBottom.value) } };
}
function writeURL(push = false) {
  const url = new URL(window.location.href);
  url.search = new URLSearchParams({ mode, type: type.value, index: field.value || "0", inc: increment.value || "1" });
  if (mode === "name") {
    url.searchParams.set("value", editor?.text || "");
  }
  window.history[push ? "pushState" : "replaceState"](null, "", url);
}
function refresh(push = false, reading = null) {
  const revision = ++version;
  current = null;
  writeURL(push);
  if (!ready) return;
  let payload;
  let action;
  if (mode === "name") {
    renderName();
    payload = { mode: "truename", value: editor.accepted, type_name: type.value };
    if (!payload.value) { display.clear(); sourceName.textContent = ""; message.textContent = ""; loading = Promise.resolve(null); return; }
    action = "recognize";
  } else {
    if (!/^[0-9]+$/.test(field.value)) { display.clear(); sourceName.textContent = ""; message.textContent = ""; loading = Promise.resolve(null); return; }
    payload = { value: field.value, type_name: type.value, ...settings() };
    if (mode === "clock") {
      reading ||= clockReading(new Date(), Number(interval.value), timeOnly.checked, displayUTC.checked);
      payload.source_type = reading.type;
      payload.source_value = reading.value;
    }
    action = "count";
  }
  loading = request(action, payload).then((result) => {
    if (revision !== version) return null;
    const name = result.full_truename || result.truename;
    if (!name) { message.textContent = result.message || result.browse_error || ""; return null; }
    current = { ...result, truename: name };
    sourceName.textContent = name;
    if (mode === "clock") {
      field.value = result.index;
      clockCount.textContent = result.index;
      clockDate.textContent = reading.displayDate;
      clockHours.textContent = reading.displayTime;
      time.dateTime = reading.value;
    }
    display.show(result.display);
    fitValueText();
    if (mode === "clock") {
      for (const button of display.container.querySelectorAll("button")) button.disabled = true;
      writeURL();
    }
    if (mode === "name") playCurrent().catch(report);
    message.textContent = result.browse_error || "";
    return current;
  }).catch((error) => { if (revision === version) report(error); return null; });
}
function playCurrent() {
  const revision = version;
  if (!player) return Promise.reject(new Error("Audio is unavailable."));
  const unlocked = muted ? Promise.resolve() : player.unlock();
  if (playback) return playback.then(() => revision === version ? playCurrent() : undefined);
  const value = loading;
  const render = settings();
  // Own both preparation and audio completion so concurrent requests cannot overlap.
  playback = Promise.all([value, unlocked]).then(([item]) => {
    if (!item || revision !== version) return null;
    return request("preview_truename", { value: item.truename, absolute: !type.value, ...render })
      .then((music) => ({ item, music }));
  }).then((result) => {
    if (!result || revision !== version) return;
    const { item, music } = result;
    if (music.playback_error) throw new Error(music.playback_error);
    // TunePlayer.play stops its previous voices before starting the new tune.
    if (player.context.state === "running") player.play(music.playback);
    playingBpm = render.bpm;
    playingName.textContent = item.truename;
    score.replaceChildren();
    if (music.score) drawScore(score, music.score);
    else score.textContent = music.score_error || "";
    // Browsers suspend audio before the first gesture; muted Count still advances.
    if (player.context.state !== "running") {
      const duration = Math.max(0, ...music.playback.map((i) => i.onset + i.duration));
      return new Promise((resolve) => setTimeout(() => {
        if (!retain.checked) clearPlayback();
        resolve();
      }, (duration + 0.05) * 1000));
    }
    if (!player.playing) { if (!retain.checked) clearPlayback(); return; }
    return new Promise((resolve) => { ended = resolve; });
  }).finally(() => { playback = null; });
  return playback;
}
function activate(push = false) {
  runner.stop();
  workspace.dataset.mode = mode;
  heading.textContent = mode[0].toUpperCase() + mode.slice(1);
  for (const radio of modes) radio.checked = radio.value === mode;
  nameField.hidden = mode !== "name";
  field.hidden = mode !== "count";
  clockReadingButton.hidden = mode !== "clock";
  sourceName.hidden = mode === "name";
  refresh(push);
  if (mode === "count" && ready && increment.value && increment.validity.valid) runner.start();
  if (mode === "clock" && ready) playCurrent().catch(report);
}
function readURL() {
  const query = new URL(window.location.href).searchParams;
  mode = ["name", "count", "clock"].includes(query.get("mode")) ? query.get("mode") : "name";
  type.value = query.get("type") || "";
  const index = query.get("index") || "0";
  field.value = /^[0-9]+$/.test(index) ? index : "0";
  const inc = query.get("inc") || "1";
  increment.value = /^[0-9]+$/.test(inc) && BigInt(inc) > 0n ? inc : "1";
  increment.setCustomValidity("");
  editor?.load(query.get("value") || "");
  activate();
}
for (const radio of modes) radio.addEventListener("change", () => {
  mode = radio.value;
  if (mode === "clock") type.value = "";
  activate(true);
});
clockReadingButton.addEventListener("click", () => {
  time.hidden = !time.hidden;
  clockCount.hidden = !time.hidden;
  clockReadingButton.setAttribute("aria-label", time.hidden ? "Show date and time" : "Show count");
});
type.addEventListener("change", () => {
  if (mode === "name") {
    if (current) editor.load(current.truename);
    editor.prefix = type.value ? type.value.split(":").at(-1) + ": " : "";
  }
  activate(true);
});
sound.addEventListener("click", () => {
  muted = !muted;
  sound.setAttribute("aria-pressed", String(muted));
  player.setVolume(muted ? 0 : 1, 0.02);
  if (!muted) player.unlock().catch(report);
});
retain.addEventListener("change", () => { if (!retain.checked && !player?.playing) clearPlayback(); });
color.addEventListener("input", () => score.style.setProperty("--playing-note-color", color.value));
for (const input of [field, increment]) {
  let accepted = input.value;
  input.addEventListener("beforeinput", (event) => { accepted = input.value; if (event.data && /[^0-9]/.test(event.data)) event.preventDefault(); });
  input.addEventListener("input", () => {
    if (/[^0-9]/.test(input.value)) input.value = accepted;
    accepted = input.value;
    increment.setCustomValidity(!increment.value || BigInt(increment.value) === 0n ? "Increment must be positive." : "");
    if (mode === "count") runner.stop();
    refresh();
    if (mode === "count" && increment.value && increment.validity.valid && /^[0-9]+$/.test(field.value)) runner.start();
  });
}
function nameKey(key) {
  if (!editor) return;
  const changed = key === "ArrowRight" ? editor.right()
    : ["ArrowLeft", "Backspace"].includes(key) ? editor.left()
    : ["ArrowUp", "ArrowDown"].includes(key) ? editor.cycle(key === "ArrowUp" ? -1 : 1)
    : editor.type(key);
  if (changed) refresh();
  else renderName();
}
nameField.addEventListener("keydown", (event) => {
  if (event.key === "Tab" || event.metaKey || event.ctrlKey) return;
  event.preventDefault();
  if (event.key === "Enter") playCurrent().catch(report);
  else nameKey(event.key);
});
nameField.addEventListener("beforeinput", (event) => { event.preventDefault(); nameKey(event.inputType === "deleteContentBackward" ? "Backspace" : event.data || ""); });
nameField.addEventListener("paste", (event) => {
  event.preventDefault();
  if (editor?.load(event.clipboardData.getData("text/plain"))) refresh();
});
for (const input of [scoreTop, scoreBottom, timeOnly, displayUTC, interval]) input.addEventListener("change", () => {
  if (scoreTop.validity.valid) refresh();
});
for (const input of [document.querySelector("#tune-root"), document.querySelector("#tune-position")]) input.addEventListener("change", () => refresh());
window.addEventListener("popstate", readURL);
function tick() {
  if (mode === "clock" && ready) {
    const reading = clockReading(new Date(), Number(interval.value), timeOnly.checked, displayUTC.checked);
    refresh(false, reading);
    if (reading.due && !playback) playCurrent().catch(report);
  }
  setTimeout(tick, 1000 - Date.now() % 1000);
}
configured.then((info) => {
  for (const [path, detail] of Object.entries(info.types)) {
    const option = document.createElement("option");
    option.value = path;
    option.textContent = path.split(":").at(-1);
    option.title = detail;
    type.append(option);
  }
  editor = new TruenameEditor(info.words);
  ready = true;
  readURL();
  nameField.dataset.ready = "true";
  sound.disabled = !player;
}).catch(report);
tick();
