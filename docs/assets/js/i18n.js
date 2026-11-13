/* EKARUS wiki: languages (English, Italiano, Français).

   How it works
   - Content pages (Team, Telescope, Bench, ...) hold three blocks in the page itself:
     <div data-lang-block="en">, "it" and "fr". Edit each language there.
   - Menus, buttons, forms and messages are translated with the dictionary below:
     each English phrase with its Italian and French version side by side.
     To change a translation, edit it here. To add a phrase, copy a line.
   - The chosen language is kept in this browser (localStorage "ekarus.lang").

   The French translation was made with AI; the note shown on French pages says so. */
(function () {
  "use strict";

  var NB = "\u00a0";   // no-break space before French : ; ? !

  window.EKARUS_I18N = {
    // ---------- header, menus, footer
    "Skip to content": { it: "Vai al contenuto", fr: "Aller au contenu" },
    "EKARUS home": { it: "Home di EKARUS", fr: "Accueil EKARUS" },
    "Sign out": { it: "Esci", fr: "Se déconnecter" },
    "Project": { it: "Progetto", fr: "Projet" },
    "Activities": { it: "Attività", fr: "Activités" },
    "Team": { it: "Team", fr: "Équipe" },
    "Telescope": { it: "Telescopio", fr: "Télescope" },
    "Bench Architecture": { it: "Architettura del banco", fr: "Architecture du banc" },
    "(opens in a new tab)": { it: "(si apre in una nuova scheda)", fr: "(s’ouvre dans un nouvel onglet)" },
    "Documentation": { it: "Documentazione", fr: "Documentation" },
    "Observation schedule": { it: "Programma osservativo", fr: "Programme d’observation" },
    "Observation Schedule": { it: "Programma osservativo", fr: "Programme d’observation" },
    "Technical nights plan": { it: "Piano delle notti tecniche", fr: "Plan des nuits techniques" },
    "Calendar & proposals": { it: "Calendario e proposte", fr: "Calendrier et propositions" },
    "OAO school": { it: "Scuola OAO", fr: "École OAO" },
    "Main webpage": { it: "Sito principale", fr: "Site principal" },
    "Tutorials": { it: "Tutorial", fr: "Tutoriels" },
    "Publications": { it: "Pubblicazioni", fr: "Publications" },
    "To do’s": { it: "Cose da fare", fr: "À faire" },
    "Contact us": { it: "Contattaci", fr: "Nous contacter" },
    "Partners": { it: "Partner", fr: "Partenaires" },
    "EKARUS – INAF Asiago Astrophysical Observatory": { it: "EKARUS – INAF Osservatorio Astrofisico di Asiago", fr: "EKARUS – INAF Observatoire astrophysique d’Asiago" },
    "EKARUS, INAF Asiago Astrophysical Observatory": { it: "EKARUS, INAF Osservatorio Astrofisico di Asiago", fr: "EKARUS, INAF Observatoire astrophysique d’Asiago" },
    "Instrument": { it: "Strumento", fr: "Instrument" },
    "Operations": { it: "Operazioni", fr: "Opérations" },
    "Schedule": { it: "Programma", fr: "Programme" },
    "Logbook": { it: "Logbook", fr: "Journal de bord" },
    "User Guide": { it: "Guida utente", fr: "Guide d’utilisation" },
    "Language": { it: "Lingua", fr: "Langue" },

    // ---------- page titles (browser tab)
    "Home – EKARUS wiki": { it: "Home – EKARUS wiki", fr: "Accueil – EKARUS wiki" },
    "Team – EKARUS wiki": { it: "Team – EKARUS wiki", fr: "Équipe – EKARUS wiki" },
    "Telescope – EKARUS wiki": { it: "Telescopio – EKARUS wiki", fr: "Télescope – EKARUS wiki" },
    "Bench Architecture – EKARUS wiki": { it: "Architettura del banco – EKARUS wiki", fr: "Architecture du banc – EKARUS wiki" },
    "Documentation – EKARUS wiki": { it: "Documentazione – EKARUS wiki", fr: "Documentation – EKARUS wiki" },
    "Technical nights plan – EKARUS wiki": { it: "Piano delle notti tecniche – EKARUS wiki", fr: "Plan des nuits techniques – EKARUS wiki" },
    "Observation Schedule – EKARUS wiki": { it: "Programma osservativo – EKARUS wiki", fr: "Programme d’observation – EKARUS wiki" },
    "Contact us – EKARUS wiki": { it: "Contattaci – EKARUS wiki", fr: "Nous contacter – EKARUS wiki" },
    "To do’s – EKARUS wiki": { it: "Cose da fare – EKARUS wiki", fr: "À faire – EKARUS wiki" },
    "Publications – EKARUS wiki": { it: "Pubblicazioni – EKARUS wiki", fr: "Publications – EKARUS wiki" },
    "EKARUS wiki – sign in": { it: "EKARUS wiki – accesso", fr: "EKARUS wiki – connexion" },

    // ---------- sign-in page
    "This is an internal webpage to gain easy access to relevant and timely information on the bench.": {
      it: "Questa è una pagina interna per accedere facilmente a informazioni utili e aggiornate sul banco.",
      fr: "Ceci est une page interne pour accéder facilement à des informations utiles et à jour sur le banc." },
    "Your e-mail address": { it: "Il tuo indirizzo e-mail", fr: "Votre adresse e-mail" },
    "Sign in as admin": { it: "Accedi come admin", fr: "Se connecter en tant qu’admin" },
    "Sign in": { it: "Accedi", fr: "Se connecter" },
    "Not registered? Request access": { it: "Non sei registrato? Richiedi l’accesso", fr: "Pas encore inscrit" + NB + "? Demander un accès" },
    "Name": { it: "Nome", fr: "Nom" },
    "E-mail address": { it: "Indirizzo e-mail", fr: "Adresse e-mail" },
    "Institute": { it: "Istituto", fr: "Institut" },
    "Role on EKARUS": { it: "Ruolo in EKARUS", fr: "Rôle dans EKARUS" },
    "Send request": { it: "Invia la richiesta", fr: "Envoyer la demande" },
    "Sign-in needs JavaScript enabled.": { it: "Per accedere serve JavaScript attivo.", fr: "La connexion nécessite JavaScript." },

    // ---------- home
    "Highlights": { it: "In evidenza", fr: "À la une" },
    "News, recent results from observations, and anything the whole team should know.": {
      it: "Notizie, risultati recenti delle osservazioni e tutto ciò che il team dovrebbe sapere.",
      fr: "Actualités, résultats récents des observations et tout ce que l’équipe doit savoir." },
    "31 August – 1 September 2026": { it: "31 agosto – 1 settembre 2026", fr: "31 août – 1er septembre 2026" },
    "Official first light": { it: "Prima luce ufficiale", fr: "Première lumière officielle" },
    "of EKARUS at the Copernico telescope.": { it: "di EKARUS al telescopio Copernico.", fr: "d’EKARUS au télescope Copernico." },
    "Done": { it: "Fatto", fr: "Terminé" },
    "June 2026": { it: "Giugno 2026", fr: "Juin 2026" },
    "Common path aligned in Padova.": { it: "Cammino comune allineato a Padova.", fr: "Chemin commun aligné à Padoue." },
    "Transmitted wavefront error about 55 nm RMS over the 33 mm DM pupil, mostly coma and secondary astigmatism, to be corrected by the DM. Fast tip-tilt mirror tested and integrated.": {
      it: "Errore di fronte d’onda trasmesso di circa 55 nm RMS sulla pupilla del DM da 33 mm, soprattutto coma e astigmatismo secondario, da correggere con il DM. Specchio tip-tilt veloce testato e integrato.",
      fr: "Erreur de front d’onde transmise d’environ 55 nm RMS sur la pupille du DM de 33 mm, surtout de la coma et de l’astigmatisme secondaire, à corriger par le DM. Miroir tip-tilt rapide testé et intégré." },
    "Spring 2026": { it: "Primavera 2026", fr: "Printemps 2026" },
    "DM468 characterized at Arcetri.": { it: "DM468 caratterizzato ad Arcetri.", fr: "DM468 caractérisé à Arcetri." },
    "Best flat about 6 nm RMS wavefront, small actuator print-through, tip-tilt stroke about 15 µm surface.": {
      it: "Miglior flat di circa 6 nm RMS sul fronte d’onda, leggero print-through degli attuatori, corsa tip-tilt di circa 15 µm di superficie.",
      fr: "Meilleur flat d’environ 6 nm RMS sur le front d’onde, léger print-through des actionneurs, course tip-tilt d’environ 15 µm en surface." },
    "See more": { it: "Mostra altro", fr: "Voir plus" },
    "April 2026": { it: "Aprile 2026", fr: "Avril 2026" },
    "Coudé relay upgraded.": { it: "Relay Coudé aggiornato.", fr: "Relais Coudé amélioré." },
    "New L1 and L3 lenses installed to correct the chromatic focus of the old relay. First seeing-limited PSFs (about 1.8″ seeing) show no strong aberrations from the new relay.": {
      it: "Installate le nuove lenti L1 e L3 per correggere il fuoco cromatico del vecchio relay. Le prime PSF limitate dal seeing (seeing di circa 1,8″) non mostrano forti aberrazioni dovute al nuovo relay.",
      fr: "Nouvelles lentilles L1 et L3 installées pour corriger le focus chromatique de l’ancien relais. Les premières PSF limitées par le seeing (environ 1,8″) ne montrent pas de fortes aberrations dues au nouveau relais." },
    "PAPYRUS decommissioned": { it: "PAPYRUS dismesso", fr: "PAPYRUS démantelé" },
    "after reaching almost 65% Strehl at 1450 nm on the T152. Its components were shipped from LAM to Asiago for EKARUS.": {
      it: "dopo aver raggiunto quasi il 65% di Strehl a 1450 nm sul T152. I suoi componenti sono stati spediti dal LAM ad Asiago per EKARUS.",
      fr: "après avoir atteint près de 65" + NB + "% de Strehl à 1450 nm sur le T152. Ses composants ont été envoyés du LAM à Asiago pour EKARUS." },
    "Source:": { it: "Fonte:", fr: "Source" + NB + ":" },
    "They talk about us": { it: "Parlano di noi", fr: "Ils parlent de nous" },
    "Media INAF, 17 Sep 2026": { it: "Media INAF, 17 set 2026", fr: "Media INAF, 17 sept. 2026" },
    "CronacaLive, 17 Sep 2026": { it: "CronacaLive, 17 set 2026", fr: "CronacaLive, 17 sept. 2026" },
    "Marseille Adaptive Optics on LinkedIn": { it: "Marseille Adaptive Optics su LinkedIn", fr: "Marseille Adaptive Optics sur LinkedIn" },
    "EKARUS post by the Marseille Adaptive Optics group": { it: "Post su EKARUS del gruppo Marseille Adaptive Optics", fr: "Publication sur EKARUS du groupe Marseille Adaptive Optics" },
    "See also": { it: "Vedi anche", fr: "Voir aussi" },
    "Project page with the development newsletters: news, results and plans.": {
      it: "Pagina del progetto con le newsletter di sviluppo: notizie, risultati e programmi.",
      fr: "Page du projet avec les newsletters de développement" + NB + ": actualités, résultats et projets." },

    // ---------- contact
    "Something to fix, add or change on the wiki? Tell us here.": { it: "Qualcosa da correggere, aggiungere o cambiare nel wiki? Scrivici qui.", fr: "Quelque chose à corriger, ajouter ou modifier sur le wiki" + NB + "? Écrivez-nous ici." },
    "E-mail": { it: "E-mail", fr: "E-mail" },
    "so we can answer you": { it: "per poterti rispondere", fr: "pour pouvoir vous répondre" },
    "What is it about?": { it: "Di cosa si tratta?", fr: "De quoi s’agit-il" + NB + "?" },
    "Content correction": { it: "Correzione di un contenuto", fr: "Correction d’un contenu" },
    "New content": { it: "Nuovo contenuto", fr: "Nouveau contenu" },
    "Design / layout": { it: "Grafica / impaginazione", fr: "Design / mise en page" },
    "Broken link": { it: "Link non funzionante", fr: "Lien cassé" },
    "Other": { it: "Altro", fr: "Autre" },
    "Which page?": { it: "Quale pagina?", fr: "Quelle page" + NB + "?" },
    "optional": { it: "facoltativo", fr: "facultatif" },
    "Home": { it: "Home", fr: "Accueil" },
    "Whole site": { it: "Tutto il sito", fr: "Tout le site" },
    "Your request": { it: "La tua richiesta", fr: "Votre demande" },
    "Send": { it: "Invia", fr: "Envoyer" },
    "Contacts": { it: "Contatti", fr: "Contacts" },
    "Oleksandra Rebrysh, web developer and content manager,": { it: "Oleksandra Rebrysh, sviluppo web e gestione dei contenuti,", fr: "Oleksandra Rebrysh, développement web et gestion des contenus," },
    "Angelie Mary Alagao, web designer and content manager,": { it: "Angelie Mary Alagao, web design e gestione dei contenuti,", fr: "Angelie Mary Alagao, conception web et gestion des contenus," },

    // ---------- to do's
    "Task": { it: "Attività", fr: "Tâche" },
    "Owner": { it: "Responsabile", fr: "Responsable" },
    "Due": { it: "Scadenza", fr: "Échéance" },
    "Status": { it: "Stato", fr: "Statut" },
    "Open": { it: "Aperto", fr: "Ouvert" },
    "Custom dichroic procurement (0.1° wedge, 15° AOI): follow up supplier quotations": {
      it: "Acquisto del dicroico su misura (cuneo 0,1°, incidenza 15°): seguire i preventivi dei fornitori",
      fr: "Achat du dichroïque sur mesure (prisme 0,1°, incidence 15°)" + NB + ": suivre les devis des fournisseurs" },
    "Design of the segmented mirror path": { it: "Progetto del cammino dello specchio segmentato", fr: "Conception du trajet du miroir segmenté" },
    "Design of the IR WFS channel": { it: "Progetto del canale WFS IR", fr: "Conception de la voie WFS IR" },
    "Software updates": { it: "Aggiornamenti software", fr: "Mises à jour logicielles" },
    "EKARUS To-do spreadsheet": { it: "Foglio di calcolo delle cose da fare di EKARUS", fr: "Tableur des tâches EKARUS" },
    "Notes": { it: "Note", fr: "Notes" },
    "Live from the EKARUS To-do spreadsheet, updated at {time}.": { it: "In diretta dal foglio di calcolo delle cose da fare, aggiornato alle {time}.", fr: "En direct depuis le tableur des tâches, mis à jour à {time}." },
    "Couldn't read the spreadsheet; showing the last saved list.": { it: "Impossibile leggere il foglio di calcolo; viene mostrato l’ultimo elenco salvato.", fr: "Impossible de lire le tableur" + NB + "; affichage de la dernière liste enregistrée." },

    // ---------- publications
    "Filter publications": { it: "Filtra le pubblicazioni", fr: "Filtrer les publications" },
    "Search": { it: "Cerca", fr: "Rechercher" },
    "Title, author or conference": { it: "Titolo, autore o conferenza", fr: "Titre, auteur ou conférence" },
    "Year": { it: "Anno", fr: "Année" },
    "All years": { it: "Tutti gli anni", fr: "Toutes les années" },
    "Author": { it: "Autore", fr: "Auteur" },
    "All authors": { it: "Tutti gli autori", fr: "Tous les auteurs" },
    "Type": { it: "Tipo", fr: "Type" },
    "All types": { it: "Tutti i tipi", fr: "Tous les types" },
    "Refereed papers": { it: "Articoli con referee", fr: "Articles à comité de lecture" },
    "Proceedings": { it: "Atti di convegno", fr: "Actes de conférence" },
    "Posters": { it: "Poster", fr: "Posters" },
    "Talks": { it: "Presentazioni", fr: "Exposés" },
    "Sort by": { it: "Ordina per", fr: "Trier par" },
    "Newest first": { it: "Più recenti prima", fr: "Plus récentes d’abord" },
    "Oldest first": { it: "Meno recenti prima", fr: "Plus anciennes d’abord" },
    "Title A–Z": { it: "Titolo A–Z", fr: "Titre A–Z" },
    "First author A–Z": { it: "Primo autore A–Z", fr: "Premier auteur A–Z" },
    "Include works that mention EKARUS": { it: "Includi i lavori che citano EKARUS", fr: "Inclure les travaux qui mentionnent EKARUS" },
    "Clear filters": { it: "Azzera i filtri", fr: "Effacer les filtres" },
    "No publication matches these filters.": { it: "Nessuna pubblicazione corrisponde a questi filtri.", fr: "Aucune publication ne correspond à ces filtres." },
    "The publication list needs JavaScript.": { it: "L’elenco delle pubblicazioni richiede JavaScript.", fr: "La liste des publications nécessite JavaScript." },
    "To add a publication, edit": { it: "Per aggiungere una pubblicazione, modifica", fr: "Pour ajouter une publication, modifiez" },
    ". Sources: SPIE Astronomical Telescopes + Instrumentation 2026, HAL, Zenodo.": { it: ". Fonti: SPIE Astronomical Telescopes + Instrumentation 2026, HAL, Zenodo.", fr: ". Sources" + NB + ": SPIE Astronomical Telescopes + Instrumentation 2026, HAL, Zenodo." },
    "Refereed paper": { it: "Articolo con referee", fr: "Article à comité de lecture" },
    "Poster": { it: "Poster", fr: "Poster" },
    "Talk": { it: "Presentazione", fr: "Exposé" },
    "Mentions EKARUS": { it: "Cita EKARUS", fr: "Mentionne EKARUS" },
    ", DOI not yet available": { it: ", DOI non ancora disponibile", fr: ", DOI pas encore disponible" },
    "{n} publication": { it: "{n} pubblicazione", fr: "{n} publication" },
    "{n} publications": { it: "{n} pubblicazioni", fr: "{n} publications" },
    " of {m}": { it: " su {m}", fr: " sur {m}" },
    "and {n} more": { it: "e altri {n}", fr: "et {n} autres" },

    // ---------- messages from the sign-in and contact forms
    "Enter your e-mail address.": { it: "Inserisci il tuo indirizzo e-mail.", fr: "Saisissez votre adresse e-mail." },
    "This address isn't on the team list. Request access below.": { it: "Questo indirizzo non è nell’elenco del team. Richiedi l’accesso qui sotto.", fr: "Cette adresse ne figure pas dans la liste de l’équipe. Demandez un accès ci-dessous." },
    "Admin sign-in needs the EKARUS server, which isn't connected to the wiki.": { it: "L’accesso admin richiede il server EKARUS, che non è collegato al wiki.", fr: "La connexion admin nécessite le serveur EKARUS, qui n’est pas relié au wiki." },
    "This address isn't an admin. Untick “Sign in as admin” to enter the wiki.": { it: "Questo indirizzo non è di un admin. Togli la spunta da “Accedi come admin” per entrare nel wiki.", fr: "Cette adresse n’est pas celle d’un admin. Décochez «" + NB + "Se connecter en tant qu’admin" + NB + "» pour entrer dans le wiki." },
    "The EKARUS server can't be reached, so admin sign-in isn't possible right now.": { it: "Il server EKARUS non è raggiungibile, quindi l’accesso admin per ora non è possibile.", fr: "Le serveur EKARUS est injoignable" + NB + ": la connexion admin n’est pas possible pour le moment." },
    "Sign-in failed. Please try again.": { it: "Accesso non riuscito. Riprova.", fr: "Échec de la connexion. Veuillez réessayer." },
    "This browser can't check the address. Open the site over https in an up-to-date browser.": { it: "Questo browser non può verificare l’indirizzo. Apri il sito in https con un browser aggiornato.", fr: "Ce navigateur ne peut pas vérifier l’adresse. Ouvrez le site en https dans un navigateur à jour." },
    "Too many attempts from this connection. Please wait a few minutes and try again.": { it: "Troppi tentativi da questa connessione. Attendi qualche minuto e riprova.", fr: "Trop de tentatives depuis cette connexion. Patientez quelques minutes puis réessayez." },
    "Enter a valid e-mail address.": { it: "Inserisci un indirizzo e-mail valido.", fr: "Saisissez une adresse e-mail valide." },
    "Sending isn't available yet: the EKARUSwiki server isn't connected.": { it: "L’invio non è ancora disponibile: il server EKARUSwiki non è collegato.", fr: "L’envoi n’est pas encore disponible" + NB + ": le serveur EKARUSwiki n’est pas connecté." },
    "The server can't be reached. Please try again later.": { it: "Il server non è raggiungibile. Riprova più tardi.", fr: "Le serveur est injoignable. Veuillez réessayer plus tard." },
    "Enter your name and e-mail address.": { it: "Inserisci nome e indirizzo e-mail.", fr: "Saisissez votre nom et votre adresse e-mail." },
    "Request sent. You'll get an e-mail when you're registered.": { it: "Richiesta inviata. Riceverai un’e-mail quando sarai registrato.", fr: "Demande envoyée. Vous recevrez un e-mail une fois inscrit." },
    "Fill in your name, e-mail and request.": { it: "Compila nome, e-mail e richiesta.", fr: "Indiquez votre nom, votre e-mail et votre demande." },
    "Thank you! Your request has been sent to the wiki admins.": { it: "Grazie! La tua richiesta è stata inviata agli admin del wiki.", fr: "Merci" + NB + "! Votre demande a été envoyée aux admins du wiki." },
    "Sending failed. Please try again.": { it: "Invio non riuscito. Riprova.", fr: "Échec de l’envoi. Veuillez réessayer." },

    // ---------- French AI note (shown only on French pages)
    "fr-ai-note": { it: "", fr: "Cette traduction en français a été réalisée avec l’aide d’une IA. Si vous remarquez une erreur, contactez" },
  };

  // ---------------------------------------------------------------- engine
  var LANGS = ["en", "it", "fr"];
  var lang = document.documentElement.getAttribute("data-lang") || "en";
  if (LANGS.indexOf(lang) === -1) lang = "en";
  var dict = window.EKARUS_I18N;

  // T("English text", {n: 3}) -> the current language's text, with {placeholders} filled in
  function T(s, vars) {
    var out = s;
    if (lang !== "en" && dict[s] && dict[s][lang]) out = dict[s][lang];
    if (vars) Object.keys(vars).forEach(function (k) { out = out.split("{" + k + "}").join(vars[k]); });
    return out;
  }
  window.ekarusT = T;
  window.ekarusLang = lang;

  var SKIP = { SCRIPT: 1, STYLE: 1, CODE: 1, TEXTAREA: 1, INPUT: 1 };
  function translateNode(root) {
    if (lang === "en" || !root) return;
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        for (var p = n.parentNode; p && p !== document; p = p.parentNode) {
          if (SKIP[p.nodeName] || (p.hasAttribute && (p.hasAttribute("data-lang-block") || p.hasAttribute("data-no-translate"))))
            return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function (n) {
      var raw = n.nodeValue, core = raw.replace(/\s+/g, " ").trim();
      if (core && dict[core] && dict[core][lang]) {
        var lead = raw.match(/^\s*/)[0], trail = raw.match(/\s*$/)[0];
        n.nodeValue = lead + dict[core][lang] + trail;
      }
    });
    var els = root.querySelectorAll ? root.querySelectorAll("[alt], [aria-label], [title], [placeholder]") : [];
    Array.prototype.forEach.call(els, function (el) {
      if (el.closest("[data-lang-block], [data-no-translate]")) return;
      ["alt", "aria-label", "title", "placeholder"].forEach(function (a) {
        var v = el.getAttribute(a);
        if (v && dict[v.trim()] && dict[v.trim()][lang]) el.setAttribute(a, dict[v.trim()][lang]);
      });
    });
  }

  function addSwitcher() {
    var host = document.querySelector(".site-header") || document.body;
    var box = document.createElement("div");
    box.className = "lang-switch";
    box.setAttribute("role", "group");
    box.setAttribute("aria-label", T("Language"));
    box.setAttribute("data-no-translate", "");
    [["en", "EN", "English"], ["it", "IT", "Italiano"], ["fr", "FR", "Français"]].forEach(function (l) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = l[1];
      b.title = l[2];
      b.lang = l[0];
      b.setAttribute("aria-pressed", l[0] === lang ? "true" : "false");
      b.addEventListener("click", function () {
        if (l[0] === lang) return;
        try { window.localStorage.setItem("ekarus.lang", l[0]); } catch (e) {}
        window.location.reload();
      });
      box.appendChild(b);
    });
    // top right, next to Sign out
    var tools = document.createElement("div");
    tools.className = "header-tools";
    tools.appendChild(box);
    var signout = host.querySelector("[data-signout]");
    if (signout) tools.appendChild(signout);
    host.insertBefore(tools, host.firstChild);
  }

  function addFrenchNote() {
    if (lang !== "fr") return;
    var note = document.createElement("p");
    note.className = "ai-note";
    note.setAttribute("role", "note");
    note.setAttribute("data-no-translate", "");
    note.appendChild(document.createTextNode(dict["fr-ai-note"].fr + " "));
    var a = document.createElement("a");
    a.href = "mailto:oleksandra.rebrysh@inaf.it";
    a.textContent = "Oleksandra Rebrysh (oleksandra.rebrysh@inaf.it)";
    note.appendChild(a);
    note.appendChild(document.createTextNode("."));
    var main = document.querySelector("main");
    if (main) main.insertBefore(note, main.firstChild);
    else document.body.insertBefore(note, document.body.firstChild);
  }

  function start() {
    addSwitcher();
    addFrenchNote();
    if (lang !== "en") {
      if (dict[document.title]) document.title = dict[document.title][lang] || document.title;
      translateNode(document.body);
      // text added later by the page's scripts (messages, lists, highlights)
      new MutationObserver(function (records) {
        records.forEach(function (r) {
          Array.prototype.forEach.call(r.addedNodes, function (n) {
            if (n.nodeType === 1) translateNode(n);
            else if (n.nodeType === 3 && n.parentNode) translateNode(n.parentNode);
          });
          if (r.type === "characterData" && r.target.parentNode) translateNode(r.target.parentNode);
        });
      }).observe(document.body, { childList: true, subtree: true });
      // a link like bench.html#vis-imager points to the English block: follow it in this language
      if (location.hash) {
        var target = document.getElementById(location.hash.slice(1) + "-" + lang);
        if (target) setTimeout(function () { target.scrollIntoView(); }, 0);
      }
    }
    document.documentElement.classList.remove("i18n-pending");
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
