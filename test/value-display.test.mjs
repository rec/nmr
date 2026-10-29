import assert from "node:assert/strict";
import test from "node:test";
import { ValueDisplay, mapSpec } from "../nmr/web/value-display.mjs";

class Element {
  constructor(tag, namespaceURI = null) {
    this.tag = tag;
    this.namespaceURI = namespaceURI;
    this.children = [];
    this.attributes = {};
    this.events = {};
    this.style = { setProperty() {} };
    this.className = "";
    this.classList = { toggle: (name, active) => {
      const values = new Set(this.className.split(" "));
      if (active) values.add(name); else values.delete(name);
      this.className = [...values].join(" ");
    } };
  }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  addEventListener(name, callback) { this.events[name] = callback; }
  all() { return [this, ...this.children.flatMap((i) => i.all())]; }
  click() { assert.ok(!this.disabled); this.events.click(); }
}

function display(check) {
  const previous = globalThis.document;
  globalThis.document = {
    createElement: (tag) => new Element(tag),
    createElementNS: (namespace, tag) => new Element(tag, namespace),
  };
  try {
    const root = new Element("section");
    const actions = [];
    check(new ValueDisplay(root, (i) => actions.push(i)), root, actions);
  } finally { globalThis.document = previous; }
}

test("chess clicks select a piece and a legal destination", () => display((view, root, actions) => {
  const board = Array(64).fill("");
  board[12] = "P";
  view.show({ kind: "chess", board, moves: ["e2e4", "e2e3"], turn: "White", undo: false });
  assert.equal(root.all().filter((i) => i.className.includes("chess-square")).length, 64);
  root.all().find((i) => i.title === "e2").click();
  root.all().find((i) => i.title === "e4").click();
  assert.deepEqual(actions, [{ action: "move", move: "e2e4" }]);
}));

test("chess promotions offer every legal piece instead of silently choosing", () => display((view, root, actions) => {
  const board = Array(64).fill("");
  board[49] = "P";
  view.show({ kind: "chess", board, moves: ["b7a8b", "b7a8n", "b7a8q", "b7a8r"], turn: "White", undo: true });
  root.all().find((i) => i.title === "b7").click();
  root.all().find((i) => i.title === "a8").click();
  assert.equal(actions.length, 0);
  for (const name of ["Bishop", "Knight", "Queen", "Rook"]) assert.ok(root.all().some((i) => i.textContent === name));
  root.all().find((i) => i.textContent === "Knight").click();
  assert.deepEqual(actions, [{ action: "move", move: "b7a8n" }]);
}));

test("Go renders all intersections, disables illegal moves, and supports Pass and Undo", () => display((view, root, actions) => {
  view.show({ kind: "go", size: 9, board: Array(81).fill(0), moves: ["D4", "pass"], turn: "Black", undo: true });
  assert.equal(root.all().filter((i) => i.className === "go-point").length, 81);
  assert.equal(root.all().find((i) => i.title === "A1").disabled, true);
  root.all().find((i) => i.title === "D4").click();
  root.all().find((i) => i.textContent === "Pass").click();
  root.all().find((i) => i.textContent === "Undo").click();
  assert.deepEqual(actions, [{ action: "move", move: "D4" }, { action: "move", move: "pass" }, { action: "undo" }]);
}));

test("cards display all 52 labels and only swap after two distinct selections", () => display((view, root, actions) => {
  view.show({ kind: "cards", cards: Array.from({ length: 52 }, (_, i) => i) });
  const cards = () => root.all().filter((i) => i.className.includes("deck-card"));
  assert.equal(cards().length, 52);
  assert.equal(cards()[3].textContent, "4♣");
  assert.equal(cards()[51].textContent, "K♠");
  cards()[0].click();
  assert.equal(actions.length, 0);
  assert.equal(cards()[0].attributes["aria-pressed"], "true");
  cards()[51].click();
  assert.deepEqual(actions, [{ action: "swap", first: 0, second: 51 }]);
}));

test("text displays quote strings and disappear when there is no decoded object", () => display((view, root) => {
  view.show({ kind: "text", type: "string", value: "" });
  assert.equal(root.children[0].textContent, 'string: ""');
  view.show(null);
  assert.equal(root.children.length, 0);
}));

test("map bounds contain the exact location, including the antimeridian", () => {
  for (const [latitude, longitude] of [[0, 0], [48.8566, 2.3522], [85, 180], [-85, -180]]) {
    const spec = mapSpec(latitude, longitude);
    const url = new URL(spec.url);
    assert.equal(spec.kind, "iframe");
    assert.equal(url.origin, "https://www.openstreetmap.org");
    const [west, south, east, north] = url.searchParams.get("bbox").split(",").map(Number);
    assert.ok(west <= longitude && longitude <= east);
    assert.ok(south <= latitude && latitude <= north);
    assert.ok(west >= -180 && east <= 180);
    assert.equal(url.searchParams.get("marker"), `${latitude},${longitude}`);
  }
});

test("polar positions have a geographic map and a correctly positioned marker", () => {
  for (const [latitude, longitude] of [[90, 0], [-90, 0], [88, 45], [-88, -180]]) {
    const spec = mapSpec(latitude, longitude);
    assert.equal(spec.kind, "image");
    const url = new URL(spec.url);
    assert.equal(url.searchParams.get("SRS"), "EPSG:4326");
    const [west, south, east, north] = url.searchParams.get("BBOX").split(",").map(Number);
    assert.ok(south <= latitude && latitude <= north);
    assert.equal(spec.x, (longitude - west) / (east - west) * 100);
    assert.equal(spec.y, (north - latitude) / (north - south) * 100);
  }
});
