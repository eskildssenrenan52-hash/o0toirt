import { app as a, ipcMain as r, shell as P, dialog as m, Notification as D, BrowserWindow as w } from "electron";
import h from "node:path";
import { fileURLToPath as E } from "node:url";
import { createServer as I } from "node:http";
import u from "node:fs/promises";
var f = {
  openExternal: "managed-auth:open-external",
  redirectTarget: "managed-auth:redirect-target",
  deepLink: "managed-auth:deep-link"
}, x = (o) => `runable-${o}`;
function A(o) {
  const { getWindow: e } = o, t = o.applicationId ? x(o.applicationId) : void 0, n = (s) => t !== void 0 && s.startsWith(`${t}://`), c = [], l = (s) => {
    const i = e();
    if (!i || i.webContents.isLoading()) {
      c.push(s);
      return;
    }
    i.isMinimized() && i.restore(), i.focus(), i.webContents.send(f.deepLink, s);
  };
  a.on("browser-window-created", (s, i) => {
    i.webContents.once("did-finish-load", () => {
      for (; c.length; )
        l(c.shift());
    });
  });
  const d = o.onDeepLink ?? l, L = (s) => {
    const i = s.find(n);
    i && d(i);
  };
  t && (process.defaultApp && process.argv[1] ? a.setAsDefaultProtocolClient(t, process.execPath, [h.resolve(process.argv[1])]) : a.setAsDefaultProtocolClient(t)), a.on("open-url", (s, i) => {
    n(i) && (s.preventDefault(), d(i));
  }), r.handle(f.openExternal, (s, i) => {
    if (URL.canParse(i) && ["http:", "https:"].includes(new URL(i).protocol))
      return P.openExternal(i);
  });
  const b = a.isPackaged ? void 0 : C(d);
  return r.handle(f.redirectTarget, () => b), { scheme: t, isDeepLink: n, handleArgv: L, sendDeepLink: l };
}
var k = `<!doctype html><meta charset="utf-8"><title>Sign-in complete</title>
<body style="font-family:system-ui;display:grid;place-items:center;min-height:100vh;margin:0;background:#0b0b0c;color:#fafafa">
<p id="msg">Completing sign-in…</p>
<script>
  const hash = location.hash;
  history.replaceState(null, "", "/");
  fetch("/deliver", { method: "POST", body: hash })
    .then(() => { document.getElementById("msg").textContent = "Signed in — return to the app."; })
    .catch(() => { document.getElementById("msg").textContent = "Could not reach the app."; });
<\/script>`;
function C(o) {
  return new Promise((e) => {
    const t = I((n, c) => {
      if (n.method === "POST" && n.url === "/deliver") {
        let l = "";
        n.on("data", (d) => {
          l += d;
        }), n.on("end", () => {
          const d = t.address();
          l.startsWith("#") && d && typeof d == "object" && o(`http://localhost:${d.port}/${l}`), c.writeHead(204).end();
        });
        return;
      }
      c.writeHead(200, { "content-type": "text/html; charset=utf-8" }).end(k);
    });
    t.on("error", () => e(void 0)), t.unref(), t.listen(0, "127.0.0.1", () => {
      const n = t.address();
      e(n && typeof n == "object" ? `http://localhost:${n.port}/` : void 0);
    });
  });
}
function S(o) {
  r.handle("dialog:open", async (e, t) => {
    const n = await m.showOpenDialog(t);
    return n.canceled ? [] : n.filePaths;
  }), r.handle("dialog:save", async (e, t) => {
    const n = await m.showSaveDialog(t);
    return n.canceled ? null : n.filePath;
  }), r.handle("fs:read", async (e, t) => u.readFile(t, "utf-8")), r.handle("fs:write", async (e, t, n) => {
    await u.writeFile(t, n, "utf-8");
  }), r.handle("notification:show", (e, t, n) => {
    new D({ title: t, body: n }).show();
  }), r.handle("window:minimize", () => {
    var e;
    return (e = o()) == null ? void 0 : e.minimize();
  }), r.handle("window:maximize", () => {
    const e = o();
    e != null && e.isMaximized() ? e.unmaximize() : e == null || e.maximize();
  }), r.handle("window:close", () => {
    var e;
    return (e = o()) == null ? void 0 : e.close();
  });
}
const v = h.dirname(E(import.meta.url)), T = process.env.NODE_ENV !== "production", R = process.env.WEBSITE_URL ?? "http://localhost:3000", U = h.join(v, "../web-dist");
let p = null;
const y = () => p, g = A({
  applicationId: process.env.APPLICATION_ID,
  getWindow: y
});
function _() {
  p = new w({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: h.join(v, "preload.mjs"),
      contextIsolation: !0,
      nodeIntegration: !1
    }
  }), T ? p.loadURL(R) : p.loadFile(h.join(U, "index.html"));
}
S(y);
a.on("window-all-closed", () => {
  process.platform !== "darwin" && (a.quit(), p = null);
});
a.on("activate", () => {
  w.getAllWindows().length === 0 && _();
});
a.requestSingleInstanceLock() ? (a.on("second-instance", (o, e) => g.handleArgv(e)), a.whenReady().then(() => {
  _(), g.handleArgv(process.argv);
})) : a.quit();
