/* EKARUS wiki — sign-in gate.
   Loaded in the <head> of every protected page, before anything is drawn.
   If the visitor has not signed in on this browser, send them to index.html.

   This is a convenience gate only: on a public host such as GitHub Pages the
   page files can still be fetched directly. See README.md. */
(function () {
  var KEY = "ekarus.access";
  var root = document.documentElement.getAttribute("data-root") || "";
  var signedIn = false;
  try { signedIn = !!window.localStorage.getItem(KEY); } catch (e) { /* storage blocked */ }

  if (!signedIn) {
    // remember where the visitor wanted to go, e.g. "pages/logbook.html"
    var parts = window.location.pathname.split("/");
    var file = parts.pop() || "home.html";
    var next = (root ? "pages/" : "") + file;
    window.location.replace(root + "index.html?next=" + encodeURIComponent(next));
  }
})();
