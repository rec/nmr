/* Display canonical values with their short type labels. */
export function describeObject({ type, value }) {
  return `${type}: ${type === "string" ? JSON.stringify(value) : value}`;
}
