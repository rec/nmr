import test from "node:test";
import assert from "node:assert/strict";
import { describeObject } from "../nmr/web/description.mjs";

test("lists display each item's own value without typed JSON records", () => {
  const items = [{type: "frac", value: "0/0"}, {type: "ipv4", value: "10.0.0.1"}];
  assert.equal(describeObject({type: "list", value: JSON.stringify(items)}), "list: [0/0, 10.0.0.1]");
});

test("nested lists retain their structure and strings remain quoted", () => {
  const items = [
    {type: "string", value: "two, words"},
    {type: "list", value: [{type: "frac", value: "2/4"}, {type: "date", value: "2000-01-01"}]},
  ];
  assert.equal(describeObject({type: "list", value: JSON.stringify(items)}),
    'list: ["two, words", [2/4, 2000-01-01]]');
});

test("strings preserve whitespace, quotes, and numeric-looking text", () => {
  const items = [{type: "string", value: ' "0/0" '}, {type: "string", value: "42"}];
  assert.equal(describeObject({type: "list", value: JSON.stringify(items)}),
    'list: [" \\"0/0\\" ", "42"]');
});

test("scalar descriptions retain their type label and canonical formatting", () => {
  assert.equal(describeObject({type: "string", value: "Tom"}), 'string: "Tom"');
  assert.equal(describeObject({type: "chess", value: ""}), 'chess: ');
  assert.equal(describeObject({type: "float", value: "-0.0"}), 'float: -0.0');
});

test("empty chess games remain visible and distinct from empty strings inside lists", () => {
  const items = [
    {type: "int", value: "0"},
    {type: "list", value: [{type: "chess", value: ""}, {type: "string", value: ""}]},
  ];
  assert.equal(describeObject({type: "list", value: JSON.stringify(items)}),
    'list: [0, [chess: "", ""]]');
});
