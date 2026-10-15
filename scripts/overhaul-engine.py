from pathlib import Path
import re
root=Path('/home/user/Uiop-3486/packages/web/src/web')
def change(f,a,b):
 p=root/f;s=p.read_text();assert a in s,(f,a[:80]);p.write_text(s.replace(a,b))
def section(f,a,b,text):
 p=root/f;s=p.read_text();i=s.index(a);j=s.index(b,i);p.write_text(s[:i]+text+s[j:])
section('game/skills.ts','/**\n * Os slots padrão','/** Slots de um kit','''/** Ultimate is always outside the six ordinary slots. */
export function exclusiveUltimate<T extends Skill>(skills: T[]): T | undefined {
 const a=skills.filter(s=>s.kind==="attack");
 return a.find(s=>s.tags?.includes("ultimate")) ?? [...a].sort((x,y)=>y.power-x.power)[0];
}
export function normalizeLoadout(skills: Skill[], selected: string[]=[]): string[] {
 const ult=exclusiveUltimate(skills)?.id;
 const ordinary=skills.filter(s=>s.id!==ult);
 const chosen=[...new Set(selected)].map(id=>ordinary.find(s=>s.id===id)).filter((s):s is Skill=>!!s);
 const pick=(kind:Skill["kind"],n:number)=>[...new Set([...chosen,...ordinary].filter(s=>s.kind===kind).map(s=>s.id))].slice(0,n);
 return [...pick("attack",4),...pick("defense",2)];
}
export function defaultLoadout(skills: Skill[]): string[] { return normalizeLoadout(skills); }

''')
change('game/kits/index.ts','defaultLoadout, MAX_LOADOUT','defaultLoadout')
section('game/kits/index.ts','/** Loadout padrão:','/** Todas as mecanicas','''/** Four attacks + two defenses; ultimate separate. */
export function defaultKitLoadout(robotId:string):string[] { return defaultLoadout(skillsOf(robotId)); }

''')
change('game/save.ts','defaultLoadout, MAX_LOADOUT','defaultLoadout, normalizeLoadout')
section('game/save.ts','  const valid = new Set(def.skills.map((k) => k.id));','\n}\n\nexport function setLoadout','  return normalizeLoadout(def.skills,s.loadouts[robotId] ?? []);')
section('game/save.ts','  const valid = new Set((def?.skills ?? []).map((k) => k.id));','\n}\n\n/** Reseta','''  if (!def) return;
  const clean=normalizeLoadout(def.skills,skillIds);
  setState(st=>({...st,loadouts:{...st.loadouts,[robotId]:clean}}));''')
f='game/combat.ts'
change(f,'defaultLoadout,','defaultLoadout, normalizeLoadout, exclusiveUltimate,')
change(f,'  /** medidor individual (0..10). */\n  combo: number;','  /** Independent charge, 0–100%, retained while benched. */\n  ultimateCharge: number;')
change(f,'  /** medidor que alimenta a ultimate do time. */','  /** Chassis stacks, not a shared ultimate meter. */')
change(f,'  /** medidor de combo do time (0..10). */\n  combo: number;\n  /** ultimate combinado disponivel. */\n  comboReady: boolean;','')
change(f,'{ kind: "combo"; targetUid?: string }','{ kind: "ultimate"; targetUid?: string }')
change(f,'{ t: "combo"; side: Side; value: number; label: string }','{ t: "charge"; side: Side; uid: string; value: number }\n  | { t:"ultimate"; side:Side; uid:string; robotId:string; label:string }')
change(f,'export const COMBO_COST = 8;\nexport const COMBO_MAX = 10;','export const ULTIMATE_MAX = 100;')
section(f,'/**\n * A ultimate de um lutador:','/** Habilidades realmente','''/** Exclusive kit ultimate, independent of equipped skills. */
export function ultimateOf(m:FighterView):KitSkill { return exclusiveUltimate(kitOf(m.robotId).skills)!; }

''')
section(f,'  const kit = skillsOf(robotId);','\n/* =================================================== status','''  const skills=skillsOf(robotId);
  const ordinary=skills.filter(s=>s.id!==exclusiveUltimate(skills)?.id);
  const n=1+seed%3;
  return normalizeLoadout(skills,[ordinary.find(s=>s.kind==="attack"&&s.mp===0)?.id??"",...ordinary.slice(n).map(s=>s.id),...ordinary.slice(0,n).map(s=>s.id)]);
}
''')
section(f,'  const kitIds = new Set(kit.skills.map((s) => s.id));','  const resId: ResourceId','''  const fallback=ai?aiLoadout(save.id,save.level*31+save.id.length*17):defaultLoadout(kit.skills);
  const skillIds=normalizeLoadout(kit.skills,save.loadout??fallback);

''')
change(f,'      combo: 0,\n      comboReady: false,','')
change(f,'    combo: 0,','    ultimateCharge: 0,')
section(f,'function comboEv(','function phaseEv(','''function chargeEv(ctx:Ctx,m:Combatant):void { push(ctx,{t:"charge",side:m.side,uid:m.uid,value:m.ultimateCharge}); }

''')
p=root/f;s=p.read_text();s=re.sub(r'teamOf\(c, (who|foe|atk|vic)\.side\)\.combo',r'\1.ultimateCharge / 10',s);p.write_text(s)
section(f,'/** Medidor de combo do time:','/** Aliado de guarda','''/** One charge increment per action, not per hit. */
function gainUltimate(ctx:Ctx,m:Combatant,amount:number):void {
 if(amount<=0||!alive(m))return;
 const before=m.ultimateCharge;
 m.ultimateCharge=Math.min(ULTIMATE_MAX,Math.round(before+amount));
 if(before!==m.ultimateCharge)chargeEv(ctx,m);
 if(before<ULTIMATE_MAX&&m.ultimateCharge===ULTIMATE_MAX){msg(ctx,`${m.name}: ULTIMATE PRONTO — 100%.`);hist(ctx,`${m.name}: ultimate carregado`);}
}

''')
change(f,'  addCombo(ctx, atk.side, skill.meter ?? 1);','')
change(f,'  vic.hp = Math.max(0, vic.hp - dmg);','  const hpLost=Math.min(vic.hp,dmg);\n  vic.hp = Math.max(0, vic.hp - dmg);\n  if(hpLost>0)gainUltimate(ctx,vic,Math.min(16,Math.max(4,Math.ceil(hpLost/vic.maxHp*40))));')
change(f,'  dst.hp = Math.max(0, dst.hp - d);','  const hpLost=Math.min(dst.hp,d);\n  dst.hp = Math.max(0, dst.hp - d);\n  if(src.uid!==dst.uid&&hpLost>0)gainUltimate(ctx,dst,Math.min(16,Math.max(4,Math.ceil(hpLost/dst.maxHp*40))));')
change(f,'      if (!skill) return;','      if (!skill || !m.skillIds.includes(skill.id) || skill.id===ultimateOf(m).id) return;')
change(f,'        if (skill.mp > 0) clampMp(m, m.mp - skill.mp);\n        return;','        if (skill.mp > 0) clampMp(m, m.mp - skill.mp);\n        gainUltimate(ctx,m,18);\n        return;')
change(f,'      const spent = spendRes(ctx, m, skill.cost);','      const spent = spendRes(ctx, m, skill.cost);\n      gainUltimate(ctx,m,skill.kind==="defense"?14:18);')
change(f,'    case "guard": {\n      if (m.side','    case "guard": {\n      gainUltimate(ctx,m,14);\n      if (m.side')
change(f,'    case "dodge": {\n      m.evadeTurns','    case "dodge": {\n      gainUltimate(ctx,m,14);\n      m.evadeTurns')
change(f,'    case "combo": {\n      fireCombo(ctx, m.side, plan.target);','    case "ultimate": {\n      fireUltimate(ctx,m,plan.target);')
section(f,'/** Ultimate combinado:','/** Foe aleatorio','''/** One actor, consumes charge, no MP/resource payment or teammate action. */
function fireUltimate(ctx:Ctx,m:Combatant,target?:Combatant):void {
 if(m.ultimateCharge<ULTIMATE_MAX)return;
 const skill=ultimateOf(m);
 const vic=target&&alive(target)&&target.side!==m.side&&reachesBench(skill)?target:foeOf(ctx,m);
 if(!vic||!alive(vic))return;
 m.ultimateCharge=0;chargeEv(ctx,m);
 msg(ctx,`${m.name} — ${skill.name}!`);hist(ctx,`${m.name} usa ultimate exclusivo ${skill.name}`);
 push(ctx,{t:"ultimate",side:m.side,uid:m.uid,robotId:m.robotId,label:skill.name});
 clipEv(ctx,m.side,"attack",m.uid);vfxEv(ctx,m.side,skill.vfx,m.uid);
 const hits=Math.max(1,skill.hits??1);
 for(let i=0;i<hits&&alive(m)&&alive(vic);i++)strike(ctx,m,vic,skill,{idx:i,hits,spent:0});
}

''')
section(f,'  // 3. ultimate combinado:','  // 4. golpe:','''  if(m.ultimateCharge>=ULTIMATE_MAX&&foes.length)return {kind:"ultimate",target:pickTarget(ctx,m,foes)??undefined};

''')
change(f,'    case "combo":\n      return { kind: "combo", target: pick(action.targetUid) };','    case "ultimate":\n      return { kind: "ultimate", target: pick(action.targetUid) };')
change('game/battle.ts','export { COMBO_COST, COMBO_MAX, DIFFICULTY }','export { ULTIMATE_MAX, DIFFICULTY }')
for name in ['game/mechanics.ts','game/passives.ts']:
 p=root/name;s=p.read_text().replace('combo: number','charge: number').replace('.combo *','.charge *').replace('medidor de combo do time (0..10)','carga individual normalizada (0..10)');p.write_text(s)
change(f,'res: number, combo: number','res: number, charge: number')
change(f,'m: Combatant, combo: number, turn: number','m: Combatant, charge: number, turn: number')
change(f,'    combo,','    charge,')
print('Engine migration applied')