from pathlib import Path
from PIL import Image
import json,hashlib
src=Path('/home/user/assets_gen/overhaul')
out=Path('/home/user/Uiop-3486/packages/web/public/overhaul/ultimates');out.mkdir(exist_ok=True)
ids=json.loads((src/'identities-01.json').read_text())
if isinstance(ids,dict): ids=ids.get('ids',ids.get('identities',[]))
manifest={};report=[]
# Hand-inspected separators in the generated sources, not an assumed 10x10 grid.
# Keep the row bounds explicit: uniform crops leaked adjacent identities.
bounds = {
 'ultimate': {'x':[0,97,198,302,405,507,611,711,833,932,1024],
              'y':[0,99,198,296,390,490,592,692,794,898,1024]},
 'special': {'x':[0,103,205,307,409,511,615,718,819,921,1024],
             'y':[0,107,211,317,422,527,633,737,836,926,1024]},
}
contact=Image.new('RGB',(1280,10*288),(12,16,22))
for kind in ['ultimate','special']:
 im=Image.open(src/f'{kind}-01.png').convert('RGBA')
 assert im.size==(1024,1024),'Reinspect separators if the source resolution changes.'
 xs,ys=bounds[kind]['x'],bounds[kind]['y']
 for row,rid in enumerate(ids):
  strip=Image.new('RGBA',(1280,128));hashes=[]
  for col in range(10):
   inset=4 if kind=='special' else 3
   box=(xs[col]+inset,ys[row]+inset,xs[col+1]-inset,ys[row+1]-inset)
   c=im.crop(box)
   # Scale once per row, keeping each frame's artwork aspect ratio intact.
   scale=min(120/(ys[row+1]-ys[row]-2*inset),
             120/max(xs[i+1]-xs[i]-2*inset for i in range(10)))
   c=c.resize((round(c.width*scale),round(c.height*scale)),Image.Resampling.NEAREST)
   frame=Image.new('RGBA',(128,128))
   frame.alpha_composite(c,((128-c.width)//2,124-c.height))
   c=frame
   px=c.load()
   for y in range(128):
    for x in range(128):
     r,g,b,a=px[x,y]
     if max(r,g,b)<18:px[x,y]=(r,g,b,0)
   hashes.append(hashlib.sha256(c.tobytes()).hexdigest());strip.paste(c,(col*128,0))
  assert len(set(hashes))==10,(kind,rid)
  strip.save(out/f'{rid}-{kind}.webp',lossless=True)
  contact.paste(strip,(0,row*288+(0 if kind=='ultimate' else 136)),strip)
  manifest.setdefault(rid,{})[kind]=f'/overhaul/ultimates/{rid}-{kind}.webp'
  report.append({'id':rid,'kind':kind,'frames':10,'distinct':10,'size':[1280,128],
                 'sourceRow':[ys[row]+inset,ys[row+1]-inset],
                 'note':'Distinct hashes check file integrity, not animation/identity quality.'})
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
(src/'ultimate-validation.json').write_text(json.dumps(report,indent=2))
contact.save(src/'cut-inspection-all.png')
print(f'{len(manifest)} identities, {len(report)} strips, ten distinct frames each.')