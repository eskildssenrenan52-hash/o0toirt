import { mkdir, writeFile } from "node:fs/promises";
import { ROBOTS } from "../packages/web/src/web/game/robots";
import { NPC_DEFS } from "../packages/web/src/web/game/enemies";
import { kitOf } from "../packages/web/src/web/game/kits";
import { exclusiveUltimate } from "../packages/web/src/web/game/skills";

const themes=[
 ["DUNA","TERRA","sandstone armor, amber glass reactor, wind-eroded plating"],
 ["MARÉ","AGUA","deep-sea pressure suit, coral horns, translucent water pipes"],
 ["NEON","ELETRICO","street racing chassis, luminous turquoise trim, angular optics"],
 ["BRASA","FOGO","volcanic ceramic plates, exposed ember furnace, soot seams"],
 ["GEADA","GELO","faceted ice armor, frost vents, cobalt spear mechanisms"],
 ["BOSQUE","BIO","living wooden limbs, moss circuits, branching antlers"],
 ["ASTRO","COSMICO","meteor iron plates, star-map core, orbital rings"],
 ["ONIX","SOMBRA","black obsidian facets, violet seams, crescent optics"],
 ["PRISMA","CRISTAL","transparent quartz shell, iridescent joints, refractive blades"],
 ["FERRUGEM","METAL","industrial rivets, copper pistons, salvaged train plating"],
 ["VAPOR","IMPACTO","brass boiler armor, steam pipes, flywheel shoulders"],
 ["LÓTUS","ARCANO","ceremonial porcelain plating, rose mechanical petals, floating sigils"],
 ["PÓLEN","BIO","bee-wing panels, golden hexagonal reactor, petal exhaust"],
 ["CINZA","FOGO","ashen bone-shaped ceramics, red coal optics, forge gauntlets"],
 ["CORAL","AGUA","fan-coral shield panels, pearl dome, articulated diver hoses"],
 ["TUNDRA","GELO","white shaggy fiber plating, polar blue eye, insulated joints"],
 ["CROMO","METAL","mirror chrome shoulder plates, violet pressure pistons, segmented spine"],
 ["GRAV","QUANTICO","floating disconnected limbs, gravity gyros, black spherical core"],
 ["CÍRCULO","ARCANO","clockwork ritual wheels, ivory dials, emerald rune center"],
 ["RADAR","LUZ","solar sail panels, bright scanning lens, thin gold frames"],
 ["TÓXIS","TOXICO","sealed acid tanks, rubber bellows, jade exhaust globules"],
 ["TEMPESTADE","AR","folding turbine wings, swept-back fins, cloud-gray titanium"],
 ["RUBI","CRISTAL","deep crimson gems, prismatic sword joints, copper lattice"],
 ["LUNAR","COSMICO","chalk-white lunar plating, navy joints, moon-crater shield"],
 ["ELETRON","ELETRICO","orange induction coils, four-pronged lightning crown, rubber seals"],
 ["MIRAGEM","SOMBRA","holographic ribbons, dark mirrored mask, violet segmented limbs"],
 ["RAIZ","TERRA","stone bark armor, emerald roots, terraced rock shoulders"],
 ["AURORA","LUZ","aurora glass armor, articulated feather turbines, gold halo reactor"],
] as const;
const forms=[
 ["MANTÍDEA","lean mantis biped, scythe forearms, triangular head"],
 ["BASTIÃO","wide quadruped fortress, huge front shield, back-mounted cannon"],
 ["SERPENTE","long coiled segmented tail, upright cobra torso, twin blades"],
 ["CORVO","winged avian biped, pointed beak helmet, feather-like blade wings"],
 ["CARANGUEJO","six-legged low crab tank, asymmetric giant claw, dorsal eye"],
 ["LEÃO","heavy feline quadruped, circular mane gears, fang-shaped muzzle"],
 ["MEDUSA","floating bell dome, six dangling articulated tentacles, central lens"],
 ["CAVALEIRO","tall armored humanoid, lance arm, kite shield, angular crest"],
 ["BESOURO","round squat beetle biped, lifting horn, hydraulic fists"],
] as const;
const ready=new Set(["aurorion","ferrovax","cryolance","voltronin","pyrokaiser","terrabyte","zephyrblade","nullshade","acidra","gravitus"]);
const existing=ROBOTS.map(r=>({id:r.id,name:r.name,element:r.element,recruitable:true,status:"playable",normalArt:"verified",ultimateArt:ready.has(r.id)?"ready-first-lot":"pending",specialArt:ready.has(r.id)?"ready-first-lot":"pending",ultimate:exclusiveUltimate(kitOf(r.id).skills)?.name}));
const proposals=Array.from({length:244},(_,i)=>{
 const theme=themes[Math.floor(i/9)],form=forms[i%9],id=`mc_${String(i+257).padStart(3,"0")}`;
 return {id,name:`${form[0]} ${theme[0]}`,element:theme[1],recruitable:true,status:"planned-not-playable",normalArt:"pending",ultimateArt:"pending",specialArt:"pending",identity:`${form[1]}; ${theme[2]}. Original detailed anime pixel-art robot, stable silhouette and colors, directional rim lighting.`,ratios:{hp:90+i*7%51,mp:85+i*11%46,str:90+i*13%41,def:90+i*17%41,ag:80+i*19%61,mv:10+i%5,xv:10+i%6},ordinaryAttacks:[`PULSO ${theme[0]}`,`GARRA ${form[0]}`,`RUPTURA ${theme[0]}`,`INVESTIDA ${form[0]}`],defenses:[`ESCUDO ${theme[0]}`,`REPARO ${form[0]}`],ultimate:`APOGEU ${form[0]} ${theme[0]}`,regularBatch:Math.floor(i/9)+1,regularRow:i%9};
});
const npcs=NPC_DEFS.map(r=>({id:r.id,name:r.name,element:r.element,recruitable:false,status:"playable",normalArt:"verified",ultimateArt:"pending",specialArt:"pending",ultimate:exclusiveUltimate(kitOf(r.id).skills)?.name}));
const identities=[...existing,...proposals,...npcs];
const batches=(list:{id:string}[],n:number)=>Array.from({length:Math.ceil(list.length/n)},(_,i)=>({batch:i+1,ids:list.slice(i*n,(i+1)*n).map(x=>x.id),rows:Math.min(n,list.length-i*n),columns:n===9?16:10,unusedRows:n-Math.min(n,list.length-i*n)}));
if(new Set(identities.map(r=>r.id)).size!==508)throw new Error("Identity collision");
await mkdir("/home/user/Uiop-3486/assets/overhaul",{recursive:true});
await writeFile("/home/user/Uiop-3486/assets/overhaul/production-manifest.json",JSON.stringify({note:"Production plan, not a completed playable roster. New design proposals and combat kits require generation and validation before registration.",counts:{playableRecruitable:existing.length,plannedRecruitable:500,npc:8,exclusiveAnimationPairsReady:10,exclusiveAnimationPairsPending:498},identities,regularBatches:batches(proposals,9),ultimateBatches:batches(identities,10),specialBatches:batches(identities,10)},null,2));
console.log("Plan: 244 new chassis, 28 regular batches (last: 1), 51 ultimate and 51 VFX batches (last: 8). Playable roster remains 256 + 8 NPCs until art validation.");