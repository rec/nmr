import test from "node:test";
import assert from "node:assert/strict";
import { Editor } from "../nmr/web/editor.mjs";

function editor(text = "") {
  const value = new Editor();
  value.replace(text);
  return value;
}
test("inserts and replaces at the owned cursor and selection", () => {
  const value = editor("1234");
  value.move(2);
  value.replace("0");
  assert.equal(value.text, "12034");
  assert.equal(value.cursor, 3);
  value.move(1);
  value.move(4, true);
  assert.equal(value.selection(), "203");
  value.replace("9");
  assert.equal(value.text, "194");
  assert.equal(value.cursor, 2);
  value.erase(-1);
  assert.equal(value.text, "14");
  value.erase(1);
  assert.equal(value.text, "1");
});
test("moves and deletes whole Unicode characters and words", () => {
  const value = editor("42 🎵");
  value.erase(-1);
  assert.equal(value.text, "42 ");
  value.erase(-1, true);
  assert.equal(value.text, "");
  value.replace("hello world");
  value.move(0);
  value.erase(1, true);
  assert.equal(value.text, " world");
});
test("typing across word boundaries preserves the original case", () => {
  const value = editor("A");
  assert.equal(value.text, "A");
  value.replace("N");
  assert.equal(value.text, "AN");
  value.replace("D");
  assert.equal(value.text, "AND");
  value.replace(" TH");
  assert.equal(value.text, "AND TH");
});
test("replacement and clearing preserve the original case and reset the cursor", () => {
  const value = editor("THE ");
  assert.equal(value.text, "THE ");
  value.move(0);
  value.erase(1);
  assert.equal(value.text, "HE ");
  value.selectAll();
  value.replace("42");
  value.selectAll();
  value.replace("THE OF");
  assert.equal(value.text, "THE OF");
  value.clear();
  assert.equal(value.cursor, 0);
});
test("pasted multiline text stays a single controlled line", () => {
  const value = editor("THE\nOF");
  assert.equal(value.text, "THE OF");
  assert.equal(value.cursor, 6);
});
test("phone input rejects letters without changing text, cursor, or selection", () => {
  const value = editor("+1");
  assert.equal(value.replace("x"), false);
  assert.equal(value.text, "+1");
  assert.equal(value.cursor, 2);
  value.move(1);
  value.move(2, true);
  assert.equal(value.replace("é"), false);
  assert.equal(value.selection(), "1");
  assert.equal(value.replace("44"), true);
  assert.equal(value.text, "+44");
  assert.equal(value.replace(" (20) 1234-5678"), true);
});
test("phone restrictions end when cleared, fully replaced, or the plus is removed", () => {
  const value = editor("+1");
  value.selectAll();
  assert.equal(value.replace("THE"), true);
  assert.equal(value.text, "THE");
  value.clear();
  value.replace("+1");
  value.move(0);
  value.erase(1);
  assert.equal(value.replace("a"), true);
  assert.equal(value.text, "a1");
});

test("typing through a vocabulary word can still produce a case-preserving string", () => {
  const value = new Editor();
  for (const text of ["asdf", "Hello!", "iPhone"]) {
    value.clear();
    for (const character of text) value.replace(character);
    assert.equal(value.text, text);
  }
});

test("editing mixed-case text preserves its case and selection", () => {
  const value = new Editor();
  for (const character of "Tom THE oF ") value.replace(character);
  assert.equal(value.text, "Tom THE oF ");
  value.move(1);
  value.move(3, true);
  assert.equal(value.selection(), "om");
  assert.equal(value.anchor, 1);
  assert.equal(value.cursor, 3);
  value.replace("OM");
  assert.equal(value.text, "TOM THE oF ");
});

test("backward selections replace and delete the selected text in the middle", () => {
  const value = editor("12345");
  value.move(4);
  value.move(1, true);
  assert.equal(value.selection(), "234");
  value.replace("X");
  assert.equal(value.text, "1X5");
  assert.equal(value.cursor, 2);
  value.move(2);
  value.move(1, true);
  value.erase(1);
  assert.equal(value.text, "15");
  assert.equal(value.cursor, 1);
});
