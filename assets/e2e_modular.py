"""E2E Fase D: verifica os robos modulares compostos em runtime."""
import json, time
from playwright.sync_api import sync_playwright

SAVE_KEY = "campeoes-mecha-save-v1"
SAVE = {
    "version": 2, "gold": 999999, "playerLevel": 40, "playerXP": 0,
    "robots": [{"id": i, "level": 20, "xp": 0, "trained": {"str": 0, "def": 0, "agl": 0}}
               for i in ("aurorion", "ferrovax", "cryolance", "voltronin")],
    "team": ["aurorion", "ferrovax", "cryolance", "voltronin"],
    "items": {"repair_kit": 3, "energy_cell": 2},
    "wonTournaments": [], "battlesWon": 10, "cards": [], "deck": [],
}

CLICK = """(txt)=>{const b=[...document.querySelectorAll('button')]
 .filter(e=>e.textContent.includes(txt)&&!e.disabled);
 if(!b.length) return false; b[b.length-1].click(); return true;}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": 390, "height": 780})
    pg = ctx.new_page()
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://localhost:4200/", wait_until="domcontentloaded")
    pg.evaluate("([k,v])=>localStorage.setItem(k,v)", [SAVE_KEY, json.dumps(SAVE)])
    pg.reload(wait_until="networkidle")
    time.sleep(6)
    for _ in range(8):
        if pg.get_by_text("ENTRAR", exact=False).count():
            break
        try:
            pg.mouse.click(195, 700)
        except Exception:
            pass
        time.sleep(1)
    time.sleep(2)
    pg.screenshot(path="/tmp/mod_a.png")

    # HANGAR pelo atalho do hub
    print("hangar:", pg.evaluate(CLICK, "HANGAR"))
    time.sleep(2)
    pg.screenshot(path="/tmp/mod_b.png")

    # avanca a paginacao ate entrar na faixa modular
    for i in range(3):
        ok = pg.evaluate(CLICK, "MOSTRAR MAIS")
        time.sleep(1.5)
        print("mostrar mais", i, ok)
    time.sleep(1)
    pg.screenshot(path="/tmp/mod_c.png")

    stats = pg.evaluate("""()=>{const im=[...document.images];
      return {total: im.length,
        data: im.filter(i=>i.src.startsWith('data:image/png')).length,
        broken: im.filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src.slice(0,60)),
        sample: im.filter(i=>i.src.startsWith('data:image/png')).slice(0,3).map(i=>[i.naturalWidth,i.naturalHeight])};}""")
    print("IMGS", json.dumps(stats)[:600])

    # foca um robo modular e abre o rodape
    names = pg.evaluate("""()=>[...document.querySelectorAll('button')]
      .map(e=>e.textContent).filter(t=>/-\\d+/.test(t||'')).slice(0,5)""")
    print("nomes modulares:", names)
    pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')]
      .filter(e=>/-\\d+/.test(e.textContent||''));if(b.length)b[b.length-1].click();}""")
    time.sleep(1.5)
    pg.screenshot(path="/tmp/mod_d.png")

    # busca por nome modular
    box = pg.query_selector("input")
    if box:
        box.fill("VOLT")
        time.sleep(1.5)
        pg.screenshot(path="/tmp/mod_e.png")

    print("ERRORS", errs[:8])
    b.close()
