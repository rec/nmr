/* Only runtime assets are fetched. Values and word lists stay inside this worker. */
importScripts("https://cdn.jsdelivr.net/pyodide/v0.29.3/full/pyodide.js");
let runtime;
const ready = (async () => {
  runtime = await loadPyodide();
  await runtime.loadPackage("pydantic");
  const response = await fetch("python.zip");
  if (!response.ok) throw new Error("Could not load the Python core");
  runtime.unpackArchive(await response.arrayBuffer(), "zip");
  const bridge = await fetch("bridge.py");
  if (!bridge.ok) throw new Error("Could not load the browser bridge");
  // Evaluate the shipped Python file; no Python source is assembled from user input.
  runtime.runPython(await bridge.text());
})();
self.onmessage = async ({ data }) => {
  try {
    await ready;
    const fn = runtime.globals.get(data.action);
    try {
      const result = fn(JSON.stringify(data.payload));
      self.postMessage({ id: data.id, result: JSON.parse(result) });
    } finally {
      fn.destroy();
    }
  } catch (error) {
    self.postMessage({ id: data.id, error: String(error.message || error) });
  }
};
