/* All views share one Python worker and vocabulary configuration. */
const worker = new Worker("worker.js");
const pending = new Map();
let serial = 0;
let failure = null;

export function request(action, payload) {
  if (failure) return Promise.reject(failure);
  return new Promise((resolve, reject) => {
    const id = ++serial;
    pending.set(id, { resolve, reject });
    worker.postMessage({ id, action, payload });
  });
}
worker.onmessage = ({ data }) => {
  const task = pending.get(data.id);
  if (!task) return;
  pending.delete(data.id);
  if (data.error) task.reject(new Error(data.error));
  else task.resolve(data.result);
};
worker.onerror = (event) => {
  const error = event.error || new Error(event.message);
  failure = error;
  console.error(error);
  for (const task of pending.values()) task.reject(error);
  pending.clear();
};
export const configured = request("configure", {});
