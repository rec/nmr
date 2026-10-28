import assert from "node:assert/strict";
import test from "node:test";
import { clockReading } from "../nmr/web/clock-time.mjs";

test("formats local time with leading zeros and handles midnight", () => {
  for (const [hour, minute, second, expected] of [
    [0, 0, 0, "00:00:00"], [9, 4, 3, "09:04:03"], [23, 59, 59, "23:59:59"],
  ]) {
    const date = new Date(2026, 9, 28, hour, minute, second, 999);
    date.getTimezoneOffset = () => 0;
    const reading = clockReading(date, 10);
    assert.equal(reading.displayTime, expected);
    assert.equal(reading.second, Math.floor(date.getTime() / 1000));
  }
});

test("intervals use UTC wall-clock boundaries throughout the day", () => {
  for (const interval of [5, 10, 60, 3600]) {
    for (const hour of [0, 9, 23]) {
      const due = [];
      for (let second = 0; second < 3600; second++) {
        const reading = clockReading(new Date(Date.UTC(2026, 9, 28, hour, 0, second)), interval);
        if (reading.due) due.push(second);
      }
      assert.deepEqual(due, Array.from({ length: 3600 / interval }, (_, i) => i * interval));
    }
  }
});

test("default DateTime names use UTC while the display uses the local date and time", () => {
  const date = new Date("2026-01-01T00:30:45.999Z");
  Object.assign(date, {
    getFullYear: () => 2025, getMonth: () => 11, getDate: () => 31,
    getHours: () => 19, getMinutes: () => 30, getSeconds: () => 45,
    getTimezoneOffset: () => 300,
  });
  const local = clockReading(date, 10);
  assert.equal(local.type, "datetime");
  assert.equal(local.value, "2026-01-01T00:30:45");
  assert.equal(local.displayDate, "2025-12-31");
  assert.equal(local.displayTime, "19:30:45");
  const utc = clockReading(date, 10, false, true);
  assert.equal(utc.value, local.value);
  assert.equal(utc.displayDate, "2026-01-01");
  assert.equal(utc.displayTime, "00:30:45");
});

test("Time only keeps the displayed date and names only the UTC time", () => {
  const date = new Date("2026-01-01T00:30:45.999Z");
  Object.assign(date, {
    getFullYear: () => 2026, getMonth: () => 0, getDate: () => 1,
    getHours: () => 6, getMinutes: () => 15, getSeconds: () => 45,
    getTimezoneOffset: () => -345,
  });
  const local = clockReading(date, 10, true);
  const utc = clockReading(date, 10, true, true);
  assert.equal(local.type, "time");
  assert.equal(local.value, "00:30:45");
  assert.equal(local.displayDate, "2026-01-01");
  assert.equal(local.displayTime, "06:15:45");
  assert.equal(utc.value, local.value);
  assert.equal(utc.displayDate, "2026-01-01");
  assert.equal(utc.displayTime, "00:30:45");
});

test("offsets omit minutes only for whole hours, with the correct sign", () => {
  for (const [offset, suffix] of [
    [0, "+00"], [-60, "+01"], [60, "-01"],
    [-90, "+01:30"], [210, "-03:30"], [-345, "+05:45"], [30, "-00:30"],
  ]) {
    const date = new Date("2026-01-01T00:30:45Z");
    date.getTimezoneOffset = () => offset;
    const hidden = clockReading(date, 10);
    const shown = clockReading(date, 10, false, false, true);
    assert.equal(shown.displayTime, hidden.displayTime + suffix);
    assert.equal(shown.value, hidden.value);
    assert.equal(clockReading(date, 10, false, true, true).displayTime, "00:30:45+00");
  }
});

test("hourly playback follows UTC even in a fractional-offset local timezone", () => {
  const date = new Date("2026-01-01T00:00:00Z");
  Object.assign(date, { getHours: () => 5, getMinutes: () => 45, getSeconds: () => 0 });
  assert.equal(clockReading(date, 3600).due, true);
  assert.equal(clockReading(new Date("2026-01-01T00:15:00Z"), 3600).due, false);
});
