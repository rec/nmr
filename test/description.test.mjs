import test from "node:test";
import assert from "node:assert/strict";
import { describeObject } from "../nmr/web/description.mjs";

test("string descriptions preserve whitespace and quote their contents", () => {
  assert.equal(describeObject({type: "string", value: "two, words"}), '"two, words"');
  assert.equal(describeObject({type: "string", value: ""}), '""');
  assert.equal(describeObject({type: "string", value: ' "42" '}), '" \\"42\\" "');
});

test("scalar descriptions omit type labels and retain canonical formatting", () => {
  assert.equal(describeObject({type: "string", value: "Tom"}), '"Tom"');
  assert.equal(describeObject({type: "chess", value: ""}), '');
  assert.equal(describeObject({type: "frac", value: "-1/2"}), '-1/2');
  assert.equal(describeObject({type: "time", value: "12:34:00"}), '12:34:00');
});
