/* A deliberately small Markdown subset, rendered as text and DOM nodes. */
const panel = document.querySelector("#help-panel");
let loaded = false;

function inline(parent, text) {
  const tokens = /\[([^\]]+)\]\(([^\s)]+)\)|\*\*(.+?)\*\*(?!\*)|\*([^*]+)\*/g;
  let end = 0;
  for (const match of text.matchAll(tokens)) {
    parent.append(document.createTextNode(text.slice(end, match.index)));
    const element = document.createElement(match[1] ? "a" : match[3] ? "strong" : "em");
    if (match[1]) {
      try {
        const url = new URL(match[2], window.location.href);
        if (["http:", "https:", "mailto:"].includes(url.protocol)) element.href = url.href;
      } catch (error) {
        if (!(error instanceof TypeError)) throw error;
      }
    }
    inline(element, match[1] || match[3] || match[4]);
    parent.append(element);
    end = match.index + match[0].length;
  }
  parent.append(document.createTextNode(text.slice(end)));
}

function render(text) {
  panel.replaceChildren();
  let paragraph = null;
  for (const line of text.split(/\r?\n/)) {
    const heading = /^(#{1,2})\s+(.+)$/.exec(line);
    if (heading) {
      const element = document.createElement(`h${heading[1].length}`);
      inline(element, heading[2]);
      panel.append(element);
      paragraph = null;
    } else if (!line.trim()) paragraph = null;
    else {
      if (!paragraph) {
        paragraph = document.createElement("p");
        panel.append(paragraph);
      } else paragraph.append(document.createTextNode(" "));
      inline(paragraph, line);
    }
  }
}

panel.addEventListener("beforetoggle", (event) => {
  if (event.newState !== "open" || loaded) return;
  loaded = true;
  fetch(new URL("./help.md", import.meta.url)).then((response) => {
    if (!response.ok) throw new Error(`Help could not be loaded (${response.status}).`);
    return response.text();
  }).then(render).catch((error) => {
    panel.textContent = "Help could not be loaded.";
    console.error(error);
  });
});
