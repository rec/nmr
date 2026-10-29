import { describeObject } from "./description.mjs";
import { drawScore } from "./music-notation.mjs";

export class ValueDisplay {
  constructor(container, onAction) {
    this.container = container;
    this.onAction = onAction;
    this.worldMap = null;
    this.marker = null;
  }
  clear(keepMap = false) {
    if (keepMap && this.worldMap && this.container.firstElementChild === this.worldMap) {
      this.marker.setAttribute("visibility", "hidden");
    } else this.container.replaceChildren();
    this.container.inert = false;
  }
  show(value) {
    if (value?.kind === "latlong") {
      this.map(value);
      return;
    }
    this.clear();
    if (!value) return;
    if (value.kind === "chess") this.chess(value);
    else if (value.kind === "go") this.go(value);
    else if (value.kind === "cards") this.cards(value);
    else if (value.kind === "tune") {
      if (value.error) this.container.append(node("p", value.error));
      else drawScore(this.container, value.score);
    }
    else this.container.append(node("pre", describeObject(value), "value-text"));
  }
  controls(value) {
    const controls = node("div", "", "value-board-controls");
    controls.append(node("span", value.terminal ? "Play ended" : `${value.turn} to move`));
    const undo = node("button", "Undo");
    undo.type = "button";
    undo.disabled = !value.undo;
    undo.addEventListener("click", () => this.onAction({ action: "undo" }));
    controls.append(undo);
    return controls;
  }
  chess(value, selected = null) {
    this.container.replaceChildren();
    const layout = node("div", "", "value-board-layout");
    const board = node("div", "", "chess-board");
    board.setAttribute("aria-label", "Chess board");
    const controls = this.controls(value);
    for (let row = 7; row >= 0; row--) for (let column = 0; column < 8; column++) {
      const square = "abcdefgh"[column] + (row + 1);
      const piece = value.board[row * 8 + column];
      const moves = selected ? value.moves.filter((i) => i.startsWith(selected + square)) : [];
      const button = node("button", CHESS_PIECES[piece] || "", `chess-square ${(row + column) % 2 ? "light" : "dark"}`);
      button.type = "button";
      button.setAttribute("aria-label", `${square}${piece ? " " + (piece === piece.toUpperCase() ? "White " : "Black ") + PIECE_NAMES[piece.toLowerCase()] : ""}`);
      button.setAttribute("aria-pressed", String(square === selected));
      button.title = square;
      button.classList.toggle("selected", square === selected);
      button.classList.toggle("legal-target", moves.length > 0);
      button.disabled = !moves.length && !value.moves.some((i) => i.startsWith(square));
      button.addEventListener("click", () => {
        if (moves.length === 1) this.onAction({ action: "move", move: moves[0] });
        else if (moves.length > 1) {
          controls.replaceChildren(node("span", "Promote to"));
          for (const move of moves) {
            const promote = node("button", PROMOTIONS[move[4]]);
            promote.type = "button";
            promote.addEventListener("click", () => this.onAction({ action: "move", move }));
            controls.append(promote);
          }
        } else this.chess(value, square === selected ? null : square);
      });
      board.append(button);
    }
    layout.append(board, controls);
    this.container.append(layout);
  }
  go(value) {
    const layout = node("div", "", "value-board-layout");
    const board = node("div", "", "go-board");
    board.setAttribute("aria-label", "Go board");
    board.style.setProperty("--size", value.size);
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", `0 0 ${value.size} ${value.size}`);
    svg.setAttribute("aria-hidden", "true");
    for (let i = 0; i < value.size; i++) {
      for (const coordinates of [[0.5, i + 0.5, value.size - 0.5, i + 0.5], [i + 0.5, 0.5, i + 0.5, value.size - 0.5]]) {
        const line = document.createElementNS(svg.namespaceURI, "line");
        for (const [j, name] of ["x1", "y1", "x2", "y2"].entries()) line.setAttribute(name, coordinates[j]);
        svg.append(line);
      }
    }
    const edge = value.size === 9 ? 2 : 3;
    for (const row of [edge, (value.size - 1) / 2, value.size - 1 - edge]) {
      for (const column of [edge, (value.size - 1) / 2, value.size - 1 - edge]) {
        if (value.size !== 19 && (row === (value.size - 1) / 2) !== (column === (value.size - 1) / 2)) continue;
        const star = document.createElementNS(svg.namespaceURI, "circle");
        star.setAttribute("cx", column + 0.5);
        star.setAttribute("cy", row + 0.5);
        star.setAttribute("r", "0.09");
        svg.append(star);
      }
    }
    board.append(svg);
    for (let row = value.size - 1; row >= 0; row--) for (let column = 0; column < value.size; column++) {
      const move = "ABCDEFGHJKLMNOPQRST"[column] + (row + 1);
      const stone = value.board[row * value.size + column];
      const button = node("button", "", "go-point");
      button.type = "button";
      button.title = move;
      button.setAttribute("aria-label", `${move}${stone ? stone === 1 ? " Black" : " White" : ""}`);
      button.disabled = !value.moves.includes(move);
      if (stone) button.append(node("span", "", `go-stone ${stone === 1 ? "black" : "white"}`));
      button.addEventListener("click", () => this.onAction({ action: "move", move }));
      board.append(button);
    }
    const controls = this.controls(value);
    const pass = node("button", "Pass");
    pass.type = "button";
    pass.disabled = !value.moves.includes("pass");
    pass.addEventListener("click", () => this.onAction({ action: "move", move: "pass" }));
    controls.append(pass);
    layout.append(board, controls);
    this.container.append(layout);
  }
  cards(value, selected = null) {
    const previous = this.container.firstElementChild;
    const left = previous?.scrollLeft || 0;
    const top = previous?.scrollTop || 0;
    this.container.replaceChildren();
    const layout = node("div", "", "card-layout");
    layout.append(node("p", selected === null ? "Select two cards to interchange them." : "Select the other card."));
    const cards = node("div", "", "card-deck");
    for (const [position, card] of value.cards.entries()) {
      const suit = Math.floor(card / 13);
      const label = CARD_RANKS[card % 13] + "♣♦♥♠"[suit];
      const button = node("button", label, `deck-card${suit === 1 || suit === 2 ? " red" : ""}`);
      button.type = "button";
      button.title = `Position ${position + 1}: ${label}`;
      button.setAttribute("aria-pressed", String(position === selected));
      button.addEventListener("click", () => {
        if (selected === null || selected === position) this.cards(value, selected === position ? null : position);
        else this.onAction({ action: "swap", first: selected, second: position });
      });
      cards.append(button);
    }
    layout.append(cards);
    this.container.append(layout);
    layout.scrollLeft = left;
    layout.scrollTop = top;
  }
  map(value) {
    if (!this.worldMap) {
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("viewBox", "-4 -4 368 188");
      svg.setAttribute("class", "world-map");
      svg.setAttribute("role", "img");
      const image = document.createElementNS(svg.namespaceURI, "image");
      image.setAttribute("href", "world-map.svg");
      image.setAttribute("width", "360");
      image.setAttribute("height", "180");
      this.marker = document.createElementNS(svg.namespaceURI, "circle");
      this.marker.setAttribute("class", "world-map-marker");
      this.marker.setAttribute("r", "2.5");
      svg.append(image, this.marker);
      this.worldMap = svg;
    }
    this.marker.setAttribute("cx", value.longitude + 180);
    this.marker.setAttribute("cy", 90 - value.latitude);
    this.marker.setAttribute("visibility", "visible");
    this.worldMap.setAttribute("aria-label", `World map: ${value.latitude}, ${value.longitude}`);
    this.container.inert = false;
    if (this.container.firstElementChild !== this.worldMap) this.container.replaceChildren(this.worldMap);
  }
}

function node(tag, text = "", className = "") {
  const element = document.createElement(tag);
  element.textContent = text;
  element.className = className;
  return element;
}

const CHESS_PIECES = { K: "♔", Q: "♕", R: "♖", B: "♗", N: "♘", P: "♙", k: "♚", q: "♛", r: "♜", b: "♝", n: "♞", p: "♟" };
const PIECE_NAMES = { k: "king", q: "queen", r: "rook", b: "bishop", n: "knight", p: "pawn" };
const PROMOTIONS = { q: "Queen", r: "Rook", b: "Bishop", n: "Knight" };
const CARD_RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"];
