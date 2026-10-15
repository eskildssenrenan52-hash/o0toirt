exec(open('/home/user/Uiop-3486/scripts/overhaul-engine.py').read().split("section('game/skills.ts'")[0])
f='game/combat.ts'
change(f,'defaultLoadout, normalizeLoadout, exclusiveUltimate, normalizeLoadout, exclusiveUltimate, MAX_LOADOUT','defaultLoadout, normalizeLoadout, exclusiveUltimate')
change(f,'  const glevel = ai ? aiGadgetLevel(save.id, save.level) : Math.max(0, save.gadgetLevel ?? 0);','  const gear=ai?DIFFICULTY[difficulty].gear:1;\n  const glevel=ai?Math.round(aiGadgetLevel(save.id,save.level)*gear):Math.max(0,save.gadgetLevel??0);')
change(f,'const chipIds = ai ? aiChips(save.id, save.level) : gadgetChipsOf(st8, save.id);','const chipIds = ai ? scaleKit(aiChips(save.id,save.level),gear) : gadgetChipsOf(st8,save.id);')
change(f,'const aiIds = ai ? aiDeck(save.id, save.level) : [];','const aiIds = ai ? scaleKit(aiDeck(save.id, save.level),gear) : [];')
change(f,'resolveDeck(aiIds, aiRefineMap(aiIds, save.level))','resolveDeck(aiIds,Object.fromEntries(aiIds.map(id=>[id,Math.max(1,Math.round(aiRefine(save.level)*gear))])))')
change(f,'    res,\n    resMax,','    res: 0,\n    resMax,\n    fainted: false,')
change(f,'if (p.out.mp) clampMp(ctx, m, 0);','if (p.out.mp) clampMp(m,m.mp+p.out.mp);')
change(f,'m.charged = { skillId: skill.id, targetUid: vic.uid };','m.charged = skill.id;')
# Charges resolve when the actor gets its next turn, not while ticking inactive fighters.
change(f,'    if (m.chargeTurns <= 0) resolveCharged(ctx, m);','')
change(f,'  if (!canAct(ctx, m)) return;\n  const imp','  if (!canAct(ctx,m)) return;\n  if(m.charged&&m.chargeTurns<=0){resolveCharged(ctx,m);return;}\n  const imp')
change(f,'        resPolicy(ctx, m, "onTurn");','        gainUltimate(ctx,m,18);')
# Only stepOrder applies the resource turn policy, exactly once.
p=root/f;s=p.read_text();a=s.index('function runPlan(');b=s.index('/** Abre uma das 5 defesas',a);chunk=s[a:b].replace('      resPolicy(ctx, m, "onTurn");\n','');s=s[:a]+chunk+s[b:];p.write_text(s)
change(f,'        strike(ctx, m, target, skill, { idx: i, hits, spent });\n      }\n      return;', '''        strike(ctx, m, target, skill, { idx: i, hits, spent });
      }
      if(reach)for(const b of livingMembers(teamOf(c,other(m.side)))){
        if(!alive(m))break;
        if(b.uid===vic.uid||b.uid===foeOf(ctx,m).uid)continue;
        strike(ctx,m,b,skill,{mult:0.4,noMiss:true,spent:0});
      }
      return;''')
section(f,'function coverGuard(', '\n/* ========================================================== virada', 'function coverGuard(_ctx:Ctx,_vic:Combatant):Combatant|null{return null;}\n')
section(f,'    case "reposition": {','    default: {', '''    case "reposition": {
      const ally=plan.target;const team=teamOf(c,m.side);const idx=ally?team.fighters.indexOf(ally):-1;
      if(ally&&alive(ally)&&idx>=0&&idx!==team.active){team.active=idx;msg(ctx,`${m.name} recua e ${ally.name} entra em campo!`);clipEv(ctx,m.side,"enter",ally.uid);animEv(ctx,m.side,"enter_teleport",0,ally.uid);orderEv(ctx);}
      return;
    }
''')
# Deduplicate recovery-era visual calls, no change to numerical rules.
p=root/f;s=p.read_text();lines=s.splitlines();out=[]
for line in lines:
 if out and line==out[-1] and 'animEv' in line:continue
 if 'if (skill.tags?.includes("ultimate")) animEv' in line:continue
 out.append(line)
p.write_text('\n'.join(out)+'\n')
# Keep stable passive ids referenced by old kits, migrate the hooks/semantics.
for p in (root/'game').rglob('*.ts'):
 s=p.read_text().replace('onCombo','onUltimateCharge').replace('GUARDIÃO DO COMBO','GUARDIÃO DO REATOR').replace('Alimenta o medidor de combo com +2 por ação.','Ao carregar o ultimate, recupera +2 de recurso do chassi.').replace('combo alimentado','reator alimentado').replace('medidor de combo do time','carga individual de ultimate');p.write_text(s)
change(f,' if(before!==m.ultimateCharge)chargeEv(ctx,m);',' if(before!==m.ultimateCharge){chargeEv(ctx,m);const f=fieldOf(ctx.c,other(m.side));if(f){const p=hook(ctx,m,f,"onUltimateCharge",{value:amount});if(p.out.res)gainRes(ctx,m,p.out.res);}}')
print('Engine restored and migrated')