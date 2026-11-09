/* EKARUS wiki — site settings.
   Edit these values; no other file needs to change for them. */
window.EKARUS_CONFIG = {
  // Not used any more: access requests and the contact form are sent by the EKARUSwiki
  // server (serverUrl) to the admins listed there in ADMIN_EMAILS.
  adminEmail: "oleksandra.rebrysh@inaf.it",

  // Subject line used for access-request e-mails.
  requestSubject: "EKARUS wiki: access request",

  // Address of the EKARUSwiki server (server/ folder), e.g. "https://ekaruswiki.example.org"
  // or a Cloudflare tunnel address. It runs the wiki's admin pages and the Observation
  // Schedule, and receives the contact form and access requests.
  // Empty = those features show "not available yet".
  serverUrl: "https://ekarus-scheduler.tail5e4104.ts.net",

  // GitHub repository of this site, as "owner/name" (e.g. "oleksandra-rebrysh/ekarus").
  // Used for the link to resources/EKARUS_todo.xlsx on the To-do page.
  githubRepo: "alphaCassi/EKARUSwiki",
  githubBranch: "main",

  // To-do list: the Google Sheet's "Publish to web" CSV link (File > Share > Publish to web >
  // sheet "To do" > Comma-separated values). Empty = the page shows the list written in todo.html.
  todoSheetUrl: "",

  // Page opened after a successful sign-in (relative to the site root).
  homePage: "home.html"
};
