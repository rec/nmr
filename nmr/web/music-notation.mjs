const timelines = new WeakMap();

export function highlightScore(container, seconds, bpm = 180) {
  const timeline = timelines.get(container.firstElementChild);
  if (!timeline) return;
  const beat = seconds === null ? -1 : seconds * bpm / 60;
  const current = timeline.symbols.find((i) => beat >= i.start && beat < i.end)?.element;
  if (current === timeline.active) return;
  timeline.active?.classList.toggle("playing-symbol", false);
  current?.classList.toggle("playing-symbol", true);
  timeline.active = current;
}

/* VexFlow 5.0.0, locally bundled with Bravura and Academico. */
export function drawScore(container, score) {
  const frame = document.createElement("div");
  frame.className = "music-score";
  frame.setAttribute("aria-label", `Music notation in ${score.top}/${score.bottom}`);
  container.append(frame);
  return Promise.resolve(document.fonts?.ready).then(() => {
    if (container.firstElementChild !== frame) return;
    const vf = globalThis.VexFlow;
    const widths = score.measures.map((i, index) => Math.max(180, i.length * 65 + (index ? 35 : 130 + score.top.length * 20)));
    const renderer = new vf.Renderer(frame, vf.Renderer.Backends.SVG);
    const pitches = score.measures.flat().filter((i) => i.pitch !== null).map((i) =>
      7 * (Math.floor(i.pitch / 12) - 1) + [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6][i.pitch % 12]);
    const bottomLine = score.clef === "bass" ? 18 : 30;
    const above = Math.max(0, Math.max(...pitches) - bottomLine - 8) * 5;
    const below = Math.max(0, bottomLine - Math.min(...pitches)) * 5;
    renderer.resize(widths.reduce((a, b) => a + b, 20), 200 + above + below);
    const context = renderer.getContext();
    const timeline = [];
    timelines.set(frame, { symbols: timeline, active: null });
    let beat = 0;
    const ties = [];
    const previous = new Map();
    let x = 10;
    for (const [index, measure] of score.measures.entries()) {
      const stave = new vf.Stave(x, 40 + above, widths[index]);
      if (!index) stave.addClef(score.clef).addTimeSignature(`${score.top}/${score.bottom}`);
      stave.setContext(context).draw();
      const notes = measure.map((i) => {
        const names = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"];
        const key = i.pitch === null ? (score.clef === "bass" ? "d/3" : "b/4") : `${names[i.pitch % 12]}/${Math.floor(i.pitch / 12) - 1}`;
        const note = new vf.StaveNote({ clef: score.clef, keys: [key], duration: i.glyph + "d".repeat(i.dots) + (i.pitch === null ? "r" : "") });
        for (let dot = 0; dot < i.dots; dot++) vf.Dot.buildAndAttach([note], { all: true });
        if (i.tie) ties.push(new vf.StaveTie({ firstNote: previous.get(i.attack), lastNote: note, firstIndexes: [0], lastIndexes: [0] }));
        if (i.pitch !== null) previous.set(i.attack, note);
        return note;
      });
      const tuplets = [];
      for (let first = 0; first < notes.length;) {
        const ratio = measure[first].ratio;
        let end = first + 1;
        while (end < notes.length && end - first < ratio[0] && measure[end].ratio[0] === ratio[0] && measure[end].ratio[1] === ratio[1]) end++;
        if (ratio[0] !== ratio[1]) tuplets.push(new vf.Tuplet(notes.slice(first, end), { numNotes: ratio[0], notesOccupied: ratio[1], bracketed: true, ratioed: true }));
        first = end;
      }
      const voice = new vf.Voice().setMode(vf.Voice.Mode.SOFT).addTickables(notes);
      vf.Accidental.applyAccidentals([voice], "C");
      new vf.Formatter().joinVoices([voice]).formatToStave([voice], stave);
      voice.draw(context, stave);
      for (const [index, note] of notes.entries()) {
        const [numerator, denominator = 1] = measure[index].duration.split("/").map(Number);
        const end = beat + numerator / denominator;
        timeline.push({ element: note.getSVGElement(), start: beat, end });
        beat = end;
      }
      for (const tuplet of tuplets) tuplet.setContext(context).draw();
      x += widths[index];
    }
    for (const tie of ties) tie.setContext(context).draw();
  }).catch((error) => {
    if (container.firstElementChild !== frame) return;
    frame.textContent = `Notation unavailable: ${error.message}`;
    console.error(error);
  });
}
