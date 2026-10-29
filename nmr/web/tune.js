/* Exact pitches and times come from the shared Python core. */
const masterOutputs = new Map();
let masterGain = 10 ** (-30 / 20);

export function setMasterVolume(level) {
  masterGain = level === 0 ? 0 : 10 ** ((level - 120) / 20);
  for (const [context, output] of masterOutputs) {
    const now = context.currentTime;
    const current = output.gain.value;
    output.gain.cancelScheduledValues(now);
    output.gain.setValueAtTime(current, now);
    output.gain.linearRampToValueAtTime(masterGain, now + 0.02);
  }
}

export class TunePlayer {
  constructor(onEnded = () => {}, onPosition = null) {
    this.onPosition = onPosition;
    this.animation = null;
    this.onEnded = onEnded;
    this.context = new AudioContext();
    const master = this.context.createGain();
    master.gain.value = masterGain;
    master.connect(this.context.destination);
    masterOutputs.set(this.context, master);
    this.output = this.context.createGain();
    this.output.connect(master);
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
  setVolume(volume, seconds) {
    const now = this.context.currentTime;
    const level = this.output.gain.value;
    this.output.gain.cancelScheduledValues(now);
    this.output.gain.setValueAtTime(level, now);
    this.output.gain.linearRampToValueAtTime(volume, now + seconds);
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
    gain.gain.setValueAtTime(0.05, start);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.020);
    voice.connect(gain).connect(this.output);
    voice.onended = () => { voice.disconnect(); gain.disconnect(); };
    voice.start(start);
    voice.stop(start + 0.020);
  }
  stop() {
    cancelAnimationFrame(this.animation);
    this.onPosition?.(null);
    for (const voice of this.voices) voice.stop();
    this.voices.clear();
    this.onEnded();
  }
  play(events) {
    this.introPlayed = true;
    this.stop();
    const start = this.context.currentTime + 0.05;
    if (this.onPosition && events.length) {
      const update = () => {
        this.onPosition(this.context.currentTime - start);
        this.animation = requestAnimationFrame(update);
      };
      this.animation = requestAnimationFrame(update);
    }
    for (const event of events) {
      const voice = this.context.createOscillator();
      const gain = this.context.createGain();
      const onset = start + event.onset;
      const end = onset + event.duration;
      const edge = Math.min(0.005, event.duration / 4);
      voice.type = "triangle";
      voice.frequency.value = 440 * 2 ** ((event.pitch - 69) / 12);
      gain.gain.setValueAtTime(0, onset);
      gain.gain.linearRampToValueAtTime(1, onset + edge);
      gain.gain.setValueAtTime(1, end - edge);
      gain.gain.linearRampToValueAtTime(0, end);
      voice.connect(gain).connect(this.output);
      voice.onended = () => {
        voice.disconnect();
        gain.disconnect();
        this.voices.delete(voice);
        if (!this.playing) {
          cancelAnimationFrame(this.animation);
          this.onPosition?.(null);
          this.onEnded();
        }
      };
      voice.start(onset);
      voice.stop(end);
      this.voices.add(voice);
    }
  }
}
