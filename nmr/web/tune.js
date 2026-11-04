/* Exact pitches and times come from the shared Python core. */
const masterOutputs = new Map();
let masterGain = 10 ** (-20 / 20);

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
    this.input = this.context.createGain();
    this.brightInput = this.context.createGain();
    // Explicit coefficients avoid the native sawtooth's peak normalization,
    // which otherwise makes it quieter than a triangle of the same RMS level.
    this.brightWave = this.context.createPeriodicWave(
      new Float32Array(2049),
      Float32Array.from({ length: 2049 }, (_, n) => n ? 2 * (n % 2 ? 1 : -1) / (Math.PI * n) : 0),
      { disableNormalization: true },
    );
    this.dry = this.context.createGain();
    this.evolved = this.context.createGain();
    this.dry.gain.value = 0;
    // StereoPanner splits a mono signal between two channels at equal power;
    // the plain mono path is copied at full level to each destination channel.
    this.evolved.gain.value = Math.SQRT2;
    this.input.connect(this.dry).connect(this.output);
    const warm = this.context.createGain();
    const bright = this.context.createGain();
    warm.gain.value = 0;
    bright.gain.value = 0;
    const timbre = this.context.createOscillator();
    timbre.frequency.value = 1 / 12;
    // Triangle and sawtooth have equal RMS and a correlation of 3/4.
    // Compensate their overlap so the blend keeps the plain tone's RMS level.
    for (const [parameter, side] of [[warm.gain, 0], [bright.gain, 1]]) {
      const shape = this.context.createWaveShaper();
      shape.curve = Float32Array.from({ length: 1025 }, (_, i) => {
        const mix = 0.05 + 0.9 * i / 1024;
        const level = Math.sqrt((1 - mix) ** 2 + mix ** 2 + 1.5 * mix * (1 - mix));
        return (side ? mix : 1 - mix) / level;
      });
      timbre.connect(shape).connect(parameter);
    }
    timbre.start();
    const pan = this.context.createStereoPanner();
    const delay = this.context.createDelay(1);
    delay.delayTime.value = 0.19;
    const echo = this.context.createGain();
    echo.gain.value = 0.05;
    const feedback = this.context.createGain();
    feedback.gain.value = 0.12;
    this.input.connect(warm).connect(pan).connect(this.evolved).connect(this.output);
    this.brightInput.connect(bright).connect(pan);
    pan.connect(delay).connect(echo).connect(this.evolved);
    delay.connect(feedback).connect(delay);
    // These audio-clock modulations run continuously across tune boundaries.
    for (const [parameter, period, depth] of [[pan.pan, 47, 0.2], [echo.gain, 173, 0.025]]) {
      const oscillator = this.context.createOscillator();
      const amount = this.context.createGain();
      oscillator.frequency.value = 1 / period;
      amount.gain.value = depth;
      oscillator.connect(amount).connect(parameter);
      oscillator.start();
    }
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
  setEvolution(enabled) {
    const now = this.context.currentTime;
    for (const [parameter, target] of [[this.dry.gain, enabled ? 0 : 1], [this.evolved.gain, enabled ? Math.SQRT2 : 0]]) {
      const level = parameter.value;
      parameter.cancelScheduledValues(now);
      parameter.setValueAtTime(level, now);
      parameter.linearRampToValueAtTime(target, now + 0.5);
    }
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
      // Both sources keep running so Evolve also switches during held notes.
      for (const [type, input] of [["triangle", this.input], ["sawtooth", this.brightInput]]) {
        const voice = this.context.createOscillator();
        const gain = this.context.createGain();
        const onset = start + event.onset;
        const end = onset + event.duration;
        const edge = Math.min(0.005, event.duration / 4);
        voice.type = type;
        if (type === "sawtooth") voice.setPeriodicWave(this.brightWave);
        voice.frequency.value = 440 * 2 ** ((event.pitch - 69) / 12);
        gain.gain.setValueAtTime(0, onset);
        gain.gain.linearRampToValueAtTime(1, onset + edge);
        gain.gain.setValueAtTime(1, end - edge);
        gain.gain.linearRampToValueAtTime(0, end);
        voice.connect(gain).connect(input);
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
}
