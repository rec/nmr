import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import vm from "node:vm";

test("all views share F3 and middle defaults and can select each note and position", () => {
  const source = fs.readFileSync(new URL("../nmr/web/presentation.mjs", import.meta.url), "utf8").replace("export const", "const");
  const elements = Object.fromEntries(["#tune-root", "#tune-position"].map((i) => [i, {
    addEventListener(event, callback) { this[event] = callback; },
  }]));
  const context = { document: { querySelector: (i) => elements[i] } };
  vm.runInNewContext(source + "\nglobalThis.settings = presentation;", context);
  assert.equal(context.settings.root, 53);
  assert.equal(context.settings.position, "middle");
  for (let note = 48; note < 60; note++) {
    elements["#tune-root"].value = String(note);
    elements["#tune-root"].change();
    assert.equal(context.settings.root, note);
  }
  for (const position of ["start", "middle", "end"]) {
    elements["#tune-position"].value = position;
    elements["#tune-position"].change();
    assert.equal(context.settings.position, position);
  }
  assert.equal(context.settings.bpm, 180);
});
