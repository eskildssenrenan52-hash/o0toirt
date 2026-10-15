import assert from "node:assert/strict";
const storage=new Map<string,string>();
Object.defineProperty(globalThis,"localStorage",{value:{getItem:(k:string)=>storage.get(k)??null,setItem:(k:string,v:string)=>storage.set(k,v)}});
const save=await import("../packages/web/src/web/game/save");
const city=await import("../packages/web/src/web/game/city-actions");
const research=await import("../packages/web/src/web/game/city-research-actions");
const dims=await import("../packages/web/src/web/game/dimension-actions");
const meta=await import("../packages/web/src/web/game/meta-actions");
const expansion=await import("../packages/web/src/web/game/expansion");
const development=await import("../packages/web/src/web/game/city-development");
const catalogue=await import("../packages/web/src/web/game/meta");
const fresh=()=>{save.resetGame();save.unlockRobot("aurorion");save.setTeam(["aurorion"]);save.addGold(100000);};
const snapshot=()=>JSON.stringify(save.getState());
fresh();
for(const preset of ["balanced","exploration","combat"] as const){
 assert(research.powerPreset(preset));const e=save.getState().expansion;
 assert.equal(Object.values(e.distribution).reduce((a,b)=>a+b,0),4+e.plant*2);assert(Object.values(e.distribution).every(v=>v>=0&&v<=6));
}
const unchanged=snapshot();assert.equal(city.distributePower("portal",2),false);assert.equal(research.setPowerProtocol("bogus" as never),false);assert.equal(snapshot(),unchanged);
save.setState(s=>({...s,expansion:{...s.expansion,energy:0}}));
research.setPowerProtocol("reserve");meta.recordBattle("win",["aurorion","aurorion"]);
assert.equal(save.getState().mastery.aurorion.wins,1);assert.equal(save.getState().expansion.development.capacitor,5);
const amount=research.dischargeCapacitor();assert.equal(amount,5);assert.equal(research.dischargeCapacitor(),0);
assert.equal(save.getState().expansion.energy,development.generation(save.getState().expansion)+5);

fresh();assert(research.powerPreset("exploration"));
const route=expansion.ROUTES[0];assert(city.startExpedition(route.id,"survey"));
const expeditionBefore=snapshot();city.expeditionChoice("bogus" as never);assert.equal(snapshot(),expeditionBefore);
assert.equal(city.startExpedition(route.id),false);assert.equal(research.upgradeRoute(route.id),false);
for(let i=0;i<route.length;i++)city.expeditionChoice("scan");
assert.equal(save.getState().expansion.expedition,null);assert.equal(save.getState().expansion.counters.expeditions,1);
assert.equal(save.getState().expansion.discoveries.length,route.length);assert.equal(save.getState().expansion.relics.length,1);
const gold=save.getState().gold;city.expeditionChoice("scan");city.evacuateExpedition();assert.equal(save.getState().gold,gold);
assert(research.upgradeRoute(route.id));assert.equal(save.getState().expansion.development.routeResearch[route.id],1);

fresh();assert(research.powerPreset("combat"));
assert(research.runSimulation("aurorion","str"));assert.equal(save.getState().expansion.development.drills.aurorion.str,1);
const charges=save.getState().expansion.development.drillCharges;assert(research.runSimulation("aurorion","agl"));assert.equal(save.getState().expansion.development.drillCharges,charges-1);
assert.equal(research.runSimulation("aurorion","def"),false);
const root=expansion.TALENT_NODES.find(n=>n.tier===0)!;assert(city.learnTalent("aurorion",root.id));assert.equal(city.learnTalent("aurorion",root.id),false);
assert.equal(research.upgradeResonance(0),false);
save.setState(s=>({...s,expansion:{...s.expansion,relics:expansion.RELICS.filter(r=>r.set===0).slice(0,2).map(r=>r.id)}}));
assert(research.upgradeResonance(0));assert.equal(save.getState().expansion.development.resonance[0],1);

fresh();save.setState(s=>({...s,battlesWon:10000,mastery:{aurorion:{pts:10000,wins:100,claimed:0,winClaimed:0}}}));
assert(research.toggleTrackedContract("contract_0_0"));const n=research.claimContractChain(0);assert.equal(n,15);
assert.equal(save.getState().expansion.development.tracked.length,0);const rewards=save.getState().gold;
assert.equal(research.claimContractChain(0),0);assert.equal(city.claimContract("contract_0_0"),false);assert.equal(save.getState().gold,rewards);
assert(research.claimContractMilestone(15));assert.equal(research.claimContractMilestone(15),false);

fresh();assert(research.powerPreset("exploration"));
const picks=dims.draftPool().slice(0,4);const draftState=snapshot();
assert.equal(dims.startDimension("draft",[...picks,picks[0]]),false);assert.equal(dims.startDimension("draft",picks,"","bogus"),false);assert.equal(snapshot(),draftState);
assert(dims.startDimension("draft",picks));assert.equal(save.getState().expansion.run!.team.length,4);
let run=save.getState().expansion.run!;assert(dims.launchDimension(run.uid,1));assert.equal(dims.launchDimension(run.uid,1),false);
assert.equal(dims.startDimension("rift"),false);dims.finishDimension(run.uid,1,"win");
assert.equal(save.getState().expansion.run!.phase,"choice");const bank=save.getState().expansion.run!.bank;
dims.finishDimension(run.uid,1,"win");assert.equal(save.getState().expansion.run!.bank,bank);
assert.equal(dims.runChoice(run.uid,"bogus"),false);assert(dims.runChoice(run.uid,"safe"));assert.equal(dims.runChoice(run.uid,"safe"),false);
for(let step=2;step<=run.length;step++){assert(dims.launchDimension(run.uid,step));dims.finishDimension(run.uid,step,"win");if(step<run.length)assert(dims.runChoice(run.uid,"safe"));}
assert.equal(save.getState().expansion.run!.phase,"won");assert.equal(save.getState().expansion.counters.draftWins,1);
const paid=save.getState().gold;dims.finishDimension(run.uid,run.length,"win");assert.equal(save.getState().gold,paid);assert.equal(save.getState().robots.length,1);
dims.closeRun(run.uid);assert.equal(save.getState().expansion.run,null);
assert.equal(dims.startDimension("draft",dims.draftPool().slice(0,4),"",undefined,1),true); // New run sequence rotates the pool.

fresh();assert(research.powerPreset("exploration"));assert(dims.startDimension("caravan"));run=save.getState().expansion.run!;assert(dims.launchDimension(run.uid,1));
dims.finishDimension(run.uid,1,"win",{aurorion:{hp:NaN,mp:Infinity},__core:{hp:-100,mp:0}});
assert.deepEqual(save.getState().expansion.run!.carry.aurorion,{hp:1,mp:1});assert.equal(save.getState().expansion.run!.core,0);
fresh();const forged=meta.forge(false)!;assert(forged);const equipmentState=snapshot();meta.equipTo("bogus",forged.uid);meta.applySkin("aurorion","bogus");assert.equal(snapshot(),equipmentState);
meta.equipTo("aurorion",forged.uid);assert.deepEqual(save.getState().equipped.aurorion,[forged.uid]);meta.sellEquip(forged.uid);assert.deepEqual(save.getState().equipped.aurorion,[]);
const sold=save.getState().gold;meta.sellEquip(forged.uid);assert.equal(save.getState().gold,sold);
const skin=catalogue.SKINS[0];meta.applySkin("aurorion",skin.id);assert.equal(save.getState().skinOf.aurorion,undefined);
console.log("PASS: power budgets/capacitor, expedition inputs/rewards, simulation charges/talent duplicates, museum resonance, contract chains/milestones, exact draft team, dimensional phase/reward idempotency and carry sanitization, equipment ownership/sales and owned skins.");