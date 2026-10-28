/* Names and playback boundaries use UTC; presentation can use local time. */
export function clockReading(date, interval, timeOnly = false, displayUTC = false, show_timezone = false) {
  const utc = date.toISOString().slice(0, 19);
  const displayedDate = displayUTC
    ? utc.slice(0, 10)
    : [date.getFullYear(), date.getMonth() + 1, date.getDate()]
      .map((i, j) => String(i).padStart(j === 0 ? 4 : 2, "0")).join("-");
  const displayedTime = displayUTC
    ? utc.slice(11)
    : [date.getHours(), date.getMinutes(), date.getSeconds()]
      .map((i) => String(i).padStart(2, "0")).join(":");
  const offset = displayUTC ? 0 : -date.getTimezoneOffset();
  const hours = String(Math.floor(Math.abs(offset) / 60)).padStart(2, "0");
  const minutes = Math.abs(offset) % 60;
  const zone = (offset < 0 ? "-" : "+") + hours
    + (minutes ? ":" + String(minutes).padStart(2, "0") : "");
  const second = Math.floor(date.getTime() / 1000);
  return {
    type: timeOnly ? "time" : "datetime",
    value: timeOnly ? utc.slice(11) : utc,
    displayDate: displayedDate,
    displayTime: displayedTime + (show_timezone ? zone : ""),
    second,
    due: second % interval === 0,
  };
}
