import assert from "node:assert/strict";
import { preloadQueue } from "../packages/web/src/web/game/preload";
const storage=new Map<string,string>();
Object.defineProperty(globalThis,"localStorage",{value:{getItem:(key:string)=>storage.get(key)??null,setItem:(key:string,value:string)=>storage.set(key,value)}});
const save=await import("../packages/web/src/web/game/save");
const economy=await import("../packages/web/src/web/game/economy-actions");
const {ITEM_MAP}=await import("../packages/web/src/web/game/config");
const {UNLOCK_LEVEL,systemUnlocked}=await import("../packages/web/src/web/game/progression");
const {SYSTEM_GUIDES}=await import("../packages/web/src/web/game/system-guides");
const {LAUNCH_ASSETS}=await import("../packages/web/src/web/game/launch-assets");
const combat=await import("../packages/web/src/web/game/combat");
const {existsSync}=await import("node:fs");

for(const id of Object.keys(UNLOCK_LEVEL) as (keyof typeof UNLOCK_LEVEL)[]){
 assert(SYSTEM_GUIDES[id]?.steps.length>=3,id);
 const gate={playerLevel:UNLOCK_LEVEL[id],tutorial:{started:true,completed:true,chapter:5,legacyAccess:false}};
 assert(systemUnlocked(gate,id),id);
 if(UNLOCK_LEVEL[id]>1)assert.equal(systemUnlocked({...gate,playerLevel:UNLOCK_LEVEL[id]-1},id),false,id);
}
assert.equal(new Set(LAUNCH_ASSETS).size,LAUNCH_ASSETS.length);
for(const path of LAUNCH_ASSETS)assert(existsSync(`/home/user/Uiop-3486/packages/web/public${path}`),path);
let inFlight=0,max=0;const calls:string[]=[];const snapshots:number[]=[];
const result=await preloadQueue(["a","b","a","bad","throws"],async url=>{
 calls.push(url);max=Math.max(max,++inFlight);await Promise.resolve();inFlight--;
 if(url==="throws")throw Error("expected failure");return url!=="bad";
},state=>snapshots.push(state.completed),undefined,2);
assert(max<=2);assert.equal(calls.length,4);assert.equal(result.completed,4);assert.deepEqual(result.failed,["bad","throws"]);assert(snapshots.every((n,i)=>i===0||n>=snapshots[i-1]));
const controller=new AbortController();controller.abort();let cancelledCalls=0;
await preloadQueue(["a"],async()=>{cancelledCalls++;return true;},()=>{},controller.signal);
assert.equal(cancelledCalls,0);

save.resetGame();assert.equal(save.unlockRobot("not-a-robot"),false);
assert.equal(save.unlockRobot("aurorion"),true);assert.equal(save.getState().robots[0].level,1);
save.setTeam(["aurorion","aurorion","bogus"]);assert.deepEqual(save.getState().team,["aurorion"]);
save.setTeam([]);assert.deepEqual(save.getState().team,["aurorion"]);
save.addGold(ITEM_MAP.repair_kit.price*5);
const purchase=economy.purchaseSupplies("repair_kit",5);assert(purchase.ok);
assert.equal(save.getState().gold,0);assert.equal(save.getState().items.repair_kit,5);
const unchanged=JSON.stringify(save.getState());
assert.equal(economy.purchaseSupplies("repair_kit").ok,false);assert.equal(economy.purchaseSupplies("repair_kit",-1).ok,false);assert.equal(economy.purchaseSupplies("bogus").ok,false);
assert.equal(JSON.stringify(save.getState()),unchanged);
save.addGold(10000);const before=save.getState().gold;
const train=economy.trainRobotStat("aurorion","str");assert(train.ok);assert.equal(save.getState().gold,before-train.cost);assert.equal(save.getState().robots[0].trained.str,1);
assert.equal(economy.trainRobotStat("bogus","str").ok,false);
save.resetGame();save.addGold(ITEM_MAP.capsule.price);
const capsule=economy.purchaseSupplies("capsule",1,()=>0);assert(capsule.ok&&capsule.robotId);
assert.equal(save.getState().robots[0].level,1);assert.deepEqual(save.getState().team,[capsule.robotId]);assert.equal(save.getState().gold,0);

const robot=(id:string)=>({id,level:1,xp:0,trained:{str:0,def:0,agl:0},borrowed:true});
const c=combat.createCombat({arena:"hangar",playerTeam:[robot("aurorion")],enemyTeam:[robot("ferrovax")],items:{}});
c.phase="menu";c.order=["player0","enemy0"];c.cursor=1;c.ready="player0";
const p=c.player.fighters[0];p.ultimateCharge=100;p.mp=0;p.res=0;p.passives=[];
const events=combat.resolveRound(c,{kind:"ultimate"});
const event=events.find(e=>e.t==="ultimate");assert(event?.t==="ultimate");
assert.equal(event.uid,p.uid);assert.equal(event.targetUid,c.enemy.fighters[0].uid);assert(event.vfx);assert(events.some(e=>e.t==="dmg"));
console.log(`PASS: ${LAUNCH_ASSETS.length} real asset paths; preload concurrency/errors/dedupe/abort; all system guides and level boundaries; live transactional shop/training; legal team and empty-roster recruitment; ultimate actor/target event.`);