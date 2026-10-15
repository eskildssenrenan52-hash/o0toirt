import assert from "node:assert/strict";

const storage=new Map<string,string>();
const mode=process.argv[2]??"new";
if(mode==="legacy")storage.set("campeoes-mecha-save-v1",JSON.stringify({version:2,gold:4321,playerLevel:2,playerXP:7,robots:[{id:"aurorion",level:3,xp:1,trained:{str:2,def:1,agl:0}}],team:["aurorion"],items:{repair_kit:4},loadouts:{aurorion:["aurorion_ultimate","aurorion_basic"]},customs:[]}));
if(mode==="empty")storage.set("campeoes-mecha-save-v1",JSON.stringify({version:3,gold:77,robots:[],team:[],items:{},tutorial:{started:false,completed:false,chapter:0,legacyAccess:false}}));
Object.defineProperty(globalThis,"localStorage",{value:{getItem:(key:string)=>storage.get(key)??null,setItem:(key:string,value:string)=>storage.set(key,value)}});
const save=await import("../packages/web/src/web/game/save");
const {systemUnlocked}=await import("../packages/web/src/web/game/progression");
if(mode==="legacy"){
 const g=save.getState();assert.equal(g.gold,4321);assert.equal(g.robots[0].level,3);assert.equal(g.items.repair_kit,4);assert.equal(g.tutorial.legacyAccess,true);assert.equal(systemUnlocked(g,"portal"),true);
 assert.equal(save.loadoutOf(g,"aurorion").includes("aurorion_ultimate"),false);
 console.log("PASS: legacy save migrated without losing gold/robots/items or access.");process.exit(0);
}
if(mode==="empty"){assert.equal(save.getState().gold,77);assert.equal(save.getState().robots.length,0);console.log("PASS: valid empty save preserved, not reset.");process.exit(0);}
const {ROBOTS}=await import("../packages/web/src/web/game/robots");
const {NPC_DEFS}=await import("../packages/web/src/web/game/enemies");
const {kitOf}=await import("../packages/web/src/web/game/kits");
const {normalizeLoadout,exclusiveUltimate}=await import("../packages/web/src/web/game/skills");
const combat=await import("../packages/web/src/web/game/combat");
const tutorial=await import("../packages/web/src/web/game/tutorial");
const robot=(id:string)=>({id,level:1,xp:0,trained:{str:0,def:0,agl:0},borrowed:true});
const g=save.getState();assert.equal(g.gold,0);assert.equal(g.robots.length,0);assert.deepEqual(g.items,{});assert.equal(systemUnlocked(g,"roster"),true);assert.equal(systemUnlocked(g,"shop"),false);assert.equal(systemUnlocked(g,"portal"),false);
for(const def of [...ROBOTS,...NPC_DEFS]){
 const kit=kitOf(def.id);const ult=exclusiveUltimate(kit.skills)!;assert(ult,def.id);
 const ids=normalizeLoadout(kit.skills,[ult.id,"bogus",...kit.skills.map(s=>s.id)]);
 assert.equal(ids.length,6,def.id);assert.equal(ids.includes(ult.id),false,def.id);assert.equal(new Set(ids).size,6);
 assert(ids.slice(0,4).every(id=>kit.skills.find(s=>s.id===id)?.kind==="attack"));assert(ids.slice(4).every(id=>kit.skills.find(s=>s.id===id)?.kind==="defense"));
 const f=combat.makeCombatant({save:robot(def.id),side:"player",slot:0,ai:false,pos:"guarda",difficulty:"normal"});
 assert.equal(f.ultimateCharge,0);assert.equal("combo" in f,false);assert.equal(combat.ultimateOf(f).id,ult.id);assert.equal(combat.fighterSkills(f).length,6);
}
const setup=()=>{
 const c=combat.createCombat({arena:"hangar",playerTeam:[robot("aurorion"),robot("ferrovax")],enemyTeam:[robot("ferrovax")],items:{}});
 c.phase="menu";c.order=["player0","enemy0"];c.cursor=1;c.ready="player0";
 const p=c.player.fighters[0],e=c.enemy.fighters[0];
 e.hp=e.maxHp=100000;e.base.str=e.str=1;e.base.def=e.def=1;e.base.agl=e.agl=1;e.skillIds=["ferrovax_basic"];e.passives=[];
 p.hp=p.maxHp=100000;p.passives=[];return c;
};
{
 const c=setup();const p=c.player.fighters[0];const basic=combat.fighterSkills(p).find(s=>s.kind==="attack"&&s.mp===0)!;
 const events=combat.resolveRound(c,{kind:"skill",skillId:basic.id});
 const actorCharges=events.filter(e=>e.t==="charge"&&e.uid===p.uid);
 assert.equal(actorCharges[0]?.t==="charge"?actorCharges[0].value:-1,18);assert.equal(c.player.fighters[1].ultimateCharge,0);assert.equal("combo" in c.player,false);
}
{
 const c=setup();const p=c.player.fighters[0];const events=combat.resolveRound(c,{kind:"guard"});
 const first=events.find(e=>e.t==="charge"&&e.uid===p.uid);assert.equal(first?.t==="charge"?first.value:-1,14);
}
{
 const c=setup();const p=c.player.fighters[0];p.ultimateCharge=100;p.mp=0;const bench=c.player.fighters[1];bench.ultimateCharge=72;
 const events=combat.resolveRound(c,{kind:"ultimate"});
 assert(events.some(e=>e.t==="ultimate"&&e.uid===p.uid));assert(p.mp>=0);assert.equal(bench.ultimateCharge,72);assert.equal(bench.hits,0);
 const charges=events.filter(e=>e.t==="charge"&&e.uid===p.uid);assert.equal(charges[0]?.t==="charge"?charges[0].value:-1,0);
 assert(charges.slice(1).every(e=>e.t==="charge"&&e.value<=16));
}
{
 const c=setup();const p=c.player.fighters[0];p.ultimateCharge=99;
 assert.equal(combat.resolveRound(c,{kind:"ultimate"}).some(e=>e.t==="ultimate"&&e.uid===p.uid),false);
}
{
 const c=setup();c.player.fighters[0].ultimateCharge=55;c.player.fighters[1].ultimateCharge=23;
 combat.resolveRound(c,{kind:"reposition",withUid:"player1"});assert.equal(c.player.active,1);assert.equal(c.player.fighters[0].ultimateCharge,55);assert(c.player.fighters[1].ultimateCharge>=23);
}
tutorial.startTutorial();tutorial.startTutorial();assert.equal(save.getState().robots.length,1);assert.equal(save.getState().gold,0);
for(let i=0;i<5;i++){assert.equal(tutorial.completeTutorialChapter(i),true);const gold=save.getState().gold;assert.equal(tutorial.completeTutorialChapter(i),false);assert.equal(save.getState().gold,gold);}
assert.equal(save.getState().tutorial.completed,true);assert.equal(save.getState().gold,640);assert.equal(save.getState().robots.length,2);assert.equal(save.getState().items.repair_kit,1);assert.equal(save.getState().battlesWon,5);
const simulations=[];
for(let chapter=0;chapter<5;chapter++){
 const c=combat.createCombat({arena:"hangar",difficulty:"facil",playerTeam:[robot("aurorion"),...(chapter>=3?[robot("ferrovax")]:[])],enemyTeam:tutorial.tutorialEnemy(chapter),items:{repair_kit:1}});
 let actions=0;
 while(c.phase!=="over"&&actions++<100){
  if(c.phase==="forced_swap"){
   combat.applyForcedSwap(combat.combatView(c),c.player.fighters.findIndex(f=>f.hp>0));continue;
  }
  const actor=combat.readyOf(c);
  const skill=combat.fighterSkills(actor).filter(s=>s.kind==="attack"&&actor.mp>=s.mp&&!s.charge&&!s.cost).sort((a,b)=>b.power-a.power)[0]??combat.fighterSkills(actor)[0];
  combat.resolveRound(c,actor.ultimateCharge>=100?{kind:"ultimate"}:{kind:"skill",skillId:skill.id});
 }
 assert.equal(c.phase,"over",`Tutorial ${chapter+1} must terminate`);
 simulations.push({chapter:chapter+1,result:c.result,rounds:c.turn});
}
console.log("Tutorial engine simulations (no browser):",simulations);
console.log(`PASS: ${ROBOTS.length} recruitable + ${NPC_DEFS.length} NPC kits, 4+2/ultimate isolation, charge, zero-MP ultimate, swapping, zero start and idempotent tutorial rewards.`);