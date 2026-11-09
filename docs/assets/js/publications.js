/* EKARUS wiki — Publications page: filters and sorting over publications-data.js. */
(function () {
  "use strict";
  var data = (window.EKARUS_PUBLICATIONS || []).slice();
  var list = document.getElementById("pub-list");
  var form = document.getElementById("pub-filters");
  if (!list || !form) return;

  var TYPES = { paper: "Refereed paper", proceedings: "Proceedings", poster: "Poster", talk: "Talk" };
  var SHOW_AUTHORS = 6;

  function surname(a) { return a.split(",")[0].trim(); }
  function display(a) {                       // "Héritier, C. T." -> "C. T. Héritier"
    var p = a.split(",");
    return p.length > 1 ? p[1].trim() + " " + p[0].trim() : a;
  }
  function norm(s) { return s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase(); }

  // ---- fill the Year and Author menus from the data
  var years = [], authors = [];
  data.forEach(function (p) {
    if (years.indexOf(p.year) === -1) years.push(p.year);
    p.authors.forEach(function (a) { if (authors.indexOf(a) === -1) authors.push(a); });
  });
  years.sort(function (a, b) { return b - a; });
  authors.sort(function (a, b) { return norm(a).localeCompare(norm(b)); });
  years.forEach(function (y) { form.year.add(new Option(String(y), String(y))); });
  authors.forEach(function (a) { form.author.add(new Option(a, a)); });

  // ---- render
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  }

  function item(p, highlight) {
    var li = el("li", "pub");
    var link = p.doi ? "https://doi.org/" + p.doi : p.url;

    var head = el("div", "pub-head");
    head.appendChild(el("span", "pub-year", String(p.year)));
    head.appendChild(el("span", "pub-type", TYPES[p.type] || p.type));
    if (p.related) head.appendChild(el("span", "pub-type pub-related", "Mentions EKARUS"));
    li.appendChild(head);

    var title = el("h3", "pub-title");
    if (link) {
      var a = el("a", "ext", p.title);
      a.href = link; a.target = "_blank"; a.rel = "noopener";
      title.appendChild(a);
    } else {
      title.textContent = p.title;
    }
    li.appendChild(title);

    // authors: the first few, the rest behind "show all"; the selected author is highlighted
    var names = p.authors.map(display);
    var authorsEl = el("p", "pub-authors");
    function addNames(arr, into) {
      arr.forEach(function (n, i) {
        var s = el("span", p.authors[names.indexOf(n)] === highlight ? "pub-me" : "", n);
        into.appendChild(s);
        if (i < arr.length - 1) into.appendChild(document.createTextNode(", "));
      });
    }
    if (names.length > SHOW_AUTHORS) {
      addNames(names.slice(0, SHOW_AUTHORS), authorsEl);
      var more = el("details", "pub-more");
      more.appendChild(el("summary", "", "\u00a0and " + (names.length - SHOW_AUTHORS) + " more"));
      var rest = el("span");
      rest.appendChild(document.createTextNode(", "));
      addNames(names.slice(SHOW_AUTHORS), rest);
      more.appendChild(rest);
      authorsEl.appendChild(more);
    } else {
      addNames(names, authorsEl);
      if (p.authorsIncomplete) authorsEl.appendChild(document.createTextNode(", et al."));
    }
    li.appendChild(authorsEl);

    var venue = el("p", "pub-venue", p.venue);
    if (p.doi) {
      venue.appendChild(document.createTextNode(", DOI "));
      var d = el("a", "", p.doi);
      d.href = "https://doi.org/" + p.doi; d.target = "_blank"; d.rel = "noopener";
      venue.appendChild(d);
    } else if (p.url && (p.type === "paper" || p.type === "proceedings")) {
      venue.appendChild(document.createTextNode(", DOI not yet available"));
    }
    li.appendChild(venue);
    return li;
  }

  function update() {
    var q = norm(form.q.value.trim());
    var year = form.year.value, author = form.author.value, type = form.type.value;
    var withRelated = form.related.checked;

    var rows = data.filter(function (p) {
      if (year && String(p.year) !== year) return false;
      if (author && p.authors.indexOf(author) === -1) return false;
      if (type && p.type !== type) return false;
      if (!withRelated && p.related) return false;
      if (q && norm(p.title + " " + p.authors.join(" ") + " " + p.venue).indexOf(q) === -1) return false;
      return true;
    });

    var sort = form.sort.value;
    rows.sort(function (a, b) {
      if (sort === "oldest") return a.year - b.year || (a.related - b.related) || a.title.localeCompare(b.title);
      if (sort === "title") return a.title.localeCompare(b.title);
      if (sort === "author") return norm(surname(a.authors[0])).localeCompare(norm(surname(b.authors[0])));
      return b.year - a.year || (a.related - b.related) || a.title.localeCompare(b.title);  // newest first, EKARUS papers before related ones
    });

    list.textContent = "";
    rows.forEach(function (p) { list.appendChild(item(p, author)); });
    document.getElementById("pub-count").textContent =
      rows.length + (rows.length === 1 ? " publication" : " publications") +
      (rows.length !== data.length ? " of " + data.length : "");
    document.getElementById("pub-empty").hidden = rows.length > 0;
  }

  form.addEventListener("input", update);
  form.addEventListener("change", update);
  form.addEventListener("submit", function (e) { e.preventDefault(); });
  form.addEventListener("reset", function () { setTimeout(update, 0); });
  update();
})();
