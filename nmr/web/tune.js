/* Exact pitches and times come from the shared Python core. */
export class TunePlayer {
  constructor() {
    this.context = new AudioContext();
    this.voices = new Set();
    this.intro = null;
    this.introPlayed = false;
    this.context.addEventListener("statechange", () => this.startIntro());
  }
  setIntro(events) {
    this.intro = events;
    this.startIntro();
  }
  startIntro() {
    if (this.intro && !this.introPlayed && this.context.state === "running") {
      this.introPlayed = true;
      this.play(this.intro);
    }
  }
  unlock() {
    return this.context.resume();
  }
  stop() {
    for (const voice of this.voices) voice.stop();
    this.voices.clear();
  }
  play(events) {
    this.introPlayed = true;
    this.stop();
    const start = this.context.currentTime + 0.05;
    for (const event of events) {
      const voice = this.context.createOscillator();
      const gain = this.context.createGain();
      const onset = start + event.onset;
      const end = onset + event.duration;
      const edge = Math.min(0.005, event.duration / 4);
      voice.type = "triangle";
      voice.frequency.value = 440 * 2 ** ((event.pitch - 69) / 12);
      gain.gain.setValueAtTime(0, onset);
      gain.gain.linearRampToValueAtTime(0.15, onset + edge);
      gain.gain.setValueAtTime(0.15, end - edge);
      gain.gain.linearRampToValueAtTime(0, end);
      voice.connect(gain).connect(this.context.destination);
      voice.onended = () => {
        voice.disconnect();
        gain.disconnect();
        this.voices.delete(voice);
      };
      voice.start(onset);
      voice.stop(end);
      this.voices.add(voice);
    }
  }
}
