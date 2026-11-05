/* EKARUS wiki — page behaviour.
   Loaded with "defer" on every page. Each block below only runs if the page
   contains the elements it needs, so one file serves the whole site. */
(function () {
  "use strict";

  var KEY = "ekarus.access";
  var html = document.documentElement;
  var root = html.getAttribute("data-root") || "";
  var config = window.EKARUS_CONFIG || {};
  html.classList.add("js");

  /* ---------- The EKARUSwiki server (active parts of the wiki), if configured */
  var server = (config.serverUrl || "").replace(/\/$/, "");

  /* Observation Schedule button: the schedule module of the server */
  if (server) {
    document.querySelectorAll("[data-schedule-link]").forEach(function (a) {
      a.href = server + "/schedule/";
    });
  }

  /* ---------- Sign out (header button on every protected page) */
  document.querySelectorAll("[data-signout]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      try { window.localStorage.removeItem(KEY); } catch (e) {}
      window.location.href = root + "index.html";
    });
  });

  /* ---------- Access page: sign in with a registered e-mail */
  var signinForm = document.getElementById("signin-form");
  if (signinForm) {
    var msg = document.getElementById("signin-message");
    var home = config.homePage || "home.html";

    // Only allow redirects to pages inside this site.
    var next = new URLSearchParams(window.location.search).get("next");
    var target = next && /^(home\.html|pages\/[a-z0-9-]+\.html)$/.test(next) ? next : home;

    // Already signed in on this browser? Go straight in.
    try {
      if (window.localStorage.getItem(KEY)) { window.location.replace(target); return; }
    } catch (e) {}

    signinForm.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var email = signinForm.elements.email.value.trim().toLowerCase();
      if (!email) { setMessage(msg, "error", "Enter your e-mail address."); return; }

      if (!(window.crypto && window.crypto.subtle)) {
        setMessage(msg, "error", "This browser can't check the address. Open the site over https in an up-to-date browser.");
        return;
      }
      sha256(email).then(function (hash) {
        var users = window.EKARUS_USERS || [];
        if (users.indexOf(hash) !== -1) {
          try { window.localStorage.setItem(KEY, "1"); } catch (e) {}
          setMessage(msg, "ok", "Signed in.");
          window.location.href = target;
        } else {
          setMessage(msg, "error", "This address isn't registered. Check the spelling, or request access below.");
        }
      });
    });
  }

  /* ---------- Sending to the admins (contact form, access requests) via the EKARUSwiki server.
     No mail program is involved: the server stores the message for the admin page and
     e-mails it to the admins. */
  function sendToAdmins(payload, button, msgEl, onDone) {
    if (!server) {
      setMessage(msgEl, "error", "Sending isn't available yet: the EKARUSwiki server isn't connected.");
      return;
    }
    button.disabled = true;
    setMessage(msgEl, "", "Sending…");
    fetch(server + "/api/contact", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); })
      .then(function (res) {
        if (res.ok) { onDone(); }
        else { setMessage(msgEl, "error", res.error || "Sending failed. Please try again later."); }
      })
      .catch(function () { setMessage(msgEl, "error", "The server can't be reached. Please try again later."); })
      .then(function () { button.disabled = false; });
  }

  /* ---------- Access page: request access */
  var requestForm = document.getElementById("request-form");
  if (requestForm) {
    var rmsg = document.getElementById("request-message");
    requestForm.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var f = requestForm.elements;
      var name = f.name.value.trim();
      var email = f.email.value.trim().toLowerCase();
      if (!name || !email) { setMessage(rmsg, "error", "Enter your name and e-mail address."); return; }
      sendToAdmins({
        kind: "access", name: name, email: email,
        message: "Institute: " + f.institute.value.trim() + "\nRole on EKARUS: " + f.role.value.trim(),
        website: f.website ? f.website.value : ""
      }, requestForm.querySelector("button"), rmsg, function () {
        requestForm.reset();
        setMessage(rmsg, "ok", "Request sent. You'll get an e-mail when you're registered.");
      });
    });
  }

  /* ---------- Contact page: change requests */
  var contactForm = document.getElementById("contact-form");
  if (contactForm) {
    var cmsg = document.getElementById("contact-message");
    contactForm.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var f = contactForm.elements;
      var data = {
        kind: "contact",
        name: f.name.value.trim(),
        email: f.email.value.trim(),
        topic: f.topic.value,
        page: f.page.value,
        message: f.message.value.trim(),
        website: f.website.value
      };
      if (!data.name || !data.email || !data.message) {
        setMessage(cmsg, "error", "Fill in your name, e-mail and request.");
        return;
      }
      sendToAdmins(data, contactForm.querySelector("button[type=submit]"), cmsg, function () {
        contactForm.reset();
        setMessage(cmsg, "ok", "Thank you! Your request has been sent to the wiki admins.");
      });
    });
  }

  /* ---------- Footer "Admin" link: the wiki's admin pages live on the server */
  if (server) {
    document.querySelectorAll("[data-admin-link]").forEach(function (a) {
      a.href = server + "/admin/";
      a.closest("[data-admin-wrap]").hidden = false;
    });
  }

  /* ---------- Banner and highlights from data/site.json (edited on the admin page).
     If the file can't be loaded (e.g. page opened from disk), the HTML version stays. */
  var bannerEl = document.querySelector("[data-site-banner]");
  var highlightsEl = document.querySelector("[data-highlights]");
  if ((bannerEl || highlightsEl) && window.fetch && location.protocol !== "file:") {
    fetch(root + "data/site.json", { cache: "no-cache" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (site) {
        if (bannerEl && site.banner) bannerEl.textContent = site.banner;
        if (highlightsEl && Array.isArray(site.highlights) && site.highlights.length) {
          renderHighlights(highlightsEl, site.highlights);
        }
      })
      .catch(function () { /* keep the HTML version */ });
  }

  function renderHighlights(container, items) {
    var VISIBLE = 3;
    function list(part) {
      var ul = document.createElement("ul");
      ul.className = "highlights";
      part.forEach(function (h) {
        var li = document.createElement("li");
        if (h.date) { var t = document.createElement("time"); t.textContent = h.date; li.appendChild(t); }
        if (h.title) { var b = document.createElement("strong"); b.textContent = h.title; li.appendChild(b); }
        if (h.text) li.appendChild(document.createTextNode(" " + h.text));
        if (h.done) { var tag = document.createElement("span"); tag.className = "tag"; tag.textContent = "Done"; li.appendChild(tag); }
        ul.appendChild(li);
      });
      return ul;
    }
    container.textContent = "";
    container.appendChild(list(items.slice(0, VISIBLE)));
    if (items.length > VISIBLE) {
      var more = document.createElement("details");
      more.className = "more";
      var sum = document.createElement("summary");
      sum.textContent = "See more";
      more.appendChild(sum);
      more.appendChild(list(items.slice(VISIBLE)));
      container.appendChild(more);
    }
  }

  /* ---------- Bench page: switch the detail panel by subsystem */
  var picker = document.querySelector("[data-subsystems]");
  if (picker) {
    var buttons = Array.prototype.slice.call(picker.querySelectorAll("button[data-target]"));
    var panels = Array.prototype.slice.call(document.querySelectorAll(".subsystem-panel"));

    function show(id, updateHash) {
      var found = panels.some(function (p) { return p.id === id; });
      if (!found) id = panels[0].id;
      panels.forEach(function (p) { p.hidden = p.id !== id; });
      buttons.forEach(function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-target") === id ? "true" : "false");
      });
      if (updateHash) history.replaceState(null, "", "#" + id);
    }

    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        var id = b.getAttribute("data-target");
        // clicking the selected subsystem again returns to the specifications
        if (b.getAttribute("aria-pressed") === "true") id = panels[0].id;
        show(id, true);
      });
    });
    window.addEventListener("hashchange", function () { show(location.hash.slice(1), false); });
    show(location.hash.slice(1), false);
  }

  /* ---------- To-do page: link to the spreadsheet kept in the GitHub repository */
  var todoFile = document.querySelector("[data-todo-file]");
  if (todoFile) {
    if (config.githubRepo) {
      todoFile.href = "https://github.com/" + config.githubRepo + "/blob/" +
        (config.githubBranch || "main") + "/resources/EKARUS_todo.xlsx";
    } else {
      // repository not configured yet: show plain text instead of a dead link
      var span = document.createElement("span");
      span.textContent = todoFile.textContent;
      todoFile.replaceWith(span);
    }
  }

  /* ---------- To-do page: load the list from the published Google Sheet (CSV) */
  var todoTable = document.querySelector("[data-todo-table]");
  if (todoTable && config.todoSheetUrl && window.fetch) {
    var todoNote = document.querySelector("[data-todo-source]");
    fetch(config.todoSheetUrl, { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then(function (text) {
        var rows = parseCSV(text).filter(function (r) { return r.some(function (c) { return c.trim(); }); });
        var head = rows.shift().map(function (h) { return h.trim().toLowerCase(); });
        var col = function (name) { return head.indexOf(name); };
        var iTask = col("task"), iOwner = col("owner"), iDue = col("due"), iStatus = col("status");
        if (iTask === -1) throw new Error("no Task column");
        var body = todoTable.tBodies[0];
        body.textContent = "";
        rows.forEach(function (r) {
          var task = (r[iTask] || "").trim();
          if (!task) return;
          var status = iStatus > -1 ? (r[iStatus] || "").trim() : "";
          var tr = document.createElement("tr");
          if (/^done$/i.test(status)) tr.className = "is-done";
          [task, iOwner > -1 ? r[iOwner] : "", iDue > -1 ? r[iDue] : "", status].forEach(function (v) {
            var td = document.createElement("td");
            td.textContent = (v || "").trim() || "—";   // textContent: sheet text is never run as HTML
            tr.appendChild(td);
          });
          body.appendChild(tr);
        });
        if (todoNote) todoNote.textContent = "Live from the EKARUS To-do spreadsheet.";
      })
      .catch(function () {
        if (todoNote) todoNote.textContent = "Couldn't load the spreadsheet; showing the last saved list.";
      });
  }

  /* ---------- helpers */
  function parseCSV(text) {
    var rows = [], row = [], field = "", inQuotes = false;
    for (var i = 0; i < text.length; i++) {
      var ch = text[i];
      if (inQuotes) {
        if (ch === '"' && text[i + 1] === '"') { field += '"'; i++; }
        else if (ch === '"') { inQuotes = false; }
        else { field += ch; }
      } else if (ch === '"') { inQuotes = true; }
      else if (ch === ",") { row.push(field); field = ""; }
      else if (ch === "\n" || ch === "\r") {
        if (ch === "\r" && text[i + 1] === "\n") i++;
        row.push(field); rows.push(row); row = []; field = "";
      } else { field += ch; }
    }
    if (field || row.length) { row.push(field); rows.push(row); }
    return rows;
  }

  function setMessage(el, state, text) {
    if (!el) return;
    el.setAttribute("data-state", state);
    el.textContent = text;
  }

  function sha256(text) {
    var data = new TextEncoder().encode(text);
    return window.crypto.subtle.digest("SHA-256", data).then(function (buf) {
      return Array.prototype.map.call(new Uint8Array(buf), function (b) {
        return ("0" + b.toString(16)).slice(-2);
      }).join("");
    });
  }
})();
