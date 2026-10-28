const mainView = document.querySelector("#main-view");
const clockView = document.querySelector("#clock-view");
const mainLink = document.querySelector("#main-link");
const clockLink = document.querySelector("#clock-link");
let mainURL = new URL(window.location.href);
if (mainURL.searchParams.get("type") === "clock") mainURL.search = "desc=";

function showView() {
  const clock = new URL(window.location.href).searchParams.get("type") === "clock";
  mainView.hidden = clock;
  clockView.hidden = !clock;
  document.title = clock ? "Clock · nmr" : "nmr";
  if (!clock) mainURL = new URL(window.location.href);
  mainLink.href = mainURL.href;
  window.dispatchEvent(new Event("viewchange"));
}
for (const link of [clockLink, mainLink]) {
  link.addEventListener("click", (event) => {
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (!mainView.hidden) mainURL = new URL(window.location.href);
    const url = new URL(link === clockLink ? window.location.href : mainURL.href);
    if (link === clockLink) url.search = "type=clock";
    if (url.pathname !== "/") url.pathname = url.pathname.replace(/\/$/, "");
    window.history.pushState(null, "", url);
    showView();
    (clockView.hidden ? mainView : clockView).querySelector("h1").focus({ preventScroll: true });
  });
}
window.addEventListener("popstate", showView);
showView();
