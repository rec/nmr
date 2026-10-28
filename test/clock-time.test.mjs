import assert from "node:assert/strict";
import test from "node:test";
import { clockReading } from "../nmr/web/clock-time.mjs";

test("formats local time with leading zeros and handles midnight", () => {
  for (const [hour, minute, second, expected] of [
    [0, 0, 0, "00:00:00"], [9, 4, 3, "09:04:03"], [23, 59, 59, "23:59:59"],
  ]) {
    const date = new Date(2026, 9, 28, hour, minute, second, 999);
    const reading = clockReading(date, 10);
    assert.equal(reading.value, expected);
    assert.equal(reading.second, Math.floor(date.getTime() / 1000));
  }
});

test("intervals use local wall-clock boundaries throughout the day", () => {
  for (const interval of [5, 10, 60, 3600]) {
    for (const hour of [0, 9, 23]) {
      const due = [];
      for (let second = 0; second < 3600; second++) {
        const reading = clockReading(new Date(2026, 9, 28, hour, 0, second), interval);
        if (reading.due) due.push(second);
      }
      assert.deepEqual(due, Array.from({ length: 3600 / interval }, (_, i) => i * interval));
    }
  }
});
