/* EKARUS wiki — sign-in gate.
   Loaded in the <head> of every protected page, before anything is drawn.

   1. Coming back from an e-mail sign-in link, the address ends in #ekarus-auth=…
      (set by the EKARUSwiki server): remember who signed in, then clean the address.
   2. If nobody is signed in on this browser (or the sign-in expired), go to index.html.

   This only decides what the browser shows: on GitHub Pages the page files are public.
   Everything that changes something (admin, proposals) is checked again on the server. */
(function () {
  var root = document.documentElement.getAttribute("data-root") || "";
  var store;
  try { store = window.localStorage; } catch (e) { store = null; }

  var m = /[#&]ekarus-auth=([A-Za-z0-9_-]+)/.exec(window.location.hash);
  if (m && store) {
    try {
      var b64 = m[1].replace(/-/g, "+").replace(/_/g, "/");
      while (b64.length % 4) b64 += "=";
      var info = JSON.parse(decodeURIComponent(escape(window.atob(b64))));
      store.setItem("ekarus.access", "1");
      store.setItem("ekarus.email", info.email || "");
      store.setItem("ekarus.name", info.name || "");
      store.setItem("ekarus.admin", info.admin ? "1" : "");
      store.setItem("ekarus.exp", String(info.exp || 0));
    } catch (e) { /* malformed: ignore */ }
    history.replaceState(null, "", window.location.pathname + window.location.search);
  }

  var signedIn = false;
  if (store) {
    var exp = parseInt(store.getItem("ekarus.exp") || "0", 10);
    signedIn = !!store.getItem("ekarus.access") && (!exp || exp * 1000 > Date.now());
  }
  if (!signedIn) {
    var file = window.location.pathname.split("/").pop() || "home.html";
    var next = (root ? "pages/" : "") + file;
    window.location.replace(root + "index.html?next=" + encodeURIComponent(next));
  }
})();
