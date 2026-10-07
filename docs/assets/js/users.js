/* EKARUS wiki — registered users.
   Each entry is the SHA-256 hash of a lower-case e-mail address, so the
   addresses themselves are not written in the repository.

   Do not edit by hand: use   python tools/manage_users.py add someone@inaf.it
   (see README.md, "Registering users").

   NOTE: this list only controls the sign-in screen. GitHub Pages serves every
   file publicly, so it is a convenience gate, not real access protection. */
window.EKARUS_USERS = [
  // "<sha256-hex>",  // <optional note, e.g. initials>
  "7eb5a7820761a8952c4384cc23c5775780e66b8faa77287b529b4fc03275115b",  // admin
  "66c68c58da26df95d0adb22b79ca6b202410a9b8566743a8f1176d4888747d4e",
];
