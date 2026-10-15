const $ = (id) => document.getElementById(id);
const worker = new Worker("worker.js");
const pending = new Map();
let serial = 0;
let mode = "decode";
let vocabulary;
let busy = false;

function message(text, error = false) {
  $("message").textContent = text;
  $("message").classList.toggle("error", error);
}
function request(action, payload) {
  return new Promise((resolve, reject) => {
    const id = ++serial;
    pending.set(id, { resolve, reject });
    worker.postMessage({ id, action, payload });
  });
}
worker.onmessage = ({ data }) => {
  const task = pending.get(data.id);
  if (!task) return;
  pending.delete(data.id);
  if (data.error)
    task.reject(new Error(data.error.split("\n").filter(Boolean).pop()));
  else task.resolve(data.result);
};
worker.onerror = () => {
  for (const task of pending.values())
    task.reject(
      new Error(
        "Local engine could not start. Check your connection and reload.",
      ),
    );
  pending.clear();
  $("engine-status").textContent = "Engine unavailable";
};
function selectMode(selected) {
  mode = selected;
  document
    .querySelectorAll("[data-mode]")
    .forEach((button) =>
      button.setAttribute("aria-pressed", String(button.dataset.mode === mode)),
    );
  $("encode-options").hidden = mode !== "encode";
  $("mode-description").textContent = {
    encode:
      "Choose a type. Exact text preserves names, addresses, email, URLs, and reference numbers.",
    decode: "Recover an exact detail from its canonical name.",
    browse:
      "Explore a name. Save the returned canonical name to preserve the result.",
  }[mode];
  $("input-label").textContent =
    mode === "encode" ? "Detail to name" : "Word name";
  $("value").placeholder =
    mode === "encode"
      ? "Enter your detail exactly"
      : "Paste a name, including its prefix";
  $("convert").textContent = {
    encode: "Create name",
    decode: "Decode name",
    browse: "Explore name",
  }[mode];
  $("result").hidden = true;
  message("");
}
function updateType() {
  const path = $("type").value;
  $("type-description").textContent = vocabulary.types[path] || "";
  $("scope").replaceChildren();
  const full = document.createElement("option");
  full.value = path;
  full.textContent = "Full type prefix (recommended)";
  $("scope").append(full);
  const parts = path.split(":");
  for (let i = parts.length - 1; i > 0; i--) {
    const scope = parts.slice(0, i).join(":");
    const option = document.createElement("option");
    option.value = scope;
    option.textContent = scope + ":";
    $("scope").append(option);
  }
  const none = document.createElement("option");
  none.value = "";
  none.textContent = "No prefix";
  $("scope").append(none);
}
async function configure(settings) {
  busy = true;
  $("convert").disabled = true;
  $("apply-words").disabled = true;
  $("default-words").disabled = true;
  try {
    const info = await request("configure", settings);
    vocabulary = info;
    const previous = $("type").value;
    $("type").replaceChildren();
    for (const [path, description] of Object.entries(info.types)) {
      const option = document.createElement("option");
      option.value = path;
      option.textContent = path + " / " + description;
      $("type").append(option);
    }
    $("type").value = previous in info.types ? previous : "universal:math:int";
    updateType();
    $("vocabulary-id").value = info.identifier;
    $("vocabulary-count").textContent =
      info.count +
      " ordered words · payloads of up to " +
      info.count +
      " nonrepeating words";
    $("engine-status").textContent = "Ready · runs on your device";
    $("result").hidden = true;
    $("export-words").disabled = false;
    message(
      "Vocabulary ready. Its order and case policy are part of the encoding.",
    );
  } catch (error) {
    if (!vocabulary) $("engine-status").textContent = "Engine unavailable";
    message(error.message, true);
  } finally {
    busy = false;
    $("convert").disabled = !vocabulary;
    $("apply-words").disabled = false;
    $("default-words").disabled = false;
  }
}
async function convert(event) {
  event.preventDefault();
  if (busy || !vocabulary) return;
  busy = true;
  $("convert").disabled = true;
  $("result").hidden = true;
  message("Working locally…");
  try {
    const expected = $("expected-id").value.trim();
    if (expected && expected !== vocabulary.identifier)
      throw new Error(
        "Vocabulary identifier does not match the selected list.",
      );
    const result = await request("convert", {
      operation: mode,
      value: $("value").value,
      type_name: $("type").value,
      scope: $("scope").value,
      vocabulary: expected || null,
    });
    $("result-type").textContent = result.type;
    $("result-value").value = result.value;
    $("result-name").value = result.name;
    const count = result.name
      .slice(result.name.lastIndexOf(":") + 1)
      .split(/\s+/).length;
    $("result-note").textContent =
      count +
      " payload words. " +
      (result.canonical
        ? "Canonical name."
        : "Browsing discovery: the input is not canonical and may explore differently in a future tree.");
    $("result").hidden = false;
    message(
      mode === "encode"
        ? "Name created. Check the decoded detail before sharing."
        : "Done. Verify this is the detail you expected.",
    );
  } catch (error) {
    message(error.message, true);
  } finally {
    busy = false;
    $("convert").disabled = false;
  }
}
document
  .querySelectorAll("[data-mode]")
  .forEach((button) =>
    button.addEventListener("click", () => selectMode(button.dataset.mode)),
  );
$("type").addEventListener("change", updateType);
$("convert-form").addEventListener("submit", convert);
$("apply-words").addEventListener("click", () => {
  if (busy) return;
  const raw = $("word-list").value;
  const count = $("word-count").value;
  configure({
    words: raw.trim() ? raw.split(/\r?\n/) : null,
    count: count ? Number(count) : null,
    case_sensitive: $("case-sensitive").checked,
  });
});
$("default-words").addEventListener("click", () => {
  if (busy) return;
  $("word-list").value = "";
  $("word-count").value = "";
  $("case-sensitive").checked = false;
  configure({});
});
$("word-file").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    $("word-list").value = new TextDecoder("utf-8", { fatal: true }).decode(
      await file.arrayBuffer(),
    );
  } catch {
    message("The vocabulary file must be valid UTF-8.", true);
  }
});
$("export-words").addEventListener("click", () => {
  const url = URL.createObjectURL(
    new Blob([vocabulary.words.join("\n") + "\n"], {
      type: "text/plain;charset=utf-8",
    }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = "nmr-words.txt";
  link.click();
  URL.revokeObjectURL(url);
});
for (const part of ["name", "value"]) {
  $("copy-" + part).addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText($("result-" + part).value);
      message("Copied.");
    } catch {
      $("result-" + part).focus();
      $("result-" + part).select();
      message("Select and copy the highlighted text.");
    }
  });
}
$("example").addEventListener("click", async () => {
  if (busy || !vocabulary) return;
  if (mode === "encode") {
    $("type").value = "physical:time:date";
    updateType();
    $("value").value = "2000-02-29";
  } else if (mode === "browse")
    $("value").value = "universal:" + vocabulary.words[3 % vocabulary.count];
  else {
    try {
      const result = await request("convert", {
        operation: "encode",
        value: "2/4",
        type_name: "frac",
      });
      $("value").value = result.name;
    } catch (error) {
      message(error.message, true);
    }
  }
});
configure({});
