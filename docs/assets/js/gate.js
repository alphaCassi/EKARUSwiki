/* EKARUS wiki — sign-in gate.
   Loaded in the <head> of every protected page, before anything is drawn.
   If nobody signed in during this browser session, go to the sign-in page (index.html).

   This only decides what the browser shows: on GitHub Pages the page files are public.
   Everything that changes something (admin pages, proposals) is checked on the server. */
(function () {
  var root = document.documentElement.getAttribute("data-root") || "";
  var signedIn = false;
  try {
    signedIn = !!window.sessionStorage.getItem("ekarus.access");
  } catch (e) { /* storage blocked */ }
  if (!signedIn) {
    var file = window.location.pathname.split("/").pop() || "home.html";
    var next = (root ? "pages/" : "") + file;
    window.location.replace(root + "index.html?next=" + encodeURIComponent(next));
  }
})();
