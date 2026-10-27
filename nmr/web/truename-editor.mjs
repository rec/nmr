/* A vocabulary-only cursor: accepted text followed by one suggested word. */
export class TruenameEditor {
  constructor(words) {
    this.words = words;
    this.prefix = "";
    this.typed = "";
    this.choice = "";
    this.suggest();
  }
  get current() {
    return this.typed.slice(this.typed.lastIndexOf(" ") + 1);
  }
  get options() {
    const used = new Set(this.typed.slice(0, this.typed.lastIndexOf(" ") + 1).split(" "));
    return this.words.filter((word) => !used.has(word) && word.startsWith(this.current));
  }
  get guessed() {
    return this.choice.slice(this.current.length);
  }
  get text() {
    return this.prefix + this.typed;
  }
  get accepted() {
    const words = this.typed.slice(0, this.typed.lastIndexOf(" ") + 1).trimEnd();
    return words ? this.prefix + words : "";
  }
  suggest() {
    const options = this.options;
    if (!options.includes(this.choice)) this.choice = options[Math.floor(Math.random() * options.length)] || "";
  }
  load(value) {
    const colon = value.lastIndexOf(":");
    const prefix = value.slice(0, colon + 1).trim().toLowerCase();
    if (!/^(?::)?(?:[a-z]+:)*$/.test(prefix)) return false;
    const tokens = value.slice(colon + 1).trim().toLowerCase().split(/\s+/).filter(Boolean);
    const used = new Set();
    for (const word of tokens.slice(0, -1)) {
      if (!this.words.includes(word) || used.has(word)) return false;
      used.add(word);
    }
    const current = tokens.at(-1) || "";
    if (current && !this.words.some((word) => word.startsWith(current) && !used.has(word))) return false;
    this.prefix = prefix ? prefix + " " : "";
    this.typed = tokens.join(" ");
    this.choice = "";
    if (this.words.includes(current)) this.typed += " ";
    this.suggest();
    return true;
  }
  accept() {
    if (!this.choice) return false;
    this.typed += this.guessed + " ";
    this.choice = "";
    this.suggest();
    return true;
  }
  type(character) {
    if (character === " ") return this.accept();
    if (!/^[a-z]$/.test(character)) return false;
    const next = this.current + character;
    if (!this.options.some((word) => word.startsWith(next))) return false;
    this.typed += character;
    this.suggest();
    if (this.current === this.choice) this.accept();
    return true;
  }
  right() {
    if (!this.choice) return false;
    this.typed += this.guessed[0];
    while (this.current !== this.choice) {
      const options = this.options;
      const next = options[0][this.current.length];
      if (!next || !options.every((word) => word[this.current.length] === next)) break;
      this.typed += next;
    }
    if (this.current === this.choice) this.accept();
    return true;
  }
  left() {
    if (!this.typed) return false;
    if (this.typed.endsWith(" ")) {
      this.typed = this.typed.slice(0, -1);
      this.choice = this.current;
    }
    do {
      this.typed = this.typed.slice(0, -1);
      if (!this.current) break;
      const next = new Set(this.options.map((word) => word[this.current.length]));
      if (next.size > 1) break;
    } while (this.current);
    return true;
  }
  cycle(direction) {
    const options = this.options;
    if (!options.length) return false;
    this.choice = options[(options.indexOf(this.choice) + direction + options.length) % options.length];
    if (this.current && this.current === this.choice) this.accept();
    return true;
  }
}
