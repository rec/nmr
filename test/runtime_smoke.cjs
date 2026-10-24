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
  assert.equal("meta:record" in info.types, false);
  assert.equal("meta:list" in info.types, false);
  assert.ok("list" in info.types);
  const qualified = JSON.parse(convert(JSON.stringify({
    operation: "decode", value: ":play:game:chess:in get",
  })));
  assert.equal(qualified.name, "chess:in get");
  assert.equal(qualified.type, "chess");
  assert.equal(qualified.canonical, true);
  assert.equal(JSON.parse(convert(JSON.stringify({
    operation: "decode", value: "play:game:will gas",
  }))).name, "game:will gas");
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
    assert.equal(encoded.name, sample.name);
    const decoded = JSON.parse(
      convert(JSON.stringify({ operation: "decode", value: sample.name })),
    );
    assert.equal(decoded.value, sample.value);
  }
  for (const [type, value] of [
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
      convert(JSON.stringify({ operation: "decode", value: encoded.name })),
    );
    assert.equal(decoded.value, encoded.value);
    if (type === "phone") assert.equal(encoded.value, "+442079460958;ext=004");
    console.log(`${type}: ${encoded.name}`);
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
      convert(JSON.stringify({ operation: "decode", value: custom.name })),
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
      convert(JSON.stringify({ operation: "decode", value: browsed.name })),
    ).value,
    browsed.value,
  );
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
  assert.equal(tuneCustom.name, "tune:é");
  assert.equal(JSON.parse(convert(JSON.stringify({operation: "decode", value: tuneCustom.name}))).value, "@1");
  const item = {operation: "encode", type_name: "int", value: "2"};
  const projected = JSON.parse(previewItem(JSON.stringify(item)));
  assert.equal(projected.value, "@1 -1@1");
  const absoluteItem = JSON.parse(previewItem(JSON.stringify({...item, absolute: true})));
  assert.notEqual(absoluteItem.value, projected.value);
  const itemName = JSON.parse(convert(JSON.stringify(item))).name;
  assert.deepEqual(JSON.parse(previewItem(JSON.stringify({operation: "decode", value: itemName}))), projected);
  previewItem.destroy();
  preview.destroy();
  convert.destroy();
  console.log(
    `WebAssembly bridge, all sample codecs, custom words, and browsing passed in ${Date.now() - started}ms`,
  );
})().catch((error) => {
  console.error(String(error));
  process.exitCode = 1;
});
