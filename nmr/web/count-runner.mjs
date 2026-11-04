/* Mode changes stop the runner; transport pause retains its next iteration. */
export class CountRunner {
  constructor(play, advance, onError, schedule = (callback, delay) => setTimeout(callback, delay), cancel = (timer) => clearTimeout(timer)) {
    this.play = play;
    this.advance = advance;
    this.onError = onError;
    this.schedule = schedule;
    this.cancel = cancel;
    this.running = false;
    this.playing = null;
    this.timer = null;
    this.advanceNext = true;
    this.paused = false;
    this.pending = null;
  }
  start() {
    if (this.running) return;
    this.running = true;
    if (this.playing) this.advanceNext = false;
    else {
      this.advanceNext = true;
      this.step();
    }
  }
  stop() {
    this.running = false;
    this.cancel(this.timer);
    this.timer = null;
    this.paused = false;
    this.pending = null;
  }
  pause() {
    this.paused = true;
  }
  resume() {
    this.paused = false;
    const pending = this.pending;
    this.pending = null;
    pending?.();
  }
  step() {
    this.playing = Promise.resolve().then(() => this.play());
    this.playing.then(() => {
      this.playing = null;
      if (!this.running) return;
      const next = () => {
        this.timer = null;
        if (!this.running) return;
        if (this.paused) { this.pending = next; return; }
        if (this.advanceNext) this.advance();
        this.advanceNext = true;
        this.step();
      };
      this.timer = this.schedule(next, 2000);
    }, (error) => {
      this.playing = null;
      this.stop();
      this.onError(error);
    });
  }
}
