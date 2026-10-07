/* EKARUS scheduler — small progressive enhancements. Every form also works without JS. */
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
