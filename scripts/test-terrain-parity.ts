import assert from "node:assert/strict";
import * as combat from "../packages/web/src/web/game/combat";
import { kitOf } from "../packages/web/src/web/game/kits";
import { arenaWeather, makeField, weatherDamage } from "../packages/web/src/web/game/terrain";
import { TUTORIAL_CHAPTERS } from "../packages/web/src/web/game/tutorial";
const robot = (id: string) => ({ id, level: 1, xp: 0, trained: { str: 0, def: 0, agl: 0 }, borrowed: true });
function setup(arena = "hangar") {
  const c = combat.createCombat({ arena, playerTeam: [robot("aurorion")], enemyTeam: [robot("ferrovax")], items: {} });
  const p = c.player.fighters[0], e = c.enemy.fighters[0];
  for (const f of [p, e]) {
    f.passives = []; f.effects = []; f.talent = null; f.hp = f.maxHp = 10000; f.mp = f.maxMp = 200;
    f.res = 0; f.resId = null; f.base.str = f.base.def = 100; f.base.agl = 1;
  }
  e.skillIds = [];
  c.phase = "menu"; c.order = [p.uid]; c.cursor = 1; c.ready = p.uid;
  c.field.weather = { id: "test", label: "TEST", desc: "", color: "#fff" };
  return { c, p, e };
}
function climate(arena: string, index: number) {
  const field = makeField(arena); field.weather = arenaWeather(arena)[index]; return field;
}
assert.equal(weatherDamage(climate("dojo", 1), "LUZ", ["area"]), -6);
assert.equal(weatherDamage(climate("dojo", 1), "LUZ", ["corpo"]), 0);
assert.equal(weatherDamage(climate("foundry", 1), "LUZ", ["contundente"]), 18);
assert.equal(weatherDamage(climate("crystal", 2), "LUZ", ["area"]), 18);
assert.equal(weatherDamage(climate("sky", 2), "LUZ"), -10);
assert.equal(weatherDamage(climate("orbital", 2), "LUZ"), -20);
assert.equal(weatherDamage(climate("orbit", 2), "SOMBRA"), 20);
assert.equal(weatherDamage(climate("frozen", 2), "GELO"), 0);
assert(!TUTORIAL_CHAPTERS.some(ch => /esfera/i.test(ch.text + ch.hint)));
const skill = kitOf("aurorion").skills.find(s => s.kind === "attack" && !s.charge && s.mp === 0)!;
const saved = structuredClone(skill);
try {
  Object.assign(skill, { power: 30, hits: 1, each: false, tags: ["projetil"], mech: [], status: [], self: [], effect: undefined, gain: undefined });
  {
    const { c, p, e } = setup();
    const before = JSON.stringify(c);
    const preview = combat.damagePreview(c, p.uid, e.uid, skill.id)!;
    assert.equal(JSON.stringify(c), before, "forecast must not mutate live combat");
    combat.resolveRound(c, { kind: "skill", skillId: skill.id });
    assert(e.damageTaken >= preview.min && e.damageTaken <= preview.max, "real strike shares forecast rules");
  }
  for (const each of [true, false]) {
    skill.hits = 3; skill.each = each;
    const { c, p, e } = setup();
    const f = combat.damagePreview(c, p.uid, e.uid, skill.id)!;
    combat.resolveRound(c, { kind: "skill", skillId: skill.id });
    assert(e.damageTaken >= f.min && e.damageTaken <= f.max, `multihit each=${each}`);
  }
  skill.hits = 1; skill.each = false;
  for (const [attack, target] of [["TOXICO", "METAL"], ["TOXICO", "CRISTAL"], ["QUANTICO", "QUANTICO"], ["METAL", "TOXICO"]]) {
    const { c, p, e } = setup(); p.attackElement = attack as typeof p.attackElement; e.element = target as typeof e.element; e.hp = 5000;
    const f = combat.damagePreview(c, p.uid, e.uid, skill.id)!;
    assert.equal(f.min, 0); assert.equal(f.max, 0); assert.equal(f.tier, "absorve");
    combat.resolveRound(c, { kind: "skill", skillId: skill.id });
    assert(e.hp > 5000, `${attack} absorbed by ${target}`); assert.equal(e.damageTaken, 0); assert.equal(p.hits, 0); assert.equal(e.ultimateCharge, 0);
  }
  {
    const { c, p } = setup("dojo"); p.pos = "suporte"; p.hp = 5000;
    combat.resolveRound(c, { kind: "pass" }); assert.equal(p.hp, 5500);
  }
  {
    const { c, p } = setup("dojo"); p.pos = "suporte"; p.hp = 5000; p.passives = ["terrainMaster"];
    combat.resolveRound(c, { kind: "pass" }); assert.equal(p.hp, 6000);
  }
  {
    const { c, p } = setup("dojo"); p.pos = "suporte"; p.hp = 5000; c.field.weather.noTerrainHeal = true;
    combat.resolveRound(c, { kind: "pass" }); assert.equal(p.hp, 5000);
  }
  {
    const { c, p } = setup("dojo"); p.hp = 5000; c.field.weather.healIn = 20;
    combat.resolveRound(c, { kind: "pass" }); assert.equal(p.hp, 5000, "heal multiplier is not autonomous healing");
  }
  for (const master of [false, true]) {
    const { c, p } = setup("dojo"); p.pos = "nucleo"; p.mp = 50; p.passives = master ? ["terrainMaster"] : [];
    combat.resolveRound(c, { kind: "pass" }); assert.equal(p.mp, master ? 62 : 56);
  }
  for (const walker of [false, true]) {
    const { c, p } = setup("neodojo"); p.pos = "nucleo"; p.mp = 50; p.passives = walker ? ["hazardWalker"] : [];
    combat.resolveRound(c, { kind: "pass" }); assert.equal(p.hp, walker ? 10000 : 9500); assert.equal(p.mp, walker ? 56 : 50);
  }
  {
    const { c, p } = setup(); c.field.weather.mpDrain = 8;
    combat.resolveRound(c, { kind: "pass" }); assert.equal(p.mp, 184, "weather drains % max MP");
  }
  {
    const { c, p } = setup(); p.effects = [{ type: "drain", power: 10, stacks: 2, turns: 3 }];
    combat.resolveRound(c, { kind: "pass" }); assert.equal(p.mp, 160, "status drains % max MP per stack");
  }
  {
    const { c, p, e } = setup();
    const plain = combat.damagePreview(c, p.uid, e.uid, skill.id)!;
    e.effects = [{ type: "marked", power: 20, stacks: 1, turns: 3 }];
    const marked = combat.damagePreview(c, p.uid, e.uid, skill.id)!;
    assert(marked.min > plain.min, "marked increases damage instead of reducing it");
    e.effects = []; e.passives = ["terrainMaster"];
    assert(combat.damagePreview(c, p.uid, e.uid, skill.id)!.min < plain.min, "master doubles cover");
    p.pos = "flanco"; p.passives = ["terrainMaster"];
    assert.equal(combat.effectiveStats(c, p).str, 124, "strength zone is doubled once");
  }
  {
    const { c, p, e } = setup("orbital");
    const exposed = combat.damagePreview(c, p.uid, e.uid, skill.id)!;
    e.pos = "flanco";
    const neutral = combat.damagePreview(c, p.uid, e.uid, skill.id)!;
    // Ignore position differences by placing a neutral zone at the same position.
    e.pos = "guarda"; const originalArena = c.field.arena; c.field.arena = "frozen";
    const noVoid = combat.damagePreview(c, p.uid, e.uid, skill.id)!;
    c.field.arena = originalArena;
    assert(exposed.min > noVoid.min); assert(neutral.min > 0);
  }
  {
    const { c, p } = setup("frozen"); c.field.weather = arenaWeather("frozen")[2]; p.pos = "flanco";
    assert.equal(combat.effectiveStats(c, p).crit, -3);
  }
  {
    const { c, p } = setup("orbital"); p.hp = 5000; p.effects = [{ type: "hp_regen", power: 5, stacks: 1, turns: 3 }];
    combat.resolveRound(c, { kind: "pass" }); assert.equal(p.hp, 5500, "void does not block repairs");
  }
  {
    const { c, p, e } = setup(); const hp = e.hp;
    assert.equal(combat.damagePreview(c, p.uid, e.uid, "invalid"), null);
    combat.resolveRound(c, { kind: "skill", skillId: "invalid" });
    assert.equal(e.hp, hp); assert.equal(c.ready, p.uid); assert.equal(c.turn, 1);
    const view = combat.combatView(c);
    assert.equal(combat.applyForcedSwap(view, 0).events.length, 0);
  }
  console.log("PASS: scoped weather, inherited climate, terrain ticks/masters/hazards, max-MP drain, absorption, forecast immutability/multihit parity, invalid inputs, current tutorial controls.");
} finally {
  for (const key of Object.keys(skill)) if (!(key in saved)) delete (skill as unknown as Record<string, unknown>)[key];
  Object.assign(skill, saved);
}