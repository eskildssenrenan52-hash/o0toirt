import json, time
from playwright.sync_api import sync_playwright

SAVE_KEY = "campeoes-mecha-save-v1"
OUT = "/tmp/e2e_cards"


def jsclick(pg, text, exact=True, nth=0):
    ok = pg.evaluate(
        """([t, exact, nth]) => {
      const els = Array.from(document.querySelectorAll('button'));
      const hit = els.filter(e => exact ? e.innerText.trim() === t : e.innerText.includes(t));
      if (!hit.length) return false;
      const el = nth < 0 ? hit[hit.length - 1] : (hit.length > nth ? hit[nth] : null);
      if (!el) return false;
      el.click();
      return true;
    }""",
        [text, exact, nth],
    )
    time.sleep(1.0)
    return ok


with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": 390, "height": 780})
    pg = ctx.new_page()
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append(str(e)))

    pg.goto("http://localhost:4200/", wait_until="networkidle")
    raw = None
    for _ in range(30):
        raw = pg.evaluate(f"localStorage.getItem({json.dumps(SAVE_KEY)})")
        if raw:
            break
        try:
            pg.mouse.click(195, 700)
        except Exception:
            pass
        time.sleep(1)
    print("save encontrado:", bool(raw))
    st = json.loads(raw) if raw else {
        "version": 2,
        "robots": [
            {"id": i, "level": 20, "xp": 0, "trained": {"str": 0, "def": 0, "agl": 0}}
            for i in (1, 2, 3, 4)
        ],
        "team": [1, 2, 3, 4],
        "items": {"repair_kit": 2, "energy_cell": 1},
        "wonTournaments": [],
        "battlesWon": 0,
    }
    st["gold"] = 999999
    st["playerLevel"] = 60
    st["cards"] = []
    st["deck"] = []
    pg.evaluate("([k,v]) => localStorage.setItem(k, v)", [SAVE_KEY, json.dumps(st)])
    pg.reload(wait_until="networkidle")
    time.sleep(4)
    for _ in range(6):
        try:
            pg.mouse.click(195, 700)
        except Exception:
            pass
        time.sleep(0.6)
        if pg.get_by_text("ENTRAR", exact=False).count():
            break
    pg.screenshot(path=f"{OUT}_00_hub.png")

    print("atalho cards:", jsclick(pg, "SALAO DE CARDS"))
    time.sleep(2.5)
    pg.screenshot(path=f"{OUT}_01_tela.png")
    body = pg.inner_text("body")
    print("tem ENERGIA:", "ENERGIA" in body)

    print("aba loja:", jsclick(pg, "LOJA", True, -1))
    pg.screenshot(path=f"{OUT}_02_loja.png")

    bought = 0
    for i in range(30):
        n = pg.evaluate(
            "document.querySelectorAll(\"button:has(img[src^='/cards/'])\").length"
        )
        if i >= n:
            break
        pg.evaluate(
            "(i) => document.querySelectorAll(\"button:has(img[src^='/cards/'])\")[i].click()",
            i,
        )
        time.sleep(1.0)
        if jsclick(pg, "COMPRAR", False, -1):
            if jsclick(pg, "EQUIPAR", True, -1):
                bought += 1
        jsclick(pg, "FECHAR", True, -1)
        if bought >= 3:
            break
    print("comprados+equipados:", bought)
    time.sleep(1)
    pg.screenshot(path=f"{OUT}_03_deck.png")

    body = pg.inner_text("body")
    print("--- topo ---")
    print(body[:700])

    save = json.loads(pg.evaluate(f"localStorage.getItem({json.dumps(SAVE_KEY)})"))
    print("deck salvo:", save.get("deck"))

    broken = pg.evaluate(
        "Array.from(document.images).filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src)"
    )
    print("IMAGENS QUEBRADAS", broken)
    print("ERRORS", errs[:10])
    b.close()
