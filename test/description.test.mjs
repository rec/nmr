import test from "node:test";
import assert from "node:assert/strict";
import { describeObject } from "../nmr/web/description.mjs";

test("string descriptions preserve whitespace and quote their contents", () => {
  assert.equal(describeObject({type: "string", value: "two, words"}), 'string: "two, words"');
  assert.equal(describeObject({type: "string", value: ""}), 'string: ""');
  assert.equal(describeObject({type: "string", value: ' "42" '}), 'string: " \\"42\\" "');
});

test("scalar descriptions retain their type label and canonical formatting", () => {
  assert.equal(describeObject({type: "string", value: "Tom"}), 'string: "Tom"');
  assert.equal(describeObject({type: "chess", value: ""}), 'chess: ');
  assert.equal(describeObject({type: "frac", value: "-1/2"}), 'frac: -1/2');
  assert.equal(describeObject({type: "time", value: "12:34:00"}), 'time: 12:34:00');
});
