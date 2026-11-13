/* EKARUS wiki: pick the language before the page is drawn.
   Saved choice first (the EN / IT / FR buttons), otherwise the browser's language. */
(function () {
  var lang = null;
  try { lang = window.localStorage.getItem("ekarus.lang"); } catch (e) {}
  if (!lang) {
    var nav = ((navigator.languages && navigator.languages[0]) || navigator.language || "en").slice(0, 2).toLowerCase();
    lang = nav === "it" || nav === "fr" ? nav : "en";
  }
  if (lang !== "it" && lang !== "fr") lang = "en";
  var root = document.documentElement;
  root.setAttribute("data-lang", lang);
  root.setAttribute("lang", lang);
  if (lang !== "en") {
    root.classList.add("i18n-pending");          // hidden until translated (i18n.js), at most 2 s
    setTimeout(function () { root.classList.remove("i18n-pending"); }, 2000);
  }
})();
