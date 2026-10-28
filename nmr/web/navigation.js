const mainView = document.querySelector("#main-view");
const clockView = document.querySelector("#clock-view");
const countView = document.querySelector("#count-view");
const mainLink = document.querySelector("#main-link");
const clockLink = document.querySelector("#clock-link");
const countLink = document.querySelector("#count-link");
const clockCountLink = document.querySelector("#clock-count-link");
const countMainLink = document.querySelector("#count-main-link");
const countClockLink = document.querySelector("#count-clock-link");
let mainURL = new URL(window.location.href);
if (mainURL.searchParams.get("type") === "clock" || mainURL.searchParams.has("count")) mainURL.search = "desc=";
let countURL = new URL(window.location.href);
if (!countURL.searchParams.has("count")) countURL.search = "count=0&inc=1";

function showView() {
  const parameters = new URL(window.location.href).searchParams;
  const count = parameters.has("count");
  const clock = !count && parameters.get("type") === "clock";
  mainView.hidden = count || clock;
  clockView.hidden = !clock;
  countView.hidden = !count;
  document.title = count ? "Count · nmr" : clock ? "Clock · nmr" : "nmr";
  if (!mainView.hidden) mainURL = new URL(window.location.href);
  if (count) countURL = new URL(window.location.href);
  mainLink.href = countMainLink.href = mainURL.href;
  countLink.href = clockCountLink.href = countURL.href;
  window.dispatchEvent(new Event("viewchange"));
}
for (const [link, target] of [
  [clockLink, "clock"], [mainLink, "main"], [countLink, "count"],
  [clockCountLink, "count"], [countMainLink, "main"], [countClockLink, "clock"],
]) {
  link.addEventListener("click", (event) => {
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (!mainView.hidden) mainURL = new URL(window.location.href);
    if (!countView.hidden) countURL = new URL(window.location.href);
    const url = new URL(target === "main" ? mainURL.href : target === "count" ? countURL.href : window.location.href);
    if (target === "clock") url.search = "type=clock";
    if (url.pathname !== "/") url.pathname = url.pathname.replace(/\/$/, "");
    window.history.pushState(null, "", url);
    showView();
    const view = target === "main" ? mainView : target === "count" ? countView : clockView;
    view.querySelector("h1").focus({ preventScroll: true });
  });
}
window.addEventListener("popstate", showView);
showView();
