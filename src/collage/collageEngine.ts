/**
 * 本地 Canvas 拼贴排版引擎（AI 不可用时的兜底方案）
 * ------------------------------------------------------------------
 * 纯前端实现，不依赖任何第三方库。给定若干图片 + 一套模板主题 + 标题，
 * 直接合成一张高清 PNG 拼贴图。不同模板通过「布局 + 纹理 + 装饰」组合出差异。
 *
 * 对外只暴露 renderCollage() 一个函数，返回 dataURL，可直接用于 <img> 或下载。
 */

import type { CollageTemplate, CollageTheme } from './templates';

/** 一张待排版的图片：已解码的 HTMLImageElement */
interface PlacedImage {
  img: HTMLImageElement;
}

/** 排版选项 */
export interface RenderOptions {
  /** 拼贴大标题 */
  title?: string;
  /** 副标题 / 日期 */
  subtitle?: string;
  /** 输出画布宽度（高度按比例自适应，默认 1080） */
  width?: number;
}

/** 从 File / dataURL / 远程 URL 加载为 HTMLImageElement */
export function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous'; // 远程图尝试带 CORS，失败会被下面的兜底捕获
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('图片加载失败'));
    img.src = src;
  });
}

/** 把 File 转成 dataURL（便于跨组件复用与缓存） */
export function fileToDataURL(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error('读取图片失败'));
    reader.readAsDataURL(file);
  });
}

/* ------------------------------------------------------------------ */
/* 纹理绘制工具                                                        */
/* ------------------------------------------------------------------ */

/** 确定性伪随机数：同一 seed 总是得到同样的抖动，保证重绘一致 */
function seeded(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

/** 绘制背景（支持渐变字符串） */
function paintBackground(ctx: CanvasRenderingContext2D, w: number, h: number, theme: CollageTheme) {
  ctx.fillStyle = theme.background || '#f4f1ec';
  ctx.fillRect(0, 0, w, h);
}

/** 在已有背景上叠加纹理 */
function paintTexture(ctx: CanvasRenderingContext2D, w: number, h: number, theme: CollageTheme) {
  const rnd = seeded(w * 7 + h * 13 + theme.tilt * 97);
  const t = theme.texture;
  if (t === 'none') return;

  ctx.save();
  if (t === 'grain' || t === 'paper' || t === 'newspaper') {
    // 细密颗粒 / 纸纹：叠加半透明噪点
    const dots = Math.round((w * h) / 900);
    for (let i = 0; i < dots; i++) {
      ctx.fillStyle = `rgba(60,50,40,${rnd() * 0.05})`;
      ctx.fillRect(rnd() * w, rnd() * h, 1.5, 1.5);
    }
  } else if (t === 'dot') {
    // 波普网点
    ctx.globalAlpha = 0.16;
    ctx.fillStyle = theme.accent;
    for (let y = 12; y < h; y += 26) {
      for (let x = 12; x < w; x += 26) {
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  } else if (t === 'grid') {
    // 手账方格
    ctx.globalAlpha = 0.12;
    ctx.strokeStyle = theme.accent;
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 0; y < h; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }
  } else if (t === 'calendar') {
    // 日历表格：横向日期行 + 竖向栏目线
    ctx.globalAlpha = 0.16;
    ctx.strokeStyle = theme.accent;
    ctx.lineWidth = 1.5;
    for (let y = 0; y < h; y += 90) {
      ctx.beginPath();
      ctx.moveTo(40, y);
      ctx.lineTo(w - 40, y);
      ctx.stroke();
    }
    for (let x = 40; x < w; x += 90) {
      ctx.beginPath();
      ctx.moveTo(x, 90);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    // 星期标题点
    ctx.globalAlpha = 0.28;
    ctx.fillStyle = theme.ink;
    ctx.font = '600 20px system-ui, sans-serif';
    ['一', '二', '三', '四', '五', '六', '日'].forEach((d, i) => {
      ctx.fillText(d, 56 + i * ((w - 110) / 7), 70);
    });
  } else if (t === 'glass') {
    // 磨砂玻璃：几块半透明磨砂矩形 + 冰蓝微光
    for (let i = 0; i < 5; i++) {
      const x = rnd() * w;
      const y = rnd() * h;
      const rw = 140 + rnd() * 260;
      const rh = 120 + rnd() * 260;
      ctx.fillStyle = 'rgba(255,255,255,.22)';
      roundRect(ctx, x, y, rw, rh, 26);
      ctx.fill();
      ctx.strokeStyle = 'rgba(120,180,225,.5)';
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  } else if (t === 'graffiti') {
    // 涂鸦线条：随机白色/黑色涂鸦笔触
    ctx.globalAlpha = 0.5;
    for (let i = 0; i < 14; i++) {
      const x = rnd() * w;
      const y = rnd() * h;
      ctx.strokeStyle = i % 2 ? 'rgba(0,0,0,.5)' : 'rgba(255,255,255,.9)';
      ctx.lineWidth = 3 + rnd() * 5;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.quadraticCurveTo(x + 30 - rnd() * 60, y - 40, x + 50 - rnd() * 100, y + 20);
      ctx.stroke();
    }
  }
  ctx.restore();
}

/** 画一个圆角矩形路径（兼容没有 roundRect API 的环境） */
function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  const rr = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.arcTo(x + w, y, x + w, y + h, rr);
  ctx.arcTo(x + w, y + h, x, y + h, rr);
  ctx.arcTo(x, y + h, x, y, rr);
  ctx.arcTo(x, y, x + w, y, rr);
  ctx.closePath();
}

/** 按 cover 方式把图片画进目标矩形（居中裁切，不变形） */
function drawCover(
  ctx: CanvasRenderingContext2D,
  img: HTMLImageElement,
  x: number,
  y: number,
  w: number,
  h: number,
  radius: number,
) {
  ctx.save();
  roundRect(ctx, x, y, w, h, radius);
  ctx.clip();
  const ir = img.naturalWidth / img.naturalHeight;
  const tr = w / h;
  let sw = img.naturalWidth;
  let sh = img.naturalHeight;
  if (ir > tr) sw = sh * tr;
  else sh = sw / tr;
  const sx = (img.naturalWidth - sw) / 2;
  const sy = (img.naturalHeight - sh) / 2;
  ctx.drawImage(img, sx, sy, sw, sh, x, y, w, h);
  ctx.restore();
}

/** 画带边框（白边 / 相纸边）和轻微倾斜的照片 */
function drawFramedPhoto(
  ctx: CanvasRenderingContext2D,
  img: HTMLImageElement,
  cx: number,
  cy: number,
  w: number,
  h: number,
  theme: CollageTheme,
  tiltDeg: number,
) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate((tiltDeg * Math.PI) / 180);
  const totalW = w + theme.border * 2;
  const totalH = h + theme.border * 2;
  // 阴影
  ctx.shadowColor = 'rgba(0,0,0,.18)';
  ctx.shadowBlur = 18;
  ctx.shadowOffsetY = 8;
  // 相纸底
  ctx.fillStyle = theme.paper;
  roundRect(ctx, -totalW / 2, -totalH / 2, totalW, totalH, theme.radius + 2);
  ctx.fill();
  ctx.shadowColor = 'transparent';
  // 照片本体
  drawCover(ctx, img, -w / 2, -h / 2, w, h, Math.max(0, theme.radius - 2));
  ctx.restore();
}

/** 画装饰元素（胶带 / 爱心 / 圆点 / 涂鸦角标），按主题类型变化 */
function drawDeco(ctx: CanvasRenderingContext2D, x: number, y: number, angle: number, theme: CollageTheme, seed: number) {
  if (!theme.deco) return;
  const rnd = seeded(seed);
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate((angle * Math.PI) / 180);
  const t = theme.texture;

  if (t === 'paper' || t === 'newspaper') {
    // 和纸胶带
    ctx.fillStyle =
      t === 'newspaper' ? 'rgba(184,85,47,.55)' : 'rgba(180,140,90,.5)';
    ctx.fillRect(-42, -11, 84, 22);
    ctx.globalAlpha = 0.3;
    ctx.fillStyle = '#fff';
    for (let i = -38; i < 42; i += 8) ctx.fillRect(i, -11, 2, 22);
  } else if (t === 'dot') {
    // 小爱心
    ctx.fillStyle = theme.accent;
    ctx.font = '30px system-ui';
    ctx.fillText('♥', -14, 10);
    ctx.beginPath();
    ctx.arc(30, -8, 5, 0, Math.PI * 2);
    ctx.fill();
  } else if (t === 'glass') {
    // 微光圆点
    ctx.strokeStyle = 'rgba(90,160,215,.7)';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(0, 0, 16, 0, Math.PI * 2);
    ctx.stroke();
  } else if (t === 'graffiti') {
    // 涂鸦星芒
    ctx.strokeStyle = theme.accent;
    ctx.lineWidth = 4;
    ctx.beginPath();
    for (let i = 0; i < 4; i++) {
      const a = (i * Math.PI) / 2;
      ctx.moveTo(Math.cos(a) * 6, Math.sin(a) * 6);
      ctx.lineTo(Math.cos(a) * 24, Math.sin(a) * 24);
    }
    ctx.stroke();
  } else if (t === 'calendar' || t === 'grid') {
    // 便签贴角
    ctx.fillStyle = t === 'calendar' ? 'rgba(192,138,90,.85)' : 'rgba(201,138,160,.85)';
    ctx.beginPath();
    ctx.moveTo(-22, -12);
    ctx.lineTo(22, -12);
    ctx.lineTo(22, 12);
    ctx.lineTo(0, 26);
    ctx.lineTo(-22, 12);
    ctx.closePath();
    ctx.fill();
  } else {
    // 默认小圆点
    ctx.fillStyle = theme.accent;
    ctx.globalAlpha = 0.7;
    ctx.beginPath();
    ctx.arc(0, 0, 8 + rnd() * 6, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

/** 画标题与副标题 */
function paintTitles(
  ctx: CanvasRenderingContext2D,
  w: number,
  top: number,
  theme: CollageTheme,
  title?: string,
  subtitle?: string,
) {
  if (!title && !subtitle) return;
  ctx.save();
  ctx.textAlign = 'left';
  if (title) {
    ctx.fillStyle = theme.ink;
    ctx.font = `800 ${Math.round(w * 0.052)}px system-ui, sans-serif`;
    ctx.fillText(title, 64, top);
  }
  if (subtitle) {
    ctx.fillStyle = theme.accent;
    ctx.font = `500 ${Math.round(w * 0.021)}px system-ui, sans-serif`;
    ctx.fillText(subtitle, 66, top + Math.round(w * 0.038));
  }
  // 标题下方装饰短线
  ctx.strokeStyle = theme.accent;
  ctx.lineWidth = 5;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(64, top + Math.round(w * 0.055));
  ctx.lineTo(64 + Math.round(w * 0.09), top + Math.round(w * 0.055));
  ctx.stroke();
  ctx.restore();
}

/* ------------------------------------------------------------------ */
/* 布局：不同模板使用不同的图片排布算法                                */
/* ------------------------------------------------------------------ */

type LayoutFn = (
  ctx: CanvasRenderingContext2D,
  imgs: PlacedImage[],
  w: number,
  h: number,
  theme: CollageTheme,
) => void;

/** 错落拼贴（手账 / 胶片 / 复古 / 涂鸦通用，靠 tilt 与 deco 区分） */
const layoutScatter: LayoutFn = (ctx, imgs, w, h, theme) => {
  const rnd = seeded(imgs.length * 31 + theme.tilt * 17);
  const n = imgs.length;
  const gap = 26;
  const cols = n <= 1 ? 1 : n <= 4 ? 2 : 3;
  const rows = Math.ceil(n / cols);
  const areaTop = h * 0.16;
  const areaH = h - areaTop - 90;
  const cellW = (w - 120 - gap * (cols - 1)) / cols;
  const cellH = (areaH - gap * (rows - 1)) / rows;
  imgs.forEach((item, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const baseX = 60 + col * (cellW + gap) + cellW / 2;
    const baseY = areaTop + row * (cellH + gap) + cellH / 2;
    const tilt = theme.tilt ? (rnd() - 0.5) * 2 * theme.tilt : 0;
    const pw = cellW * (0.86 + rnd() * 0.1);
    const ph = cellH * (0.84 + rnd() * 0.1);
    drawFramedPhoto(ctx, item.img, baseX, baseY, pw, ph, theme, tilt);
    if (theme.deco && i % 2 === 0) {
      drawDeco(ctx, baseX - pw / 2 + 10, baseY - ph / 2 - 6, tilt - 18, theme, i + 1);
    }
  });
};

/** INS 留白：超大留白、不对称错落、圆角细白边 */
const layoutMinimal: LayoutFn = (ctx, imgs, w, h, theme) => {
  const rnd = seeded(imgs.length * 53 + 7);
  const n = imgs.length;
  // 一大两小错落构图
  const spots =
    n === 1
      ? [[w * 0.5, h * 0.52, w * 0.5, h * 0.5]]
      : [
          [w * 0.4, h * 0.46, w * 0.42, h * 0.44],
          [w * 0.74, h * 0.3, w * 0.26, h * 0.24],
          [w * 0.72, h * 0.68, w * 0.3, h * 0.28],
        ];
  imgs.slice(0, 3).forEach((item, i) => {
    const [cx, cy, pw, ph] = spots[Math.min(i, spots.length - 1)] as number[];
    drawFramedPhoto(ctx, item.img, cx, cy, pw, ph, theme, (rnd() - 0.5) * 4);
  });
};

/** 时间轴：竖向轴线 + 左右交替照片 */
const layoutTimeline: LayoutFn = (ctx, imgs, w, h, theme) => {
  const axisX = w / 2;
  ctx.save();
  ctx.strokeStyle = theme.accent;
  ctx.lineWidth = 3;
  ctx.setLineDash([10, 10]);
  ctx.beginPath();
  ctx.moveTo(axisX, h * 0.14);
  ctx.lineTo(axisX, h - 70);
  ctx.stroke();
  ctx.restore();
  const top = h * 0.16;
  const usable = h - top - 80;
  const step = usable / Math.max(1, imgs.length);
  imgs.forEach((item, i) => {
    const left = i % 2 === 0;
    const cy = top + step * (i + 0.5);
    const pw = Math.min(w * 0.32, step * 1.5);
    const ph = Math.min(step * 0.78, 210);
    const cx = left ? axisX - 70 - pw / 2 : axisX + 70 + pw / 2;
    // 节点
    ctx.fillStyle = theme.accent;
    ctx.beginPath();
    ctx.arc(axisX, cy, 9, 0, Math.PI * 2);
    ctx.fill();
    drawFramedPhoto(ctx, item.img, cx, cy, pw, ph, theme, left ? -3 : 3);
    if (theme.deco) drawDeco(ctx, cx, cy - ph / 2 - 8, 0, theme, i + 5);
  });
};

/** 波普海报：大色块 + 粗黑边 + 大字 */
const layoutPop: LayoutFn = (ctx, imgs, w, h, theme) => {
  const rnd = seeded(imgs.length * 71 + 3);
  const n = Math.min(imgs.length, 6);
  const cols = 3;
  const rows = Math.max(1, Math.ceil(n / cols));
  const gap = 18;
  const areaTop = h * 0.2;
  const cellW = (w - 120 - gap * (cols - 1)) / cols;
  const cellH = (h - areaTop - 90 - gap * (rows - 1)) / rows;
  imgs.slice(0, n).forEach((item, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const x = 60 + col * (cellW + gap);
    const y = areaTop + row * (cellH + gap);
    ctx.save();
    ctx.strokeStyle = '#111';
    ctx.lineWidth = 7;
    ctx.fillStyle = i % 2 ? '#ff5a3c' : '#2f6df0';
    roundRect(ctx, x, y, cellW, cellH, 0);
    ctx.fill();
    ctx.stroke();
    ctx.restore();
    drawCover(ctx, item.img, x + 10, y + 10, cellW - 20, cellH - 20, 0);
    ctx.save();
    ctx.strokeStyle = '#111';
    ctx.lineWidth = 7;
    ctx.strokeRect(x + 10, y + 10, cellW - 20, cellH - 20);
    ctx.restore();
    if (rnd() > 0.5 && theme.deco) drawDeco(ctx, x + cellW - 16, y + 18, (rnd() - 0.5) * 30, theme, i);
  });
};

/** 日历归档：网格小照片 + 便签数字 */
const layoutCalendar: LayoutFn = (ctx, imgs, w, h, theme) => {
  const n = Math.min(imgs.length, 8);
  const cols = 4;
  const rows = Math.max(1, Math.ceil(n / cols));
  const gap = 20;
  const areaTop = h * 0.15;
  const cellW = (w - 120 - gap * (cols - 1)) / cols;
  const cellH = (h - areaTop - 80 - gap * (rows - 1)) / rows;
  imgs.slice(0, n).forEach((item, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const x = 60 + col * (cellW + gap);
    const y = areaTop + row * (cellH + gap);
    drawFramedPhoto(ctx, item.img, x + cellW / 2, y + cellH / 2, cellW - 8, cellH - 8, theme, (i % 2 ? 1 : -1) * 2);
    // 日期角标
    ctx.save();
    ctx.fillStyle = theme.accent;
    ctx.fillRect(x + cellW - 46, y, 46, 34);
    ctx.fillStyle = '#fff';
    ctx.font = '700 20px system-ui';
    ctx.textAlign = 'center';
    ctx.fillText(String(i + 1).padStart(2, '0'), x + cellW - 23, y + 24);
    ctx.restore();
  });
};

/** 根据模板 id 选择布局函数 */
function pickLayout(id: string): LayoutFn {
  switch (id) {
    case 'ins-minimal':
    case 'macaron-cream':
      return layoutMinimal;
    case 'four-seasons':
    case 'japanese-film':
      return layoutTimeline;
    case 'pop-art':
      return layoutPop;
    case 'calendar-diary':
      return layoutCalendar;
    case 'frosted-tech':
      return layoutScatter; // 磨砂科技用规整错落（tilt=0）
    default:
      return layoutScatter; // 手账 / 复古 / 涂鸦 / 文艺
  }
}

/* ------------------------------------------------------------------ */
/* 对外主函数                                                          */
/* ------------------------------------------------------------------ */

/**
 * 把多张图片按模板合成一张拼贴图。
 * @param sources 图片来源（dataURL 或可访问的 URL）
 * @param template 模板定义
 * @param options 标题 / 副标题 / 宽度
 * @returns PNG dataURL
 */
export async function renderCollage(
  sources: string[],
  template: CollageTemplate,
  options: RenderOptions = {},
): Promise<string> {
  if (!sources.length) throw new Error('请至少选择一张图片');

  // 并行加载所有图片；失败的单张跳过，保证健壮
  const loaded = await Promise.all(
    sources.map((src) => loadImage(src).catch(() => null)),
  );
  const imgs: PlacedImage[] = loaded.filter((x): x is HTMLImageElement => !!x).map((img) => ({ img }));
  if (!imgs.length) throw new Error('所有图片都无法读取，请更换图片重试');

  const w = options.width || 1080;
  const ratio = Math.min(Math.max(w / 1080, 0.8), 2);
  // 根据图片数量决定画布高度：图越多画布越高，保证排版不拥挤
  const rows = Math.ceil(imgs.length / (imgs.length <= 4 ? 2 : 3));
  const h = Math.round((720 + Math.max(0, rows - 1) * 300) * ratio);

  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('当前浏览器不支持 Canvas');

  paintBackground(ctx, w, h, template.theme);
  paintTexture(ctx, w, h, template.theme);
  paintTitles(ctx, w, Math.round(120 * ratio), template.theme, options.title, options.subtitle);
  pickLayout(template.id)(ctx, imgs, w, h, template.theme);

  // 右下角落款
  ctx.save();
  ctx.fillStyle = template.theme.ink;
  ctx.globalAlpha = 0.55;
  ctx.font = `600 ${Math.round(18 * ratio)}px system-ui, sans-serif`;
  ctx.textAlign = 'right';
  ctx.fillText('resonance · 生活拼贴', w - 40, h - 34);
  ctx.restore();

  return canvas.toDataURL('image/png');
}

/** 把 dataURL 触发浏览器下载 */
export function downloadDataURL(dataURL: string, filename: string) {
  const a = document.createElement('a');
  a.href = dataURL;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
