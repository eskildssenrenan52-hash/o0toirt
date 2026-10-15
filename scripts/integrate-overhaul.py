from pathlib import Path
root=Path('/home/user/Uiop-3486/packages/web/src/web')
def edit(path,fn):
 p=root/path;s=p.read_text();p.write_text(fn(s))
def battle(s):
 s=s.replace('  COMBO_COST,\n','').replace('  type Forecast,\n','')
 s='import { BattleCommands, preloadCommandArt } from "@/components/battle-commands";\nimport { UltimateCinematic } from "@/components/ultimate-cinematic";\n'+s
 s=s.replace('  startState,\n','  startState,\n  recordProgress = true,\n',1)
 s=s.replace('  arena: string;\n  round?: number;','  arena: string;\n  recordProgress?: boolean;\n  round?: number;',1)
 s=s.replace('useEffect(() => { void preloadVictoryArt(); }, []);','useEffect(() => { void preloadVictoryArt(); preloadCommandArt(); }, []);')
 s=s.replace('  const [vs, setVs] = useState(true);','  const [vs, setVs] = useState(true);\n  const [cinematic, setCinematic] = useState<{robotId:string;label:string;key:number}|null>(null);')
 s=s.replace('  const pCombo = combat.player.combo;\n  const eCombo = combat.enemy.combo;\n','')
 s=s.replace('  const finalUlt = pSkills.length ? ultimateOf(pActive) : null;\n  const comboReady = pCombo >= COMBO_COST && pActive.hp > 0;','  const finalUlt = ultimateOf(pActive);')
 a=s.index('    } else if (ev.t === "combo") {');b=s.index('    } else if (ev.t === "passive") {',a)
 s=s[:a]+'''    } else if (ev.t === "charge") {
      setBattle(b => {
        const team = b[ev.side];
        const fighters = team.fighters.map(f => f.uid === ev.uid ? {...f, ultimateCharge:ev.value} : f);
        const updated = {...team, fighters};
        return {...b, [ev.side]:updated, combat:{...b.combat, [ev.side]:{...b.combat[ev.side], fighters}}};
      });
      delay = 30;
    } else if (ev.t === "ultimate") {
      const key = ++keyRef.current;
      setStageActors(a => ({...a,[ev.side]:ev.uid}));
      setCinematic({robotId:ev.robotId,label:ev.label,key});
      window.setTimeout(() => setCinematic(c => c?.key === key ? null : c), 1700);
      delay = 1740;
'''+s[b:]
 s=s.replace('    recordBattle(\n','    if (recordProgress) recordBattle(\n',1)
 s=s.replace('          combo={pCombo}','          charge={pActive.ultimateCharge}').replace('          combo={eCombo}','          charge={eActive.ultimateCharge}')
 a=s.index('            {menu === "root" && (');b=s.index('            {menu === "extra" && (',a)
 s=s[:a]+'''            {menu === "root" && <>
              <TargetPicker foes={foeList} chosen={foeUid} activeUid={eActive.uid} onPick={setTargetUid}/>
              <BattleCommands key={pActive.uid} fighter={pActive} skills={pSkills} ultimate={finalUlt}
                onMenu={setMenu} onSelect={setSelSkill}
                forecast={id=>damagePreview(combat,pActive.uid,foeUid,id)}
                onAction={action=>act(action.kind==="skill"||action.kind==="ultimate" ? {...action,targetUid:foeUid||undefined}:action)}/>
            </>}

'''+s[b:]
 a=s.index('/** Linha de skill com previsao');b=s.index('/** Registro de combate',a);s=s[:a]+s[b:]
 s=s.replace('      {/* HUD superior */}','      {cinematic && <UltimateCinematic key={cinematic.key} robotId={cinematic.robotId} label={cinematic.label}/>}\n\n      {/* HUD superior */}',1)
 s=s.replace('  combo,','  charge,').replace('  combo: number;','  charge: number;')
 a=s.index('        {/* medidor de combo/sincronia da equipe */}');b=s.index('        {effects.length > 0',a)
 s=s[:a]+'''        <div className="mk-title" title="Carga individual de ultimate: 100% libera o golpe exclusivo, sem MP."
          style={{display:"flex",alignItems:"center",gap:4,marginTop:3,fontSize:5,color:charge>=100?"#ffe278":"var(--mk-muted)"}}>
          <span>ULT {charge}%</span>
          <span style={{flex:1,height:4,background:"#ffffff22"}}><span style={{display:"block",height:"100%",width:`${charge}%`,background:"#ffe278"}}/></span>
        </div>

'''+s[b:]
 s=s.replace('campo, combo,','campo, carga,').replace('alternativo, combo,','alternativo, carga,')
 return s
edit(Path('screens/battle.tsx'),battle)
edit(Path('components/battle-commands.tsx'),lambda s:s.replace('||tags.includes("lamina")','').replace('||tags.includes("energia")',''))
edit(Path('game/combat.ts'),lambda s:s.replace(', ultimateAnimFor,',',').replace('/** Ultimate combinado: medidor cheio a este valor. */','/** Carga individual necessária para o ultimate exclusivo. */').replace('paineis, ordem, combo e fases','paineis, ordem, carga e fases').replace('recursos do golpe e medidor de combo','recursos do golpe').replace('analisar, combo, reposicionar','analisar, ultimate, reposicionar'))
edit(Path('game/battle.ts'),lambda s:s.replace('IA tatica, combo e ultimate\n * combinada.','IA tatica e ultimate\n * individual.').replace('(combo e dificuldade)','(carga e dificuldade)'))
def loadout(s):
 s=s.replace('EFFECT_LABEL, MAX_LOADOUT,','EFFECT_LABEL, MAX_LOADOUT, exclusiveUltimate,')
 s=s.replace('`SLOT ${i + 1}`','i < 4 ? `ATAQUE ${i + 1}` : `DEFESA ${i - 3}`')
 s=s.replace('  const list = def.skills.filter((s) =>','  const ultimate = exclusiveUltimate(def.skills)!;\n  const list = def.skills.filter(s=>s.id!==ultimate.id).filter((s) =>')
 s=s.replace('    const already = equipped.indexOf(id);','    const chosen = byId[id];\n    if (!chosen || chosen.id === ultimate.id || chosen.kind !== (slot < 4 ? "attack" : "defense")) return;\n    const already = equipped.indexOf(id);')
 a=s.index('  function preset(');b=s.index('\n  return (',a)
 s=s[:a]+'''  function preset(kind: "offense" | "balanced" | "defense") {
    const ordinary=def.skills.filter(s=>s.id!==ultimate.id);
    const atk=ordinary.filter(s=>s.kind==="attack").sort((a,b)=>kind==="offense"?b.power-a.power:a.mp-b.mp);
    const dfs=ordinary.filter(s=>s.kind==="defense").sort((a,b)=>kind==="defense"?b.power-a.power:a.mp-b.mp);
    setLoadout(robotId,[...atk.slice(0,4),...dfs.slice(0,2)].map(s=>s.id));
    setSlot(0);
  }
'''+s[b:]
 s=s.replace('      {/* RESUMO */}','''      <div style={{marginTop:6,padding:8,border:"1px solid #ffcc68",background:"#241906"}}>
        <strong className="mk-title" style={{fontSize:7,color:"#ffe39a"}}>ULTIMATE EXCLUSIVO · {ultimate.name}</strong>
        <p style={{fontSize:11,lineHeight:1.4,margin:"6px 0"}}>{ultimate.desc}</p>
        <small>Separado dos 4 ataques e 2 defesas · 100% de carga · sem MP.</small>
      </div>
      {/* RESUMO */}''')
 s=s.replace('            onClick={() => equip(s.id)}','            disabled={s.kind !== (slot < 4 ? "attack" : "defense")}\n            onClick={() => equip(s.id)}')
 return s
edit(Path('components/loadout.tsx'),loadout)
print('Integrated battle commands, individual HUD and typed loadout slots.')