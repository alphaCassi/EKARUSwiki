# EKARUSwiki

```
docs/        The wiki pages: static, published by GitHub Pages (Settings → Pages → folder /docs)
server/      The EKARUSwiki server: the Observation Schedule site (its own address), team
             sign-in check, admin pages, contact form. Docker setup: server/LINUX_SETUP.md
```

The wiki (internal, for the team) works on its own. Its active parts (team sign-in check, Admin,
Contact us, access requests, the Calendar & proposals site) work when the server is running
and its address is set as `serverUrl` in `docs/assets/js/config.js`.

Details: `docs/README.md` (editing and publishing the wiki) and `server/README.md`
(running the server, on your PC or on a server).
