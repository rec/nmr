/* The page owns text and selection; the Python core recognizes the whole input. */
export class Editor {
  constructor() {
    this.text = "";
    this.anchor = 0;
    this.cursor = 0;
  }
  replace(value) {
    const start = Math.min(this.anchor, this.cursor);
    const end = Math.max(this.anchor, this.cursor);
    const replacingAll = start === 0 && end === this.text.length;
    if (!replacingAll && this.text.trimStart().startsWith("+") &&
        /[0-9]/.test(this.text) && /\p{L}/u.test(value)) return false;
    this.text = this.text.slice(0, start) + value.replace(/[\r\n]+/g, " ") + this.text.slice(end);
    this.anchor = this.cursor = start + value.replace(/[\r\n]+/g, " ").length;
    return true;
  }
  move(position, extend = false) {
    this.cursor = Math.max(0, Math.min(this.text.length, position));
    if (!extend) this.anchor = this.cursor;
  }
  boundary(direction, word = false) {
    if (direction < 0) {
      const before = this.text.slice(0, this.cursor);
      const size = word ? (before.match(/\S*\s*$/)?.[0].length || 0) : ([...before].pop()?.length || 0);
      return this.cursor - size;
    }
    const after = this.text.slice(this.cursor);
    const size = word ? (after.match(/^\s*\S*/)?.[0].length || 0) : ([...after][0]?.length || 0);
    return this.cursor + size;
  }
  erase(direction, word = false) {
    if (this.anchor === this.cursor) this.anchor = this.boundary(direction, word);
    this.replace("");
  }
  selectAll() {
    this.anchor = 0;
    this.cursor = this.text.length;
  }
  selection() {
    return this.text.slice(Math.min(this.anchor, this.cursor), Math.max(this.anchor, this.cursor));
  }
  clear() {
    this.selectAll();
    this.replace("");
  }
}
