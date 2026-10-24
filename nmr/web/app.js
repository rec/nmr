import { Editor } from "./editor.mjs";
import { TunePlayer } from "./tune.js";

const field = document.querySelector("#value");
const nameButton = document.querySelector("#name");
const presentation = { root: 48, bpm: 180 };
const editor = new Editor();
const worker = new Worker("worker.js");
const pending = new Map();
let serial = 0;
let version = 0;
let playVersion = 0;
let timer;
let ready = false;
let composing = false;
let currentName = null;
let previewPending = false;
let player;
try {
  player = new TunePlayer(() => nameButton.setAttribute("aria-pressed", "false"));
} catch (error) {
  console.error("Audio is unavailable in this browser.", error);
}

function request(action, payload) {
  return new Promise((resolve, reject) => {
    const id = ++serial;
    pending.set(id, { resolve, reject });
    worker.postMessage({ id, action, payload });
  });
}
worker.onmessage = ({ data }) => {
  const task = pending.get(data.id);
  if (!task) return;
  pending.delete(data.id);
  if (data.error) task.reject(new Error(data.error));
  else task.resolve(data.result);
};
worker.onerror = () => {
  ready = false;
  const error = new Error("Could not start the local naming engine. Reload to try again.");
  console.error(error);
  for (const task of pending.values()) task.reject(error);
  pending.clear();
};

function render() {
  field.value = editor.text;
  field.setSelectionRange(Math.min(editor.anchor, editor.cursor), Math.max(editor.anchor, editor.cursor),
    editor.cursor < editor.anchor ? "backward" : "forward");
}
function focus() {
  field.focus({ preventScroll: true });
  render();
}
function unlock() {
  player?.unlock().catch(() => {
    console.error("Sound needs permission from your browser.");
  });
}
function changed() {
  version++;
  playVersion++;
  previewPending = false;
  player?.stop();
  currentName = null;
  nameButton.hidden = true;
  render();
  clearTimeout(timer);
  if (ready) timer = setTimeout(recognize, 120);
}
async function recognize() {
  const revision = version;
  try {
    const result = await request("recognize", { value: editor.text, name_mode: editor.nameMode });
    if (revision !== version) return;
    if (result.name_mode) editor.nameMode = true;
    editor.normalize();
    render();
    currentName = result.name;
    nameButton.textContent = (result.name || "").replace(":", ": ");
    nameButton.hidden = !result.name;
  } catch (error) {
    if (revision === version) console.error(error);
  }
}
async function playName() {
  if (!player || !currentName) return;
  if (previewPending || player.playing) {
    playVersion++;
    previewPending = false;
    player.stop();
    return;
  }
  const name = currentName;
  const revision = ++playVersion;
  previewPending = true;
  unlock();
  try {
    const music = await request("preview_name", { value: name, ...presentation });
    if (revision !== playVersion || currentName !== name) return;
    if (music.playback_error) throw new Error(music.playback_error);
    previewPending = false;
    player.play(music.playback);
    nameButton.setAttribute("aria-pressed", "true");
  } catch (error) {
    if (revision === playVersion) {
      previewPending = false;
      console.error(error);
    }
  }
}

function insert(text) {
  if (editor.replace(text)) changed();
  else { player?.tick(); render(); }
}

// Mouse placement never changes the selection owned by the editor.
field.addEventListener("pointerdown", (event) => {
  event.preventDefault();
  focus();
});
field.addEventListener("click", (event) => { event.preventDefault(); render(); });
field.addEventListener("focus", render);
document.addEventListener("selectionchange", () => {
  if (document.activeElement === field && !composing &&
      (field.selectionStart !== Math.min(editor.anchor, editor.cursor) ||
       field.selectionEnd !== Math.max(editor.anchor, editor.cursor))) render();
});
document.addEventListener("pointerdown", unlock, true);
nameButton.addEventListener("click", playName);
document.addEventListener("keydown", (event) => {
  unlock();
  if (event.isComposing || event.key === "Tab") return;
  const command = event.ctrlKey || event.metaKey;
  if (command && event.key.toLowerCase() === "a") {
    event.preventDefault(); focus(); editor.selectAll(); render(); return;
  }
  if (command && ["c", "x", "v"].includes(event.key.toLowerCase())) { focus(); return; }
  if (event.key === "Enter") { event.preventDefault(); playName(); return; }
  if (event.key === "Escape") { event.preventDefault(); editor.clear(); changed(); focus(); return; }
  if (event.key === " " && document.activeElement === nameButton) return;
  if (["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
    event.preventDefault(); focus();
    const left = event.key === "ArrowLeft";
    let position;
    if (event.key === "Home" || event.key === "End" || event.metaKey) {
      position = event.key === "Home" || left ? 0 : editor.text.length;
    } else if (editor.anchor !== editor.cursor && !event.shiftKey) {
      position = left ? Math.min(editor.anchor, editor.cursor) : Math.max(editor.anchor, editor.cursor);
    } else position = editor.boundary(left ? -1 : 1, event.ctrlKey || event.altKey);
    editor.move(position, event.shiftKey); render(); return;
  }
  if (event.key === "Backspace" || event.key === "Delete") {
    event.preventDefault(); focus();
    editor.erase(event.key === "Backspace" ? -1 : 1, command || event.altKey);
    changed(); return;
  }
  if (!command && !event.altKey && [...event.key].length === 1) {
    event.preventDefault(); focus(); insert(event.key);
  }
}, true);
document.addEventListener("paste", (event) => {
  event.preventDefault(); focus();
  insert(event.clipboardData.getData("text/plain"));
});
for (const action of ["copy", "cut"]) document.addEventListener(action, (event) => {
  event.preventDefault();
  event.clipboardData.setData("text/plain", editor.selection());
  if (action === "cut") { editor.replace(""); changed(); }
});
field.addEventListener("compositionstart", () => { composing = true; });
field.addEventListener("compositionend", (event) => {
  composing = false; insert(event.data);
});
field.addEventListener("beforeinput", (event) => {
  if (composing || event.inputType === "insertCompositionText") return;
  event.preventDefault();
  if (event.inputType === "insertText" || event.inputType === "insertReplacementText") {
    insert(event.data || "");
  } else if (event.inputType === "deleteContentBackward" || event.inputType === "deleteContentForward") {
    editor.erase(event.inputType === "deleteContentBackward" ? -1 : 1); changed();
  }
});
field.addEventListener("input", () => { if (!composing) render(); });

async function start() {
  try {
    const info = await request("configure", {});
    editor.setWords(info.words);
    ready = true;
    field.dataset.ready = "true";
    render();
    await recognize();
    // tune:the is the one-beat zeroth tune, independently of its root routing.
    const intro = await request("preview", { value: "@1", ...presentation });
    player?.setIntro(intro.playback);
  } catch (error) {
    console.error(error);
  }
}
focus();
start();
