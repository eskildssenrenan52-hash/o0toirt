import assert from "node:assert/strict";
const storage=new Map<string,string>();
Object.defineProperty(globalThis,"localStorage",{value:{getItem:(k:string)=>storage.get(k)??null,setItem:(k:string,v:string)=>storage.set(k,v)}});
const save=await import("../packages/web/src/web/game/save");
const lab=await import("../packages/web/src/web/game/lab");
const cards=await import("../packages/web/src/web/game/cards");
const pets=await import("../packages/web/src/web/game/pets");
const gadgets=await import("../packages/web/src/web/game/gadgets");
const snapshot=()=>JSON.stringify(save.getState());
save.resetGame();save.unlockRobot("aurorion");save.setTeam(["aurorion"]);save.addGold(10000000);
save.setState(s=>({...s,playerLevel:30,robots:s.robots.map(r=>({...r,level:30})),mining:{...s.mining,bars:{ferro:10000}}}));
{
 const before=snapshot();
 for(const q of [NaN,Infinity,-Infinity,-1])assert.equal(save.mineOre("ferro",q),0);
 assert.equal(save.mineOre("unknown",1),0);
 for(const d of [NaN,Infinity,-1,0,1.5,9])assert.equal(save.upgradeDrill(d),false);
 for(const q of [NaN,Infinity,-1,0,1.5])assert.equal(save.startRefine("ferro",q),false);
 assert.equal(save.startRefine("unknown",1),false);
 for(const t of [NaN,Infinity,-1])assert.deepEqual(save.miningTick(t),{gained:0,ms:0});
 assert.equal(save.collectRefine(NaN),0);assert.equal(snapshot(),before);
}
assert.equal(save.mineOre("ferro",35.7),35);assert(save.startRefine("ferro",2));
assert.equal(save.startRefine("ferro",1),false);const job=save.getState().mining.job!;
const before=snapshot();assert.equal(save.collectRefine(NaN),0);assert.equal(save.collectRefine(job.endsAt-1),0);assert.equal(snapshot(),before);
assert.equal(save.collectRefine(job.endsAt),2);assert.equal(save.collectRefine(job.endsAt),0);
assert(save.sellMining()>0);assert.equal(save.sellMining(),0);
save.setState(s=>({...s,mining:{...s.mining,bars:{ferro:10000}}}));
{
 const card=cards.CARD_LIST?.[0] ?? Object.values(cards.CARD_MAP)[0];
 assert(save.buyCard(card.id));const gold=save.getState().gold;assert.equal(save.buyCard(card.id),false);assert.equal(save.getState().gold,gold);
 assert(save.toggleCard(card.id));assert.equal(save.getState().deck.filter(id=>id===card.id).length,1);
 assert(save.refineCard(card.id));assert.equal(save.cardRefineOf(save.getState(),card.id),2);
 const pet=Object.values(pets.PET_MAP)[0];assert(save.buyPet(pet.id));assert.equal(save.buyPet(pet.id),false);assert(save.upgradePet(pet.id));
 assert.equal(save.getState().activePets.filter(id=>id===pet.id).length,1);
 assert(save.togglePetSlot(pet.id));assert(save.togglePetSlot(pet.id));assert.equal(save.getState().activePets.filter(id=>id===pet.id).length,1);
}
assert(save.buyGadget("aurorion"));assert.equal(save.buyGadget("aurorion"),false);
for(let n=0;n<12;n++)save.upgradeGadget("aurorion");
const chip=Object.values(gadgets.CHIP_MAP)[0];assert(save.buyChip(chip.id));assert.equal(save.buyChip(chip.id),false);
{
 const before=snapshot();for(const slot of [NaN,Infinity,-1,.5])assert.equal(save.equipChip("aurorion",slot,chip.id),false);
 assert.equal(save.equipChip("ferrovax",0,chip.id),false);assert.equal(snapshot(),before);
 assert(save.equipChip("aurorion",0,chip.id));assert.equal(save.gadgetChipsOf(save.getState(),"aurorion")[0],chip.id);
}
{
 const d=lab.emptyDraft(),before=snapshot();
 for(const invalid of [{...d,hue:NaN},{...d,hue:360},{...d,head:"unknown"},{...d,core:"unknown"},{...d,deco:"unknown"}])assert.equal(save.buildCustom(invalid),null);
 assert.equal(snapshot(),before);const id=save.buildCustom({...d,name:"TEST UNIT"})!;assert(id);save.setTeam([id]);
 const gold=save.scrapCustom(id);assert(gold>0);assert.equal(save.scrapCustom(id),0);assert.deepEqual(save.getState().team,["aurorion"]);
}
const rankBefore=snapshot();assert.equal(save.claimRankReward(NaN),0);assert.equal(save.claimRankReward(-1),0);assert.equal(save.claimRankedMission("unknown"),0);assert.equal(snapshot(),rankBefore);
assert(Number.isFinite(save.getState().gold));assert(Object.values(save.getState().mining.ores).every(Number.isFinite));
console.log("PASS: invalid/finite mining inputs, integer sockets, ownership, single-use refinery/sale, pet/card/chip duplicate purchases, custom validation/scrap/team fallback and invalid ranked claims.");