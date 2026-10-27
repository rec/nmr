/* Exact pitches and times come from the shared Python core. */
const outputGain = 10 ** (6 / 20);

export class TunePlayer {
  constructor(onEnded = () => {}) {
    this.onEnded = onEnded;
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
  get playing() {
    return this.voices.size > 0;
  }
  tick(pitch = 53) {
    const voice = this.context.createOscillator();
    const gain = this.context.createGain();
    const start = this.context.currentTime;
    voice.type = "triangle";
    voice.frequency.value = 440 * 2 ** ((pitch - 69) / 12);
    gain.gain.setValueAtTime(0.025 * outputGain, start);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.020);
    voice.connect(gain).connect(this.context.destination);
    voice.onended = () => { voice.disconnect(); gain.disconnect(); };
    voice.start(start);
    voice.stop(start + 0.020);
  }
  stop() {
    for (const voice of this.voices) voice.stop();
    this.voices.clear();
    this.onEnded();
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
      gain.gain.linearRampToValueAtTime(0.15 * outputGain, onset + edge);
      gain.gain.setValueAtTime(0.15 * outputGain, end - edge);
      gain.gain.linearRampToValueAtTime(0, end);
      voice.connect(gain).connect(this.context.destination);
      voice.onended = () => {
        voice.disconnect();
        gain.disconnect();
        this.voices.delete(voice);
        if (!this.playing) this.onEnded();
      };
      voice.start(onset);
      voice.stop(end);
      this.voices.add(voice);
    }
  }
}
