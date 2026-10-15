#!/usr/bin/env python3
"""E2E G3 — catalogo de 100 animacoes, 28 VFX e 11 arenas em spritesheet unico.

Confere:
  1. anim.ts expoe 100 AnimSpec e resolve burst/hit/windup para toda familia;
  2. todos os VFX registrados em skills.ts respondem 200 e decodificam 384x96;
  3. todas as arenas de arenas.ts tem _sheet.png 480x1088;
  4. uma batalha real roda turnos com o evento "anim" sem pageerror,
     sem imagem quebrada e sem HTTP >= 400.
"""
import json
import re
import time

from playwright.sync_api import sync_playwright

URL = "http://localhost:4200/"
SHOTS = "/tmp/shots"

errors: list[str] = []
bad_http: list[str] = []

CATALOG = """async () => {
  const anim = await import('/src/web/game/anim.ts');
  const skills = await import('/src/web/game/skills.ts');
  const arenas = await import('/src/web/game/arenas.ts');
  const robots = await import('/src/web/game/robots.ts');
  // todo elemento de chassi tem que resolver para um burst existente
  const elements = [...new Set(robots.ROBOTS.map((r) => r.element))];
  const bursts = elements.map((e) => [e, anim.burstAnimFor(e)]);
  const badBurst = bursts.filter(([, id]) => !anim.animSpec(id));
  const hits = [[10, 100, false], [30, 100, false], [40, 100, true], [5, 100, true], [1, 100, false]]
    .map(([d, m, c]) => anim.hitAnimFor(d, m, c));
  const winds = ['s_a', 's_b', 's_c', 's_d', 's_e', 's_f', 's_g'].map((s) => anim.windupAnimFor(s, 4));
  const bad = [...hits, ...winds, anim.windupAnimFor('x', 30)].filter((id) => !anim.animSpec(id));
  return {
    count: anim.ANIM_COUNT,
    ids: anim.ANIM_IDS,
    elements: elements.length,
    distinctBursts: new Set(bursts.map(([, id]) => id)).size,
    badBurst,
    hits,
    winds,
    badResolved: bad,
    vfx: Object.values(skills.VFX),
    elementVfx: ['FOGO','GELO','TROVAO','TERRA','VENTO','AGUA','VENENO','CRISTAL','PLASMA','METAL','BIO','COSMICO','SOM','TEMPO','SANGUE','FORTALEZA','LUZ','METEORO','SOMBRA','VAZIO','ZZQQ'].map((e) => [e, skills.vfxForElement(e)]),
    arenas: arenas.ARENA_IDS,
    arenaElements: ['AREIA','GELO','TEMPESTADE','FERRUGEM','CRISTAL','AGUA','SAMURAI','NEBULOSA','CHAMA','CEU','BIO','XXYY'].map((e) => [e, arenas.arenaForElement(e, e)]),
  };
}"""

PROBE_EVENTS = """async () => {
  const battle = await import('/src/web/game/battle.ts');
  const anim = await import('/src/web/game/anim.ts');
  const skills = await import('/src/web/game/skills.ts');
  const sv = (id, level) => ({ id, level, xp: 0, trained: { str: 0, def: 0, agl: 0 } });
  let st = battle.createBattle({
    arena: 'storm',
    playerTeam: [sv('aurorion', 40), sv('titanox', 40)],
    enemyTeam: [sv('bioreaper', 40), sv('cryolance', 40)],
    items: { potion_small: 3 },
  });
  const kinds = {};
  const animIds = new Set();
  const unknown = new Set();
  let turns = 0;
  while (st.phase !== 'over' && turns < 60) {
    const act = st.player.fighters[st.player.active];
    let action;
    if (st.phase === 'forced_swap') {
      const idx = st.player.fighters.findIndex((f) => f.hp > 0);
      if (idx < 0) break;
      action = { kind: 'swap', index: idx };
    } else if (turns === 3) {
      action = { kind: 'item', itemId: 'potion_small', targetIndex: st.player.active };
    } else if (turns === 5) {
      const idx = st.player.fighters.findIndex((f, i) => f.hp > 0 && i !== st.player.active);
      action = idx >= 0
        ? { kind: 'swap', index: idx }
        : { kind: 'skill', skillId: act.skillIds[0] };
    } else {
      action = { kind: 'skill', skillId: act.skillIds[turns % act.skillIds.length] };
    }
    const res = battle.resolveTurn(st, action);
    st = res.battle;
    for (const ev of res.events) {
      kinds[ev.t] = (kinds[ev.t] ?? 0) + 1;
      if (ev.t === 'anim') {
        animIds.add(ev.id);
        if (!anim.animSpec(ev.id)) unknown.add(ev.id);
      }
    }
    turns += 1;
  }
  return {
    turns,
    kinds,
    distinctAnims: animIds.size,
    unknown: [...unknown],
    sample: [...animIds].slice(0, 24),
    phase: st.phase,
    result: st.result,
  };
}"""

with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", args=["--no-sandbox"])
    ctx = br.new_context(viewport={"width": 390, "height": 800})
    pg = ctx.new_page()
    pg.on("console", lambda m: errors.append(f"console:{m.text}") if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append(f"pageerror:{e}"))
    pg.on(
        "response",
        lambda r: bad_http.append(f"{r.status} {r.url}") if r.status >= 400 else None,
    )
    pg.goto(URL, wait_until="domcontentloaded")
    time.sleep(1.5)

    cat = pg.evaluate(CATALOG)
    print(
        "animacoes:", cat["count"],
        "| elementos de chassi:", cat["elements"],
        "| bursts distintos:", cat["distinctBursts"],
    )
    assert cat["count"] == 100, f"catalogo deveria ter 100 animacoes: {cat['count']}"
    assert len(set(cat["ids"])) == 100, "ids de animacao duplicados"
    assert not cat["badBurst"], f"elemento sem burst valido: {cat['badBurst'][:5]}"
    assert not cat["badResolved"], f"hit/windup invalido: {cat['badResolved']}"
    assert cat["distinctBursts"] >= 12, f"pouca variedade de burst: {cat['distinctBursts']}"
    assert len(set(cat["hits"])) == 5, f"hitAnimFor nao diferencia faixas: {cat['hits']}"

    vfx = sorted(set(cat["vfx"]))
    print("vfx registrados:", len(vfx))
    assert len(vfx) >= 28, f"esperava >= 28 vfx, achei {len(vfx)}"

    # cada vfx responde 200 e tem a tira 384x96
    probe_img = """async (list) => {
      const out = [];
      for (const src of list) {
        const r = await fetch(src);
        const ok = r.ok;
        let dim = null;
        if (ok) {
          const blob = await r.blob();
          const bmp = await createImageBitmap(blob);
          dim = [bmp.width, bmp.height];
        }
        out.push([src, ok, dim]);
      }
      return out;
    }"""
    for src, ok, dim in pg.evaluate(probe_img, vfx):
        assert ok, f"vfx nao carregou: {src}"
        assert dim == [384, 96], f"vfx com dimensao errada: {src} -> {dim}"
    print("todos os vfx 384x96 OK")

    sheets = [f"/arenas/{a}_sheet.png" for a in cat["arenas"]]
    print("arenas:", cat["arenas"])
    assert len(cat["arenas"]) == 11, f"esperava 11 arenas: {cat['arenas']}"
    for src, ok, dim in pg.evaluate(probe_img, sheets):
        assert ok, f"arena nao carregou: {src}"
        assert dim == [480, 1088], f"sheet com dimensao errada: {src} -> {dim}"
    print("todos os sheets de arena 480x1088 OK")

    print("vfx por elemento:", json.dumps(cat["elementVfx"], ensure_ascii=False))
    assert all(v for _, v in cat["elementVfx"]), "vfxForElement devolveu vazio"
    print("arena por elemento:", json.dumps(cat["arenaElements"], ensure_ascii=False))
    assert all(v for _, v in cat["arenaElements"]), "arenaForElement devolveu vazio"

    ev = pg.evaluate(PROBE_EVENTS)
    print("simulacao:", json.dumps(ev, ensure_ascii=False)[:800])
    assert ev["kinds"].get("anim", 0) > 0, "nenhum evento de animacao emitido"
    assert not ev["unknown"], f"evento anim com id fora do catalogo: {ev['unknown']}"
    assert ev["distinctAnims"] >= 15, f"pouca variedade de animacao: {ev['distinctAnims']}"

    # ---- batalha real na UI
    for _ in range(6):
        pg.mouse.click(195, 400)
        pg.wait_for_timeout(900)
        if re.search(r"HANGAR", pg.inner_text("body"), re.I):
            break
    pg.get_by_text(re.compile("ARENA", re.I)).first.click()
    pg.wait_for_timeout(1200)
    pg.get_by_text(re.compile("PARTIDA RAPIDA", re.I)).first.click()
    pg.wait_for_timeout(2000)
    for pat in ["LUTAR", "INICIAR", "COMECAR", "JOGAR", "CONFIRMAR"]:
        loc = pg.get_by_text(re.compile(pat, re.I)).first
        if loc.count() and loc.is_visible():
            loc.click()
            pg.wait_for_timeout(2500)
            break
    pg.screenshot(path=f"{SHOTS}/g3_00_battle.png")

    shots = 0
    for turn in range(6):
        hit = False
        for pat in ["ATACAR", "ATAQUE"]:
            loc = pg.get_by_text(re.compile(pat, re.I)).first
            if loc.count() and loc.is_visible():
                loc.click()
                hit = True
                break
        if not hit:
            break
        pg.wait_for_timeout(260)
        shots += 1
        pg.screenshot(path=f"{SHOTS}/g3_{shots:02d}_anim.png")
        pg.wait_for_timeout(1800)

    layers = pg.evaluate(
        "() => ({ vfx: document.querySelectorAll('.mk-a').length, sheets: [...document.querySelectorAll('div')].filter(d=>(d.style.backgroundImage||'').includes('_sheet.png')).length })"
    )
    print("camadas em cena:", json.dumps(layers))

    broken = pg.evaluate(
        "() => [...document.images].filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src).slice(0,10)"
    )
    print("imagens quebradas:", broken)
    assert not broken, f"imagem quebrada: {broken}"

    bad = [u for u in bad_http if "favicon" not in u]
    print("http>=400:", bad[:10])
    assert not bad, f"http ruim: {bad[:5]}"
    assert not errors, f"erros: {errors[:8]}"
    br.close()

print("OK BATALHA G3")
