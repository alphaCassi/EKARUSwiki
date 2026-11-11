/* EKARUSwiki server — small progressive enhancements. Every form also works without JS. */
(function () {
  "use strict";

  /* Confirm destructive actions (withdraw, reject, remove night, cancel allocation) */
  document.addEventListener("submit", function (ev) {
    var form = ev.target;
    var btn = ev.submitter;
    var msg = (btn && btn.getAttribute("data-confirm")) || form.getAttribute("data-confirm");
    if (msg && !window.confirm(msg)) ev.preventDefault();
  });

  /* Proposal form: add / remove target rows */
  var table = document.querySelector("[data-targets]");
  var addBtn = document.querySelector("[data-add-row]");
  if (table && addBtn) {
    var body = table.tBodies[0];
    var max = parseInt(table.getAttribute("data-max"), 10) || 30;

    function refresh() {
      addBtn.disabled = body.rows.length >= max;
      Array.prototype.forEach.call(body.querySelectorAll("[data-remove-row]"), function (b) {
        b.hidden = body.rows.length === 1;
      });
    }
    addBtn.addEventListener("click", function () {
      var row = body.rows[body.rows.length - 1].cloneNode(true);
      Array.prototype.forEach.call(row.querySelectorAll("input"), function (i) { i.value = ""; });
      body.appendChild(row);
      row.querySelector("input").focus();
      refresh();
    });
    body.addEventListener("click", function (ev) {
      var b = ev.target.closest("[data-remove-row]");
      if (b && body.rows.length > 1) { b.closest("tr").remove(); refresh(); }
    });
    refresh();
  }

  /* Proposal form: live count of selected nights */
  var counter = document.querySelector("[data-night-count]");
  if (counter) {
    var boxes = document.querySelectorAll('input[name="nights"]');
    function count() {
      var n = Array.prototype.filter.call(boxes, function (b) { return b.checked; }).length;
      counter.textContent = n === 0 ? "No nights selected yet." : n + (n === 1 ? " night selected." : " nights selected.");
    }
    Array.prototype.forEach.call(boxes, function (b) { b.addEventListener("change", count); });
    count();
  }
})();

/* Bench page shown from the wiki: switch the subsystem panel (same behaviour as on the wiki) */
(function () {
  var picker = document.querySelector(".wiki-content [data-subsystems]");
  if (!picker) return;
  var buttons = Array.prototype.slice.call(picker.querySelectorAll("button[data-target]"));
  var panels = Array.prototype.slice.call(document.querySelectorAll(".wiki-content .subsystem-panel"));
  function show(id) {
    if (!panels.some(function (p) { return p.id === id; })) id = panels[0].id;
    panels.forEach(function (p) { p.hidden = p.id !== id; });
    buttons.forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-target") === id ? "true" : "false"); });
  }
  buttons.forEach(function (b) {
    b.addEventListener("click", function () {
      var id = b.getAttribute("data-target");
      show(b.getAttribute("aria-pressed") === "true" ? panels[0].id : id);
    });
  });
  show(location.hash.slice(1));
})();

/* Proposal form: a section's number turns green when it's filled in correctly */
(function () {
  var form = document.querySelector("[data-proposal-form]");
  if (!form) return;
  var sections = Array.prototype.slice.call(form.querySelectorAll("[data-step-section]"));

  function sectionOk(sec) {
    var fields = Array.prototype.slice.call(sec.querySelectorAll("input, select, textarea"));
    for (var i = 0; i < fields.length; i++) {
      var f = fields[i];
      if (f.type === "hidden" || f.type === "checkbox") continue;
      if (f.required && !f.value.trim()) return false;
      if (!f.checkValidity()) return false;
    }
    if (sec.hasAttribute("data-needs-night") &&
        !sec.querySelector('input[name="nights"]:checked')) return false;
    // targets: a row with coordinates or magnitude also needs a name
    var rows = sec.querySelectorAll("[data-targets] tbody tr");
    for (var r = 0; r < rows.length; r++) {
      var name = rows[r].querySelector('input[name="t_name"]');
      var others = Array.prototype.some.call(rows[r].querySelectorAll('input:not([name="t_name"])'),
        function (x) { return x.value.trim(); });
      if (others && !name.value.trim()) return false;
    }
    return true;
  }
  function refresh() {
    sections.forEach(function (sec) {
      var badge = sec.querySelector(".step");
      if (badge) badge.classList.toggle("step-done", sectionOk(sec));
    });
  }
  form.addEventListener("input", refresh);
  form.addEventListener("change", refresh);
  form.addEventListener("click", function () { setTimeout(refresh, 0); });   // added / removed target rows
  refresh();
})();

/* Close the "Wiki" menu when clicking elsewhere */
document.addEventListener("click", function (ev) {
  document.querySelectorAll("details.nav-menu[open]").forEach(function (d) {
    if (!d.contains(ev.target)) d.open = false;
  });
});

/* Calendar: renders months in the page, switches instantly (data fetched in the background
   and cached; the neighbouring months are fetched ahead of time). */
(function () {
  var root = document.querySelector("[data-calendar]");
  if (!root) return;
  var grid = root.querySelector("[data-cal-grid]");
  var title = root.querySelector(".cal-title");
  var jsonUrl = root.getAttribute("data-json-url");
  var newUrl = root.getAttribute("data-new-url");
  var cache = {};
  var current = JSON.parse(root.getAttribute("data-initial"));
  cache[key(current.year, current.month)] = current;
  var MOONS = ["\uD83C\uDF11", "\uD83C\uDF12", "\uD83C\uDF13", "\uD83C\uDF14", "\uD83C\uDF15", "\uD83C\uDF16", "\uD83C\uDF17", "\uD83C\uDF18"];
  var LABEL = { open: "Available", booked: "Booked", closed: "Unavailable" };

  function key(y, m) { return y + "-" + m; }
  function pad(n) { return (n < 10 ? "0" : "") + n; }

  function moon(y, m, d) {                      // phase on that evening (~20:00 UTC)
    var t = Date.UTC(y, m - 1, d, 20) / 86400000 + 2440587.5;
    var age = ((t - 2451550.26) / 29.530588853) % 1;
    if (age < 0) age += 1;
    return { icon: MOONS[Math.round(age * 8) % 8], pct: Math.round((1 - Math.cos(2 * Math.PI * age)) / 2 * 100) };
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function render(data) {
    current = data;
    title.textContent = data.title;
    var byDate = {};
    data.nights.forEach(function (n) { byDate[n.date] = n; });
    var first = new Date(Date.UTC(data.year, data.month - 1, 1));
    var days = new Date(Date.UTC(data.year, data.month, 0)).getUTCDate();
    var lead = (first.getUTCDay() + 6) % 7;            // Monday first
    var frag = document.createDocumentFragment();

    for (var i = 0; i < lead; i++) frag.appendChild(el("div", "cal-cell cal-pad"));
    for (var d = 1; d <= days; d++) {
      var iso = data.year + "-" + pad(data.month) + "-" + pad(d);
      var n = byDate[iso];
      var weekday = (lead + d - 1) % 7;
      var past = iso < data.today;
      var state = n ? (n.mine ? "mine" : n.status) : "none";
      var clickable = n && n.status === "open" && !past;
      var cell = el(clickable ? "a" : "div",
        "cal-cell st-" + state + (past ? " is-past" : "") + (iso === data.today ? " is-today" : "") +
        (weekday >= 5 ? " is-we" : ""));
      if (clickable) {
        cell.href = newUrl + "?night=" + n.id;
        cell.title = "Propose this night";
      }
      cell.setAttribute("role", "gridcell");

      var top = el("div", "cal-top");
      top.appendChild(el("span", "cal-day", String(d)));
      var mo = moon(data.year, data.month, d);
      var ms = el("span", "cal-moon", mo.icon + " " + mo.pct + "%");
      ms.title = "Moon " + mo.pct + "% illuminated";
      top.appendChild(ms);
      cell.appendChild(top);

      if (n) {
        var label = n.mine ? "Your night" : LABEL[n.status];
        cell.appendChild(el("span", "cal-pill", label));
        if (n.code) cell.appendChild(el("span", "cal-code", n.code));
        if (n.note) cell.appendChild(el("span", "cal-note", n.note));
        cell.setAttribute("aria-label", iso + ", " + label + (n.note ? ", " + n.note : ""));
      } else {
        cell.setAttribute("aria-label", iso + ", no observing night");
      }
      frag.appendChild(cell);
    }
    var total = lead + days;
    for (var k = total; k % 7 !== 0; k++) frag.appendChild(el("div", "cal-cell cal-pad"));

    grid.textContent = "";
    grid.appendChild(frag);
    var url = new URL(window.location.href);
    url.searchParams.set("y", data.year); url.searchParams.set("m", data.month);
    history.replaceState(null, "", url.pathname + url.search);
    prefetch(data.prev); prefetch(data.next);
  }

  function load(y, m) {
    var k = key(y, m);
    if (cache[k] && cache[k].then) return cache[k];
    if (cache[k]) return Promise.resolve(cache[k]);
    var p = fetch(jsonUrl + "?y=" + y + "&m=" + m, { credentials: "same-origin" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) { cache[k] = data; return data; })
      .catch(function (e) { delete cache[k]; throw e; });
    cache[k] = p;
    return p;
  }
  function prefetch(ym) { load(ym.y, ym.m).catch(function () {}); }

  function go(ym) {
    root.classList.add("is-loading");
    load(ym.y, ym.m).then(render).catch(function () {
      window.location.href = "?y=" + ym.y + "&m=" + ym.m;      // fall back to a normal page load
    }).then(function () { root.classList.remove("is-loading"); });
  }

  root.addEventListener("click", function (ev) {
    var b = ev.target.closest("[data-cal]");
    if (!b) return;
    var what = b.getAttribute("data-cal");
    if (what === "prev") go(current.prev);
    else if (what === "next") go(current.next);
    else { var t = current.today.split("-"); go({ y: +t[0], m: +t[1] }); }
  });
  root.addEventListener("keydown", function (ev) {
    if (ev.target.closest("input, textarea, select")) return;
    if (ev.key === "ArrowLeft" && ev.altKey) go(current.prev);
    if (ev.key === "ArrowRight" && ev.altKey) go(current.next);
  });

  render(current);
})();
