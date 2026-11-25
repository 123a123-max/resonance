/**
 * 生活拼贴 —— Canvas 合成引擎（无第三方依赖，手机/电脑浏览器通用）。
 *
 * 与旧版最大的不同：
 *  1. 不再固定 4 个照片位。会根据「今日照片数量」动态排版：
 *     - 1~4 张：从模板的 4 个空位里挑出合适的 N 个放照片，
 *       剩下的空位画成手账便签卡（不会留下刺眼的空白相纸框）；
 *     - 5~8 张：4 个空位全部使用，并把其中几个空位拆成双图拼贴；
 *     - >8 张：取前 8 张并在界面提示。
 *  2. 每次点「立即生成」都会换一个随机种子（可用同一个种子复现），
 *     随机种子决定：挑哪几个空位、照片的先后分配、便签文案、
 *     以及画面边角的少量手绘点缀 —— 所以同一风格连点几次，
 *     成品的排布是不同的（底图美术风格保持一致，这才叫“同一风格”）。
 *
 * 模板底图由 tools/make_*.py 预先生成，照片空位坐标写在 templateStyles.ts，
 * 本文件只负责“把照片/便签塞进这些空位”，不改动模板美术本身。
 */
import type { PhotoSlot, SlotShape, TemplateStyle } from './templateStyles';

const W = 900;
const H = 1600;

/** 便签 / 手绘点缀的配色，按风格取色，避免所有风格长得一样 */
const STYLE_TINT: Record<string, { ink: string; card: string; accent: string }> = {
  'ins-minimal': { ink: '#7a7f78', card: '#f2f2ee', accent: '#b8bdb4' },
  'japanese-salt': { ink: '#6c7c74', card: '#eff1ea', accent: '#9fb0a4' },
  'american-retro': { ink: '#7c412e', card: '#f7e9d2', accent: '#c15132' },
  macaron: { ink: '#a4778e', card: '#fdf1f4', accent: '#e6a9bd' },
  'tech-frost': { ink: '#5a7488', card: '#eef7fb', accent: '#8fc6dd' },
  'xuan-paper': { ink: '#6e6050', card: '#f3ecdc', accent: '#a6563f' },
  'street-graffiti': { ink: '#e9ff5a', card: '#26262a', accent: '#ff4fa3' },
  'calendar-diary': { ink: '#8a6b52', card: '#fbf0e2', accent: '#d59a6a' },
  'travel-journal': { ink: '#79563c', card: '#f4e9d5', accent: '#b5844f' },
  'forest-green': { ink: '#5c6c56', card: '#f0f2e8', accent: '#9bb38c' },
  'four-seasons': { ink: '#7d7a86', card: '#f7f3f4', accent: '#d5a7b5' },
  'popart-city': { ink: '#1b2b57', card: '#fff6c9', accent: '#e5322d' },
  'vintage-montage': { ink: '#6d4a30', card: '#f5e6cb', accent: '#b35c33' },
  'minimal-photo': { ink: '#8a847a', card: '#f6f4ef', accent: '#b9b2a5' },
};

/** 便签短句池：同一风格每次随机取不同句子 */
const NOTE_TEXTS = [
  ['今天也要', '好好生活'],
  ['把日子', '过成诗'],
  ['小小的', '确幸'],
  ['慢慢来', '比较快'],
  ['记录', '当下'],
  ['日常', '碎片'],
  ['此刻', '心情'],
  ['留一点', '空白'],
  ['风很轻', '日子很长'],
  ['喜欢的', '一天'],
];

/** 轻量可复现随机数（mulberry32），避免引入任何依赖 */
function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a += 0x6d2b79f5;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** 加载图片（含 blob URL / dataURL / 同源或可跨域 URL） */
export function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('图片加载失败'));
    img.src = src;
  });
}

/** 把 blob URL 转成 dataURL，避免 canvas 被跨域图片污染导致导出失败 */
export async function toSafeDataURL(src: string): Promise<string> {
  if (/^data:/.test(src)) return src;
  try {
    const resp = await fetch(src);
    const blob = await resp.blob();
    return await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result));
      reader.onerror = () => reject(new Error('读取图片失败'));
      reader.readAsDataURL(blob);
    });
  } catch {
    // fetch 失败时退回原 URL（同源 blob 一般可直接用）
    return src;
  }
}

/** 圆角矩形路径 */
function roundRectPath(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  const rr = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.lineTo(x + w - rr, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + rr);
  ctx.lineTo(x + w, y + h - rr);
  ctx.quadraticCurveTo(x + w, y + h, x + w - rr, y + h);
  ctx.lineTo(x + rr, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - rr);
  ctx.lineTo(x, y + rr);
  ctx.quadraticCurveTo(x, y, x + rr, y);
  ctx.closePath();
}

/** 撕边路径：四边带轻微锯齿，模拟手撕纸 */
function tornPath(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, seed: number) {
  const step = 14;
  ctx.beginPath();
  let s = seed * 9301 + 49297;
  const rnd = () => { s = (s * 9301 + 49297) % 233280; return s / 233280; };
  const jitter = () => (rnd() - 0.5) * 9;
  ctx.moveTo(x + jitter(), y + jitter());
  for (let px = x + step; px < x + w; px += step) ctx.lineTo(px, y + jitter());
  ctx.lineTo(x + w + jitter(), y + jitter());
  for (let py = y + step; py < y + h; py += step) ctx.lineTo(x + w + jitter(), py);
  ctx.lineTo(x + w + jitter(), y + h + jitter());
  for (let px = x + w - step; px > x; px -= step) ctx.lineTo(px, y + h + jitter());
  ctx.lineTo(x + jitter(), y + h + jitter());
  for (let py = y + h - step; py > y; py -= step) ctx.lineTo(x + jitter(), py);
  ctx.closePath();
}

/** 按形状生成蒙版路径 */
function shapePath(ctx: CanvasRenderingContext2D, shape: SlotShape, x: number, y: number, w: number, h: number, seed: number) {
  switch (shape) {
    case 'rounded': roundRectPath(ctx, x, y, w, h, 24); break;
    case 'frost': roundRectPath(ctx, x, y, w, h, 18); break;
    case 'torn': tornPath(ctx, x, y, w, h, seed); break;
    default:
      ctx.beginPath(); ctx.rect(x, y, w, h); ctx.closePath();
  }
}

/** 以 cover 方式把图片画进目标矩形（居中裁切，不变形） */
function drawCover(ctx: CanvasRenderingContext2D, img: HTMLImageElement, x: number, y: number, w: number, h: number) {
  const scale = Math.max(w / img.width, h / img.height);
  const sw = w / scale;
  const sh = h / scale;
  const sx = (img.width - sw) / 2;
  const sy = (img.height - sh) / 2;
  ctx.drawImage(img, sx, sy, sw, sh, x, y, w, h);
}

/** 把一张照片画进某个局部矩形（局部坐标以空位中心为原点） */
function drawPhotoMasked(
  ctx: CanvasRenderingContext2D,
  img: HTMLImageElement,
  lx: number, ly: number, w: number, h: number,
  shape: SlotShape, seed: number,
) {
  ctx.save();
  shapePath(ctx, shape, lx, ly, w, h, seed);
  ctx.clip();
  drawCover(ctx, img, lx, ly, w, h);
  ctx.restore();

  ctx.save();
  shapePath(ctx, shape, lx, ly, w, h, seed);
  ctx.strokeStyle = shape === 'torn' ? 'rgba(255,255,255,0.92)' : 'rgba(255,255,255,0.62)';
  ctx.lineWidth = shape === 'torn' ? 4 : 1.5;
  ctx.stroke();
  ctx.restore();
}

/** 在单个空位贴一张照片（保留模板里的相纸/磨砂底） */
function placePhoto(
  ctx: CanvasRenderingContext2D,
  img: HTMLImageElement,
  slot: PhotoSlot,
  index: number,
) {
  const { x, y, w, h, angle, shape } = slot;
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate((angle * Math.PI) / 180);
  const lx = -w / 2;
  const ly = -h / 2;

  // 细框 / 磨砂：画半透明底与描边（模板已有相纸底，这里只加玻璃感）
  if (shape === 'frame' || shape === 'frost') {
    ctx.save();
    ctx.fillStyle = shape === 'frost' ? 'rgba(250,253,255,0.72)' : 'rgba(255,255,255,0.38)';
    roundRectPath(ctx, lx - 5, ly - 5, w + 10, h + 10, 18);
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.9)';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.restore();
  }

  drawPhotoMasked(ctx, img, lx, ly, w, h, shape, index + 1);
  ctx.restore();
}

/** 一个空位里放两张照片：按长边方向对半分，中间加一道细白缝 */
function placeDoublePhoto(
  ctx: CanvasRenderingContext2D,
  imgs: HTMLImageElement[],
  slot: PhotoSlot,
  index: number,
) {
  const { x, y, w, h, angle, shape } = slot;
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate((angle * Math.PI) / 180);
  const lx = -w / 2;
  const ly = -h / 2;
  const horizontal = w >= h; // 横向照片位上下分，纵向照片位左右分
  const gap = 6;
  if (horizontal) {
    const hw = (w - gap) / 2;
    drawPhotoMasked(ctx, imgs[0], lx, ly, hw, h, 'frame', index * 2 + 1);
    drawPhotoMasked(ctx, imgs[1], lx + hw + gap, ly, hw, h, 'frame', index * 2 + 2);
  } else {
    const hh = (h - gap) / 2;
    drawPhotoMasked(ctx, imgs[0], lx, ly, w, hh, 'frame', index * 2 + 1);
    drawPhotoMasked(ctx, imgs[1], lx, ly + hh + gap, w, hh, 'frame', index * 2 + 2);
  }
  ctx.restore();
}

/** 没分到照片的空位：画一张手账便签卡，避免留下刺眼的空白相纸框 */
function drawNoteCard(
  ctx: CanvasRenderingContext2D,
  slot: PhotoSlot,
  index: number,
  tint: { ink: string; card: string; accent: string },
  rand: () => number,
) {
  const { x, y, w, h, angle } = slot;
  const lines = NOTE_TEXTS[Math.floor(rand() * NOTE_TEXTS.length) % NOTE_TEXTS.length];
  const date = new Date();
  const dateText = `${date.getMonth() + 1}.${String(date.getDate()).padStart(2, '0')}`;

  ctx.save();
  ctx.translate(x, y);
  ctx.rotate((angle * Math.PI) / 180);
  const lx = -w / 2 + 12;
  const ly = -h / 2 + 12;
  const cw = w - 24;
  const ch = h - 24;

  // 纸卡底 + 轻微投影
  ctx.save();
  ctx.shadowColor = 'rgba(0,0,0,0.14)';
  ctx.shadowBlur = 14;
  ctx.shadowOffsetY = 5;
  ctx.fillStyle = tint.card;
  roundRectPath(ctx, lx, ly, cw, ch, 16);
  ctx.fill();
  ctx.restore();

  // 虚线内框
  ctx.save();
  ctx.setLineDash([7, 6]);
  ctx.strokeStyle = tint.accent;
  ctx.globalAlpha = 0.55;
  ctx.lineWidth = 1.5;
  roundRectPath(ctx, lx + 12, ly + 12, cw - 24, ch - 24, 10);
  ctx.stroke();
  ctx.restore();

  // 手写短句
  ctx.fillStyle = tint.ink;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  const fs = Math.max(22, Math.min(42, Math.floor(cw / 6.2)));
  ctx.font = `600 ${fs}px "KaiTi", "Microsoft YaHei", sans-serif`;
  ctx.fillText(lines[0], lx + cw / 2, ly + ch / 2 - fs * 0.62, cw - 30);
  ctx.fillText(lines[1], lx + cw / 2, ly + ch / 2 + fs * 0.62, cw - 30);

  // 日期小字
  ctx.font = '500 20px Georgia, serif';
  ctx.globalAlpha = 0.7;
  ctx.fillText(dateText, lx + cw / 2, ly + ch - 40);

  // 角上的小点缀（四角星）
  ctx.globalAlpha = 0.85;
  ctx.strokeStyle = tint.accent;
  ctx.lineWidth = 2.5;
  const sx = lx + cw - 34;
  const sy = ly + 34;
  ctx.beginPath();
  ctx.moveTo(sx - 12, sy); ctx.lineTo(sx + 12, sy);
  ctx.moveTo(sx, sy - 12); ctx.lineTo(sx, sy + 12);
  ctx.stroke();
  ctx.restore();

  void index; // 预留：将来可按槽位序号换不同版式
}

/** 画面边角的极少量手绘点缀：每次随机位置/数量，让成品各不相同 */
function drawDoodles(
  ctx: CanvasRenderingContext2D,
  slots: PhotoSlot[],
  tint: { ink: string; card: string; accent: string },
  rand: () => number,
) {
  // 候选点都在画面留白较多的边缘，避开照片位主体
  const candidates = [
    [70, 210], [820, 180], [450, 250], [80, 760], [830, 820],
    [450, 880], [90, 1330], [820, 1350], [450, 1520], [180, 1540], [700, 1540],
  ];
  const free = candidates.filter(([px, py]) =>
    slots.every((s) => Math.hypot(px - s.x, py - s.y) > Math.max(s.w, s.h) * 0.52),
  );
  const count = 2 + Math.floor(rand() * 3); // 2~4 个，克制不堆砌
  ctx.save();
  ctx.strokeStyle = tint.accent;
  ctx.fillStyle = tint.accent;
  ctx.globalAlpha = 0.55;
  ctx.lineWidth = 2.5;
  for (let i = 0; i < count && free.length; i++) {
    const pick = Math.floor(rand() * free.length);
    const [px, py] = free.splice(pick, 1)[0];
    const kind = Math.floor(rand() * 3);
    if (kind === 0) {
      const r = 9 + rand() * 5;
      ctx.beginPath();
      ctx.moveTo(px - r, py); ctx.lineTo(px + r, py);
      ctx.moveTo(px, py - r); ctx.lineTo(px, py + r);
      ctx.stroke();
    } else if (kind === 1) {
      ctx.beginPath();
      ctx.arc(px, py, 5 + rand() * 3, 0, Math.PI * 2);
      ctx.stroke();
    } else {
      ctx.beginPath();
      ctx.moveTo(px - 12, py);
      ctx.quadraticCurveTo(px, py - 10, px + 12, py);
      ctx.stroke();
    }
  }
  ctx.restore();
}

/** 一个空位的排版计划：放几张照片 */
interface SlotPlan {
  slot: PhotoSlot;
  subs: number; // 0 = 便签卡，1 = 单图，2 = 双图
}

/**
 * 根据照片数量生成排版计划。
 * 这里决定了“同一风格每次不同”的核心：随机种子换空位组合与照片顺序。
 */
function buildLayout(slots: PhotoSlot[], count: number, rand: () => number): SlotPlan[] {
  const plans: SlotPlan[] = slots.slice(0, 4).map((slot) => ({ slot, subs: 0 }));
  if (!plans.length) return plans;

  if (count <= 4) {
    let chosen: number[];
    if (count === 1) {
      // 挑最大的那个空位，让单张照片尽可能大
      const idx = plans
        .map((p, i) => ({ i, area: p.slot.w * p.slot.h }))
        .sort((a, b) => b.area - a.area)
        .slice(0, 2)[Math.floor(rand() * 2)]?.i ?? 0;
      chosen = [idx];
    } else if (count === 2) {
      // 对角线组合：错落但不挤在一起
      chosen = rand() < 0.5 ? [0, 3] : [1, 2];
    } else if (count === 3) {
      const omit = Math.floor(rand() * plans.length);
      chosen = plans.map((_, i) => i).filter((i) => i !== omit);
    } else {
      chosen = plans.map((_, i) => i);
    }
    chosen.slice(0, plans.length).forEach((i) => { if (plans[i]) plans[i].subs = 1; });
    return plans;
  }

  // 5~8 张：所有空位都用，按面积从大到小挑几个放双图
  plans.forEach((p) => { p.subs = 1; });
  const extras = Math.min(count - 4, plans.length);
  const byArea = plans
    .map((p, i) => ({ i, area: p.slot.w * p.slot.h }))
    .sort((a, b) => b.area - a.area);
  for (let k = 0; k < extras; k++) plans[byArea[k].i].subs = 2;
  return plans;
}

/** 把照片顺序做“轻度打乱”：整体轮转 + 可能交换两张，保留大致时间顺序又每次不同 */
function arrangePhotos(photos: HTMLImageElement[], rand: () => number): HTMLImageElement[] {
  if (photos.length < 2) return photos.slice();
  const out = photos.slice();
  const shift = Math.floor(rand() * out.length);
  const rotated = out.slice(shift).concat(out.slice(0, shift));
  if (rotated.length >= 2 && rand() < 0.6) {
    const a = Math.floor(rand() * rotated.length);
    let b = Math.floor(rand() * rotated.length);
    if (b === a) b = (b + 1) % rotated.length;
    [rotated[a], rotated[b]] = [rotated[b], rotated[a]];
  }
  return rotated;
}

export interface RenderResult {
  dataURL: string;
  used: number;
  seed: number;
}

/**
 * 生成一张带照片的拼贴图。
 * @param style  选中的风格（模板底图 + 空位坐标）
 * @param photos 今日照片 URL（dataURL / blob URL）
 * @param seed   随机种子；不传则每次用当前时间+随机数，保证同风格每次排布不同
 */
export async function renderStyleCollage(
  style: TemplateStyle,
  photos: string[],
  seed?: number,
): Promise<RenderResult> {
  if (!photos.length) throw new Error('今天还没有照片，先记录几条再生成');

  // 最多展示 8 张（4 个空位 × 每格最多 2 张），多余的直接忽略
  const usedPhotos = photos.slice(0, 8);
  const actualSeed = seed ?? ((Date.now() ^ Math.floor(Math.random() * 0x7fffffff)) >>> 0);
  const rand = rng(actualSeed);
  const tint = STYLE_TINT[style.id] || STYLE_TINT['ins-minimal'];

  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('当前浏览器不支持 Canvas');

  // 1. 底图（模板美术，保持风格一致）
  const templateSrc = await toSafeDataURL(style.image);
  const bg = await loadImage(templateSrc);
  ctx.drawImage(bg, 0, 0, W, H);

  // 2. 读取照片（单张失败自动跳过，不影响整张拼贴）
  const safeSources = await Promise.all(usedPhotos.map((p) => toSafeDataURL(p).catch(() => '')));
  const loaded = await Promise.all(safeSources.map((src) => (src ? loadImage(src).catch(() => null) : null)));
  const imgs = loaded.filter((x): x is HTMLImageElement => !!x);
  if (!imgs.length) throw new Error('照片读取失败，请刷新页面重试');

  // 3. 动态排版：按照片数量挑空位、分单图/双图/便签
  const plan = buildLayout(style.slots, imgs.length, rand);
  const ordered = arrangePhotos(imgs, rand);
  let cursor = 0;
  plan.forEach((p, i) => {
    if (p.subs === 1 && cursor < ordered.length) {
      placePhoto(ctx, ordered[cursor++], p.slot, i);
    } else if (p.subs === 2 && cursor < ordered.length) {
      const pair = ordered.slice(cursor, cursor + 2);
      cursor += pair.length;
      if (pair.length === 2) {
        placeDoublePhoto(ctx, pair, p.slot, i);
      } else {
        placePhoto(ctx, pair[0], p.slot, i);
      }
    } else {
      drawNoteCard(ctx, p.slot, i, tint, rand);
    }
  });

  // 4. 少量手绘点缀（位置/数量随种子变化）
  drawDoodles(ctx, style.slots, tint, rand);

  // 5. 导出 JPG（体积更小，手机下载更快）
  return {
    dataURL: canvas.toDataURL('image/jpeg', 0.92),
    used: Math.min(cursor, ordered.length),
    seed: actualSeed,
  };
}

/** 触发下载 */
export function downloadCollage(dataURL: string, filename: string) {
  const a = document.createElement('a');
  a.href = dataURL;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
