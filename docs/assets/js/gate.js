/* EKARUS wiki — sign-in gate.
   Loaded in the <head> of every protected page, before anything is drawn.
   If nobody is signed in on this browser (or the sign-in expired after 30 days), go to index.html.

   This only decides what the browser shows: on GitHub Pages the page files are public.
   Everything that changes something (admin pages, proposals) is checked on the server. */
(function () {
  var root = document.documentElement.getAttribute("data-root") || "";
  var signedIn = false;
  try {
    var exp = parseInt(window.localStorage.getItem("ekarus.exp") || "0", 10);
    signedIn = !!window.localStorage.getItem("ekarus.access") && (!exp || exp * 1000 > Date.now());
  } catch (e) { /* storage blocked */ }
  if (!signedIn) {
    var file = window.location.pathname.split("/").pop() || "home.html";
    var next = (root ? "pages/" : "") + file;
    window.location.replace(root + "index.html?next=" + encodeURIComponent(next));
  }
})();
