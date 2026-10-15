"""E2E Fase F: laboratorio de construcao de robos."""
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
    "mining": {"bars": {"ferro": 60, "cobre": 40}},
}

CLICK = """(txt)=>{const b=[...document.querySelectorAll('button')]
 .filter(e=>e.textContent.includes(txt)&&!e.disabled);
 if(!b.length) return false; b[b.length-1].click(); return true;}"""

ARROW = """(lbl)=>{const b=[...document.querySelectorAll('button')]
 .filter(e=>(e.getAttribute('aria-label')||'')===lbl&&!e.disabled);
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

    print("lab:", pg.evaluate(CLICK, "LABORATORIO"))
    time.sleep(2.5)
    pg.screenshot(path="/tmp/lab_a.png")

    def sprite_info():
        return pg.evaluate("""()=>{const im=[...document.images]
          .filter(i=>(i.src||'').startsWith('data:image/png'));
          return im.map(i=>[i.naturalWidth,i.naturalHeight]);}""")

    print("sprites preview:", sprite_info())

    def power():
        t = pg.evaluate("()=>{const m=document.body.innerText.match(/POT [0-9]+/);return m?m[0]:null;}")
        return t

    print("pot inicial:", power())

    # troca de pecas pelos carrosseis
    for lbl in ("CABECA proximo", "TORSO proximo", "BRACOS proximo",
                "PERNAS proximo", "MODULO proximo", "PALETA proximo", "NUCLEO proximo"):
        ok = pg.evaluate(ARROW, lbl)
        time.sleep(0.45)
        print(lbl, ok, power())
    pg.screenshot(path="/tmp/lab_b.png")
    print("sprites apos troca:", sprite_info())

    # nome + construir
    pg.fill('input[aria-label="nome do chassi"]', "TESTAO")
    time.sleep(0.4)
    print("custo:", pg.evaluate(
        "()=>{const m=document.body.innerText.match(/[0-9]+g\\n[0-9]+ LINGOTES[^\\n]*/);return m?m[0]:null;}"))
    print("construir:", pg.evaluate(CLICK, "CONSTRUIR"))
    time.sleep(2)
    pg.screenshot(path="/tmp/lab_c.png")

    save = pg.evaluate("()=>JSON.parse(localStorage.getItem('campeoes-mecha-save-v1'))")
    print("customs:", json.dumps(save.get("customs", [])))
    print("robots:", [r["id"] for r in save.get("robots", [])])
    print("bars:", save.get("mining", {}).get("bars"))

    print("hangar tab:", pg.evaluate(CLICK, "PROTOTIPOS"))
    time.sleep(1.5)
    pg.screenshot(path="/tmp/lab_d.png")
    print("sprites hangar:", sprite_info())

    # volta ao hub e confere o robo no HANGAR do jogo
    print("voltar:", pg.evaluate(CLICK, "VOLTAR"))
    time.sleep(1.5)
    print("hangar:", pg.evaluate(CLICK, "HANGAR"))
    time.sleep(2.5)
    print("tem TESTAO:", pg.evaluate("()=>document.body.innerText.includes('TESTAO')"))
    pg.screenshot(path="/tmp/lab_e.png")

    stats = pg.evaluate("""()=>{const im=[...document.images];
      return {total: im.length,
        broken: im.filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src.slice(-40))};}""")
    print("IMGS", json.dumps(stats)[:600])
    print("ERRORS", errs[:8])
    b.close()
