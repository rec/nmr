/* Non-UI WebAssembly verification. Requires pyodide@0.29.3 on NODE_PATH. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const { loadPyodide } = require("pyodide");
(async () => {
  const started = Date.now();
  const runtime = await loadPyodide({
    packageCacheDir: "/tmp/nmr-pyodide-packages",
  });
  await runtime.loadPackage("pydantic");
  runtime.unpackArchive(
    new Uint8Array(fs.readFileSync("dist/web/python.zip")),
    "zip",
  );
  runtime.runPython(fs.readFileSync("dist/web/bridge.py", "utf8"));
  const configure = runtime.globals.get("configure");
  const convert = runtime.globals.get("convert");
  const preview = runtime.globals.get("preview");
  const previewItem = runtime.globals.get("preview_item");
  const info = JSON.parse(configure("{}"));
  const fixture = JSON.parse(fs.readFileSync("test/format.json", "utf8"));
  assert.equal(info.count, 1628);
  assert.equal(info.identifier, fixture.vocabulary);
  assert.equal("data:text" in info.types, false);
  assert.ok("data:string" in info.types);
  assert.equal("meta:record" in info.types, false);
  assert.equal("meta:list" in info.types, false);
  assert.ok("list" in info.types);
  const qualified = JSON.parse(convert(JSON.stringify({
    operation: "decode", value: ":play:game:chess:in also",
  })));
  assert.equal(qualified.truename, "chess:in also");
  assert.equal(qualified.type, "chess");
  assert.equal(qualified.canonical, true);
  assert.equal(JSON.parse(convert(JSON.stringify({
    operation: "decode", value: "play:game:was hope",
  }))).truename, "game:was hope");
  for (const sample of fixture.cases) {
    const encoded = JSON.parse(
      convert(
        JSON.stringify({
          operation: "encode",
          type_name: sample.type,
          value: sample.input,
          scope: sample.scope,
        }),
      ),
    );
    assert.equal(encoded.truename, sample.truename);
    const decoded = JSON.parse(
      convert(JSON.stringify({ operation: "decode", value: sample.truename })),
    );
    assert.equal(decoded.value, sample.value);
  }
  for (const [type, value] of [
    ["string", "  Mixed Case 🎵  "],
    ["frac", "2/4"],
    ["date", "2000-02-29"],
    ["chess", "e4 e5 Nf3"],
    ["go", "9x9:D4 E4 pass pass"],
    ["phone", "+44 (0)20 7946 0958 ext. 004"],
    ["tune", "@1 2@1/2 2@1/2 r@1/3 -1@2/3 @1"],
    ["semver", "1.2.3-rc.1+build.004"],
  ]) {
    const encoded = JSON.parse(
      convert(JSON.stringify({ operation: "encode", type_name: type, value })),
    );
    const decoded = JSON.parse(
      convert(JSON.stringify({ operation: "decode", value: encoded.truename })),
    );
    assert.equal(decoded.value, encoded.value);
    if (type === "phone") assert.equal(encoded.value, "+442079460958;ext=004");
    console.log(`${type}: ${encoded.truename}`);
  }
  configure(
    JSON.stringify({
      words: ["é", "red", "blue", "green", "gold", "white", "black"],
    }),
  );
  const custom = JSON.parse(
    convert(
      JSON.stringify({ operation: "encode", type_name: "int", value: "-2" }),
    ),
  );
  assert.equal(
    JSON.parse(
      convert(JSON.stringify({ operation: "decode", value: custom.truename })),
    ).value,
    "-2",
  );
  assert.throws(() =>
    convert(JSON.stringify({ operation: "decode", value: "pure:green" })),
  );
  const browsed = JSON.parse(
    convert(JSON.stringify({ operation: "browse", value: "pure:green" })),
  );
  assert.equal(browsed.canonical, false);
  assert.equal(
    JSON.parse(
      convert(JSON.stringify({ operation: "decode", value: browsed.truename })),
    ).value,
    browsed.value,
  );
  configure("{}");
  const recognize = runtime.globals.get("recognize");
  const previewTruename = runtime.globals.get("preview_truename");
  const { Editor } = await import("../nmr/web/editor.mjs");
  for (const value of ["asdf", "asdfasdf", "Hello!", "dfasdfasdf", "iPhone"]) {
    const editor = new Editor();
    let result;
    for (const character of value) {
      editor.replace(character);
      result = JSON.parse(recognize(JSON.stringify({ value: editor.text })));
    }
    assert.equal(editor.text, value, "String typing must preserve case");
    assert.equal(result.kind, "string", `Typing ${value} must reach String recognition`);
    assert.ok(result.truename && result.full_truename, "Both truename lines need a value");
    assert.equal(JSON.parse(convert(JSON.stringify({ operation: "decode", value: result.truename }))).value, value);
  }

  const person = new Editor();
  for (const [character, kind] of [["T", "string"], ["o", "string"], ["m", "string"], [" ", "string"], ["R", "string"]]) {
    person.replace(character);
    const result = JSON.parse(recognize(JSON.stringify({value: person.text})));
    assert.equal(result.kind, kind);
    assert.ok(result.truename && (kind === "truename" ? result.browsed : result.full_truename), `Both results must exist for ${person.text}`);
  }
  assert.equal(person.text, "Tom R");
  for (const [value, kind] of [["42", "int"], ["+1", "phone"], ["8/5", "frac"], ["12:34", "time"], ["2000-02-29", "date"]]) {
    const result = JSON.parse(recognize(JSON.stringify({ value })));
    assert.equal(result.kind, kind);
    assert.ok(result.truename.startsWith(kind + ":"));
  }
  for (const value of ["Tom", "Tom ", "tOm THE oF", "TUNE:sUcH LiKe"]) {
    const result = JSON.parse(recognize(JSON.stringify({ value, mode: "truename" })));
    assert.equal(result.kind, "truename");
    assert.ok(result.truename && result.browsed);
    assert.equal(result.truename, value);
  }
  const string = JSON.parse(recognize('{"value":"  xyzzy!  "}'));
  assert.equal(string.kind, "string");
  assert.equal(JSON.parse(convert(JSON.stringify({operation: "decode", value: string.truename}))).value, "  xyzzy!  ");
  assert.equal(JSON.parse(recognize('{"value":"th"}')).kind, "string");
  assert.equal(JSON.parse(previewTruename('{"value":"int:the"}')).value, "@1");
  assert.equal(JSON.parse(previewTruename('{"value":"tune:the"}')).value, "@1");
  assert.notEqual(JSON.parse(previewTruename('{"value":"tune:the","absolute":true}')).value, "@1");
  assert.equal(JSON.parse(recognize('{"value":"NAME:THE OF","mode":"truename"}')).truename, "NAME:THE OF");
  assert.deepEqual(JSON.parse(previewTruename('{"value":"name:the"}')),
    JSON.parse(previewTruename('{"value":"the"}')));
  assert.deepEqual(JSON.parse(previewTruename('{"value":"name:tune:the"}')),
    JSON.parse(previewTruename('{"value":"tune:the"}')));
  const ode = JSON.parse(recognize('{"value":"tune:post were","mode":"truename"}'));
  assert.equal(ode.browsed.type, "tune");
  assert.equal(ode.browsed.value, "@1 @1 1@1 2@1 @1 -2@1 -1@1 -2@1");
  assert.equal(JSON.parse(previewTruename(JSON.stringify({ value: ode.truename }))).value,
    "@1 @1 1@1 2@1 @1 -2@1 -1@1 -2@1");
  assert.deepEqual(JSON.parse(previewItem(JSON.stringify({operation: "encode", type_name: ode.browsed.type, value: ode.browsed.value}))),
    JSON.parse(previewTruename(JSON.stringify({value: ode.truename}))));
  recognize.destroy();
  previewTruename.destroy();
  configure(JSON.stringify({ words: ["é", "red", "blue", "green", "gold", "white", "black"] }));
  configure.destroy();
  const music = JSON.parse(preview(JSON.stringify({
    value: "@1 2@1/2 2@1/2 r@1/3 -1@2/3 @1",
  })));
  assert.deepEqual(music.events.map((event) => event.pitch), ["58", "60", "62", "61", "61"]);
  assert.deepEqual(music.events.map((event) => event.onset), ["0", "1", "3/2", "7/3", "3"]);
  assert.equal(music.playback[3].onset, 7 / 6);
  assert.equal(JSON.parse(preview(JSON.stringify({value: "@1 @1", tie: 1}))).value, "@2");
  assert.throws(() => preview(JSON.stringify({ value: "@1/9" })));
  assert.match(JSON.parse(preview(JSON.stringify({value: "@1 200@1"}))).playback_error, /MIDI/);
  const widePitch = JSON.parse(preview(JSON.stringify({value: "@1 18014398509481986@1"})));
  assert.deepEqual(widePitch.events.map((event) => event.pitch), ["-9007199254740933", "9007199254741053"]);
  const tuneCustom = JSON.parse(convert(JSON.stringify({operation: "encode", type_name: "tune", value: "@1"})));
  assert.equal(tuneCustom.truename, "tune:é");
  assert.equal(JSON.parse(convert(JSON.stringify({operation: "decode", value: tuneCustom.truename}))).value, "@1");
  const item = {operation: "encode", type_name: "int", value: "2"};
  const projected = JSON.parse(previewItem(JSON.stringify(item)));
  assert.equal(projected.value, "@1 -1@1");
  const absoluteItem = JSON.parse(previewItem(JSON.stringify({...item, absolute: true})));
  assert.notEqual(absoluteItem.value, projected.value);
  const itemTruename = JSON.parse(convert(JSON.stringify(item))).truename;
  assert.deepEqual(JSON.parse(previewItem(JSON.stringify({operation: "decode", value: itemTruename}))), projected);
  previewItem.destroy();
  preview.destroy();
  convert.destroy();
  console.log(
    `WebAssembly bridge, smart recognition, truename playback, codecs, custom words, and browsing passed in ${Date.now() - started}ms`,
  );
})().catch((error) => {
  console.error(String(error));
  process.exitCode = 1;
});
