from pathlib import Path
root=Path('/home/user/Uiop-3486/packages/web/src/web')
p=root/'components/hub-city.tsx';s=p.read_text()
s='import { SystemDock } from "./system-dock";\nimport { systemUnlocked } from "@/game/progression";\n'+s
s=s.replace('export function HubCity({ onEnter }: { onEnter: (s: Exclude<Screen, "menu">) => void })','export function HubCity({ onEnter, enabled=true }: { onEnter: (s: Exclude<Screen, "menu">) => void; enabled?:boolean })')
s=s.replace('  const st = useGame();','  const st = useGame();\n  const stateRef=useRef(st);stateRef.current=st;')
s=s.replace('  busyRef.current = busy;','  busyRef.current = busy || !enabled || picker;')
s=s.replace('    jumpBuf.current = BUFFER;','    if(busyRef.current)return;\n    jumpBuf.current = BUFFER;',1)
s=s.replace('    if (!b || busyRef.current) return;','    if (!b || busyRef.current || !systemUnlocked(stateRef.current,b.id)) return;')
s=s.replace('      const k = e.key.toLowerCase();','      if(busyRef.current)return;\n      const k = e.key.toLowerCase();',1)
s=s.replace('      t += dt;','      if(busyRef.current){input.current={left:false,right:false,run:false,jumpHeld:false};raf=requestAnimationFrame(tick);return;}\n      t += dt;',1)
s=s.replace('BUILDINGS.find((bb) => Math.abs(bb.x - P.x)','BUILDINGS.find((bb) => systemUnlocked(stateRef.current,bb.id) && Math.abs(bb.x - P.x)')
s=s.replace('      for (const bd of BUILDINGS) {\n        const im = imgs[bd.art];','      for (const bd of BUILDINGS) {\n        if(!systemUnlocked(stateRef.current,bd.id))continue;\n        const im = get(bd.art);')
s=s.replace('        ⬢ {score}\n        {combo > 1 && <span style={{ color: "#ff5fd0" }}> x{combo}</span>}','        PILOTO NV {st.playerLevel}\n        <div style={{fontSize:5,color:"#86b0c5",marginTop:5}}>NÚCLEOS {score}{combo>1?` ×${combo}`:""}</div>')
a=s.index('      {/* Atalhos rápidos */}');b=s.index('      {/* Trocar robô de exploração',a)
s=s[:a]+'''      <SystemDock disabled={busy||!enabled} onEnter={id=>{
        if(systemUnlocked(stateRef.current,id))transition(()=>onEnter(id));
      }}/>

'''+s[b:]
s=s.replace('          top: 40,','          top: 60,',1)
p.write_text(s)
p=root/'components/game-shell.tsx';s=p.read_text().replace('<HubCity onEnter={enter} />','<HubCity onEnter={enter} enabled={screen==="menu"} />');p.write_text(s)
p=root/'components/ultimate-cinematic.tsx';s=p.read_text().replace('REAT OR','REATOR').replace('<RobotSprite id={robotId}','<RobotSprite robotId={robotId}');p.write_text(s)
p=root/'screens/battle.tsx';s=p.read_text().replace('  recordProgress = true,','  recordProgress = true,\n  difficulty,',1).replace('  recordProgress?: boolean;','  recordProgress?: boolean;\n  difficulty?: import("@/game/battle").Difficulty;',1).replace('createBattle({ arena, playerTeam, enemyTeam, items })','createBattle({ arena, playerTeam, enemyTeam, items, difficulty })');p.write_text(s)
print('Title/tutorial routing, level-gated city and grouped symbolic shortcuts integrated.')