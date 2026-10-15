import json
import re
import time

from playwright.sync_api import sync_playwright

ERRORS = []
SHOTS = "/tmp/shots"
import os

os.makedirs(SHOTS, exist_ok=True)


def shot(page, name):
    page.screenshot(path=f"{SHOTS}/{name}.png")


def click_text(page, pattern, timeout=8000):
    loc = page.get_by_text(re.compile(pattern, re.I)).first
    loc.wait_for(state="visible", timeout=timeout)
    loc.click()
    page.wait_for_timeout(900)


with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": 390, "height": 780})
    page = ctx.new_page()
    page.on("console", lambda m: ERRORS.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: ERRORS.append(str(e)))
    page.goto("http://localhost:4200/", wait_until="networkidle")
    page.wait_for_timeout(4000)
    shot(page, "01_boot")
    # avanca telas de loading/gate clicando no centro
    for i in range(6):
        page.mouse.click(195, 400)
        page.wait_for_timeout(1200)
        shot(page, f"02_step{i}")
        txt = page.inner_text("body")
        if re.search(r"TORNEIO|ROSTER|OFICINA|MODOS|CIDADE|HUB", txt, re.I):
            break
    print("BODY:", page.inner_text("body")[:600].replace("\n", " | "))
    shot(page, "03_hub")

    for label in ["HANGAR", "LOJA", "ARENA", "TORRE RANQUEADA", "COLISEU", "OFICINA DO ENGENHEIRO"]:
        try:
            click_text(page, label)
            page.wait_for_timeout(1200)
            shot(page, "04_" + label.split("|")[0])
            print(label, "->", page.inner_text("body")[:200].replace("\n", " | "))
            # volta
            try:
                click_text(page, r"VOLTAR|<|SAIR", 3000)
            except Exception:
                page.mouse.click(30, 40)
                page.wait_for_timeout(600)
        except Exception as e:
            print("FALHOU", label, type(e).__name__, str(e)[:120])

    # imagens quebradas
    broken = page.evaluate(
        "() => [...document.images].filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src).slice(0,10)"
    )
    print("IMGS QUEBRADAS:", broken)
    print("ERRORS", json.dumps(ERRORS[:15], ensure_ascii=False))
    b.close()
