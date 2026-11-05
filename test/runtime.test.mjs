import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = fs.readFileSync(new URL("../nmr/web/runtime.js", import.meta.url), "utf8").replaceAll("export ", "");
function runtime() {
  let worker;
  const context = vm.createContext({
    Worker: class {
      constructor() { worker = this; this.messages = []; }
      postMessage(message) { this.messages.push(message); }
    },
    console: { error() {} },
  });
  vm.runInContext(source, context);
  return { worker, configured: vm.runInContext("configured", context), request: vm.runInContext("request", context) };
}

test("Python startup errors retain their traceback and original exception message", async () => {
  const app = runtime();
  const message = "Traceback (most recent call last):\nValueError: Duplicate words after vocabulary normalization";
  const rejected = assert.rejects(app.configured, (error) => error.message === message);
  app.worker.onmessage({ data: { id: app.worker.messages[0].id, error: message } });
  await rejected;
});

test("worker crashes preserve the original error for pending and subsequent requests", async () => {
  const app = runtime();
  const original = new Error("Failed to import Pyodide");
  const pending = app.request("count", { value: "0" });
  const rejected = [app.configured, pending].map((promise) => assert.rejects(promise, (error) => error === original));
  app.worker.onerror({ error: original, message: original.message });
  await Promise.all(rejected);
  await assert.rejects(app.request("count", { value: "1" }), (error) => error === original);
});

test("worker errors without an Error object retain the browser's message", async () => {
  const app = runtime();
  const message = "Uncaught NetworkError: Failed to load pyodide.js";
  const rejected = assert.rejects(app.configured, (error) => error.message === message);
  app.worker.onerror({ message });
  await rejected;
});
