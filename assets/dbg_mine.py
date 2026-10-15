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
    pg = b.new_context(viewport={"width": 390, "height": 780}).new_page()
    logs = []
    pg.on("console", lambda m: logs.append(f"[{m.type}] {m.text}"))
    pg.on("pageerror", lambda e: logs.append("[pageerror] " + str(e)))
    pg.goto("http://localhost:4200/", wait_until="domcontentloaded")
    pg.evaluate("([k,v])=>localStorage.setItem(k,v)", [SAVE_KEY, json.dumps(SAVE)])
    pg.reload(wait_until="networkidle")
    time.sleep(9)
    for attempt in range(4):
        ok = pg.evaluate(CLICK, "MINA PROFUNDA")
        time.sleep(3.5)
        has = pg.evaluate("()=>document.body.innerText.includes('CAMADA')||document.body.innerText.includes('SILO')")
        print("attempt", attempt, "click", ok, "mineVisible", has)
        if has:
            break
    print("TEXT:", repr(pg.inner_text("body"))[:700])
    print("MODAL HTML:", pg.evaluate(
        "()=>{const d=[...document.querySelectorAll('div')].find(e=>e.style.zIndex==='20');return d? d.innerHTML.slice(0,900):'no-modal';}"))
    pg.screenshot(path="/tmp/dbg_mine.png")
    print("LOGS:")
    for l in logs[-15:]:
        print(" ", l[:250])
    b.close()
