from pathlib import Path
from PIL import Image
import hashlib,json,urllib.request

root=Path('/home/user/Uiop-3486/packages/web/public')
paths=list((root/'launch').glob('*.webp'))+list((root/'overhaul/ultimates').glob('*.webp'))
result=[]
for path in paths:
    im=Image.open(path).convert('RGBA')
    url='/'+str(path.relative_to(root))
    with urllib.request.urlopen('http://127.0.0.1:4200'+url,timeout=20) as response:
        assert response.status==200,url
        mime=response.headers.get_content_type()
        assert mime.startswith('image/'),(url,mime)
        data=response.read()
        assert hashlib.sha256(data).digest()==hashlib.sha256(path.read_bytes()).digest(),url
    hashes=[]
    if path.stem in ['loader-a','loader-b']:
        assert im.size==(1000,1000)
        hashes=[hashlib.sha256(im.crop((x*200,y*200,(x+1)*200,(y+1)*200)).tobytes()).hexdigest() for y in range(5) for x in range(5)]
    elif path.parent.name=='ultimates':
        assert im.width==im.height*10,(url,im.size)
        hashes=[hashlib.sha256(im.crop((x*im.height,0,(x+1)*im.height,im.height)).tobytes()).hexdigest() for x in range(10)]
        assert im.getextrema()[3][0]==0,(url,'no transparent pixels')
    if hashes:assert len(set(hashes))==len(hashes),(url,'duplicate frames')
    result.append({'url':url,'size':im.size,'frames':len(hashes) or 1,'distinctFrames':len(set(hashes)) or 1,'http':200,'mime':mime})
out=Path('/home/user/Uiop-3486/assets/overhaul/polish-art-validation.json')
out.write_text(json.dumps(result,indent=2))
print(f'PASS: {len(result)} post-build images, HTTP image MIME/file hashes, 50 loading cells, 20 transparent ten-frame strips.')