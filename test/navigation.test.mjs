import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = fs.readFileSync(new URL("../nmr/web/navigation.js", import.meta.url), "utf8");

function navigation(address) {
  let url = new URL(address);
  const elements = Object.fromEntries(["#main-view", "#clock-view", "#main-link", "#clock-link"].map((i) => [i, {
    hidden: true,
    addEventListener(event, callback) { this[event] = callback; },
    querySelector() { return { focus() {} }; },
  }]));
  const listeners = {};
  const entries = [url.href];
  let position = 0;
  const window = {
    location: { get href() { return url.href; } },
    history: {
      pushState(state, title, next) {
        url = new URL(next);
        entries.splice(++position, entries.length, url.href);
      },
    },
    addEventListener(event, callback) { listeners[event] = callback; },
    dispatchEvent(event) { listeners[event.type]?.(event); },
  };
  const document = { querySelector(selector) { return elements[selector]; } };
  vm.runInNewContext(source, { document, window, URL, Event });
  return {
    elements, document,
    get url() { return url; },
    edit(next) { url = new URL(next); entries[position] = url.href; },
    click(selector, modifiers = {}) {
      let prevented = false;
      elements[selector].click({ button: 0, preventDefault() { prevented = true; }, ...modifiers });
      return prevented;
    },
    back() { url = new URL(entries[--position]); window.dispatchEvent(new Event("popstate")); },
    forward() { url = new URL(entries[++position]); window.dispatchEvent(new Event("popstate")); },
  };
}

test("a direct clock URL selects the clock view", () => {
  const app = navigation("https://ax.to/nmr?type=clock");
  assert.equal(app.elements["#main-view"].hidden, true);
  assert.equal(app.elements["#clock-view"].hidden, false);
  assert.equal(app.document.title, "Clock · nmr");
  app.click("#main-link");
  assert.equal(app.url.href, "https://ax.to/nmr?desc=");
});

test("switching views preserves the editor URL and supports Back and Forward", () => {
  const app = navigation("https://ax.to/nmr/?desc=");
  app.edit("https://ax.to/nmr?name=one+love");
  assert.equal(app.click("#clock-link"), true);
  assert.equal(app.url.href, "https://ax.to/nmr?type=clock");
  assert.equal(app.elements["#main-link"].href, "https://ax.to/nmr?name=one+love");
  app.click("#main-link");
  assert.equal(app.url.href, "https://ax.to/nmr?name=one+love");
  assert.equal(app.elements["#clock-view"].hidden, true);
  app.back();
  assert.equal(app.elements["#clock-view"].hidden, false);
  app.forward();
  assert.equal(app.elements["#main-view"].hidden, false);
  assert.equal(app.document.title, "nmr");
});

test("modified link clicks retain native browser behavior", () => {
  for (const modifiers of [{ ctrlKey: true }, { metaKey: true }, { shiftKey: true }, { altKey: true }, { button: 1 }]) {
    const app = navigation("https://ax.to/nmr?desc=Tom");
    assert.equal(app.click("#clock-link", modifiers), false);
    assert.equal(app.url.search, "?desc=Tom");
  }
});
