/**
 * Fumaça SSR (sem navegador): renderiza cada tela da cidade e a ficha TREINAR/INFO + equipamentos + loadout
 * de todos os robôs, em save vazio, inicial e completo. Qualquer exceção de render = tela preta no jogo.
 */
import assert from "node:assert/strict";
const storage = new Map<string, string>();
Object.defineProperty(globalThis, "localStorage", { value: { getItem: (k: string) => storage.get(k) ?? null, setItem: (k: string, v: string) => storage.set(k, v), removeItem: (k: string) => storage.delete(k), clear: () => storage.clear() } });
// Telas cliente leem window/matchMedia no estado inicial (o jogo nunca usa SSR em produção).
Object.assign(globalThis, { window: Object.assign(globalThis, { matchMedia: () => ({ matches: false, addEventListener() {}, removeEventListener() {} }), innerWidth: 480, innerHeight: 900, setInterval, clearInterval, setTimeout, clearTimeout, addEventListener() {}, removeEventListener() {}, devicePixelRatio: 1 }) });
const { renderToStaticMarkup } = await import("react-dom/server");
const save = await import("../packages/web/src/web/game/save");
const { ROBOTS, CATALOG_IDS } = await import("../packages/web/src/web/game/robots");
const { RobotDetail } = await import("../packages/web/src/web/screens/roster");
const { LoadoutEditor } = await import("../packages/web/src/web/components/loadout");
const { EquipPanel } = await import("../packages/web/src/web/screens/meta");
const { GateProvider } = await import("../packages/web/src/web/components/gate");
const { HubCity } = await import("../packages/web/src/web/components/hub-city");

const screens: Record<string, () => Promise<React.ComponentType<{ onBack: () => void }>>> = {
  roster: async () => (await import("../packages/web/src/web/screens/roster")).RosterScreen,
  shop: async () => (await import("../packages/web/src/web/screens/shop")).ShopScreen,
  modes: async () => (await import("../packages/web/src/web/screens/modes")).ModesScreen,
  ranked: async () => (await import("../packages/web/src/web/screens/ranked")).RankedScreen,
  tournaments: async () => (await import("../packages/web/src/web/screens/tournaments")).TournamentsScreen,
  engineer: async () => (await import("../packages/web/src/web/screens/engineer")).EngineerScreen,
  pets: async () => (await import("../packages/web/src/web/screens/pets")).PetsScreen,
  cards: async () => (await import("../packages/web/src/web/screens/cards")).CardsScreen,
  mine: async () => (await import("../packages/web/src/web/screens/mine")).MineScreen,
  lab: async () => (await import("../packages/web/src/web/screens/lab")).LabScreen,
  profile: async () => (await import("../packages/web/src/web/screens/meta")).ProfileScreen,
  mastery: async () => (await import("../packages/web/src/web/screens/meta")).MasteryScreen,
  skins: async () => (await import("../packages/web/src/web/screens/meta")).SkinsScreen,
  observatory: async () => (await import("../packages/web/src/web/screens/city-observatory")).ObservatoryScreen,
  academy: async () => (await import("../packages/web/src/web/screens/city-academy")).AcademyScreen,
  contracts: async () => (await import("../packages/web/src/web/screens/city-contracts")).ContractsScreen,
  power: async () => (await import("../packages/web/src/web/screens/city-power")).PowerScreen,
  museum: async () => (await import("../packages/web/src/web/screens/city-museum")).MuseumScreen,
  portal: async () => (await import("../packages/web/src/web/screens/city-portal")).PortalScreen,
};

let renders = 0;
const failures: string[] = [];
function render(label: string, el: React.ReactElement) {
  try { const html = renderToStaticMarkup(<GateProvider>{el}</GateProvider>); assert(html.length > 0, label); renders += 1; }
  catch (e) { failures.push(`${label}: ${(e as Error).message.split("\n")[0]}`); }
}

const states: [string, () => void][] = [
  ["vazio", () => { save.resetGame(); }],
  ["inicial", () => { save.resetGame(); save.unlockRobot("aurorion"); }],
  ["completo", () => {
    save.resetGame();
    for (const r of ROBOTS) save.unlockRobot(r.id);
    save.setState(s => ({ ...s, gold: 9_999_999, diamonds: 99_999, playerLevel: 60, tutorial: { ...s.tutorial, started: true, completed: true, chapter: 5, legacyAccess: true }, robots: s.robots.map((r, i) => ({ ...r, level: 1 + (i % 50), xp: 0 })) }));
  }],
];

for (const [name, setup] of states) {
  setup();
  for (const [id, load] of Object.entries(screens)) {
    const Screen = await load();
    render(`${name} · tela ${id}`, <Screen onBack={() => {}} />);
  }
  render(`${name} · cidade (hub)`, <HubCity onEnter={() => {}} />);
  for (const robot of save.getState().robots) {
    render(`${name} · TREINAR/INFO ${robot.id}`, <RobotDetail save={robot} onClose={() => {}} />);
    render(`${name} · equipamentos ${robot.id}`, <EquipPanel robotId={robot.id} />);
  }
}
// Loadout de todos os kits recrutáveis (cobre todos os efeitos de status exibidos).
for (const id of CATALOG_IDS) render(`loadout ${id}`, <LoadoutEditor robotId={id} />);

if (failures.length) { console.log(failures.slice(0, 30).join("\n")); console.log(`${failures.length} falhas de render.`); process.exit(1); }
console.log(`PASS: ${renders} renders SSR sem exceção (19 telas + cidade × 3 saves, TREINAR/INFO + equipamentos de todos os robôs, loadout dos 256).`);
