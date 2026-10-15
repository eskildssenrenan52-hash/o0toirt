from pathlib import Path
from PIL import Image
import hashlib,json
src=Path('/home/user/assets_gen/overhaul');out=Path('/home/user/Uiop-3486/packages/web/public/overhaul');out.mkdir(exist_ok=True)
im=Image.open(src/'ui-atlas.png').convert('RGBA')
names=['attack','defense','items','ultimate','fist','blades','missiles','vortex','shield','repair','hangar','arena','coliseum','systems','star','pilot']
for i,name in enumerate(names):
 c=im.crop((i%4*256,i//4*256,(i%4+1)*256,(i//4+1)*256))
 # Remove only the black matte; preserve luminous anti-aliased details.
 px=c.load()
 for y in range(c.height):
  for x in range(c.width):
   r,g,b,a=px[x,y];px[x,y]=(r,g,b,0 if max(r,g,b)<12 else a)
 c.save(out/f'{name}.webp',quality=95)
report=[]
for name in ['holo-a','holo-b']:
 im=Image.open(src/f'{name}.png').convert('RGB');sheet=Image.new('RGB',(1000,1000))
 hashes=[]
 for i in range(25):
  x=i%5;y=i//5;c=im.crop((round(x*im.width/5),round(y*im.height/5),round((x+1)*im.width/5),round((y+1)*im.height/5))).resize((200,200),Image.Resampling.LANCZOS)
  hashes.append(hashlib.sha256(c.tobytes()).hexdigest());sheet.paste(c,(x*200,y*200))
 assert len(set(hashes))==25
 sheet.save(out/f'{name}.webp',quality=96);report.append({'asset':name,'frames':25,'distinct':25,'dimensions':[1000,1000]})
Image.open(src/'title.png').save(out/'title.webp',quality=94)
(src/'validation.json').write_text(json.dumps(report,indent=2));print(report)