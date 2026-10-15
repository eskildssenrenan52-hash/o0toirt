/**
 * Fundo da cidade: o céu animado (50 quadros) precisa cobrir a tela inteira em
 * qualquer posição de câmera (inclusive no topo do mundo), e o tráfego aéreo não
 * pode lançar exceção nem se mover com movimento reduzido.
 */
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
const B = await import("../packages/web/src/web/components/city-backdrop");

type Rect = [number, number, number, number];
function mockCtx() {
  const rects: Rect[] = [];
  const stack: { tx: number; ty: number; sx: number; sy: number }[] = [];
  let m = { tx: 0, ty: 0, sx: 1, sy: 1 };
  let draws = 0;
  const grad = { addColorStop() {} };
  const ctx = {
    imageSmoothingEnabled: false, globalAlpha: 1, fillStyle: "", globalCompositeOperation: "source-over",
    save() { stack.push({ ...m }); }, restore() { m = stack.pop() ?? { tx: 0, ty: 0, sx: 1, sy: 1 }; },
    translate(x: number, y: number) { m.tx += x * m.sx; m.ty += y * m.sy; },
    scale(x: number, y: number) { m.sx *= x; m.sy *= y; },
    createLinearGradient() { return grad; }, fillRect() {}, beginPath() {}, moveTo() {}, lineTo() {}, closePath() {}, fill() {},
    drawImage(_im: unknown, ...a: number[]) {
      draws++;
      for (const v of a) assert(Number.isFinite(v), "coordenada não finita");
      const [dx, dy, dw, dh] = a.length === 8 ? a.slice(4) : a.length === 4 ? a : [a[0], a[1], 0, 0];
      const x0 = m.tx + m.sx * dx, x1 = m.tx + m.sx * (dx + dw);
      const y0 = m.ty + m.sy * dy, y1 = m.ty + m.sy * (dy + dh);
      rects.push([Math.min(x0, x1), Math.min(y0, y1), Math.max(x0, x1), Math.max(y0, y1)]);
    },
  };
  return { ctx: ctx as unknown as CanvasRenderingContext2D, rects, draws: () => draws, raw: ctx };
}
const img = (w: number, h: number) => ({ complete: true, naturalWidth: w, naturalHeight: h }) as unknown as HTMLImageElement;
const sky = img(2400, 2700), atlas = img(1100, 669);

const GROUND_Y = 620, SKY_TOP = -260;
let checks = 0;
for (const w of [320, 390, 480, 800, 1280, 1920, 2560]) for (const h of [360, 600, 800, 1080, 1400]) {
  const cyGround = GROUND_Y + 120 - h;
  for (const cy of [cyGround + 120, cyGround, (cyGround + SKY_TOP) / 2, SKY_TOP, SKY_TOP - 300]) for (const cx of [-500, 0, 1234.5, 8600, 99999]) for (const t of [0, 0.05, 3.33, 4.99, 777]) {
    const cam = { w, h, cx, cy, cyGround, cyTop: SKY_TOP, t, still: false };
    const m = mockCtx();
    B.drawSky(m.ctx, sky, cam);
    // cobertura: varre colunas e linhas em passos de 4px
    for (let x = 0; x <= w; x += Math.max(4, w / 64)) for (let y = 0; y <= h; y += Math.max(4, h / 64)) {
      assert(m.rects.some(([a, b, c, d]) => a <= x + 0.5 && c >= x - 0.5 && b <= y + 0.5 && d >= y - 0.5), `céu não cobre (${x},${y}) w=${w} h=${h} cy=${cy} cx=${cx}`);
    }
    checks++;
    for (const slot of ["far", "mid", "near"] as const) { B.drawTraffic(m.ctx, atlas, slot, cam); checks++; }
    B.drawSearchlights(m.ctx, cam, GROUND_Y - cy);
    assert.equal(m.raw.globalAlpha, 1); assert.equal(m.raw.imageSmoothingEnabled, false);
  }
}
// movimento reduzido: tráfego parado e céu no quadro 0
const still = (t: number) => { const m = mockCtx(); const cam = { w: 800, h: 800, cx: 300, cy: -60, cyGround: -60, cyTop: SKY_TOP, t, still: true }; for (const s of ["far", "mid", "near"] as const) B.drawTraffic(m.ctx, atlas, s, cam); B.drawSky(m.ctx, sky, cam); return JSON.stringify(m.rects); };
assert.equal(still(0), still(12.7)); checks++;
// em movimento, o tráfego realmente anda
const moving = (t: number) => { const m = mockCtx(); const cam = { w: 1280, h: 800, cx: 300, cy: -60, cyGround: -60, cyTop: SKY_TOP, t, still: false }; for (const s of ["far", "mid", "near"] as const) B.drawTraffic(m.ctx, atlas, s, cam); return { n: m.draws(), r: JSON.stringify(m.rects) }; };
const a = moving(1), b = moving(2);
assert(a.n > 0, "nenhum veículo visível"); assert.notEqual(a.r, b.r); checks++;
assert.equal(B.SKY_FRAMES, 50); checks++;
// imagem ainda carregando: não desenha e não quebra
{ const m = mockCtx(); B.drawSky(m.ctx, { complete: false, naturalWidth: 0 } as unknown as HTMLImageElement, { w: 480, h: 800, cx: 0, cy: 0, cyGround: -60, cyTop: SKY_TOP, t: 1, still: false }); B.drawTraffic(m.ctx, undefined, "far", { w: 480, h: 800, cx: 0, cy: 0, cyGround: -60, cyTop: SKY_TOP, t: 1, still: false }); assert.equal(m.draws(), 0); checks++; }
// assets existem e o hub não usa mais as camadas opacas que "acabavam"
const pub = "/home/user/Uiop-3486/packages/web/public";
for (const p of [B.SKY_SHEET, B.TRAFFIC_ATLAS, "/city/pl_far_city.png", "/city/pl_near_city.png"]) { assert(existsSync(pub + p), p); checks++; }
const hub = readFileSync("/home/user/Uiop-3486/packages/web/src/web/components/hub-city.tsx", "utf8");
for (const bad of ['"/city/pl_sky.png"', '"/loading/city_f4.png"', '"/city/bg.png"']) { assert(!hub.includes(bad), `hub ainda usa ${bad}`); checks++; }
console.log(`PASS: ${checks} checagens do fundo da cidade (céu de 50 quadros cobre a tela em todas as câmeras, tráfego seguro, movimento reduzido).`);
