/* EKARUS wiki — site settings.
   Edit these values; no other file needs to change for them. */
window.EKARUS_CONFIG = {
  // Who receives access requests from the "Request access" form.
  adminEmail: "oleksandra.rebrysh@inaf.it",

  // Subject line used for access-request e-mails.
  requestSubject: "EKARUS wiki: access request",

  // Address of the observation scheduler (separate app). Empty = the button shows
  // pages/observation-schedule.html ("not online yet") instead.
  schedulerUrl: "",

  // GitHub repository of this site, as "owner/name" (e.g. "oleksandra-rebrysh/ekarus").
  // Used for the link to templates/EKARUS_todo.xlsx on the To-do page.
  githubRepo: "alphaCassi/ekarus",
  githubBranch: "main",

  // To-do list: the Google Sheet's "Publish to web" CSV link (File > Share > Publish to web >
  // sheet "To do" > Comma-separated values). Empty = the page shows the list written in todo.html.
  todoSheetUrl: "",

  // Page opened after a successful sign-in (relative to the site root).
  homePage: "home.html"
};
