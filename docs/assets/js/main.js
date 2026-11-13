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
      a.href = server + "/";
    });
  }

  /* ---------- Sign out (header button on every protected page) */
  function forgetSignin() {
    ["ekarus.access", "ekarus.email", "ekarus.name", "ekarus.admin", "ekarus.exp"].forEach(function (k) {
      try { window.sessionStorage.removeItem(k); } catch (e) {}
      try { window.localStorage.removeItem(k); } catch (e) {}     // left over from older versions
    });
  }
  document.querySelectorAll("[data-signout]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      forgetSignin();
      var back = new URL(root + "index.html", window.location.href).href;
      var srv = (config.serverUrl || "").replace(/\/$/, "");
      // also end the server session (admin), which then comes back here
      window.location.href = srv ? srv + "/account/signout?next=" + encodeURIComponent(back) : back;
    });
  });
  // Signed out on the server's pages: forget the wiki sign-in as well
  if (/[?&]signout=1/.test(window.location.search)) {
    forgetSignin();
    history.replaceState(null, "", window.location.pathname);
  }

  /* ---------- Access page: sign in with your e-mail (no password).
     With the server connected, the server checks the team list and says whether you're an
     admin. If the server can't be reached, the wiki uses its own list (users.js). */
  var signinForm = document.getElementById("signin-form");
  if (signinForm) {
    var msg = document.getElementById("signin-message");
    var home = config.homePage || "home.html";
    var next = new URLSearchParams(window.location.search).get("next");
    var target = next && /^(home\.html|pages\/[a-z0-9-]+\.html)$/.test(next) ? next : home;
    // The sign-in page always shows, even if this browser was signed in before.
    forgetSignin();

    var enter = function (email, name, admin) {
      try {   // kept only until the browser is closed
        window.sessionStorage.setItem(KEY, "1");
        window.sessionStorage.setItem("ekarus.email", email);
        window.sessionStorage.setItem("ekarus.name", name || "");
        window.sessionStorage.setItem("ekarus.admin", admin ? "1" : "");
      } catch (e) {}
      window.location.href = target;
    };

    var localCheck = function (email) {
      if (!(window.crypto && window.crypto.subtle)) {
        setMessage(msg, "error", "This browser can't check the address. Open the site over https in an up-to-date browser.");
        return;
      }
      sha256(email).then(function (hash) {
        if ((window.EKARUS_USERS || []).indexOf(hash) !== -1) { enter(email, "", false); }
        else { setMessage(msg, "error", "This address isn't on the team list. Request access below."); }
      });
    };

    signinForm.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var email = signinForm.elements.email.value.trim().toLowerCase();
      if (!email) { setMessage(msg, "error", "Enter your e-mail address."); return; }
      var asAdmin = signinForm.elements.as_admin && signinForm.elements.as_admin.checked;
      if (asAdmin && !server) {
        setMessage(msg, "error", "Admin sign-in needs the EKARUS server, which isn't connected to the wiki.");
        return;
      }
      if (!server) { localCheck(email); return; }
      var button = signinForm.querySelector("button");
      button.disabled = true;
      fetch(server + "/api/signin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, website: signinForm.elements.website ? signinForm.elements.website.value : "" })
      })
        .then(function (r) { return r.json(); })
        .then(function (res) {
          if (!res.ok) { setMessage(msg, "error", res.error || "Sign-in failed. Please try again."); return; }
          if (asAdmin && !res.admin) { setMessage(msg, "error", "This address isn't an admin. Untick “Sign in as admin” to enter the wiki."); return; }
          if (asAdmin) {
            // signed in to the wiki too, then the admin password on the server
            target = server + "/account/admin-signin?next=%2Fadmin%2F&email=" + encodeURIComponent(email);
          }
          enter(email, res.name, res.admin);
        })
        .catch(function () {
          if (asAdmin) { setMessage(msg, "error", "The EKARUS server can't be reached, so admin sign-in isn't possible right now."); return; }
          localCheck(email);                                // server off: use the wiki's own list
        })
        .then(function () { button.disabled = false; });
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

  /* ---------- Banner and highlights from data/site.json (edited on the admin page).
     If the file can't be loaded (e.g. page opened from disk), the HTML version stays. */
  var bannerEl = document.querySelector("[data-site-banner]");
  var highlightsEl = document.querySelector("[data-highlights]");
  if ((bannerEl || highlightsEl) && window.fetch && location.protocol !== "file:") {
    fetch(root + "data/site.json", { cache: "no-cache" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (site) {
        var BL = window.ekarusLang || "en";
        var banner = (BL !== "en" && site["banner_" + BL]) || site.banner;
        if (bannerEl && banner) bannerEl.textContent = banner;
        var pic = document.querySelector("[data-site-image]");
        if (pic && site.image && site.image.src) {
          pic.querySelector("img").src = root + site.image.src;
          pic.querySelector("img").alt = site.image.alt || "";
          pic.querySelector("figcaption").textContent = site.image.caption || "";
          pic.hidden = false;
        }
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
        var L = window.ekarusLang || "en";
        var title = (L !== "en" && h["title_" + L]) || h.title, text = (L !== "en" && h["text_" + L]) || h.text;
        if (title) { var b = document.createElement("strong"); b.textContent = title; li.appendChild(b); }
        if (text) li.appendChild(document.createTextNode(" " + text));
        if (h.image && h.image.src) {
          var img = document.createElement("img");
          img.className = "hl-picture";
          img.src = root + h.image.src;
          img.alt = h.image.alt || "";
          img.loading = "lazy";
          li.appendChild(img);
        }
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

  /* ---------- Bench page: switch the detail panel by subsystem.
     Each language block has its own picker; panel ids carry the language ("vis-imager-it"),
     the address keeps the plain name ("#vis-imager") so links work in every language. */
  document.querySelectorAll("[data-subsystems]").forEach(function (picker) {
    var block = picker.closest("[data-lang-block]") || document;
    var lang = block.getAttribute ? (block.getAttribute("data-lang-block") || "en") : "en";
    var suffix = lang === "en" ? "" : "-" + lang;
    var buttons = Array.prototype.slice.call(picker.querySelectorAll("button[data-target]"));
    var panels = Array.prototype.slice.call(block.querySelectorAll(".subsystem-panel"));
    if (!panels.length) return;
    function base(id) { return suffix && id.slice(-suffix.length) === suffix ? id.slice(0, -suffix.length) : id; }

    function show(name, updateHash) {
      var id = name + suffix;
      if (!panels.some(function (p) { return p.id === id; })) id = panels[0].id;
      panels.forEach(function (p) { p.hidden = p.id !== id; });
      buttons.forEach(function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-target") === id ? "true" : "false");
      });
      if (updateHash) history.replaceState(null, "", "#" + base(id));
    }
    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        var id = b.getAttribute("data-target");
        // clicking the selected subsystem again returns to the specifications
        if (b.getAttribute("aria-pressed") === "true") id = panels[0].id;
        show(base(id), true);
      });
    });
    window.addEventListener("hashchange", function () { show(location.hash.slice(1), false); });
    show(location.hash.slice(1), false);
  });

  /* ---------- To-do page: the list comes live from the Google spreadsheet linked on the page.
     The spreadsheet's address is only in that link (pages/todo.html, data-todo-file); the
     first sheet is read, or the one given by "gid=" in the link. Read again every 2 minutes
     while the page is open, and whenever the page comes back into view. */
  var todoLink = document.querySelector("[data-todo-file]");
  var todoTable = document.querySelector("[data-todo-table]");
  var sheetId = todoLink && (todoLink.getAttribute("href").match(/\/spreadsheets\/d\/([A-Za-z0-9_-]+)/) || [])[1];
  if (todoTable && sheetId && window.fetch) {
    var T = window.ekarusT || function (x, v) { if (v) Object.keys(v).forEach(function (k) { x = x.split("{" + k + "}").join(v[k]); }); return x; };
    var gid = (todoLink.getAttribute("href").match(/[#?&]gid=(\d+)/) || [])[1];
    var csvUrl = "https://docs.google.com/spreadsheets/d/" + sheetId + "/gviz/tq?tqx=out:csv" + (gid ? "&gid=" + gid : "");
    var todoNote = document.querySelector("[data-todo-source]");
    var COLS = [                                  // column on the page: names accepted in the sheet
      ["Task", ["task", "to do", "todo", "item", "action", "description"]],
      ["Owner", ["owner", "who", "responsible", "assignee", "assigned to"]],
      ["Due", ["due", "deadline", "due date", "date"]],
      ["Status", ["status", "state"]],
      ["Notes", ["notes", "note", "comments", "comment", "remarks"]]
    ];

    var loadTodo = function () {
      fetch(csvUrl + "&t=" + Date.now(), { cache: "no-store" })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
        .then(function (text) {
          var rows = parseCSV(text).filter(function (r) { return r.some(function (c) { return c.trim(); }); });
          if (!rows.length) throw new Error("empty");
          var head = rows.shift().map(function (h) { return h.trim().toLowerCase(); });
          var cols = COLS.map(function (c) {
            var idx = -1;
            c[1].some(function (name) { idx = head.indexOf(name); return idx > -1; });
            return { label: c[0], idx: idx };
          });
          if (cols[0].idx === -1) cols[0].idx = 0;            // no "Task" header: use the first column
          // show Notes only when the sheet has some
          cols = cols.filter(function (c) {
            return c.label !== "Notes" || (c.idx > -1 && rows.some(function (r) { return (r[c.idx] || "").trim(); }));
          });
          var thead = todoTable.tHead, tr0 = document.createElement("tr");
          cols.forEach(function (c) {
            var th = document.createElement("th"); th.scope = "col"; th.textContent = T(c.label); tr0.appendChild(th);
          });
          thead.textContent = ""; thead.appendChild(tr0);
          var body = todoTable.tBodies[0];
          body.textContent = "";
          rows.forEach(function (r) {
            if (!(r[cols[0].idx] || "").trim()) return;
            var tr = document.createElement("tr");
            cols.forEach(function (c) {
              var v = c.idx > -1 ? (r[c.idx] || "").trim() : "";
              if (c.label === "Status" && /^(done|completed|closed)$/i.test(v)) tr.className = "is-done";
              var td = document.createElement("td");
              td.textContent = v || "—";               // textContent: sheet text is never run as HTML
              tr.appendChild(td);
            });
            body.appendChild(tr);
          });
          var now = new Date();
          if (todoNote) todoNote.textContent = T("Live from the EKARUS To-do spreadsheet, updated at {time}.",
            { time: now.toLocaleTimeString(document.documentElement.lang || undefined, { hour: "2-digit", minute: "2-digit" }) });
        })
        .catch(function () {
          if (todoNote) todoNote.textContent = T("Couldn't read the spreadsheet; showing the last saved list.");
        });
    };
    loadTodo();
    setInterval(loadTodo, 2 * 60 * 1000);
    document.addEventListener("visibilitychange", function () { if (!document.hidden) loadTodo(); });
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
