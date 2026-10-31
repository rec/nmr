import "./volume.js";
import "./help.js";
import { configured, request } from "./runtime.js";
import { describeObject } from "./description.mjs";
import { TruenameEditor } from "./truename-editor.mjs";
import { Editor } from "./editor.mjs";
import { TunePlayer } from "./tune.js";
import { presentation } from "./presentation.mjs";
import { CountRunner } from "./count-runner.mjs";
import { clockReading } from "./clock-time.mjs";
import { ValueDisplay } from "./value-display.mjs";
import { drawScore, highlightScore } from "./music-notation.mjs";

const workspace = document.querySelector("#workspace");
const modes = document.querySelectorAll('[name="mode"]');
const type = document.querySelector("#type");
const field = document.querySelector("#count-value");
const description = document.querySelector("#value");
const descriptionRegion = document.querySelector("#description-region");
const nameField = document.querySelector("#name-editor");
const typed = document.querySelector("#typed");
const guessed = document.querySelector("#guessed");
const time = document.querySelector("#clock-time");
const currentName = document.querySelector("#current-name");
const playButton = document.querySelector("#play");
const automatic = document.querySelector("#automatic");
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
const copy = document.querySelector("#copy-link");
const enabled = { count: false, clock: false };
let mode = "name";
let direction = "description";
let editor;
let version = 0;
let current = null;
let loading = Promise.resolve(null);
let playback = null;
let ended = null;
let playingBpm = presentation.bpm;
let ready = false;
let timer;
let player;
const descriptionEditor = new Editor();
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
    else {
      direction = "description";
      description.value = type.value ? result.value : describeObject(result);
    }
    refresh();
  }).catch(report);
});
const runner = new CountRunner(playCurrent, () => {
  if (mode !== "count" || !enabled.count) return;
  field.value = String(BigInt(field.value) + BigInt(increment.value));
  refresh();
}, (error) => { enabled.count = false; automatic.checked = false; report(error); });

function report(error) { message.textContent = error.message; console.error(error); }
function clearPlayback() { playingName.textContent = ""; score.replaceChildren(); }
function renderName() { typed.textContent = editor?.text || ""; guessed.textContent = editor?.guessed || ""; }
function settings() {
  return { ...presentation, time_signature: { top: scoreTop.value || "4", bottom: Number(scoreBottom.value) } };
}
function writeURL(push = false) {
  const url = new URL(window.location.href);
  url.search = new URLSearchParams({ mode, type: type.value, index: field.value || "0", inc: increment.value || "1" });
  if (mode === "name") {
    url.searchParams.set("edit", direction);
    url.searchParams.set("value", direction === "description" ? description.value : editor?.text || "");
  }
  window.history[push ? "pushState" : "replaceState"](null, "", url);
  copy.textContent = "Copy link";
}
function clockSource() {
  const reading = clockReading(new Date(), Number(interval.value), timeOnly.checked, displayUTC.checked);
  time.textContent = `${reading.displayDate} ${reading.displayTime}`;
  time.dateTime = reading.value;
  return reading;
}
function refresh(push = false) {
  const revision = ++version;
  current = null;
  playButton.disabled = true;
  automatic.disabled = !player || mode === "name" ||
    (mode === "count" && (!/^[0-9]+$/.test(field.value) || !increment.value || !increment.validity.valid));
  message.textContent = "";
  currentName.textContent = "";
  display.clear(true);
  writeURL(push);
  if (!ready) return;
  let payload;
  let action;
  if (mode === "name") {
    renderName();
    payload = { mode: direction, value: direction === "description" ? description.value : editor.accepted, type_name: type.value };
    if (!payload.value) { loading = Promise.resolve(null); return; }
    action = "recognize";
  } else {
    if (!/^[0-9]+$/.test(field.value)) { loading = Promise.resolve(null); return; }
    payload = { value: field.value, type_name: type.value, ...settings() };
    if (mode === "clock") {
      const reading = clockSource();
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
    currentName.textContent = name;
    if (mode === "name") {
      if (direction === "description") { editor.load(name); renderName(); }
      else description.value = result.browsed ? (type.value ? result.browsed.value : describeObject(result.browsed)) : "";
    } else if (mode === "clock") field.value = result.index;
    display.show(result.display);
    if (mode === "clock") {
      for (const button of display.container.querySelectorAll("button")) button.disabled = true;
      writeURL();
    }
    playButton.disabled = !player;
    message.textContent = result.browse_error || "";
    return current;
  }).catch((error) => { if (revision === version) report(error); return null; });
}
function playCurrent() {
  const revision = version;
  if (!player) return Promise.reject(new Error("Audio is unavailable."));
  const unlocked = player.unlock();
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
    player.play(music.playback);
    playingBpm = render.bpm;
    playingName.textContent = item.truename;
    score.replaceChildren();
    if (music.score) drawScore(score, music.score);
    else score.textContent = music.score_error || "";
    if (!player.playing) { if (!retain.checked) clearPlayback(); return; }
    return new Promise((resolve) => { ended = resolve; });
  }).finally(() => { playback = null; });
  return playback;
}
function activate(push = false) {
  runner.stop();
  workspace.dataset.mode = mode;
  for (const radio of modes) radio.checked = radio.value === mode;
  nameField.hidden = mode !== "name";
  field.hidden = mode !== "count";
  time.hidden = mode !== "clock";
  descriptionRegion.inert = mode !== "name";
  descriptionRegion.setAttribute("aria-hidden", String(mode !== "name"));
  automatic.disabled = mode === "name" || !player || !ready;
  automatic.checked = enabled[mode] || false;
  refresh(push);
  if (enabled.count && mode === "count" && ready && !automatic.disabled) runner.start();
  if (enabled.clock && mode === "clock" && ready) playCurrent().catch(report);
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
  direction = query.get("edit") === "truename" ? "truename" : "description";
  if (direction === "truename") editor?.load(query.get("value") || "");
  else description.value = query.get("value") || "";
  activate();
}
for (const radio of modes) radio.addEventListener("change", () => { mode = radio.value; activate(true); });
type.addEventListener("change", () => {
  if (mode === "name") {
    if (current) editor.load(current.truename);
    editor.prefix = type.value ? type.value + ": " : "";
    direction = "truename";
  }
  activate(true);
});
automatic.addEventListener("change", () => {
  enabled[mode] = automatic.checked;
  if (mode === "count") {
    if (automatic.checked && increment.validity.valid) runner.start();
    else runner.stop();
  } else if (mode === "clock" && automatic.checked) playCurrent().catch(report);
});
playButton.addEventListener("click", () => playCurrent().catch(report));
retain.addEventListener("change", () => { if (!retain.checked && !player?.playing) clearPlayback(); });
color.addEventListener("input", () => score.style.setProperty("--playing-note-color", color.value));
for (const input of [field, increment]) {
  let accepted = input.value;
  input.addEventListener("beforeinput", (event) => { accepted = input.value; if (event.data && /[^0-9]/.test(event.data)) event.preventDefault(); });
  input.addEventListener("input", () => {
    if (/[^0-9]/.test(input.value)) input.value = accepted;
    accepted = input.value;
    increment.setCustomValidity(!increment.value || BigInt(increment.value) === 0n ? "Increment must be positive." : "");
    if (mode === "count") { runner.stop(); enabled.count = false; automatic.checked = false; }
    refresh();
  });
}
description.addEventListener("beforeinput", (event) => {
  if (!event.data) return;
  descriptionEditor.text = description.value;
  descriptionEditor.anchor = description.selectionStart;
  descriptionEditor.cursor = description.selectionEnd;
  if (!descriptionEditor.replace(event.data)) event.preventDefault();
});
description.addEventListener("input", () => { direction = "description"; clearTimeout(timer); version++; timer = setTimeout(refresh, 120); });
function nameKey(key) {
  if (!editor) return;
  const changed = key === "ArrowRight" ? editor.right()
    : ["ArrowLeft", "Backspace"].includes(key) ? editor.left()
    : ["ArrowUp", "ArrowDown"].includes(key) ? editor.cycle(key === "ArrowUp" ? -1 : 1)
    : editor.type(key);
  if (changed) { direction = "truename"; refresh(); }
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
  if (editor?.load(event.clipboardData.getData("text/plain"))) { direction = "truename"; refresh(); }
});
for (const input of [scoreTop, scoreBottom, timeOnly, displayUTC, interval]) input.addEventListener("change", () => {
  if (scoreTop.validity.valid) refresh();
});
for (const input of [document.querySelector("#tune-root"), document.querySelector("#tune-position")]) input.addEventListener("change", () => refresh());
copy.addEventListener("click", () => navigator.clipboard.writeText(window.location.href).then(() => { copy.textContent = "Copied"; }).catch(report));
window.addEventListener("popstate", readURL);
function tick() {
  if (mode === "clock" && ready) {
    const reading = clockSource();
    refresh();
    if (reading.due && enabled.clock && !playback) playCurrent().catch(report);
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
  description.dataset.ready = nameField.dataset.ready = "true";
}).catch(report);
tick();
