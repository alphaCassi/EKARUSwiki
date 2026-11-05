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
