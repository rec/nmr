import test from "node:test";
import assert from "node:assert/strict";
import { TruenameEditor } from "../nmr/web/truename-editor.mjs";

function choose(editor, word) {
  for (let i = 0; i < editor.words.length && editor.choice !== word; i++) editor.cycle(1);
  assert.equal(editor.choice, word);
}
function invariant(editor) {
  const tokens = editor.typed.split(" ");
  const current = tokens.pop();
  const completed = tokens.filter(Boolean);
  assert.equal(new Set(completed).size, completed.length);
  assert.ok(completed.every((word) => editor.words.includes(word)));
  assert.ok(!current || editor.options.length > 0);
  if (editor.choice) {
    assert.ok(editor.options.includes(editor.choice));
    assert.ok(editor.choice.startsWith(current));
    assert.equal(current + editor.guessed, editor.choice);
  } else assert.equal(editor.options.length, 0);
}

test("suggests an eligible next word without accepting it", () => {
  const editor = new TruenameEditor(["the", "there", "then"]);
  assert.equal(editor.typed, "");
  assert.equal(editor.completion, "");
  assert.ok(editor.words.includes(editor.guessed));
  choose(editor, "there");
  assert.equal(editor.type("t"), true);
  assert.equal(editor.typed, "t");
  assert.equal(editor.guessed, "here");
  assert.equal(editor.completion, "there");
});

test("right accepts shared characters and stops at each choice", () => {
  const editor = new TruenameEditor(["the", "there", "then", "thin"]);
  choose(editor, "there");
  editor.right();
  assert.equal(editor.typed, "th");
  assert.equal(editor.guessed, "ere");
  editor.right();
  assert.equal(editor.typed, "the");
  assert.equal(editor.guessed, "re");
  editor.right();
  assert.equal(editor.typed, "there ");
  assert.ok(!editor.options.includes("there"));
});

test("right accepts the entire remaining word when there is one continuation", () => {
  const editor = new TruenameEditor(["stove", "cat"]);
  assert.equal(editor.type("s"), true);
  assert.equal(editor.typed, "s");
  editor.right();
  assert.equal(editor.typed, "stove ");
  assert.equal(editor.guessed, "cat");
});

test("left restores accepted characters to the guess and crosses automatic spaces", () => {
  const editor = new TruenameEditor(["cat", "dog"]);
  choose(editor, "cat");
  editor.right();
  assert.equal(editor.typed, "cat ");
  editor.left();
  assert.equal(editor.typed, "ca");
  assert.equal(editor.guessed, "t");
  editor.left();
  assert.equal(editor.typed, "c");
  assert.equal(editor.guessed, "at");
  editor.left();
  assert.equal(editor.typed, "");
  assert.equal(editor.guessed, "cat");
  assert.equal(editor.left(), false);
});

test("cycles next words and matching continuations in both directions", () => {
  const editor = new TruenameEditor(["cat", "car", "dog"]);
  choose(editor, "cat");
  editor.cycle(1);
  assert.equal(editor.guessed, "car");
  editor.cycle(-1);
  assert.equal(editor.guessed, "cat");
  editor.type("c");
  editor.cycle(1);
  assert.equal(editor.typed, "c");
  assert.equal(editor.guessed, "ar");
  editor.cycle(1);
  assert.equal(editor.guessed, "at");
  editor.cycle(-1);
  assert.equal(editor.guessed, "ar");
});

test("space accepts the guess and used words never reappear", () => {
  const editor = new TruenameEditor(["cat", "car", "dog"]);
  choose(editor, "cat");
  editor.type(" ");
  assert.equal(editor.typed, "cat ");
  assert.equal(editor.completion, "cat");
  assert.deepEqual(editor.options, ["car", "dog"]);
  editor.type("d");
  editor.type(" ");
  assert.equal(editor.typed, "cat dog ");
  assert.equal(editor.guessed, "car");
  editor.type(" ");
  assert.equal(editor.typed, "cat dog car ");
  assert.equal(editor.guessed, "");
  assert.equal(editor.right(), false);
  assert.equal(editor.type("c"), false);
  editor.left();
  assert.equal(editor.typed, "cat dog ca");
  assert.equal(editor.guessed, "r");
  invariant(editor);
});

test("rejects impossible letters and non-lowercase input without changing the state", () => {
  const editor = new TruenameEditor(["cat", "dog"]);
  editor.type("c");
  for (const key of ["z", "C", "1", ":", "é", "🎵", "Delete", "Enter", "Escape", "cat"]) {
    const before = [editor.text, editor.guessed];
    assert.equal(editor.type(key), false);
    assert.deepEqual([editor.text, editor.guessed], before);
  }
});

test("loads bookmark and swap values with a separate fixed prefix", () => {
  const editor = new TruenameEditor(["cat", "car", "dog"]);
  assert.equal(editor.load("NAME:TUNE:CAT dog"), true);
  assert.equal(editor.text, "name:tune: cat dog ");
  assert.equal(editor.guessed, "car");
  editor.left();
  assert.equal(editor.text, "name:tune: cat do");
  assert.equal(editor.guessed, "g");
  assert.equal(editor.load("cat ca"), true);
  assert.equal(editor.guessed, "r");
  for (const invalid of ["cat cat", "unknown dog", "cat z", "42:dog"]) {
    const before = [editor.text, editor.guessed];
    assert.equal(editor.load(invalid), false);
    assert.deepEqual([editor.text, editor.guessed], before);
  }
});

test("keeps all accepted words unique through mixed editing", () => {
  const editor = new TruenameEditor(["a", "an", "and", "as", "at", "cat", "car"]);
  for (let i = 0; i < 200; i++) {
    for (const action of [() => editor.cycle(1), () => editor.right(), () => editor.left(), () => editor.type("a"), () => editor.type(" ")]) {
      action();
      invariant(editor);
    }
  }
});
