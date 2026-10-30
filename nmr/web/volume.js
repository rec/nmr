import { setMasterVolume } from "./tune.js";

const level = document.querySelector("#volume-level");
const value = document.querySelector("#volume-value");

function updateVolume() {
  const setting = Number(level.value);
  setMasterVolume(setting);
  value.textContent = setting === 0 ? "0 (muted)" : String(setting);
  level.setAttribute("aria-valuetext", value.textContent);
}
level.addEventListener("input", updateVolume);
updateVolume();
