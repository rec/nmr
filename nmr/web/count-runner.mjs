/* A Run toggle controls future iterations, never an already playing tune. */
export class CountRunner {
  constructor(play, advance, onError, schedule = setTimeout, cancel = clearTimeout) {
    this.play = play;
    this.advance = advance;
    this.onError = onError;
    this.schedule = schedule;
    this.cancel = cancel;
    this.running = false;
    this.playing = null;
    this.timer = null;
    this.advanceNext = true;
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
  }
  step() {
    this.playing = Promise.resolve().then(() => this.play());
    this.playing.then(() => {
      this.playing = null;
      if (!this.running) return;
      this.timer = this.schedule(() => {
        this.timer = null;
        if (!this.running) return;
        if (this.advanceNext) this.advance();
        this.advanceNext = true;
        this.step();
      }, 2000);
    }, (error) => {
      this.playing = null;
      this.stop();
      this.onError(error);
    });
  }
}
