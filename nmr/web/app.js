import { Editor } from "./editor.mjs";
import { TunePlayer } from "./tune.js";

const field = document.querySelector("#value");
const truenameButton = document.querySelector("#truename");
const fullTruenameButton = document.querySelector("#full-truename");
const presentation = { root: 53, bpm: 180 };
const editor = new Editor();
const worker = new Worker("worker.js");
const pending = new Map();
let serial = 0;
let version = 0;
let playVersion = 0;
let timer;
let ready = false;
let composing = false;
let currentTruename = null;
let previewPending = false;
let playingButton = null;
let player;
try {
  player = new TunePlayer(() => {
    truenameButton.setAttribute("aria-pressed", "false");
    fullTruenameButton.setAttribute("aria-pressed", "false");
    playingButton = null;
  });
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
  const error = new Error("Could not start the local truename engine. Reload to try again.");
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
  readSelection();
  field.focus({ preventScroll: true });
  render();
}
function readSelection() {
  if (composing || field.value !== editor.text) return;
  const backward = field.selectionDirection === "backward";
  editor.anchor = backward ? field.selectionEnd : field.selectionStart;
  editor.cursor = backward ? field.selectionStart : field.selectionEnd;
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
  currentTruename = null;
  truenameButton.hidden = true;
  fullTruenameButton.hidden = true;
  render();
  clearTimeout(timer);
  if (ready) timer = setTimeout(recognize, 120);
}
async function recognize() {
  const revision = version;
  try {
    const result = await request("recognize", { value: editor.text });
    if (revision !== version) return;
    currentTruename = result.truename;
    truenameButton.textContent = (result.truename || "").replace(":", ": ");
    truenameButton.hidden = !result.truename;
    fullTruenameButton.textContent = (result.full_truename || "").replace(":", ": ");
    fullTruenameButton.hidden = !result.full_truename;
  } catch (error) {
    if (revision === version) console.error(error);
  }
}
async function playTruename(absolute = false) {
  const button = absolute ? fullTruenameButton : truenameButton;
  if (!player || !currentTruename) return;
  if (playingButton === button && (previewPending || player.playing)) {
    playVersion++;
    previewPending = false;
    player.stop();
    return;
  }
  player.stop();
  playingButton = button;
  const truename = currentTruename;
  const revision = ++playVersion;
  previewPending = true;
  unlock();
  try {
    const music = await request("preview_truename", { value: truename, absolute, ...presentation });
    if (revision !== playVersion || currentTruename !== truename) return;
    if (music.playback_error) throw new Error(music.playback_error);
    previewPending = false;
    player.play(music.playback);
    playingButton = button;
    button.setAttribute("aria-pressed", "true");
  } catch (error) {
    if (revision === playVersion) {
      previewPending = false;
      playingButton = null;
      console.error(error);
    }
  }
}

function insert(text) {
  if (editor.replace(text)) changed();
  else { player?.tick(); render(); }
}

field.addEventListener("select", readSelection);
document.addEventListener("selectionchange", () => {
  if (document.activeElement === field) readSelection();
});
document.addEventListener("pointerdown", unlock, true);
truenameButton.addEventListener("click", () => playTruename());
fullTruenameButton.addEventListener("click", () => playTruename(true));
document.addEventListener("keydown", (event) => {
  unlock();
  if (event.isComposing || event.key === "Tab") return;
  const command = event.ctrlKey || event.metaKey;
  if (command && event.key.toLowerCase() === "a") {
    event.preventDefault(); focus(); editor.selectAll(); render(); return;
  }
  if (command && ["c", "x", "v"].includes(event.key.toLowerCase())) { focus(); return; }
  if (event.key === "Enter") { event.preventDefault(); playTruename(document.activeElement === fullTruenameButton); return; }
  if (event.key === "Escape") { event.preventDefault(); editor.clear(); changed(); focus(); return; }
  if (event.key === " " && [truenameButton, fullTruenameButton].includes(document.activeElement)) return;
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
  readSelection();
  event.preventDefault();
  event.clipboardData.setData("text/plain", editor.selection());
  if (action === "cut") { editor.replace(""); changed(); }
});
field.addEventListener("compositionstart", () => { readSelection(); composing = true; });
field.addEventListener("compositionend", (event) => {
  composing = false; insert(event.data);
});
field.addEventListener("beforeinput", (event) => {
  if (composing || event.inputType === "insertCompositionText") return;
  readSelection();
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
    await request("configure", {});
    ready = true;
    field.dataset.ready = "true";
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
