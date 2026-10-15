from pathlib import Path
from PIL import Image
import json, hashlib

src=Path('/home/user/assets_gen/overhaul')
out=Path('/home/user/Uiop-3486/packages/web/public/launch')
out.mkdir(exist_ok=True)
report=[]
for name in ['remulu-logo','loader-hangar','loader-city','loader-orbit']:
 im=Image.open(src/f'{name}.png').convert('RGB')
 im.save(out/f'{name}.webp',quality=94,method=6)
 report.append({'name':name,'size':im.size})
for name in ['loader-a','loader-b']:
 im=Image.open(src/f'{name}.png').convert('RGBA')
 sheet=Image.new('RGBA',(1000,1000))
 hashes=[]
 for i in range(25):
  x,y=i%5,i//5
  cell=im.crop((round(x*im.width/5)+2,round(y*im.height/5)+2,
                round((x+1)*im.width/5)-2,round((y+1)*im.height/5)-2))
  cell=cell.resize((200,200),Image.Resampling.NEAREST)
  data=list(cell.getdata())
  cell.putdata([(r,g,b,0 if max(r,g,b)<19 else a) for r,g,b,a in data])
  hashes.append(hashlib.sha256(cell.tobytes()).hexdigest())
  sheet.paste(cell,(x*200,y*200))
 assert len(set(hashes))==25,name
 sheet.save(out/f'{name}.webp',lossless=True)
 report.append({'name':name,'size':[1000,1000],'frames':25,'uniqueHashes':25})
(out/'art-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))