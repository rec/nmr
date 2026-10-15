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
  const info = JSON.parse(configure("{}"));
  const fixture = JSON.parse(fs.readFileSync("test/format.json", "utf8"));
  assert.equal(info.count, 1628);
  assert.equal(info.identifier, fixture.vocabulary);
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
    ["text", " exact 001 # é "],
    ["date", "2000-02-29"],
    ["chess", "e4 e5 Nf3"],
    ["go", "9x9:D4 E4 pass pass"],
    ["semver", "1.2.3-rc.1+build.004"],
  ]) {
    const encoded = JSON.parse(
      convert(JSON.stringify({ operation: "encode", type_name: type, value })),
    );
    const decoded = JSON.parse(
      convert(JSON.stringify({ operation: "decode", value: encoded.name })),
    );
    assert.equal(decoded.value, encoded.value);
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
    convert(JSON.stringify({ operation: "decode", value: "universal:green" })),
  );
  const browsed = JSON.parse(
    convert(JSON.stringify({ operation: "browse", value: "universal:green" })),
  );
  assert.equal(browsed.canonical, false);
  assert.equal(
    JSON.parse(
      convert(JSON.stringify({ operation: "decode", value: browsed.name })),
    ).value,
    browsed.value,
  );
  configure.destroy();
  convert.destroy();
  console.log(
    `WebAssembly bridge, all sample codecs, custom words, and browsing passed in ${Date.now() - started}ms`,
  );
})().catch((error) => {
  console.error(String(error));
  process.exitCode = 1;
});
