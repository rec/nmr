/* Rendering controls are shared by all views and do not change truenames. */
export const presentation = { root: 53, bpm: 180, position: "middle" };

const root = document.querySelector("#tune-root");
const position = document.querySelector("#tune-position");

root.addEventListener("change", () => { presentation.root = Number(root.value); });
position.addEventListener("change", () => { presentation.position = position.value; });
