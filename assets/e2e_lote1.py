"""E2E Fase D lote 1: verifica os 30 robos novos no HANGAR (roster 250)."""
import json, time
from playwright.sync_api import sync_playwright

SAVE_KEY = "campeoes-mecha-save-v1"
SAVE = {
    "version": 2, "gold": 999999, "playerLevel": 40, "playerXP": 0,
    "robots": [{"id": i, "level": 20, "xp": 0, "trained": {"str": 0, "def": 0, "agl": 0}}
               for i in ("aurorion", "ferrovax", "kagemaru", "templarion")],
    "team": ["aurorion", "ferrovax", "kagemaru", "templarion"],
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
    time.sleep(8)
    for _ in range(8):
        if pg.get_by_text("ENTRAR", exact=False).count():
            break
        try:
            pg.mouse.click(195, 700)
        except Exception:
            pass
        time.sleep(1)
    time.sleep(2)

    count = pg.evaluate("""async()=>{const m=await import('/src/web/game/robots.ts');
      return m.ROBOTS.length;}""")
    print("ROBOTS no jogo:", count)

    print("hangar:", pg.evaluate(CLICK, "HANGAR"))
    time.sleep(2)
    pg.screenshot(path="/tmp/lote1_a.png")

    box = pg.query_selector("input")
    if box:
        box.fill("KAGEMARU")
        time.sleep(2)
        pg.screenshot(path="/tmp/lote1_b.png")
        pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')]
          .filter(e=>(e.textContent||'').includes('KAGEMARU'));if(b.length)b[b.length-1].click();}""")
        time.sleep(1.5)
        pg.screenshot(path="/tmp/lote1_c.png")
        box = pg.query_selector("input")
        box.fill("TEMPLARION")
        time.sleep(2)
        pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')]
          .filter(e=>(e.textContent||'').includes('TEMPLARION'));if(b.length)b[b.length-1].click();}""")
        time.sleep(1.5)
        pg.screenshot(path="/tmp/lote1_d.png")
        box = pg.query_selector("input")
        box.fill("")
        time.sleep(1.5)

    for i in range(2):
        print("mostrar mais", i, pg.evaluate(CLICK, "MOSTRAR MAIS"))
        time.sleep(2)
    pg.screenshot(path="/tmp/lote1_e.png")

    stats = pg.evaluate("""()=>{const im=[...document.images];
      return {total: im.length,
        broken: im.filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src.slice(-40))};}""")
    print("IMGS", json.dumps(stats)[:600])
    txt = pg.evaluate("()=>document.body.innerText.match(/COLECAO[^\\n]*/)")
    print("COLECAO:", txt)
    print("ERRORS", errs[:8])
    b.close()
