/**
 * 本地 Canvas 拼贴排版引擎（第二版，AI 不可用时的兜底方案）
 * ==================================================================
 * 纯前端实现，不依赖任何第三方库。按 9:16 竖屏输出，严格按照用户给定的
 * 2/3/4/5 张照片布局规则排布，并为 13 套风格分别绘制背景纹理与装饰。
 *
 * 布局规则（用户原话）：
 *  · 2 张：画面下半部分左右并排，间距均匀，可适度旋转
 *  · 3 张：上侧靠左 / 中间靠右 / 底部靠左，错落留白，可旋转
 *  · 4 张：标准 2×2（左上/右上/左下/右下），间距均匀，可旋转
 *  · 5 张：左侧上中下 3 张 + 右侧上下叠放 2 张，可旋转
 *
 * 对外只暴露 renderCollage()：给定图片 dataURL + 模板 + 布局张数，返回 PNG dataURL。
 */

import type { CollageTemplate, CollageTheme } from './templates';

interface PlacedImage { img: HTMLImageElement }

export interface RenderOptions {
  title?: string;
  subtitle?: string;
  /** 输出宽度，默认 900（高度按 9:16 自动计算为 1600） */
  width?: number;
}

/** 加载图片（远程图带 CORS；本地 dataURL 无影响） */
export function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('图片加载失败'));
    img.src = src;
  });
}

/** File 转 dataURL */
export function fileToDataURL(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error('读取图片失败'));
    reader.readAsDataURL(file);
  });
}

/* ---------------------- 通用绘制工具 ---------------------- */

function seeded(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

/** 圆角矩形路径（兼容无 roundRect API 的环境） */
function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  const rr = Math.max(0, Math.min(r, w / 2, h / 2));
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.arcTo(x + w, y, x + w, y + h, rr);
  ctx.arcTo(x + w, y + h, x, y + h, rr);
  ctx.arcTo(x, y + h, x, y, rr);
  ctx.arcTo(x, y, x + w, y, rr);
  ctx.closePath();
}

/** 背景（支持渐变字符串） */
function paintBackground(ctx: CanvasRenderingContext2D, w: number, h: number, theme: CollageTheme) {
  ctx.fillStyle = theme.background || '#f2efe9';
  ctx.fillRect(0, 0, w, h);
}

/** 背景纹理 */
function paintTexture(ctx: CanvasRenderingContext2D, w: number, h: number, theme: CollageTheme) {
  const rnd = seeded(w * 3 + h * 7 + theme.tilt * 101);
  const t = theme.texture;
  if (t === 'none') return;
  ctx.save();
  if (t === 'grain' || t === 'paper' || t === 'newspaper' || t === 'silk') {
    // 细密颗粒 / 纸纹
    const dots = Math.round((w * h) / 700);
    for (let i = 0; i < dots; i++) {
      ctx.fillStyle = `rgba(70,58,44,${rnd() * 0.05})`;
      ctx.fillRect(rnd() * w, rnd() * h, 1.5, 1.5);
    }
    if (t === 'silk') {
      // 布纹：横向细线
      ctx.globalAlpha = 0.05;
      ctx.strokeStyle = theme.accent;
      for (let y = 0; y < h; y += 4) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
      }
    }
  } else if (t === 'dot') {
    // 波普网点
    ctx.globalAlpha = 0.18;
    ctx.fillStyle = theme.accent;
    for (let y = 14; y < h; y += 28) {
      for (let x = 14; x < w; x += 28) {
        ctx.beginPath(); ctx.arc(x, y, 3.5, 0, Math.PI * 2); ctx.fill();
      }
    }
  } else if (t === 'grid') {
    // 手账方格
    ctx.globalAlpha = 0.13;
    ctx.strokeStyle = theme.accent;
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 44) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
    for (let y = 0; y < h; y += 44) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
  } else if (t === 'calendar') {
    // 日历：方格 + 星期标题
    ctx.globalAlpha = 0.15;
    ctx.strokeStyle = theme.accent;
    ctx.lineWidth = 1.5;
    for (let y = 0; y < h; y += 100) { ctx.beginPath(); ctx.moveTo(30, y); ctx.lineTo(w - 30, y); ctx.stroke(); }
    for (let x = 30; x < w; x += 100) { ctx.beginPath(); ctx.moveTo(x, 100); ctx.lineTo(x, h); ctx.stroke(); }
    ctx.globalAlpha = 0.32;
    ctx.fillStyle = theme.ink;
    ctx.font = '600 22px system-ui, sans-serif';
    ['一', '二', '三', '四', '五', '六', '日'].forEach((d, i) => ctx.fillText(d, 46 + i * ((w - 92) / 7), 78));
  } else if (t === 'glass') {
    // 磨砂玻璃块 + 微光边
    for (let i = 0; i < 6; i++) {
      const x = rnd() * w, y = rnd() * h;
      const rw = 150 + rnd() * 260, rh = 140 + rnd() * 300;
      ctx.fillStyle = 'rgba(255,255,255,.2)';
      roundRect(ctx, x, y, rw, rh, 30); ctx.fill();
      ctx.strokeStyle = 'rgba(120,180,225,.5)'; ctx.lineWidth = 2; ctx.stroke();
    }
    // 柔和圆环
    ctx.strokeStyle = 'rgba(140,195,230,.35)'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(w * 0.5, h * 0.2, w * 0.32, 0, Math.PI * 2); ctx.stroke();
  } else if (t === 'graffiti') {
    // 克制的涂鸦线条
    ctx.globalAlpha = 0.45;
    for (let i = 0; i < 12; i++) {
      const x = rnd() * w, y = rnd() * h;
      ctx.strokeStyle = i % 2 ? 'rgba(0,0,0,.55)' : 'rgba(255,255,255,.9)';
      ctx.lineWidth = 3 + rnd() * 5;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.quadraticCurveTo(x + 30 - rnd() * 60, y - 45, x + 55 - rnd() * 110, y + 22);
      ctx.stroke();
    }
  }
  ctx.restore();
}

/** 按 cover 方式画进圆角矩形（居中裁切不变形，保留人脸不拉伸） */
function drawCover(
  ctx: CanvasRenderingContext2D, img: HTMLImageElement,
  x: number, y: number, w: number, h: number, radius: number,
) {
  ctx.save();
  roundRect(ctx, x, y, w, h, radius);
  ctx.clip();
  const ir = img.naturalWidth / img.naturalHeight;
  const tr = w / h;
  let sw = img.naturalWidth, sh = img.naturalHeight;
  if (ir > tr) sw = sh * tr; else sh = sw / tr;
  ctx.drawImage(img, (img.naturalWidth - sw) / 2, (img.naturalHeight - sh) / 2, sw, sh, x, y, w, h);
  ctx.restore();
}

/** 画带相纸边、阴影、轻微旋转的照片 */
function drawFramedPhoto(
  ctx: CanvasRenderingContext2D, img: HTMLImageElement,
  cx: number, cy: number, w: number, h: number, theme: CollageTheme, tiltDeg: number,
) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate((tiltDeg * Math.PI) / 180);
  const tw = w + theme.border * 2, th = h + theme.border * 2;
  // 阴影
  ctx.shadowColor = 'rgba(0,0,0,.16)'; ctx.shadowBlur = 20; ctx.shadowOffsetY = 9;
  ctx.fillStyle = theme.paper;
  roundRect(ctx, -tw / 2, -th / 2, tw, th, theme.radius + 2); ctx.fill();
  ctx.shadowColor = 'transparent';
  // 照片
  drawCover(ctx, img, -w / 2, -h / 2, w, h, Math.max(0, theme.radius - 2));
  // 细描边（INS/留白风格）
  if (theme.texture === 'grain' && !theme.deco) {
    ctx.strokeStyle = 'rgba(255,255,255,.85)'; ctx.lineWidth = 2;
    roundRect(ctx, -w / 2, -h / 2, w, h, Math.max(0, theme.radius - 2)); ctx.stroke();
  }
  ctx.restore();
}

/** 装饰元素：和纸胶带 / 爱心 / 微光 / 涂鸦星芒 / 便签 */
function drawDeco(ctx: CanvasRenderingContext2D, x: number, y: number, angle: number, theme: CollageTheme, seed: number) {
  if (!theme.deco) return;
  const rnd = seeded(seed);
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate((angle * Math.PI) / 180);
  const t = theme.texture;
  if (t === 'paper' || t === 'newspaper') {
    ctx.fillStyle = t === 'newspaper' ? 'rgba(184,85,47,.5)' : 'rgba(180,140,90,.48)';
    ctx.fillRect(-38, -10, 76, 20);
    ctx.globalAlpha = 0.28; ctx.fillStyle = '#fff';
    for (let i = -34; i < 38; i += 8) ctx.fillRect(i, -10, 2, 20);
  } else if (t === 'dot') {
    ctx.fillStyle = theme.accent;
    ctx.font = '26px system-ui'; ctx.fillText('♥', -12, 8);
    ctx.beginPath(); ctx.arc(26, -6, 5, 0, Math.PI * 2); ctx.fill();
  } else if (t === 'glass') {
    ctx.strokeStyle = 'rgba(90,160,215,.7)'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(0, 0, 15, 0, Math.PI * 2); ctx.stroke();
  } else if (t === 'graffiti') {
    ctx.strokeStyle = theme.accent; ctx.lineWidth = 4;
    ctx.beginPath();
    for (let i = 0; i < 4; i++) {
      const a = (i * Math.PI) / 2;
      ctx.moveTo(Math.cos(a) * 6, Math.sin(a) * 6);
      ctx.lineTo(Math.cos(a) * 22, Math.sin(a) * 22);
    }
    ctx.stroke();
  } else if (t === 'calendar' || t === 'grid') {
    ctx.fillStyle = t === 'calendar' ? 'rgba(192,138,90,.85)' : 'rgba(111,168,124,.85)';
    ctx.beginPath();
    ctx.moveTo(-20, -10); ctx.lineTo(20, -10); ctx.lineTo(20, 10);
    ctx.lineTo(0, 24); ctx.lineTo(-20, 10); ctx.closePath(); ctx.fill();
  } else {
    ctx.fillStyle = theme.accent; ctx.globalAlpha = 0.65;
    ctx.beginPath(); ctx.arc(0, 0, 7 + rnd() * 5, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}

/** 标题区 */
function paintTitles(ctx: CanvasRenderingContext2D, w: number, theme: CollageTheme, title?: string, subtitle?: string) {
  if (!title && !subtitle) return;
  ctx.save();
  ctx.textAlign = 'center';
  if (title) {
    ctx.fillStyle = theme.ink;
    ctx.font = `800 ${Math.round(w * 0.066)}px system-ui, sans-serif`;
    ctx.fillText(title, w / 2, 118);
  }
  if (subtitle) {
    ctx.fillStyle = theme.accent;
    ctx.font = `500 ${Math.round(w * 0.026)}px system-ui, sans-serif`;
    ctx.fillText(subtitle, w / 2, 158);
  }
  ctx.strokeStyle = theme.accent; ctx.lineWidth = 4; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(w / 2 - 45, 180); ctx.lineTo(w / 2 + 45, 180); ctx.stroke();
  ctx.restore();
}

/* ---------------------- 照片数量布局（核心） ---------------------- */

type LayoutFn = (ctx: CanvasRenderingContext2D, imgs: PlacedImage[], w: number, h: number, theme: CollageTheme) => void;

/** 2 张：画面下半部分左右并排，间距均匀，可适度旋转 */
const layout2: LayoutFn = (ctx, imgs, w, h, theme) => {
  const top = h * 0.5;                 // 下半部分
  const gap = w * 0.06;
  const pw = (w - gap * 3) / 2;
  const ph = pw * 1.18;
  const cy = top + (h - top) * 0.48;
  const tilt = theme.tilt ? theme.tilt * 0.35 : 0;
  drawFramedPhoto(ctx, imgs[0].img, gap + pw / 2, cy, pw, ph, theme, -tilt);
  if (imgs[1]) drawFramedPhoto(ctx, imgs[1].img, gap * 2 + pw + pw / 2, cy, pw, ph, theme, tilt);
};

/** 3 张：上侧靠左 / 中间靠右 / 底部靠左，错落留白 */
const layout3: LayoutFn = (ctx, imgs, w, h, theme) => {
  const pw = w * 0.46, ph = pw * 1.15;
  const spots: Array<[number, number, number]> = [
    [w * 0.31, h * 0.34, -theme.tilt * 0.4],   // 上侧靠左
    [w * 0.69, h * 0.55, theme.tilt * 0.4],    // 中间靠右
    [w * 0.34, h * 0.80, -theme.tilt * 0.25],  // 底部靠左
  ];
  imgs.slice(0, 3).forEach((item, i) => {
    const [cx, cy, tilt] = spots[i];
    drawFramedPhoto(ctx, item.img, cx, cy, pw, ph, theme, tilt);
    if (theme.deco && i === 1) drawDeco(ctx, cx + pw * 0.45, cy - ph * 0.42, tilt - 15, theme, i + 3);
  });
};

/** 4 张：标准 2×2，间距均匀，可适度旋转 */
const layout4: LayoutFn = (ctx, imgs, w, h, theme) => {
  const gapX = w * 0.07, gapY = w * 0.06;
  const pw = (w - gapX * 3) / 2;
  const ph = pw * 1.12;
  const top = h * 0.23;
  const positions: Array<[number, number, number]> = [
    [gapX + pw / 2, top + ph / 2, -theme.tilt * 0.3],               // 左上
    [gapX * 2 + pw + pw / 2, top + ph / 2, theme.tilt * 0.3],       // 右上
    [gapX + pw / 2, top + ph + gapY + ph / 2, theme.tilt * 0.3],    // 左下
    [gapX * 2 + pw + pw / 2, top + ph + gapY + ph / 2, -theme.tilt * 0.3], // 右下
  ];
  imgs.slice(0, 4).forEach((item, i) => {
    const [cx, cy, tilt] = positions[i];
    drawFramedPhoto(ctx, item.img, cx, cy, pw, ph, theme, tilt);
  });
};

/** 5 张：左上 / 中间左 / 底部左 三张纵向 + 中间右侧上下叠放两张 */
const layout5: LayoutFn = (ctx, imgs, w, h, theme) => {
  const gap = w * 0.05;
  const leftW = (w - gap * 3) * 0.55;
  const rightW = w - gap * 3 - leftW;
  const leftH = leftW * 1.05;
  const rightH = (h - h * 0.24 - 60 - gap) / 2;
  const top = h * 0.24;
  const leftX = gap + leftW / 2;
  const rightX = gap * 2 + leftW + rightW / 2;
  const leftYs = [top + leftH / 2, top + gap + leftH + leftH / 2, top + gap * 2 + leftH * 2 + leftH / 2];
  const leftItems = imgs.slice(0, 3);
  const rightItems = imgs.slice(3, 5);
  leftItems.forEach((item, i) => {
    drawFramedPhoto(ctx, item.img, leftX, leftYs[i], leftW, leftH, theme, (i % 2 ? 1 : -1) * theme.tilt * 0.3);
  });
  rightItems.forEach((item, i) => {
    const cy = top + i * (rightH + gap) + rightH / 2;
    drawFramedPhoto(ctx, item.img, rightX, cy, rightW, rightH, theme, (i % 2 ? -1 : 1) * theme.tilt * 0.3);
  });
};

/** 按图片数量选布局；超过 5 张时循环取前 5 张（保证布局可控、人脸不融合） */
function layoutForCount(count: number): LayoutFn {
  switch (count) {
    case 2: return layout2;
    case 3: return layout3;
    case 4: return layout4;
    case 5: return layout5;
    default: return layout4;
  }
}

/* ---------------------- 对外主函数 ---------------------- */

/**
 * 把多张图片按模板 + 布局合成 9:16 竖屏拼贴图。
 * @param sources 图片 dataURL 或可访问 URL
 * @param template 模板定义（含主题）
 * @param options 标题/副标题/宽度；内部按图片张数自动选布局
 * @returns PNG dataURL
 */
export async function renderCollage(
  sources: string[],
  template: CollageTemplate,
  options: RenderOptions = {},
): Promise<string> {
  if (!sources.length) throw new Error('请至少选择一张图片');
  // 只取前 5 张：布局规则覆盖 2~5 张，避免人多导致人脸融合
  const limited = sources.slice(0, 5);

  const loaded = await Promise.all(limited.map((src) => loadImage(src).catch(() => null)));
  const imgs: PlacedImage[] = loaded.filter((x): x is HTMLImageElement => !!x).map((img) => ({ img }));
  if (!imgs.length) throw new Error('所有图片都无法读取，请更换图片重试');

  const w = options.width || 900;
  const h = Math.round(w * 16 / 9); // 9:16 竖屏
  const canvas = document.createElement('canvas');
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('当前浏览器不支持 Canvas');

  paintBackground(ctx, w, h, template.theme);
  paintTexture(ctx, w, h, template.theme);
  paintTitles(ctx, w, template.theme, options.title, options.subtitle);
  layoutForCount(imgs.length)(ctx, imgs, w, h, template.theme);

  // 右下角落款
  ctx.save();
  ctx.fillStyle = template.theme.ink; ctx.globalAlpha = 0.5;
  ctx.font = `600 ${Math.round(w * 0.02)}px system-ui, sans-serif`;
  ctx.textAlign = 'right';
  ctx.fillText('resonance · 生活拼贴', w - 30, h - 26);
  ctx.restore();

  return canvas.toDataURL('image/png');
}

/** 触发浏览器下载 */
export function downloadDataURL(dataURL: string, filename: string) {
  const a = document.createElement('a');
  a.href = dataURL; a.download = filename;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
}
