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
    this.harmonicInputs = [this.context.createGain(), this.context.createGain()];
    // Keep the triangle's fundamental and remaining harmonic power as fixed
    // budgets; only redistribute the latter between disjoint harmonic sets.
    const fundamental = 8 / Math.PI ** 2;
    const harmonic = Math.sqrt(2 / 3 - fundamental ** 2);
    const pure = new Float32Array(17);
    pure[1] = fundamental;
    const odd = Float32Array.from({ length: 17 }, (_, n) => n >= 3 && n % 2 ? (-1) ** ((n - 1) / 2) / n ** 2 : 0);
    const even = Float32Array.from({ length: 17 }, (_, n) => n >= 2 && !(n % 2) ? 1 / n ** 2 : 0);
    for (const coefficients of [odd, even]) {
      const scale = harmonic / Math.hypot(...coefficients);
      for (let n = 0; n < coefficients.length; n++) coefficients[n] *= scale;
    }
    this.waves = [pure, odd, even].map(coefficients => this.context.createPeriodicWave(
      new Float32Array(17), coefficients, { disableNormalization: true },
    ));
    this.dry = this.context.createGain();
    this.evolved = this.context.createGain();
    this.dry.gain.value = 0;
    // StereoPanner splits a mono signal between two channels at equal power;
    // the plain mono path is copied at full level to each destination channel.
    this.evolved.gain.value = Math.SQRT2;
    this.input.connect(this.dry).connect(this.output);
    const timbre = this.context.createOscillator();
    timbre.frequency.value = 1 / 12;
    this.timbreAmount = this.context.createGain();
    this.timbreOffset = this.context.createConstantSource();
    this.timbreOffset.offset.value = 0;
    timbre.connect(this.timbreAmount);
    // Odd and even harmonic sets do not overlap. cos² + sin² keeps their
    // combined energy constant, independently of the steady fundamental.
    for (const [side, input] of this.harmonicInputs.entries()) {
      const blend = this.context.createGain();
      blend.gain.value = 0;
      const shape = this.context.createWaveShaper();
      shape.curve = Float32Array.from({ length: 1025 }, (_, i) => {
        const angle = Math.PI / 2 * i / 1024;
        return side ? Math.sin(angle) : Math.cos(angle);
      });
      this.timbreAmount.connect(shape).connect(blend.gain);
      this.timbreOffset.connect(shape);
      input.connect(blend).connect(this.input);
    }
    timbre.start();
    this.timbreOffset.start();
    const pan = this.context.createStereoPanner();
    const delay = this.context.createDelay(1);
    delay.delayTime.value = 0.19;
    const echo = this.context.createGain();
    echo.gain.value = 0.025;
    const feedback = this.context.createGain();
    feedback.gain.value = 0.12;
    this.input.connect(pan).connect(this.evolved).connect(this.output);
    pan.connect(delay).connect(echo).connect(this.evolved);
    delay.connect(feedback).connect(delay);
    // These audio-clock modulations run continuously across tune boundaries.
    for (const [parameter, period, depth] of [[pan.pan, 47, 0.2], [echo.gain, 173, 0.0125]]) {
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
    for (const [parameter, target] of [[this.dry.gain, enabled ? 0 : 1], [this.evolved.gain, enabled ? Math.SQRT2 : 0], [this.timbreAmount.gain, enabled ? 1 : 0], [this.timbreOffset.offset, enabled ? 0 : -1]]) {
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
      // All three sources share the original timing and amplitude envelope.
      for (const [index, input] of [this.input, ...this.harmonicInputs].entries()) {
        const voice = this.context.createOscillator();
        const gain = this.context.createGain();
        const onset = start + event.onset;
        const end = onset + event.duration;
        const edge = Math.min(0.005, event.duration / 4);
        voice.setPeriodicWave(this.waves[index]);
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
