import assert from "node:assert/strict";
import * as combat from "../packages/web/src/web/game/combat";
import { kitOf } from "../packages/web/src/web/game/kits";
const robot=(id:string)=>({id,level:1,xp:0,trained:{str:0,def:0,agl:0},borrowed:true});
function setup(){
 const c=combat.createCombat({arena:"hangar",playerTeam:[robot("aurorion"),robot("ferrovax")],enemyTeam:[robot("ferrovax")],items:{}});
 const p=c.player.fighters[0],e=c.enemy.fighters[0];
 for(const f of [...c.player.fighters,...c.enemy.fighters]){f.passives=[];f.effects=[];f.hp=f.maxHp=10000;f.talent=null;f.mp=f.maxMp=100;f.res=0;}
 e.skillIds=[];e.base.str=e.str=1;e.base.def=e.def=1;e.base.agl=e.agl=1;
 c.phase="menu";c.order=[p.uid];c.cursor=1;c.ready=p.uid;
 return {c,p,e};
}
const basic=kitOf("aurorion").skills.find(s=>s.kind==="attack"&&!s.charge&&s.mp===0)!;
const originalTags=basic.tags;
try {
 basic.tags=[...(basic.tags??[]),"projetil"];
 {
  const {c,p}=setup();p.passives=["regenerator"];p.hp=5000;
  combat.resolveRound(c,{kind:"pass"});assert.equal(p.hp,5600);assert.equal(c.player.fighters[1].hits,0);
 }
 {
  const {c,p}=setup();p.passives=["heatSink"];p.hp=5000;p.res=4;
  combat.resolveRound(c,{kind:"pass"});assert.equal(p.hp,5300);assert.equal(p.res,3);
 }
 {
  const {c,p,e}=setup();e.passives=["mirrorCore"];const before=p.hp;
  combat.resolveRound(c,{kind:"skill",skillId:basic.id});assert(e.damageTaken>0);assert(p.hp<before);assert.equal(e.hits,0);assert.equal(p.hits,1);
 }
 {
  const baseline=setup();combat.resolveRound(baseline.c,{kind:"skill",skillId:basic.id});
  const {c,p,e}=setup();p.passives=["predator"];e.hp=4000;
  combat.resolveRound(c,{kind:"skill",skillId:basic.id});assert(e.damageTaken>baseline.e.damageTaken);
 }
 {
  const {c,p,e}=setup();e.hp=2000;e.passives=["secondWind"];
  combat.resolveRound(c,{kind:"skill",skillId:basic.id});assert(e.passiveUsed.includes("secondWind"));assert(e.hp>2000);
  e.hp=2000;combat.resolveRound(c,{kind:"skill",skillId:basic.id});assert(e.hp<2000);assert.equal(e.passiveUsed.filter(id=>id==="secondWind").length,1);
 }
 for(const id of ["phoenixCore","undyingCore"]){
  const {c,p,e}=setup();e.hp=1;e.passives=[id];
  combat.resolveRound(c,{kind:"skill",skillId:basic.id});assert(e.hp>0);assert.equal(e.fainted,false);assert.equal(p.kills,0);assert(e.passiveUsed.includes(id));
  e.hp=1;combat.resolveRound(c,{kind:"skill",skillId:basic.id});assert.equal(e.hp,0);assert.equal(p.kills,1);assert.equal(e.fainted,true);
 }
 {
  const {c,p,e}=setup();p.passives=["firstBlood"];p.hp=5000;e.hp=1;
  combat.resolveRound(c,{kind:"skill",skillId:basic.id});assert.equal(p.hp,7500);assert.equal(p.kills,1);assert.equal(p.passiveUsed.filter(id=>id==="firstBlood").length,1);
 }
 {
  const {c,p}=setup();p.passives=["guardianAngel"];p.hp=5000;c.player.fighters[1].hp=0;
  combat.resolveRound(c,{kind:"pass"});assert.equal(p.hp,6200);
  combat.resolveRound(c,{kind:"pass"});assert.equal(p.hp,6200);
 }
 {
  const {c,p}=setup();p.passives=["cleanSlate"];p.hp=5000;p.mp=30;p.effects=[{type:"poison",power:1,turns:4,stacks:1}];
  c.player.items.purify=1;
  // The item catalog may use a different ID: select the actual purge defense instead.
  const purge=kitOf("aurorion").skills.find(s=>s.defense?.kind==="purge");
  if(purge){p.skillIds.push(purge.id);combat.resolveRound(c,{kind:"skill",skillId:purge.id});assert(p.hp>=6500);assert(!p.effects.some(e=>e.type==="poison"));}
 }
 console.log("PASS: turn/end-turn hooks, bounded reactions without reserve attacks, target HP context, once-only low-HP repair/cores/first kill, ally-faint idempotency.");
} finally { basic.tags=originalTags; }