/* Local wall-clock boundaries, independent of when playback was enabled. */
export function clockReading(date, interval) {
  const hours = date.getHours();
  const minutes = date.getMinutes();
  const seconds = date.getSeconds();
  return {
    value: [hours, minutes, seconds].map((i) => String(i).padStart(2, "0")).join(":"),
    second: Math.floor(date.getTime() / 1000),
    due: (hours * 3600 + minutes * 60 + seconds) % interval === 0,
  };
}
