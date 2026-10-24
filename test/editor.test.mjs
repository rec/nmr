import test from "node:test";
import assert from "node:assert/strict";
import { Editor } from "../nmr/web/editor.mjs";

function editor(text = "") {
  const value = new Editor();
  value.setWords(["a", "an", "and", "the", "of"]);
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
test("enters name mode on a complete word without completing its prefixes", () => {
  const value = editor("A");
  assert.equal(value.nameMode, true);
  assert.equal(value.text, "a");
  value.replace("N");
  assert.equal(value.text, "an");
  value.replace("D");
  assert.equal(value.text, "and");
  value.replace(" TH");
  assert.equal(value.text, "and th");
  assert.equal(value.nameMode, true);
});
test("name mode is sticky through edits, but clearing or replacing resets it", () => {
  const value = editor("THE");
  assert.equal(value.text, "the");
  value.move(0);
  value.erase(1);
  assert.equal(value.text, "he");
  assert.equal(value.nameMode, true);
  value.selectAll();
  value.replace("42");
  assert.equal(value.nameMode, false);
  value.selectAll();
  value.replace("THE OF");
  assert.equal(value.nameMode, true);
  assert.equal(value.text, "the of");
  value.clear();
  assert.equal(value.nameMode, false);
  assert.equal(value.cursor, 0);
});
test("pasted multiline text stays a single controlled line", () => {
  const value = editor("THE\nOF");
  assert.equal(value.text, "the of");
  assert.equal(value.cursor, 6);
});
test("typing before the vocabulary loads is recognized once it is available", () => {
  const value = new Editor();
  value.replace("THE");
  assert.equal(value.nameMode, false);
  value.setWords(["the"]);
  assert.equal(value.nameMode, true);
  assert.equal(value.text, "the");
});
