import { configured, request } from "./runtime.js";
import { clockReading } from "./clock-time.mjs";
import { TunePlayer } from "./tune.js";

const time = document.querySelector("#clock-time");
const dateDisplay = document.querySelector("#clock-date");
const hoursDisplay = document.querySelector("#clock-hours");
const truename = document.querySelector("#clock-truename");
const on = document.querySelector("#clock-on");
const interval = document.querySelector("#clock-interval");
const timeOnly = document.querySelector("#clock-time-only");
const displayUTC = document.querySelector("#clock-display-utc");
let revision = 0;
let ready = false;
let player;
try {
  player = new TunePlayer();
  player.setVolume(0, 0);
} catch (error) {
  on.disabled = true;
  console.error("Audio is unavailable in this browser.", error);
}

function showTruename(reading) {
  const currentRevision = revision;
  request("convert", { operation: "encode", type_name: reading.type, value: reading.value, scope: "" }).then((result) => {
    if (revision === currentRevision && Math.floor(Date.now() / 1000) === reading.second) {
      truename.textContent = result.truename;
    }
  }, (error) => {
    console.error("Could not name the current time.", error);
  });
}
function play(reading) {
  const currentRevision = revision;
  request("preview_item", {
    operation: "encode", type_name: reading.type, value: reading.value, scope: "", root: 53, bpm: 180,
  }).then((music) => {
    if (revision !== currentRevision || Math.floor(Date.now() / 1000) !== reading.second) return;
    if (music.playback_error) throw new Error(music.playback_error);
    player.play(music.playback);
  }).catch((error) => {
    console.error("Could not play the current time.", error);
  });
}
function update() {
  const reading = clockReading(new Date(), Number(interval.value), timeOnly.checked, displayUTC.checked);
  dateDisplay.textContent = reading.displayDate;
  dateDisplay.hidden = !reading.displayDate;
  hoursDisplay.textContent = reading.displayTime;
  time.dateTime = reading.displayDate ? `${reading.displayDate}T${reading.displayTime}` : reading.displayTime;
  time.setAttribute("aria-label", timeOnly.checked ? "Time" : "Date and time");
  if (ready) showTruename(reading);
  return reading;
}
function tick() {
  const reading = update();
  if (ready && player && reading.due) play(reading);
  setTimeout(tick, 1000 - Date.now() % 1000);
}
on.addEventListener("change", () => {
  player.setVolume(on.checked ? 1 : 0, 0.1);
  if (on.checked) {
    player.unlock().catch((error) => {
      on.checked = false;
      player.setVolume(0, 0.1);
      console.error("Could not enable clock audio.", error);
    });
  }
});
interval.addEventListener("change", () => {
  revision++;
  player?.stop();
  update();
});
timeOnly.addEventListener("change", () => {
  revision++;
  player?.stop();
  update();
});
displayUTC.addEventListener("change", update);
configured.then(() => {
  ready = true;
  update();
}, (error) => {
  on.checked = false;
  on.disabled = true;
  truename.textContent = "Could not load the time engine. Reload to try again.";
  console.error(error);
});
tick();
