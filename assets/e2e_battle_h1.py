#!/usr/bin/env python3
"""E2E H1 — bateria de combate 100x (combat.ts) ponta a ponta.

Confere:
  1. 256 robos geram kit/kit-skill coerentes e todo id de animacao citado
     pelo motor existe no catalogo de anim.ts;
  2. 80 batalhas simuladas (1v1 ate 4v4) terminam com vitoria/derrota;
  3. todas as acoes novas rodam (skill, item, reposicionar, guarda, esquiva,
     cobertura, analise, combo, auto, passar) sem pageerror;
  4. todo VFX emitido responde 200 e todo evento de animacao resolve;
  5. a troca forcada aparece quando o lider cai;
  6. uma batalha real na UI roda turnos sem erro de console, imagem
     quebrada ou HTTP >= 400.
"""
import json
import re
import time

from playwright.sync_api import sync_playwright

URL = "http://localhost:4200/"
SHOTS = "/tmp/shots"

errors: list[str] = []
bad_http: list[str] = []

KITS = """async () => {
  const kits = await import('/src/web/game/kits/index.ts');
  const anim = await import('/src/web/game/anim.ts');
  const robots = await import('/src/web/game/robots.ts');
  const bad = [];
  let skills = 0;
  for (const r of robots.ROBOTS) {
    const kit = kits.kitOf(r.id);
    if (!kit) { bad.push([r.id, 'sem kit']); continue; }
    const list = kits.skillsOf(r.id);
    if (!list.length) bad.push([r.id, 'sem skill']);
    skills += list.length;
  }
  return {
    robots: robots.ROBOTS.length,
    kits: kits.KIT_COUNT,
    skills,
    animCount: anim.ANIM_COUNT,
    bad: bad.slice(0, 10),
  };
}"""

SIM = """async (cfg) => {
  const battle = await import('/src/web/game/battle.ts');
  const combat = await import('/src/web/game/combat.ts');
  const anim = await import('/src/web/game/anim.ts');
  const robots = await import('/src/web/game/robots.ts');

  const rnd = (n) => Math.floor(Math.random() * n);
  const ids = robots.ROBOTS.map((r) => r.id);
  const sv = (id, level) => ({ id, level, xp: 0, trained: { str: 0, def: 0, agl: 0 } });
  const teamOf = (n) => Array.from({ length: n }, () => sv(ids[rnd(ids.length)], 30 + rnd(30)));
  const items = { repair_kit: 3, energy_cell: 2, shield_chip: 1, power_chip: 1, revive_core: 1, purifier: 1 };

  const kinds = {};
  const animIds = new Set();
  const vfxUrls = new Set();
  const unknownAnim = new Set();
  const results = {};
  let forced = 0;
  let turnsMax = 0;
  let legacyTurns = 0;
  let fullTurns = 0;
  const reports = [];
  const fails = [];

  // ---- pass A: API legada (a que a tela usa)
  for (let n = 0; n < cfg.legacy; n += 1) {
    const size = 1 + rnd(4);
    let st;
    try {
      st = battle.createBattle({
        arena: cfg.arenas[rnd(cfg.arenas.length)],
        playerTeam: teamOf(size),
        enemyTeam: teamOf(size),
        items,
      });
    } catch (e) { fails.push(['createBattle', String(e)]); continue; }
    let turns = 0;
    while (st.phase !== 'over' && turns < 300) {
      const f = st.player.fighters[st.player.active] ?? st.player.fighters[0];
      let action;
      if (st.phase === 'forced_swap') {
        forced += 1;
        const idx = st.player.fighters.findIndex((x) => x.hp > 0);
        if (idx < 0) break;
        action = { kind: 'swap', index: idx };
      } else if (turns % 11 === 5) {
        action = { kind: 'item', itemId: 'repair_kit', targetIndex: st.player.active };
      } else if (turns % 13 === 7) {
        const idx = st.player.fighters.findIndex((x, i) => x.hp > 0 && i !== st.player.active);
        action = idx >= 0 ? { kind: 'swap', index: idx } : { kind: 'skill', skillId: f.skillIds[0] };
      } else {
        action = { kind: 'skill', skillId: f.skillIds[turns % f.skillIds.length] };
      }
      let res;
      try { res = battle.resolveTurn(st, action); }
      catch (e) { fails.push(['resolveTurn', String(e)]); break; }
      st = res.battle;
      if (!st.combat) { fails.push(['sem combat no view', '']); break; }
      for (const ev of res.events) {
        kinds[ev.t] = (kinds[ev.t] ?? 0) + 1;
        if (ev.t === 'anim') { animIds.add(ev.id); if (!anim.animSpec(ev.id)) unknownAnim.add(ev.id); }
        if (ev.t === 'vfx') vfxUrls.add(ev.url);
      }
      turns += 1;
    }
    if (st.phase !== 'over') fails.push(['nao terminou', `${turns} turnos  ${size}v${size}`]);
    results[st.result ?? 'nulo'] = (results[st.result ?? 'nulo'] ?? 0) + 1;
    turnsMax = Math.max(turnsMax, turns);
    legacyTurns += turns;
  }

  // ---- pass B: todas as acoes novas via resolveRound
  const acts = [
    () => ({ kind: 'guard' }),
    () => ({ kind: 'dodge' }),
    () => ({ kind: 'analyze' }),
    () => ({ kind: 'pass' }),
    (c, f) => ({ kind: 'skill', skillId: f.skillIds[f.skillIds.length - 1] }),
    (c, f) => ({ kind: 'cover', withUid: c.player.fighters.find((x) => x.hp > 0 && x.uid !== f.uid)?.uid }),
    (c, f) => ({ kind: 'reposition', withUid: c.player.fighters.find((x) => x.hp > 0 && x.uid !== f.uid)?.uid ?? f.uid }),
    (c) => ({ kind: 'item', itemId: 'energy_cell', targetUid: c.player.fighters.find((x) => x.hp > 0)?.uid }),
    (c) => ({ kind: 'combo', targetUid: c.enemy.fighters.find((x) => x.hp > 0)?.uid }),
  ];
  for (let n = 0; n < cfg.full; n += 1) {
    const size = 2 + rnd(3);
    let c;
    try {
      c = combat.createCombat({
        arena: cfg.arenas[rnd(cfg.arenas.length)],
        playerTeam: teamOf(size),
        enemyTeam: teamOf(size),
        items,
        difficulty: cfg.diffs[rnd(cfg.diffs.length)],
      });
    } catch (e) { fails.push(['createCombat', String(e)]); continue; }
    let turns = 0;
    while (c.phase !== 'over' && turns < 300) {
      const ready = combat.readyOf(c);
      if (!ready) break;
      const idx = (n + turns) % acts.length;
      const action = idx === acts.length - 1 && turns < 4 ? { kind: 'auto' } : acts[idx](c, ready);
      let events;
      try { events = combat.resolveRound(c, action); }
      catch (e) { fails.push(['resolveRound', String(e)]); break; }
      for (const ev of events) {
        kinds[ev.t] = (kinds[ev.t] ?? 0) + 1;
        if (ev.t === 'anim') { animIds.add(ev.id); if (!anim.animSpec(ev.id)) unknownAnim.add(ev.id); }
        if (ev.t === 'vfx') vfxUrls.add(ev.url);
      }
      turns += 1;
    }
    if (c.phase !== 'over') fails.push(['B nao terminou', `${turns} turnos`]);
    results['B:' + (c.result ?? 'nulo')] = (results['B:' + (c.result ?? 'nulo')] ?? 0) + 1;
    fullTurns += turns;
    if (reports.length < 3 && c.phase === 'over') {
      const r = combat.battleReport(c);
      const s = combat.combatSummary(combat.readyOf(c));
      reports.push({
        result: r.result,
        rounds: r.rounds,
        timeline: r.timeline.length,
        totals: r.totals,
        summary: s ? Object.keys(s).length : 0,
      });
    }
  }

  return {
    results,
    forced,
    turnsMax,
    avgLegacy: +(legacyTurns / cfg.legacy).toFixed(1),
    avgFull: +(fullTurns / cfg.full).toFixed(1),
    kinds,
    distinctAnims: animIds.size,
    unknownAnim: [...unknownAnim],
    vfx: [...vfxUrls],
    reports,
    fails,
  };
}"""

PROBE_IMG = """async (list) => {
  const out = [];
  for (const src of list) {
    const r = await fetch(src);
    const ok = r.ok;
    let dim = null;
    let err = null;
    if (ok) {
      try {
        const blob = await r.blob();
        const bmp = await createImageBitmap(blob);
        dim = [bmp.width, bmp.height];
      } catch (e) { err = String(e); }
    }
    out.push([src, ok, dim, err, r.headers.get('content-type')]);
  }
  return out;
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
    time.sleep(2.0)

    kits = pg.evaluate(KITS)
    print("robos:", kits["robots"], "| kits:", kits["kits"], "| skills:", kits["skills"],
          "| animacoes:", kits["animCount"])
    assert kits["robots"] == 256, f"esperava 256 robos: {kits['robots']}"
    assert kits["kits"] == 256, f"esperava 256 kits: {kits['kits']}"
    assert not kits["bad"], f"kit incompleto: {kits['bad']}"

    arenas = pg.evaluate("async () => (await import('/src/web/game/arenas.ts')).ARENA_IDS")
    sim = pg.evaluate(SIM, {
        "legacy": 40,
        "full": 40,
        "arenas": arenas,
        "diffs": ["facil", "normal", "dificil", "pesadelo"],
    })

    print("resultados:", json.dumps(sim["results"], ensure_ascii=False))
    print("turnos  media legado:", sim["avgLegacy"], "| media acoes novas:", sim["avgFull"],
          "| pico:", sim["turnsMax"])
    print("eventos:", json.dumps(sim["kinds"], ensure_ascii=False))
    print("animacoes distintas:", sim["distinctAnims"], "| trocas forçadas:", sim["forced"])
    assert not sim["fails"], f"falhas na simulacao: {sim['fails'][:6]}"
    assert sim["results"].get("win", 0) > 0, "nenhuma vitoria simulada"
    assert sim["results"].get("lose", 0) > 0, "nenhuma derrota simulada"
    assert sim["forced"] > 0, "troca forcada nunca disparou"
    assert not sim["unknownAnim"], f"animacao fora do catalogo: {sim['unknownAnim']}"
    assert sim["distinctAnims"] >= 30, f"pouca variedade de animacao: {sim['distinctAnims']}"
    for k in ["msg", "clip", "vfx", "float", "sync", "anim", "faint", "end",
              "order", "passive", "status", "dmg"]:
        assert sim["kinds"].get(k, 0) > 0, f"evento {k} nunca foi emitido"
    print("relatorios pos-luta:", json.dumps(sim["reports"], ensure_ascii=False)[:400])
    assert all(r["rounds"] > 0 and r["timeline"] > 0 for r in sim["reports"]), "relatorio vazio"

    vfx = sorted(set(sim["vfx"]))
    print("vfx pedidos pelo motor:", len(vfx), vfx)
    for src, ok, dim, err, ctype in pg.evaluate(PROBE_IMG, vfx):
        assert ok, f"vfx nao carregou: {src}"
        assert dim and dim[0] > 0, f"vfx nao decodifica ({err} / {ctype}): {src}"
    print("todos os vfx do motor respondem 200 e decodificam")

    # ---- batalha real na UI
    def safe_click(loc, timeout=8000):
        """Clique tolerante: o HUD se sobrepoe aos botoes durante o playback."""
        try:
            loc.click(timeout=timeout)
            return True
        except Exception:
            try:
                loc.click(timeout=2000, force=True)
                return True
            except Exception:
                return False

    def first_visible(pat):
        loc = pg.get_by_text(re.compile(pat, re.I)).first
        try:
            if loc.count() and loc.is_visible():
                return loc
        except Exception:
            return None
        return None

    for _ in range(6):
        pg.mouse.click(195, 400)
        pg.wait_for_timeout(900)
        if re.search(r"HANGAR", pg.inner_text("body"), re.I):
            break
    safe_click(pg.get_by_text(re.compile("ARENA", re.I)).first)
    pg.wait_for_timeout(1000)
    safe_click(pg.get_by_text(re.compile("PARTIDA RAPIDA", re.I)).first)
    pg.wait_for_timeout(2000)
    for pat in ["LUTAR", "INICIAR", "COMECAR", "JOGAR", "CONFIRMAR"]:
        loc = first_visible(pat)
        if loc:
            safe_click(loc)
            pg.wait_for_timeout(2500)
            break
    pg.screenshot(path=f"{SHOTS}/h1_00_battle.png")

    # ---- HUD novo: ordem de turno, recurso, sincronia, zona e log
    body = pg.inner_text("body")
    for mark, why in [("ORDEM", "barra de ordem de turno"),
                      ("SIN", "medidor de sincronia"),
                      ("ZONA", "chip de zona de terreno"),
                      ("LOG", "botao de registro de combate"),
                      ("ATACAR", "menu raiz novo")]:
        assert re.search(mark, body, re.I), f"faltou no HUD: {why} ({mark})"
    print("HUD novo: ordem + recurso + sincronia + zona + log presentes")

    def click_button(pat):
        """Clica o primeiro <button> visivel cujo texto casa com o padrao."""
        for b in pg.query_selector_all("button"):
            try:
                if not b.is_visible():
                    continue
                txt = (b.inner_text() or "").strip()
            except Exception:
                continue
            if txt and re.search(pat, txt, re.I):
                if safe_click(b):
                    return txt
        return None

    def find_button(pat):
        for b in pg.query_selector_all("button"):
            try:
                if b.is_visible() and re.search(pat, b.inner_text() or "", re.I):
                    return b
            except Exception:
                continue
        return None

    def on_report():
        return bool(first_visible(r"CRONOLOGIA") or first_visible(r"MVP "))

    def open_skills():
        """ATACAR -> confere a previsao de dano e escolhe a primeira skill."""
        if not (click_button(r"^ATACAR$") or click_button(r"ATACAR")):
            return False
        pg.wait_for_timeout(350)
        row = find_button(r"POT \d")
        if row is None:
            click_button(r"VOLTAR")
            return False
        txt = row.inner_text()
        if not re.search(r"CRIT \d+%", txt) or not re.search(r"ERRA \d+%", txt):
            click_button(r"VOLTAR")
            return False
        return bool(safe_click(row))

    plan = ["skill", "skill", "log", "skill", "dodge", "skill", "analyze", "skill",
            "combo", "skill", "skill", "log"]
    shots = 0
    seen_forecast = False
    while shots < 260 and not on_report():
        # troca forcada pede escolha de robo
        if first_visible(r"PROXIMO ROBO"):
            click_button(r"^(?!VOLTAR$).+")
            pg.wait_for_timeout(1500)
            shots += 1
            continue
        step = plan[shots % len(plan)]
        acted = False
        if step == "skill":
            acted = open_skills()
            if acted:
                seen_forecast = True
        elif step == "log":
            if click_button(r"LOG \d"):
                pg.wait_for_timeout(500)
                pg.screenshot(path=f"{SHOTS}/h1_{shots:02d}_log.png")
                click_button(r"FECHAR")
                acted = True
        elif step in ("dodge", "analyze"):
            pat = "ESQUIVA" if step == "dodge" else "ANALISAR"
            if click_button(r"TATICAS"):
                pg.wait_for_timeout(350)
                if click_button(pat):
                    acted = True
                else:
                    click_button(r"VOLTAR")
                    acted = open_skills()
        elif step == "combo":
            if not click_button(r"COMBO \d"):
                acted = open_skills()
            else:
                acted = True
        if not acted:
            # plano B: item, troca ou qualquer skill utilizavel
            acted = bool(click_button(r"ITEM") or click_button(r"TROCAR") or open_skills())
        if not acted:
            break
        shots += 1
        pg.screenshot(path=f"{SHOTS}/h1_{shots:02d}_turn.png")
        pg.wait_for_timeout(1000)
    print("turnos clicados na UI:", shots)
    assert seen_forecast, "previsao de dano (POT/CRIT/ERRA) nunca apareceu na UI"

    # ---- painel pos-luta
    for _ in range(80):
        if on_report():
            break
        if not open_skills() and not click_button(r"COMBO \d"):
            break
        pg.wait_for_timeout(1000)
    assert on_report(), "painel pos-luta nao apareceu"
    pg.screenshot(path=f"{SHOTS}/h1_99_report.png")
    rep = pg.inner_text("body")
    for mark, why in [("MVP", "destaque da luta"), ("CRONOLOGIA", "historico de eventos"),
                      ("DANO", "coluna de dano"), ("SUA EQUIPE", "tabela da equipe")]:
        assert re.search(mark, rep, re.I), f"relatorio sem {why} ({mark})"
    print("painel pos-luta: MVP + cronologia + metricas por robo OK")
    assert click_button(r"CONTINUAR"), "botao CONTINUAR do relatorio nao respondeu"
    pg.wait_for_timeout(1500)

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

print("OK BATALHA H1")
