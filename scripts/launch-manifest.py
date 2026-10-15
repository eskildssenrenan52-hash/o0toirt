from pathlib import Path
import json
root=Path('/home/user/Uiop-3486/packages/web')
public=root/'public'
files=sorted('/'+str(p.relative_to(public)) for p in public.rglob('*')
             if p.is_file() and p.suffix.lower() in {'.png','.webp','.jpg','.jpeg','.gif'})
target=root/'src/web/game/launch-assets.ts'
target.write_text('/** Generated from actual public files by scripts/launch-manifest.py. */\n'
                  +'export const LAUNCH_ASSETS: string[] = '+json.dumps(files,indent=2)+';\n')
print(f'{len(files)} real image URLs in launch manifest')