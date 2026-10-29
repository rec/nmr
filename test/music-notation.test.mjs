import assert from "node:assert/strict";
import test from "node:test";
import { createRequire } from "node:module";
import { drawScore } from "../nmr/web/music-notation.mjs";

const require = createRequire(import.meta.url);

// A minimal SVG document exercises the real engraving API without a browser.
class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.attributes = {}; this.style = {}; this.ownerDocument = document; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  setAttributeNS(ns, name, value) { this.setAttribute(name, value); }
  getAttribute(name) { return this.attributes[name] || null; }
  append(...children) { this.children.push(...children); }
  appendChild(child) { this.append(child); return child; }
  removeChild(child) { this.children.splice(this.children.indexOf(child), 1); }
  get firstElementChild() { return this.children[0]; }
  get lastChild() { return this.children.at(-1); }
  getContext() { return { measureText: (text) => ({ width: String(text).length * 8, actualBoundingBoxAscent: 10, actualBoundingBoxDescent: 3 }), save() {}, restore() {} }; }
}
const document = {
  createElement: (tag) => new Element(tag),
  createElementNS: (ns, tag) => new Element(tag),
  createTextNode: (text) => ({ textContent: text }),
  fonts: { ready: Promise.resolve() },
};

test("VexFlow engraves dotted durations, triplets, rests, accidentals and cross-bar ties", async () => {
  const oldDocument = globalThis.document;
  const oldFlow = globalThis.VexFlow;
  globalThis.document = document;
  globalThis.VexFlow = require("../nmr/web/vexflow.js");
  const symbol = (pitch, glyph, dots = 0, ratio = [1, 1], attack = 0, tie = false) => ({ pitch, glyph, dots, ratio, attack, tie });
  try {
    for (const bottom of [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64]) {
      const container = new Element("div");
      await drawScore(container, { top: "4", bottom, clef: "bass", measures: [
        [symbol(53, "4", 1), symbol(54, "8", 0, [3, 2], 1), symbol(null, "8", 0, [3, 2], null), symbol(53, "8", 0, [3, 2], 2)],
        [symbol(53, "2", 0, [1, 1], 2, true), symbol(53, "4", 2, [1, 1], 3)],
      ] });
      assert.equal(container.firstElementChild.firstElementChild.tag, "svg");
      assert.equal(container.firstElementChild.textContent, undefined, "An engraving failure must not be swallowed by this test");
    }
    const vf = globalThis.VexFlow;
    const dotted = new vf.StaveNote({ keys: ["f/3"], duration: "4d" });
    vf.Dot.buildAndAttach([dotted], { all: true });
    assert.equal(dotted.getTicks().value(), 6144);
    const triplet = new vf.StaveNote({ keys: ["f/3"], duration: "8" });
    new vf.Tuplet([triplet], { numNotes: 3, notesOccupied: 2 });
    assert.equal(triplet.getTicks().value(), 4096 / 3);
  } finally {
    globalThis.document = oldDocument;
    globalThis.VexFlow = oldFlow;
  }
});

test("a stale score waiting for fonts cannot overwrite another value", async () => {
  const oldDocument = globalThis.document;
  globalThis.document = document;
  try {
    const container = new Element("div");
    const pending = drawScore(container, { top: "4", bottom: 4 });
    container.children = [new Element("p")];
    await pending;
    assert.equal(container.firstElementChild.tag, "p");
  } finally { globalThis.document = oldDocument; }
});
