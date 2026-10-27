import { TruenameEditor } from "./truename-editor.mjs";
import { Editor } from "./editor.mjs";
import { TunePlayer } from "./tune.js";

const field = document.querySelector("#value");
const nameField = document.querySelector("#name-editor");
const typed = document.querySelector("#typed");
const guessed = document.querySelector("#guessed");
let nameEditor;
const truenameButton = document.querySelector("#truename");
const fullTruenameButton = document.querySelector("#full-truename");
const swapButton = document.querySelector("#swap");
const sourceHeading = document.querySelector("#source-heading");
const targetHeading = document.querySelector("#target-heading");
const resultPane = document.querySelector("#result-pane");
const parameters = new URL(window.location.href).searchParams;
let mode = parameters.has("name") ? "truename" : "description";
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
let currentObject = null;
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

function inputText() {
  return mode === "truename" && nameEditor ? nameEditor.text : editor.text;
}
function render() {
  field.hidden = mode === "truename";
  nameField.hidden = mode !== "truename";
  if (mode === "truename") {
    typed.textContent = nameEditor?.text || "";
    guessed.textContent = nameEditor?.guessed || "";
    return;
  }
  field.value = editor.text;
  field.setSelectionRange(Math.min(editor.anchor, editor.cursor), Math.max(editor.anchor, editor.cursor),
    editor.cursor < editor.anchor ? "backward" : "forward");
}
function focus() {
  readSelection();
  (mode === "truename" ? nameField : field).focus({ preventScroll: true });
  render();
}
function readSelection() {
  if (mode === "truename" || composing || field.value !== editor.text) return;
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
  const url = new URL(window.location.href);
  url.search = "";
  url.searchParams.set(mode === "truename" ? "name" : "desc", inputText());
  window.history.replaceState(window.history.state, "", url);
  version++;
  playVersion++;
  previewPending = false;
  player?.stop();
  currentTruename = null;
  currentObject = null;
  truenameButton.hidden = true;
  fullTruenameButton.hidden = true;
  render();
  clearTimeout(timer);
  if (ready) timer = setTimeout(recognize, 120);
}
function describeObject(object) {
  return `${object.type}: ${object.type === "string" ? JSON.stringify(object.value) : object.value}`;
}
function captions() {
  sourceHeading.textContent = mode === "description" ? "Description" : "True Name";
  targetHeading.textContent = mode === "description" ? "True Name" : "Description";
}
async function recognize() {
  const revision = version;
  try {
    const result = await request("recognize", { value: mode === "truename" ? nameEditor?.completion || "" : editor.text, mode });
    if (revision !== version) return;
    currentTruename = result.truename;
    currentObject = result.browsed || null;
    const browsing = mode === "truename";
    truenameButton.textContent = browsing
      ? (currentObject ? describeObject(currentObject) : result.browse_error || "")
      : (result.truename || result.message || "").replace(":", ": ");
    truenameButton.hidden = !truenameButton.textContent;
    truenameButton.disabled = browsing ? !currentObject : !result.truename;
    truenameButton.setAttribute("aria-label", browsing
      ? "Play or stop the described object's tune" : "Play or stop the prefix-relative tune");
    fullTruenameButton.textContent = (result.full_truename || "").replace(":", ": ");
    fullTruenameButton.hidden = browsing || !result.full_truename;
    fullTruenameButton.disabled = false;
  } catch (error) {
    if (revision === version) console.error(error);
  }
}
async function swap() {
  const revision = version;
  clearTimeout(timer);
  if (ready) await recognize();
  if (revision !== version) return;
  const value = mode === "description" ? currentTruename : currentObject && describeObject(currentObject);
  if (mode === "description") {
    if (!nameEditor) return;
    if (!nameEditor.load(value || "")) { player?.tick(presentation.root); return; }
    mode = "truename";
  } else {
    mode = "description";
    editor.selectAll();
    editor.replace(value || "");
  }
  captions();
  changed();
  focus();
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
  const object = mode === "truename" ? currentObject : null;
  const revision = ++playVersion;
  previewPending = true;
  unlock();
  try {
    const music = object
      ? await request("preview_item", { operation: "encode", type_name: object.type, value: object.value, ...presentation })
      : await request("preview_truename", { value: truename, absolute, ...presentation });
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

function nameKey(key) {
  if (!nameEditor) return;
  const accepted = key === "ArrowRight" ? nameEditor.right()
    : key === "ArrowLeft" || key === "Backspace" ? nameEditor.left()
    : key === "ArrowUp" || key === "ArrowDown" ? nameEditor.cycle(key === "ArrowUp" ? -1 : 1)
    : nameEditor.type(key);
  if (accepted) changed();
  else { player?.tick(presentation.root); render(); }
}
function insert(text) {
  if (mode === "truename") { player?.tick(presentation.root); return; }
  if (editor.replace(text)) changed();
  else { player?.tick(); render(); }
}
function resultSelected() {
  const selection = window.getSelection();
  return selection && !selection.isCollapsed && resultPane.contains(selection.anchorNode) && resultPane.contains(selection.focusNode);
}

nameField.addEventListener("pointerdown", (event) => { event.preventDefault(); focus(); });
nameField.addEventListener("selectstart", (event) => event.preventDefault());
nameField.addEventListener("beforeinput", (event) => {
  event.preventDefault();
  nameKey(event.inputType === "deleteContentBackward" ? "Backspace" : event.data || "");
});
field.addEventListener("select", readSelection);
document.addEventListener("selectionchange", () => {
  if (document.activeElement === field) readSelection();
});
document.addEventListener("pointerdown", unlock, true);
swapButton.addEventListener("click", swap);
truenameButton.addEventListener("click", () => { if (!resultSelected()) playTruename(); });
fullTruenameButton.addEventListener("click", () => { if (!resultSelected()) playTruename(true); });
document.addEventListener("keydown", (event) => {
  unlock();
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "c" && resultSelected()) return;
  if (mode === "truename") {
    if (event.key === "Tab" || ([swapButton, truenameButton, fullTruenameButton].includes(document.activeElement) && ["Enter", " "].includes(event.key))) return;
    event.preventDefault();
    focus();
    nameKey(event.isComposing || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey ? "" : event.key);
    return;
  }
  if (event.isComposing || event.key === "Tab") return;
  if (document.activeElement === swapButton && ["Enter", " "].includes(event.key)) return;
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
  if (action === "copy" && resultSelected()) return;
  if (mode === "truename") { event.preventDefault(); player?.tick(presentation.root); return; }
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
    const info = await request("configure", {});
    nameEditor = new TruenameEditor(info.words);
    if (mode === "truename" && !nameEditor.load(editor.text)) player?.tick(presentation.root);
    render();
    ready = true;
    field.dataset.ready = "true";
    nameField.dataset.ready = "true";
    changed();
    clearTimeout(timer);
    await recognize();
    // tune:the is the one-beat zeroth tune, independently of its root routing.
    const intro = await request("preview", { value: "@1", ...presentation });
    player?.setIntro(intro.playback);
  } catch (error) {
    console.error(error);
  }
}
const query = parameters.get(mode === "truename" ? "name" : "desc");
if (query !== null) editor.replace(query);
captions();
changed();
focus();
start();
