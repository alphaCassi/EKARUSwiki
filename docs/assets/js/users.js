/* EKARUS wiki — registered users.
   Each entry is the SHA-256 hash of a lower-case e-mail address, so the
   addresses themselves are not written in the repository.

   Do not edit by hand: use   python tools/manage_users.py add someone@inaf.it
   (see README.md, "Registering users").

   NOTE: this list only controls the sign-in screen. GitHub Pages serves every
   file publicly, so it is a convenience gate, not real access protection. */
window.EKARUS_USERS = [
  // "<sha256-hex>",  // <optional note, e.g. initials>
  "7eb5a7820761a8952c4384cc23c5775780e66b8faa77287b529b4fc03275115b",
  "915aa61e46e57226c8eca9dd629642016a9956ef336ab5ab27bce329f0db95ff",
];
