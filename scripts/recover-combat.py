import json,re,os,io,builtins
from pathlib import Path
root=Path('/home/user/Uiop-3486'); target=root/'packages/web/src/web/game/combat.ts'
realopen=builtins.open
def safeopen(name,mode='r',*a,**kw):
 s=str(name)
 if s.endswith('combat.ts'): return realopen(target,mode,*a,**kw)
 if any(c in mode for c in 'wa+'):
  return io.StringIO()
 return realopen(name,mode,*a,**kw)
builtins.open=safeopen;io.open=safeopen
os.chdir(root/'packages/web')
def strings(o):
 if isinstance(o,dict):
  if isinstance(o.get('command'),str):yield o['command']
  for v in o.values():yield from strings(v)
 elif isinstance(o,list):
  for v in o:yield from strings(v)
for p in sorted(Path('/home/user/history').glob('*.json')):
 if p.stem<'1790786990343':continue
 for cmd in strings(json.loads(p.read_text())):
  if 'combat.ts' not in cmd or 'playwright' in cmd or 'import json, time' in cmd:continue
  m=re.search(r"(?:python3|python)\s+-\s+<<['\"]?(\w+)['\"]?\n(.*?)\n\1",cmd,re.S)
  if not m:continue
  code=m[2]
  if any(x in code for x in ['show(i)','print(', 's=open', 's = io.open','s=io.open']):
   if not any(x in code for x in ['write(s)','write_text(s)','write(s.replace']):continue
   try:exec(compile(code,p.name,'exec'),{})
   except Exception as e:print('SKIP',p.name,str(e)[:100])
print('Recovered',len(target.read_text().splitlines()),'lines')