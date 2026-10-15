"""E2E Fase E: sala de mineracao em tempo real."""
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

    print("mina:", pg.evaluate(CLICK, "MINA PROFUNDA"))
    time.sleep(2.5)
    pg.screenshot(path="/tmp/mine_a.png")

    def stored():
        return pg.evaluate("""()=>{const t=document.body.innerText.match(/SILO[^\\n]*/);return t?t[0]:null;}""")

    print("silo antes:", stored())
    # bate nos veios, um clique por render (a picareta faz 8 de dano)
    for i in range(16):
        pg.evaluate("""()=>{const v=[...document.querySelectorAll('[aria-label^="veio de"]')]
          .filter(e=>e.style.opacity!=='0.22'); if(v.length) v[0].click();}""")
        time.sleep(0.3)
    time.sleep(0.6)
    pg.screenshot(path="/tmp/mine_b.png")
    print("silo depois:", stored())
    print("minerios:", pg.evaluate(
        "()=>{const t=document.body.innerText.match(/ESTOQUE VALE[^\\n]*/);return t?t[0]:null;}"))

    # abas
    for tab, shot in (("PERFURATRIZ", "c"), ("REFINO", "d"), ("ESTOQUE", "e")):
        print(tab, pg.evaluate(CLICK, tab))
        time.sleep(1.2)
        pg.screenshot(path=f"/tmp/mine_{shot}.png")

    # compra de perfuratriz na aba PERFURATRIZ
    print("aba perf", pg.evaluate(CLICK, "PERFURATRIZ"))
    time.sleep(1)
    print("comprou drill:", pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')]
      .filter(e=>/^[0-9]+g$/.test((e.textContent||'').trim())&&!e.disabled);
      if(!b.length) return false; b[0].click(); return true;}"""))
    time.sleep(1)
    pg.screenshot(path="/tmp/mine_f.png")
    print("estado:", pg.evaluate(
        "()=>{const s=JSON.parse(localStorage.getItem('campeoes-mecha-save-v1'));return JSON.stringify(s.mining);}"))

    stats = pg.evaluate("""()=>{const im=[...document.images];
      return {total: im.length,
        broken: im.filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src.slice(-40))};}""")
    print("IMGS", json.dumps(stats)[:600])
    print("ERRORS", errs[:8])
    b.close()
