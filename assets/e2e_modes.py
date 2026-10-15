import os
import re

from playwright.sync_api import sync_playwright

ERRORS = []
SHOTS = "/tmp/shots"
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
    for _ in range(6):
        page.mouse.click(195, 400)
        page.wait_for_timeout(1200)
        if re.search(r"HANGAR|COLISEU", page.inner_text("body"), re.I):
            break
    # da ouro para poder adotar
    page.evaluate(
        """() => {
      const k = Object.keys(localStorage).find(k => k.toLowerCase().includes('mecha') || k.toLowerCase().includes('save') || k.toLowerCase().includes('mk'));
      if (!k) return 'sem chave';
      const s = JSON.parse(localStorage.getItem(k));
      s.gold = 999999; s.playerLevel = 99;
      localStorage.setItem(k, JSON.stringify(s));
      return k;
    }"""
    )
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(3500)
    for _ in range(6):
        page.mouse.click(195, 400)
        page.wait_for_timeout(1100)
        if re.search(r"HANGAR|COLISEU", page.inner_text("body"), re.I):
            break
    shot(page, "30_hub")
    click_text(page, "ARENA", 12000)
    page.wait_for_timeout(1500)
    shot(page, "41_modes")
    print("PETS BODY:", page.inner_text("body")[:700].replace("\n", " | "))
    for pat in ["GAUNTLET ELEMENTAL", "LUTAR"]:
        try:
            click_text(page, pat, 4000)
            page.wait_for_timeout(800)
            shot(page, "42_" + pat)
            print("clicou", pat)
        except Exception as e:
            print("nao clicou", pat, type(e).__name__)
    shot(page, "43_modes_after")

    broken = page.evaluate(
        "() => [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.src)"
    )
    pets_imgs = page.evaluate(
        "() => [...document.images].filter(i => i.src.includes('/modes/')).map(i => [i.src.split('/').pop(), i.naturalWidth])"
    )
    print("IMGS QUEBRADAS", broken)
    print("PETS IMGS", pets_imgs)
    print("ERRORS", [e for e in ERRORS][:10])
    b.close()
