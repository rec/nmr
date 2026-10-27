/* Display canonical item values without exposing the list's typed JSON records. */
export function describeObject(object) {
  return `${object.type}: ${formatValue(object)}`;
}

function formatValue({ type, value }) {
  if (type === "list") {
    const items = typeof value === "string" ? JSON.parse(value) : value;
    return `[${items.map(formatValue).join(", ")}]`;
  }
  return type === "string" ? JSON.stringify(value) : value;
}
