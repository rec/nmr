/* Display canonical values without type prefixes. */
export function describeObject({ type, value }) {
  return type === "string" ? JSON.stringify(value) : value;
}
