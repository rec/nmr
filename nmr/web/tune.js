/* Python supplies normalized notes, centered pitches and playback times. */
let audio;
let voices = [];
let previewGeneration = 0;

function stopTune() {
  for (const voice of voices) voice.stop();
  voices = [];
}
function updateTuneVisibility() {
  ++previewGeneration;
  const editing = mode === "encode" && $("type").value === "play:music:tune";
  const decoded = mode !== "encode" && !$("result").hidden &&
    $("result-type").textContent === "play:music:tune";
  $("tune-panel").hidden = !(editing || decoded);
  $("tune-editor").hidden = !editing;
  stopTune();
}
function tuneSource() {
  return mode === "encode" ? $("value").value : $("result-value").value;
}
function noteRow(note, index) {
  const row = document.createElement("div");
  row.className = "tune-note";
  for (const [key, title] of [["step", "Step"], ["duration", "Beats"], ["gap", "Rest before"]]) {
    const label = document.createElement("label");
    label.textContent = `${index + 1}. ${title}`;
    const input = document.createElement("input");
    input.dataset.field = key;
    input.value = key === "gap" && note[key] === "0" ? "" : note[key];
    input.setAttribute("aria-label", `Note ${index + 1} ${title}`);
    if (key !== "step") input.setAttribute("list", "tune-rhythms");
    if (index === 0 && key !== "duration") input.disabled = true;
    label.append(input);
    row.append(label);
  }
  if (index) {
    const tie = document.createElement("button");
    tie.type = "button";
    tie.textContent = "Tie";
    tie.addEventListener("click", () => showTune(editorText(), index).catch(tuneError));
    row.append(tie);
  }
  return row;
}
function editorText() {
  return [...$("tune-notes").children].map((row, index) => {
    const field = (key) => row.querySelector(`[data-field="${key}"]`).value.trim();
    const gap = field("gap");
    const rest = index && gap && gap !== "0" ? `r@${gap} ` : "";
    return `${rest}${index ? field("step") : ""}@${field("duration")}`;
  }).join(" ");
}
function tuneError(error) {
  $("tune-status").textContent = error.message;
}
async function showTune(value, tie = null) {
  const generation = ++previewGeneration;
  stopTune();
  const result = await request("preview", {
    value, tie,
    root: Number($("tune-root").value),
    bpm: Number($("tune-bpm").value),
  });
  if (generation !== previewGeneration) return null;
  updateTuneVisibility();
  $("tune-phrase").textContent = result.value;
  $("tune-pitches").textContent = "Centered MIDI pitches: " + result.events.map((event) => event.pitch).join(", ");
  $("tune-notes").replaceChildren(...result.notes.map(noteRow));
  if (mode === "encode") $("value").value = result.value;
  $("tune-status").textContent = result.playback_error ||
    "Ready to play. Center and tempo change the sound, not the name.";
  return result;
}
$("tune-preview").addEventListener("click", () => showTune(tuneSource()).catch(tuneError));
$("tune-use").addEventListener("click", () => showTune(editorText()).catch(tuneError));
$("tune-stop").addEventListener("click", () => {
  ++previewGeneration;
  stopTune();
  $("tune-status").textContent = "Stopped.";
});
$("tune-add").addEventListener("click", () => {
  const index = $("tune-notes").children.length;
  if (index >= 256) return tuneError(new Error("Editor limit: 256 notes"));
  $("tune-notes").append(noteRow({ step: 0, duration: "1/2", gap: "0" }, index));
});
$("tune-remove").addEventListener("click", () => {
  if ($("tune-notes").children.length > 1) $("tune-notes").lastElementChild.remove();
});
$("tune-example").addEventListener("click", () =>
  showTune("@1 2@1/2 2@1/2 r@1/3 -1@2/3 @1").catch(tuneError));
for (const id of ["tune-root", "tune-bpm", "value", "tune-notes"]) {
  $(id).addEventListener("input", () => { ++previewGeneration; stopTune(); });
}
$("tune-play").addEventListener("click", async () => {
  try {
    // Resume from the user gesture, before waiting for the worker.
    audio ||= new AudioContext();
    await audio.resume();
    const result = await showTune(tuneSource());
    if (!result || result.playback_error) return;
    const start = audio.currentTime + 0.05;
    for (const event of result.playback) {
      const voice = audio.createOscillator();
      const gain = audio.createGain();
      const onset = start + event.onset;
      const end = onset + event.duration;
      voice.type = "triangle";
      voice.frequency.value = 440 * 2 ** ((event.pitch - 69) / 12);
      gain.gain.setValueAtTime(0, onset);
      gain.gain.linearRampToValueAtTime(0.15, onset + Math.min(0.005, event.duration / 4));
      gain.gain.setValueAtTime(0.15, end - Math.min(0.005, event.duration / 4));
      gain.gain.linearRampToValueAtTime(0, end);
      voice.connect(gain).connect(audio.destination);
      voice.onended = () => {
        voice.disconnect(); gain.disconnect();
        const active = voices.includes(voice);
        voices = voices.filter((item) => item !== voice);
        if (active && !voices.length) $("tune-status").textContent = "Playback finished.";
      };
      voice.start(onset);
      voice.stop(end);
      voices.push(voice);
    }
    $("tune-status").textContent = "Playing…";
  } catch (error) { tuneError(error); }
});
