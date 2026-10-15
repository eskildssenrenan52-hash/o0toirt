import assert from "node:assert/strict";
const storage = new Map<string, string>();
Object.defineProperty(globalThis, "localStorage", { value: { getItem: (k: string) => storage.get(k) ?? null, setItem: (k: string, v: string) => storage.set(k, v), removeItem: (k: string) => storage.delete(k) } });
const roster = await import("../packages/web/src/web/game/pantheon-roster");
const pan = await import("../packages/web/src/web/game/pantheon");
const robots = await import("../packages/web/src/web/game/robots");
const tours = await import("../packages/web/src/web/game/tournaments");
const save = await import("../packages/web/src/web/game/save");

// 1. 27 chassis reais do catálogo, fora de torneios e iniciais
assert.equal(roster.PANTHEON_IDS.length, 27);
assert.equal(new Set(roster.PANTHEON_IDS).size, 27);
assert.equal(robots.CATALOG_IDS.length, 256);
const rewards = new Set((tours.TOURNAMENTS as { reward: { robot?: string } }[]).map((t) => t.reward.robot).filter(Boolean));
for (const id of roster.PANTHEON_IDS) {
  assert(robots.CATALOG_IDS.includes(id), `${id} fora do catálogo`);
  assert(!rewards.has(id), `${id} é prêmio de torneio`);
  assert(!robots.STARTER_ROBOTS.includes(id), `${id} é inicial`);
  assert(pan.trialOf(id) && pan.trialOf(id)!.cost >= 100, `${id} custo < 100`);
}
for (const r of robots.ROBOTS) assert.notEqual((r as { rarity: string }).rarity, "mythic");

// 2. loja/cápsula nunca concedem
save.resetGame();
save.unlockRobot("aurorion");
const id = roster.PANTHEON_IDS[0];
assert.equal(save.unlockRobot(id), false);
assert(!save.lockedRobotIds().some((x) => roster.isPantheonRobot(x)));

// 3. despertar só com 3 vitórias + missões + diamantes
const t = pan.trialOf(id)!;
save.setState((s) => ({ ...s, diamonds: 10000 }));
assert.equal(save.summonPantheon(id), false, "sem provações");
assert.equal(save.recordTrialWin(id, 1, false), false, "fora de ordem");
for (let i = 0; i < 3; i++) assert(save.recordTrialWin(id, i, true));
assert.equal(save.recordTrialWin(id, 3, true), false);
save.setState((s) => ({ ...s, playerLevel: 1, battlesWon: 0 }));
assert.equal(pan.summonBlock(save.getState(), id), "missions");
assert.equal(save.summonPantheon(id), false, "sem missões");
const ids = robots.CATALOG_IDS.filter((x) => !roster.isPantheonRobot(x)).slice(0, 40);
save.setState((s) => ({ ...s, playerLevel: 40, battlesWon: 500, wonTournaments: (tours.TOURNAMENTS as { id: string }[]).slice(0, 20).map((x) => x.id), robots: ids.map((x) => ({ id: x, level: 12, xp: 0, trained: { str: 0, def: 0, agl: 0 } })), diamonds: t.cost - 1 }));
assert.equal(pan.summonBlock(save.getState(), id), "diamonds");
assert.equal(save.summonPantheon(id), false, "sem diamantes");
save.setState((s) => ({ ...s, diamonds: t.cost + 7 }));
assert(save.summonPantheon(id));
assert.equal(save.getState().diamonds, 7);
assert(save.getState().robots.some((r) => r.id === id && r.level === 12));
assert.equal(save.summonPantheon(id), false, "já possui");

// 4. saves vazios/antigos preservados
assert.deepEqual(pan.normalizePantheon(undefined), { wins: {}, flawless: [] });
assert.deepEqual(pan.normalizePantheon({ wins: { [id]: 9, fake: 2, [roster.PANTHEON_IDS[1]]: "x" }, flawless: [id, id, "fake"] }), { wins: { [id]: 3 }, flawless: [id] });
console.log("pantheon ok:", roster.PANTHEON_IDS.length, "chassis");
