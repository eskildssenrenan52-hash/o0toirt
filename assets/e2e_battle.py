import json
import re

from playwright.sync_api import sync_playwright

ERRORS = []
SHOTS = "/tmp/shots"

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": 390, "height": 780})
    page = ctx.new_page()
    page.on("console", lambda m: ERRORS.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: ERRORS.append(str(e)))
    page.goto("http://localhost:4200/", wait_until="networkidle")
    page.wait_for_timeout(3500)
    for _ in range(5):
        page.mouse.click(195, 400)
        page.wait_for_timeout(1100)
        if re.search(r"HANGAR", page.inner_text("body"), re.I):
            break
    # ARENA -> partida rapida (batalha garantida)
    page.get_by_text(re.compile("ARENA", re.I)).first.click()
    page.wait_for_timeout(1500)
    page.screenshot(path=f"{SHOTS}/10_modos.png")
    page.get_by_text(re.compile("PARTIDA RAPIDA", re.I)).first.click()
    page.wait_for_timeout(2500)
    page.screenshot(path=f"{SHOTS}/11_brief.png")
    txt = page.inner_text("body")
    print("POS-MODO:", txt[:300].replace("\n", " | "))
    for pat in ["LUTAR", "INICIAR", "COMECAR", "JOGAR", "CONFIRMAR"]:
        loc = page.get_by_text(re.compile(pat, re.I)).first
        if loc.count() and loc.is_visible():
            loc.click()
            page.wait_for_timeout(3000)
            break
    page.screenshot(path=f"{SHOTS}/12_battle.png")
    print("BATALHA:", page.inner_text("body")[:400].replace("\n", " | "))
    # tenta um turno
    for pat in ["ATACAR", "ATAQUE"]:
        loc = page.get_by_text(re.compile(pat, re.I)).first
        if loc.count() and loc.is_visible():
            loc.click()
            page.wait_for_timeout(1200)
            break
    page.screenshot(path=f"{SHOTS}/13_turno.png")
    imgs = page.evaluate(
        "() => [...document.images].map(i=>({s:i.currentSrc,w:i.naturalWidth})).filter(x=>x.s.includes('/robots/')).slice(0,8)"
    )
    print("SPRITES EM CENA:", json.dumps(imgs, ensure_ascii=False))
    broken = page.evaluate(
        "() => [...document.images].filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src).slice(0,8)"
    )
    print("QUEBRADAS:", broken)
    print("ERRORS", json.dumps(ERRORS[:12], ensure_ascii=False))
    b.close()
