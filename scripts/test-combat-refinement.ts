import assert from "node:assert/strict";
import * as combat from "../packages/web/src/web/game/combat";
import { kitOf } from "../packages/web/src/web/game/kits";

const robot=(id:string)=>({id,level:1,xp:0,trained:{str:0,def:0,agl:0},borrowed:true});
function setup(){
 const c=combat.createCombat({arena:"hangar",playerTeam:[robot("aurorion"),robot("ferrovax")],enemyTeam:[robot("ferrovax")],items:{}});
 const p=c.player.fighters[0],e=c.enemy.fighters[0];
 for(const f of [...c.player.fighters,...c.enemy.fighters]){f.passives=[];f.effects=[];f.hp=f.maxHp=100000;f.maxMp=100;f.talent=null;}
 p.skillIds=[...p.skillIds.slice(0,3),"aurorion_heavy",...p.skillIds.slice(4)];
 e.base.str=e.str=1;e.base.def=e.def=1;e.base.agl=e.agl=1;e.skillIds=[];e.mp=0;
 c.phase="menu";c.order=[p.uid,e.uid];c.cursor=1;c.ready=p.uid;
 return {c,p,e};
}
const heavy=kitOf("aurorion").skills.find(s=>s.charge)!;
{
 const {c,p}=setup();p.res=5;p.mp=100;
 const ev=combat.resolveRound(c,{kind:"skill",skillId:heavy.id});
 assert.equal(p.res,3);assert.equal(p.mp,100-heavy.mp);assert.equal(c.pending[0].spent,2);assert.equal(p.ultimateCharge,18);assert.equal(p.hits,0);
 assert.equal(combat.skillUnavailable(p,heavy),"GOLPE PRONTO PARA LIBERAR");
 const beforeMp=p.mp,beforeRes=p.res;
 combat.resolveRound(c,{kind:"pass"});
 assert.equal(p.mp,beforeMp);assert.equal(p.res,beforeRes);assert.equal(p.charged,null);assert.equal(c.pending.length,0);assert.equal(p.hits,1);assert.equal(p.ultimateCharge,18);
 assert(ev.some(e=>e.t==="charge"&&e.value===18));
}
{
 const originalHits=heavy.hits,originalTags=heavy.tags;
 try{
  heavy.hits=3;heavy.tags=[...(heavy.tags??[]),"projetil"];
  const {c,p}=setup();p.res=5;p.mp=100;
  combat.resolveRound(c,{kind:"skill",skillId:heavy.id});combat.resolveRound(c,{kind:"pass"});
  assert.equal(p.hits,3);assert.equal(p.mp,100-heavy.mp);assert.equal(p.res,3);assert.equal(p.ultimateCharge,18);
 }finally{heavy.hits=originalHits;heavy.tags=originalTags;}
}
{
 const {c,p}=setup();p.res=1;p.mp=100;
 combat.resolveRound(c,{kind:"skill",skillId:heavy.id});assert.equal(p.mp,100);assert.equal(p.charged,null);assert.equal(c.pending.length,0);assert.equal(p.ultimateCharge,0);
 p.effects=[{type:"silence",power:1,turns:2,stacks:1}];assert.equal(combat.skillUnavailable(p,heavy),"SILENCIADO");
}
{
 const {c,p}=setup();p.res=5;p.mp=100;
 combat.resolveRound(c,{kind:"skill",skillId:heavy.id});p.hp=0;
 combat.resolveRound(c,{kind:"pass"});assert.equal(c.pending.length,0);assert.equal(p.charged,null);
}
{
 const {c,p}=setup();p.passives=["teamPlayer"];p.hp=50000;c.player.fighters[1].hp=50000;
 combat.resolveRound(c,{kind:"guard"});assert.equal(p.hp,53000);assert.equal(c.player.fighters[1].hp,53000);assert.equal(c.player.fighters[1].hits,0);
}
{
 const {c,p}=setup();p.passives=["ultimateBattery"];p.ultimateCharge=86;
 const ev=combat.resolveRound(c,{kind:"guard"});
 assert(ev.some(e=>e.t==="passive"&&e.label==="BATERIA FINAL"));
 for(const f of c.player.fighters){assert(f.effects.some(e=>e.type==="adrenalin"));assert(f.effects.some(e=>e.type==="evade_up"));}
 const next=combat.resolveRound(c,{kind:"guard"});assert(!next.some(e=>e.t==="passive"&&e.label==="BATERIA FINAL"));
}
console.log("PASS: charged MP/resource paid once, no double charge, multihit, rejected cost/silence, death cleanup, team repair and 100% battery transition.");