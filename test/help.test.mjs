import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = fs.readFileSync(new URL("../nmr/web/help.js", import.meta.url), "utf8")
  .replace("import.meta.url", '"https://ax.to/nmr/help.js?v=test"');
const flush = () => new Promise(setImmediate);

class Element {
  constructor(tag) { this.tag = tag; this.children = []; }
  append(...children) { this.children.push(...children); }
  replaceChildren() { this.children = []; }
  addEventListener(name, callback) { this[name] = callback; }
  get textContent() { return this.children.map((i) => i.textContent).join(""); }
  set textContent(value) { this.children = [{ textContent: value }]; }
}

function page(markdown, ok = true) {
  const panel = new Element("section");
  const requests = [];
  vm.runInNewContext(source, {
    document: {
      querySelector: () => panel,
      createElement: (tag) => new Element(tag),
      createTextNode: (textContent) => ({ textContent }),
    },
    window: { location: { href: "https://ax.to/nmr?count=7" } },
    URL, console: { error() {} },
    fetch: (url) => {
      requests.push(url.href);
      return Promise.resolve({ ok, status: 404, text: () => Promise.resolve(markdown) });
    },
  });
  return { panel, requests };
}

test("help opens the editable Markdown file once and renders its supported formatting", () => {
  const { panel, requests } = page("# What is this thing?\n\n## Details\nPlain *italic* and **bold *inside***.\nMore [**help**](https://example.com).\n\n<script>literal</script> [unsafe](javascript:alert)\n");
  assert.equal(requests.length, 0);
  panel.beforetoggle({ newState: "open" });
  return flush().then(() => {
    assert.equal(requests[0], "https://ax.to/nmr/help.md");
    assert.deepEqual(panel.children.map((i) => i.tag), ["h1", "h2", "p", "p"]);
    assert.equal(panel.children[0].textContent, "What is this thing?");
    const paragraph = panel.children[2];
    assert.equal(paragraph.textContent, "Plain italic and bold inside. More help.");
    assert.equal(paragraph.children.find((i) => i.tag === "em").textContent, "italic");
    assert.equal(paragraph.children.find((i) => i.tag === "strong").children.find((i) => i.tag === "em").textContent, "inside");
    assert.equal(paragraph.children.find((i) => i.tag === "a").href, "https://example.com/");
    assert.equal(panel.children[3].textContent, "<script>literal</script> unsafe");
    assert.equal(panel.children[3].children.find((i) => i.tag === "a").href, undefined);
    panel.beforetoggle({ newState: "closed" });
    panel.beforetoggle({ newState: "open" });
    assert.equal(requests.length, 1);
  });
});

test("a missing help file shows a readable error in the panel", () => {
  const { panel } = page("", false);
  panel.beforetoggle({ newState: "open" });
  return flush().then(() => assert.equal(panel.textContent, "Help could not be loaded."));
});
