/**
 * 共同日记 · 视频合成引擎
 *
 * 纯浏览器端实现：Canvas 绘制 + MediaRecorder 录制，不依赖任何服务端或第三方库。
 * 输出：优先 MP4（H.264），浏览器不支持时退回 WebM；静音。
 */

export type ItemKind = 'image' | 'video';

export interface PlogItem {
  id: string;
  kind: ItemKind;
  src: string;
  caption?: string;
  /** 视频原始时长（秒），图片无需填写 */
  duration?: number;
  /** 视频截取的开始时间（秒），默认 0 */
  trimStart?: number;
}

export interface PlogGroup {
  key: string;
  name: string;
  items: PlogItem[];
}

export interface PlogOptions {
  groups: PlogGroup[];
  title: string;
  caption: string;
  /** 字体 CSS font-family 值 */
  fontCss: string;
  color: string;
}

export interface PlogResult {
  blob: Blob;
  mime: string;
  ext: string;
  duration: number;
}

export interface PlogTask {
  promise: Promise<PlogResult>;
  cancel: () => void;
}

/** 画布尺寸：竖向，长宽比 1:2（高度为长边） */
export const CANVAS_W = 960;
export const CANVAS_H = 1920;
/** 单个素材的展示时长（秒） */
export const SLOT_SECONDS = 2;

const PAD_X = 56;
const MEDIA_TOP = 200;
const MEDIA_BOTTOM = 1690;
const TITLE_BASE = 150;
const CAPTION_BASE = 1810;

export const FONTS = [
  { key: 'hei', label: '黑体', css: '"Microsoft YaHei","PingFang SC","Heiti SC","Noto Sans SC",sans-serif' },
  { key: 'kai', label: '楷体', css: '"STKaiti","KaiTi","楷体",serif' },
  { key: 'song', label: '宋体', css: '"Songti SC","SimSun","宋体",serif' },
  { key: 'round', label: '圆体', css: '"YouYuan","Yuanti SC","幼圆","PingFang SC",sans-serif' },
] as const;

export const COLORS = [
  { key: 'white', label: '白', value: '#ffffff' },
  { key: 'warm', label: '暖黄', value: '#ffd45c' },
  { key: 'coral', label: '珊瑚', value: '#ff8a65' },
  { key: 'mint', label: '薄荷', value: '#9fe3c8' },
  { key: 'lavender', label: '淡紫', value: '#c9b6ff' },
] as const;

type Rect = { x: number; y: number; w: number; h: number };

/** 归一化排版（0~1，相对素材区域）。竖向画幅，格子不重叠、不越界。 */
const LAYOUTS: Record<number, Rect[]> = {
  1: [{ x: 0.14, y: 0.05, w: 0.72, h: 0.9 }],
  2: [
    { x: 0.04, y: 0.08, w: 0.44, h: 0.84 },
    { x: 0.52, y: 0.08, w: 0.44, h: 0.84 },
  ],
  3: [
    { x: 0.02, y: 0.02, w: 0.62, h: 0.28 },
    { x: 0.36, y: 0.36, w: 0.62, h: 0.28 },
    { x: 0.02, y: 0.7, w: 0.62, h: 0.28 },
  ],
  4: [
    { x: 0.03, y: 0.03, w: 0.45, h: 0.45 },
    { x: 0.52, y: 0.03, w: 0.45, h: 0.45 },
    { x: 0.03, y: 0.52, w: 0.45, h: 0.45 },
    { x: 0.52, y: 0.52, w: 0.45, h: 0.45 },
  ],
  5: [
    { x: 0.03, y: 0.02, w: 0.42, h: 0.28 },
    { x: 0.03, y: 0.36, w: 0.42, h: 0.28 },
    { x: 0.03, y: 0.7, w: 0.42, h: 0.28 },
    { x: 0.54, y: 0.14, w: 0.42, h: 0.28 },
    { x: 0.54, y: 0.56, w: 0.42, h: 0.28 },
  ],
};

/** 素材区域（像素）。标题与文案各自占用独立色带，素材不会压到文字上。 */
export function mediaArea(): Rect {
  return { x: PAD_X, y: MEDIA_TOP, w: CANVAS_W - PAD_X * 2, h: MEDIA_BOTTOM - MEDIA_TOP };
}

/** 根据人数计算每个素材格子的像素位置 */
export function cellRects(count: number): Rect[] {
  const area = mediaArea();
  const n = Math.max(1, Math.min(count, 12));
  const norm = LAYOUTS[n];
  if (norm) {
    return norm.map((r) => ({
      x: area.x + r.x * area.w,
      y: area.y + r.y * area.h,
      w: r.w * area.w,
      h: r.h * area.h,
    }));
  }
  // 6 人及以上：等分网格
  const cols = n <= 6 ? 3 : n <= 9 ? 3 : 4;
  const rows = Math.ceil(n / cols);
  const gapX = area.w * 0.03;
  const gapY = area.h * 0.04;
  const cw = (area.w - gapX * (cols - 1)) / cols;
  const ch = (area.h - gapY * (rows - 1)) / rows;
  const out: Rect[] = [];
  for (let i = 0; i < n; i += 1) {
    const r = Math.floor(i / cols);
    const c = i % cols;
    out.push({ x: area.x + c * (cw + gapX), y: area.y + r * (ch + gapY), w: cw, h: ch });
  }
  return out;
}

/** 校验排版：格子不重叠、且都在素材区域内（用于自测） */
export function validateLayout(count: number): string[] {
  const problems: string[] = [];
  const rects = cellRects(count);
  const area = mediaArea();
  rects.forEach((r, i) => {
    if (r.x < area.x - 0.5 || r.y < area.y - 0.5 || r.x + r.w > area.x + area.w + 0.5 || r.y + r.h > area.y + area.h + 0.5) {
      problems.push(`格子 ${i + 1} 超出素材区域`);
    }
  });
  for (let i = 0; i < rects.length; i += 1) {
    for (let j = i + 1; j < rects.length; j += 1) {
      const a = rects[i];
      const b = rects[j];
      const overlap = a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
      if (overlap) problems.push(`格子 ${i + 1} 与 ${j + 1} 重叠`);
    }
  }
  return problems;
}

/** 读取视频真实时长（秒） */
export function probeDuration(src: string): Promise<number> {
  return new Promise((resolve, reject) => {
    const v = document.createElement('video');
    v.preload = 'metadata';
    v.muted = true;
    v.src = src;
    const done = (value: number) => {
      v.removeAttribute('src');
      v.load();
      resolve(value);
    };
    v.onloadedmetadata = () => {
      if (Number.isFinite(v.duration) && v.duration > 0) done(v.duration);
      else reject(new Error('无法读取视频时长'));
    };
    v.onerror = () => reject(new Error('无法读取视频'));
  });
}

/** 总时长：以素材最多的那个人为准 */
export function totalSeconds(groups: PlogGroup[]): number {
  const max = groups.reduce((m, g) => Math.max(m, g.items.length), 0);
  return max * SLOT_SECONDS;
}

function fitContain(sw: number, sh: number, dw: number, dh: number) {
  if (!sw || !sh) return { w: dw, h: dh };
  const scale = Math.min(dw / sw, dh / sh);
  return { w: sw * scale, h: sh * scale };
}

function ellipsize(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string {
  if (ctx.measureText(text).width <= maxWidth) return text;
  const chars = [...text];
  while (chars.length > 1) {
    chars.pop();
    const candidate = `${chars.join('')}…`;
    if (ctx.measureText(candidate).width <= maxWidth) return candidate;
  }
  return '…';
}

/** 按宽度折行，最多 maxLines 行 */
function wrapLines(ctx: CanvasRenderingContext2D, text: string, maxWidth: number, maxLines: number): string[] {
  const chars = [...text.replace(/\s+/g, ' ').trim()];
  if (!chars.length) return [];
  const lines: string[] = [];
  let line = '';
  for (let i = 0; i < chars.length; i += 1) {
    const next = line + chars[i];
    if (ctx.measureText(next).width > maxWidth && line) {
      lines.push(line);
      line = chars[i];
      if (lines.length === maxLines) break;
    } else {
      line = next;
    }
  }
  if (lines.length < maxLines && line) lines.push(line);
  if (lines.length === maxLines) {
    const rest = chars.slice(lines.join('').length).join('');
    if (rest) lines[maxLines - 1] = ellipsize(ctx, lines[maxLines - 1] + rest, maxWidth);
  }
  return lines;
}

function drawMedia(ctx: CanvasRenderingContext2D, el: HTMLImageElement | HTMLVideoElement, rect: Rect) {
  const sw = el instanceof HTMLVideoElement ? el.videoWidth : el.naturalWidth;
  const sh = el instanceof HTMLVideoElement ? el.videoHeight : el.naturalHeight;
  if (!sw || !sh) return;
  // 只做等比缩小，完整显示在格子内，绝不超出、不裁剪
  const size = fitContain(sw, sh, rect.w, rect.h);
  const dx = rect.x + (rect.w - size.w) / 2;
  const dy = rect.y + (rect.h - size.h) / 2;
  ctx.drawImage(el, dx, dy, size.w, size.h);
}

type MimeChoice = { mime: string; ext: string };

/** 优先 MP4（Windows / 手机相册兼容性最好），失败再退回 WebM */
const MIME_CANDIDATES: MimeChoice[] = [
  { mime: 'video/mp4;codecs=avc1.42E01E', ext: 'mp4' },
  { mime: 'video/mp4', ext: 'mp4' },
  { mime: 'video/webm;codecs=vp9', ext: 'webm' },
  { mime: 'video/webm;codecs=vp8', ext: 'webm' },
  { mime: 'video/webm', ext: 'webm' },
];

let cachedMime: MimeChoice | null = null;

/** 容器类型：去掉 codecs 参数，否则部分浏览器拒绝播放 blob */
export function baseMime(mime: string): string {
  return mime.split(';')[0];
}

/** 把一个 blob 交给 <video> 实测，能出画面才算有效 */
export function isPlayable(blob: Blob): Promise<boolean> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(blob);
    const v = document.createElement('video');
    let settled = false;
    const done = (ok: boolean) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      v.removeAttribute('src');
      v.load();
      URL.revokeObjectURL(url);
      resolve(ok);
    };
    const timer = setTimeout(() => done(false), 5000);
    v.muted = true;
    v.preload = 'auto';
    v.playsInline = true;
    v.onloadeddata = () => done(v.videoWidth > 0 && v.videoHeight > 0);
    v.onerror = () => done(false);
    v.src = url;
    v.load();
  });
}

/** 用 0.4 秒的空白画布试录，确认这个格式真的能产出可播放文件 */
async function probeMime(choice: MimeChoice): Promise<boolean> {
  if (typeof MediaRecorder === 'undefined' || !MediaRecorder.isTypeSupported(choice.mime)) return false;
  if (!('captureStream' in HTMLCanvasElement.prototype)) return false;
  const canvas = document.createElement('canvas');
  canvas.width = 64;
  canvas.height = 64;
  canvas.style.cssText = 'position:fixed;left:-9999px;top:0;width:2px;height:2px;opacity:0.01;pointer-events:none';
  document.body.appendChild(canvas);
  const ctx = canvas.getContext('2d');
  let rec: MediaRecorder | null = null;
  const holder: HTMLElement | null = canvas;
  try {
    if (!ctx) return false;
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, 64, 64);
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, 32, 32);
    rec = new MediaRecorder(canvas.captureStream(15), { mimeType: choice.mime });
    const chunks: BlobPart[] = [];
    rec.ondataavailable = (e) => {
      if (e.data.size) chunks.push(e.data);
    };
    const stopped = new Promise<void>((res) => {
      rec!.onstop = () => res();
    });
    rec.start(100);
    await new Promise((r) => setTimeout(r, 420));
    if (rec.state !== 'inactive') rec.stop();
    await stopped;
    if (!chunks.length) return false;
    return await isPlayable(new Blob(chunks, { type: baseMime(choice.mime) }));
  } catch {
    return false;
  } finally {
    if (rec && rec.state !== 'inactive') {
      try { rec.stop(); } catch { /* ignore */ }
    }
    holder?.remove();
  }
}

/** 选出真正可用的录制格式（结果缓存，避免每次生成都试录） */
export async function resolveMime(): Promise<MimeChoice> {
  if (cachedMime) return cachedMime;
  for (const choice of MIME_CANDIDATES) {
    if (await probeMime(choice)) {
      cachedMime = choice;
      return choice;
    }
  }
  cachedMime = { mime: 'video/webm', ext: 'webm' };
  return cachedMime;
}

/** 绘制单帧画面。标题、素材、文案各占独立色带，互不遮挡。 */
export function paintFrame(
  ctx: CanvasRenderingContext2D,
  opts: PlogOptions,
  groups: PlogGroup[],
  t: number,
  resolve: (item: PlogItem) => HTMLImageElement | HTMLVideoElement | undefined,
): void {
  ctx.fillStyle = '#000000';
  ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);

  // 标题（顶部居中）
  ctx.textAlign = 'center';
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = opts.color;
  const maxTextW = CANVAS_W - PAD_X * 2 - 24;
  let titleSize = 54;
  ctx.font = `700 ${titleSize}px ${opts.fontCss}`;
  let titleLines = wrapLines(ctx, opts.title, maxTextW, 2);
  if (titleLines.length > 1) {
    titleSize = 44;
    ctx.font = `700 ${titleSize}px ${opts.fontCss}`;
    titleLines = wrapLines(ctx, opts.title, maxTextW, 2);
  }
  const lineH = titleSize + 8;
  const firstBaseline = TITLE_BASE - (titleLines.length - 1) * lineH;
  titleLines.forEach((line, i) => {
    ctx.fillText(line, CANVAS_W / 2, firstBaseline + i * lineH);
  });

  // 素材
  const rects = cellRects(groups.length);
  groups.forEach((group, gi) => {
    const rect = rects[gi];
    const idx = Math.floor(t / SLOT_SECONDS) % group.items.length;
    const el = resolve(group.items[idx]);
    if (el) drawMedia(ctx, el, rect);
  });

  // 文案（右下角）
  ctx.textAlign = 'right';
  ctx.font = `400 38px ${opts.fontCss}`;
  ctx.fillStyle = opts.color;
  const captionText = ellipsize(ctx, opts.caption, maxTextW);
  if (captionText) ctx.fillText(captionText, CANVAS_W - PAD_X, CAPTION_BASE);
}

/** 开始合成。返回可取消的任务。 */
export function startPlogVideo(opts: PlogOptions, onProgress?: (ratio: number) => void): PlogTask {
  let cancelled = false;
  let cleanup = () => {};

  const promise = new Promise<PlogResult>((resolve, reject) => {
    const groups = opts.groups.filter((g) => g.items.length > 0);
    if (!groups.length) {
      reject(new Error('还没有可以制作的素材'));
      return;
    }

    const duration = totalSeconds(groups);
    const canvas = document.createElement('canvas');
    canvas.width = CANVAS_W;
    canvas.height = CANVAS_H;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      reject(new Error('浏览器不支持画布'));
      return;
    }
    // 画布必须挂到文档里，否则部分浏览器不会产生视频帧，导出的文件将无法播放
    canvas.setAttribute('aria-hidden', 'true');
    canvas.style.cssText = 'position:fixed;left:-9999px;top:0;width:2px;height:2px;opacity:0.01;pointer-events:none';
    document.body.appendChild(canvas);

    // 隐藏容器：视频元素需要挂载才能稳定解码
    const holder = document.createElement('div');
    holder.setAttribute('aria-hidden', 'true');
    holder.style.cssText = 'position:fixed;left:-9999px;top:0;width:2px;height:2px;overflow:hidden;opacity:0.01;pointer-events:none';
    document.body.appendChild(holder);

    const images = new Map<string, HTMLImageElement>();
    const videos = new Map<string, HTMLVideoElement>();
    const createdUrls: string[] = [];

    /**
     * 把素材转成同源地址。
     * 页面是 localhost、图片是 127.0.0.1 时属于跨源，画进画布会让画布"被污染"，
     * captureStream 会直接抛错，所以先 fetch 成 blob 再用同源 blob URL 绘制。
     */
    const toSameOrigin = async (src: string): Promise<string> => {
      if (!src) return src;
      let abs: URL;
      try {
        abs = new URL(src, location.href);
      } catch {
        return src;
      }
      if (abs.origin === location.origin) return abs.href;
      const res = await fetch(abs.href, { mode: 'cors', credentials: 'omit' });
      if (!res.ok) throw new Error(`素材加载失败（HTTP ${res.status}）`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      createdUrls.push(url);
      return url;
    };

    const loadImage = (src: string) =>
      new Promise<HTMLImageElement>((res, rej) => {
        void (async () => {
          try {
            const url = await toSameOrigin(src);
            const img = new Image();
            img.decoding = 'async';
            img.onload = () => res(img);
            img.onerror = () => rej(new Error('图片加载失败'));
            img.src = url;
          } catch (e) {
            rej(e);
          }
        })();
      });
    const loadVideo = (src: string) =>
      new Promise<HTMLVideoElement>((res, rej) => {
        void (async () => {
          try {
            const url = await toSameOrigin(src);
            const v = document.createElement('video');
            v.muted = true;
            v.playsInline = true;
            v.preload = 'auto';
            v.src = url;
            const ok = () => res(v);
            v.onloadeddata = ok;
            v.oncanplay = ok;
            v.onerror = () => rej(new Error('视频加载失败'));
            holder.appendChild(v);
            v.load();
          } catch (e) {
            rej(e);
          }
        })();
      });

    const rafRef = { id: 0 };
    let recorder: MediaRecorder | null = null;
    let stream: MediaStream | null = null;

    cleanup = () => {
      cancelAnimationFrame(rafRef.id);
      if (recorder && recorder.state !== 'inactive') recorder.stop();
      stream?.getTracks().forEach((t) => t.stop());
      videos.forEach((v) => {
        v.pause();
        v.removeAttribute('src');
        v.load();
      });
      holder.remove();
      canvas.remove();
      createdUrls.forEach((u) => URL.revokeObjectURL(u));
    };

    (async () => {
      // 1. 预加载全部素材
      const tasks: Promise<void>[] = [];
      for (const g of groups) {
        for (const item of g.items) {
          if (item.kind === 'image') {
            tasks.push(loadImage(item.src).then((img) => { images.set(item.id, img); }));
          } else {
            tasks.push(loadVideo(item.src).then((v) => { videos.set(item.id, v); }));
          }
        }
      }
      await Promise.all(tasks);
      if (cancelled) throw new Error('cancelled');

      // 2. 排版与逐帧绘制
      const cursor = groups.map(() => ({ idx: -1, lastSwitch: 0 }));

      const drawFrame = (t: number) => {
        groups.forEach((group, gi) => {
          const idx = Math.floor(t / SLOT_SECONDS) % group.items.length;
          const state = cursor[gi];
          if (state.idx === idx) return;
          state.idx = idx;
          state.lastSwitch = t;
          videos.forEach((v) => {
            if (v.dataset.group === group.key) v.pause();
          });
          const item = group.items[idx];
          if (item.kind === 'video') {
            const v = videos.get(item.id);
            if (v) {
              v.dataset.group = group.key;
              v.currentTime = item.trimStart ?? 0;
              void v.play().catch(() => {});
            }
          }
        });
        paintFrame(ctx, opts, groups, t, (item) => images.get(item.id) || videos.get(item.id));
      };

      // 3. 录制（先确认该格式真能产出可播放文件）
      const picked = await resolveMime();

      const recordOnce = async (): Promise<Blob> => {
        const st = canvas.captureStream(30);
        stream = st;
        const rec = new MediaRecorder(st, { mimeType: picked.mime, videoBitsPerSecond: 8_000_000 });
        recorder = rec;
        const chunks: BlobPart[] = [];
        rec.ondataavailable = (e) => {
          if (e.data.size) chunks.push(e.data);
        };
        const finished = new Promise<void>((res) => {
          rec.onstop = () => res();
        });

        // 先画一帧再开录，避免开头没有画面
        drawFrame(0);
        const startedAt = performance.now();
        rec.start(200);

        // 页面在后台时 rAF 会被暂停，改用定时器继续出帧
        let timer = 0;
        const stopTimers = () => {
          cancelAnimationFrame(rafRef.id);
          if (timer) clearTimeout(timer);
        };
        const loop = () => {
          if (cancelled) {
            stopTimers();
            if (rec.state !== 'inactive') rec.stop();
            return;
          }
          const t = (performance.now() - startedAt) / 1000;
          if (t >= duration) {
            drawFrame(duration - 0.001);
            stopTimers();
            if (rec.state !== 'inactive') rec.stop();
            return;
          }
          drawFrame(t);
          onProgress?.(Math.min(1, t / duration));
          if (document.hidden) timer = window.setTimeout(loop, 120);
          else rafRef.id = requestAnimationFrame(loop);
        };
        rafRef.id = requestAnimationFrame(loop);

        await finished;
        st.getTracks().forEach((tr) => tr.stop());
        return new Blob(chunks, { type: baseMime(picked.mime) });
      };

      let blob = await recordOnce();
      if (blob.size < 1024) {
        // 后台录制偶尔一帧都收不到，回前台再试一次
        await new Promise((r) => setTimeout(r, 500));
        blob = await recordOnce();
      }
      if (cancelled) throw new Error('cancelled');
      if (blob.size < 1024) {
        throw new Error('录制失败：没有捕获到画面。请保持本页面在前台（不要切到其他窗口或锁屏）后重试');
      }
      if (!(await isPlayable(blob))) {
        throw new Error(`录制失败：${picked.ext.toUpperCase()} 文件无法播放，请改用 Chrome / Edge 重试`);
      }
      cleanup();
      resolve({ blob, mime: baseMime(picked.mime), ext: picked.ext, duration });
    })().catch((err) => {
      cleanup();
      reject(err);
    });
  });

  return {
    promise,
    cancel: () => {
      cancelled = true;
      cleanup();
    },
  };
}
