# -*- coding: utf-8 -*-
"""复古蒙太奇拼贴 9:16 模板：纯平面二维剪报蒙太奇，无立体透视。

高饱和老式画报配色（酒红/芥末/石油蓝/米黄新闻纸），
旧报刊底纹 + 版画印刷网点 + 全覆盖印刷噪点 + 撕边毛边，
碎片化人像（套色错位/双色调）与报刊残页多层叠加、分离式肢体局部，
插画线条与纪实人像混合。
照片位矩形系（撕边/拍立得/圆角/细框），尺寸大、随性错落倾斜、不裁内容；
坐标与 src/collage/templateStyles.ts 的 DEFAULT_SLOTS 完全一致。
装饰素材与文字置于照片上层且避开照片内容区，保证展露。
素材来自 public/assets/collage/popart 与 pexels/american-retro（授权见各 SOURCES.json）。
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageOps, ImageEnhance

random.seed(1987)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "public", "assets", "collage")
POP = os.path.join(ASSETS, "popart")
RETRO = os.path.join(ASSETS, "pexels", "american-retro")
OUT = os.path.join(ASSETS, "template-vintage-montage.jpg")
W, H = 900, 1600

FONT_IMPACT = "C:/Windows/Fonts/impact.ttf"
FONT_EN_B = "C:/Windows/Fonts/arialbd.ttf"
FONT_EN_I = "C:/Windows/Fonts/georgiai.ttf"
FONT_CN = "C:/Windows/Fonts/simhei.ttf"

# 高饱和老式画报配色（浓郁、不现代）
BURGUNDY = (168, 42, 38, 255)
MUSTARD = (216, 158, 40, 255)
PETROL = (32, 92, 96, 255)
CREAM = (232, 214, 176, 255)
INK = (34, 26, 20, 255)
RUST = (198, 92, 40, 255)


def _odd(n):
    n = int(n)
    return n if n % 2 == 1 else max(1, n + 1)


def load(name, folder=None):
    return Image.open(os.path.join(folder or ASSETS, name)).convert("RGBA")


def cover(im, size):
    iw, ih = im.size
    sw, sh = size
    s = max(sw / iw, sh / ih)
    im = im.resize((int(iw * s) + 1, int(ih * s) + 1), Image.LANCZOS)
    x = (im.width - sw) // 2
    y = (im.height - sh) // 2
    return im.crop((x, y, x + sw, y + sh))


def fit(im, w, h=None):
    if h is None:
        h = im.height * w / im.width
    s = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


def torn_edges(im, seed=0, amp=7, step=12):
    """毛糙撕边剪报。"""
    rnd = random.Random(seed)
    w, h = im.size
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    pts = []
    for x in range(0, w + 1, step):
        pts.append((x, rnd.randint(0, amp)))
    for y in range(0, h + 1, step):
        pts.append((w - rnd.randint(0, amp), y))
    for x in range(w, -1, -step):
        pts.append((x, h - rnd.randint(0, amp)))
    for y in range(h, -1, -step):
        pts.append((rnd.randint(0, amp), y))
    d.polygon(pts, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(0.5))
    out = im.copy()
    out.putalpha(Image.composite(out.getchannel("A"), Image.new("L", (w, h), 0), m))
    return out


def halftone(size, cell=8, dot=2, color=(60, 40, 24, 42)):
    """整幅版画网点层。"""
    ly = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ly)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            d.ellipse((x, y, x + dot, y + dot), fill=color)
    return ly


def woodcut(im, contrast=1.5, cut=(52, 205), bits=3):
    """版画处理：高对比 + 色调分离 + 颗粒。"""
    im = ImageEnhance.Contrast(im).enhance(contrast)
    lo, hi = cut
    lut = [0 if x < lo else (255 if x > hi else int((x - lo) * 255 / (hi - lo))) for x in range(256)]
    im = im.point(lut * 3)
    step = 256 // (2 ** bits)
    im = im.point(lambda p: int(p / step) * step)
    return im


def duotone(im, dark, light, keep=0.16):
    """双色调套印：暗部/亮部两色，保留少量原始纪实色彩。"""
    g = im.convert("L")
    colored = ImageOps.colorize(g, black=dark, white=light).convert("RGB")
    return Image.blend(colored, im.convert("RGB"), keep)


def misregister(layer, dx=3, dy=2, c1=(214, 58, 48, 150), c2=(40, 120, 130, 140)):
    """套色错位：平面印刷不对齐效果，无立体阴影。"""
    a = layer.getchannel("A")
    r1 = Image.new("RGBA", layer.size, c1)
    r1.putalpha(a)
    r2 = Image.new("RGBA", layer.size, c2)
    r2.putalpha(a)
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.alpha_composite(r1, (dx, dy))
    sh.alpha_composite(r2, (-dx, -dy))
    return sh


def outline(layer, color=INK, width=3):
    a = layer.getchannel("A")
    grow = a.filter(ImageFilter.MaxFilter(_odd(width * 2 + 1)))
    inner = a.filter(ImageFilter.MaxFilter(_odd(max(1, width))))
    ring = ImageChops.subtract(grow, inner)
    r = Image.new("RGBA", layer.size, color)
    r.putalpha(ring)
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(r)
    out.alpha_composite(layer)
    return out


def place(canvas, layer, cx, cy, angle=0, misreg=False):
    """平面贴放，可选套色错位，绝无立体阴影。"""
    if angle:
        layer = layer.rotate(angle, Image.BICUBIC, expand=True)
    if misreg:
        base = misregister(layer)
        canvas.alpha_composite(base, (int(cx - base.width / 2), int(cy - base.height / 2)))
    x = int(cx - layer.width / 2)
    y = int(cy - layer.height / 2)
    canvas.alpha_composite(layer, (x, y))
    return layer


def text_layer(txt, font_path, size, color, rot=0, stroke=0, spacing=0, stroke_fill=INK):
    f = ImageFont.truetype(font_path, size)
    if spacing:
        widths = [f.getlength(ch) for ch in txt]
        total = sum(widths) + spacing * (len(txt) - 1)
        im = Image.new("RGBA", (int(total) + 24, size + 32), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        x = 12
        for ch, wch in zip(txt, widths):
            d.text((x, 12), ch, font=f, fill=color, stroke_width=stroke, stroke_fill=stroke_fill)
            x += wch + spacing
    else:
        box = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), txt, font=f)
        im = Image.new("RGBA", (box[2] - box[0] + 24, box[3] - box[1] + 32), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.text((12 - box[0], 12 - box[1]), txt, font=f, fill=color,
               stroke_width=stroke, stroke_fill=stroke_fill)
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    return im


def color_block(w, h, color, seed, amp=9):
    rnd = random.Random(seed)
    blk = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(blk)
    pts = []
    for x in range(0, w + 1, 16):
        pts.append((x, rnd.randint(0, amp)))
    for y in range(0, h + 1, 16):
        pts.append((w - rnd.randint(0, amp), y))
    for x in range(w, -1, -16):
        pts.append((x, h - rnd.randint(0, amp)))
    for y in range(h, -1, -16):
        pts.append((rnd.randint(0, amp), y))
    d.polygon(pts, fill=color)
    return blk


def portrait(name, folder, width, crop, dark, light, seed, keep=0.14, amp=7):
    """碎片化人像/肢体局部：裁切 + 版画 + 双色套印 + 网点 + 撕边。"""
    im = load(name, folder).convert("RGB")
    iw, ih = im.size
    im = im.crop((int(iw * crop[0]), int(ih * crop[1]), int(iw * crop[2]), int(ih * crop[3])))
    im = woodcut(im)
    im = duotone(im, dark, light, keep=keep)
    im = fit(im, width).convert("RGBA")
    im.alpha_composite(halftone((im.width, im.height), cell=6, dot=2, color=(24, 18, 14, 30)))
    im = torn_edges(im, seed=seed, amp=amp)
    return outline(im, INK, 3)


def scrap(name, folder, width, seed, amp=7, alpha=255, desat=0.7):
    """报刊残页剪报：做旧 + 网点 + 撕边，保留文字可读。"""
    im = load(name, folder).convert("RGB")
    im = ImageEnhance.Color(im).enhance(desat)
    im = ImageEnhance.Contrast(im).enhance(1.15)
    im = Image.blend(im, Image.new("RGB", im.size, (220, 198, 156)), 0.16)
    im = fit(im, width).convert("RGBA")
    im.alpha_composite(halftone((im.width, im.height), cell=6, dot=2, color=(60, 42, 24, 26)))
    im = torn_edges(im, seed=seed, amp=amp)
    if alpha < 255:
        im.putalpha(im.getchannel("A").point(lambda a: int(a * alpha / 255)))
    return outline(im, INK, 2)


def slogan_bar(w, h, text, bg, seed, fsize=26, fg=(244, 228, 194, 250)):
    bar = color_block(w, h, bg, seed, amp=4)
    d = ImageDraw.Draw(bar)
    f = ImageFont.truetype(FONT_IMPACT, fsize)
    bb = d.textbbox((0, 0), text, font=f)
    d.text(((w - (bb[2] - bb[0])) / 2, (h - fsize) / 2 - 4), text, font=f, fill=fg)
    return outline(bar, INK, 3)


def photo_slot(shape, w, h, seed):
    """矩形系照片位（撕边/拍立得/圆角/细框），新闻纸底，不裁内容。"""
    rnd = random.Random(seed)
    pad = 18
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    paper = CREAM
    edge = (150, 110, 62, 220)
    dark = (96, 62, 34, 220)
    if shape == "torn":
        pts = []
        for x in range(pad, pad + w + 1, 14):
            pts.append((x, pad + rnd.randint(-6, 6)))
        for y in range(pad, pad + h + 1, 14):
            pts.append((pad + w + rnd.randint(-6, 6), y))
        for x in range(pad + w, pad - 1, -14):
            pts.append((x, pad + h + rnd.randint(-6, 6)))
        for y in range(pad + h, pad - 1, -14):
            pts.append((pad + rnd.randint(-6, 6), y))
        d.polygon(pts, fill=paper)
        d.rectangle((pad + 8, pad + 8, pad + w - 8, pad + h - 8), outline=edge, width=2)
    elif shape == "polaroid":
        d.rectangle((pad, pad, pad + w, pad + h), fill=paper)
        d.rectangle((pad + 8, pad + 8, pad + w - 8, pad + h - 42), outline=dark, width=2)
        d.text((pad + 12, pad + h - 36), "cut & paste", font=ImageFont.truetype(FONT_EN_I, 15), fill=(120, 78, 44, 220))
    elif shape == "frame":
        d.rectangle((pad, pad, pad + w, pad + h), fill=paper)
        d.rectangle((pad + 6, pad + 6, pad + w - 6, pad + h - 6), outline=dark, width=4)
        d.rectangle((pad + 13, pad + 13, pad + w - 13, pad + h - 13), outline=edge, width=1)
    else:  # rounded
        d.rounded_rectangle((pad, pad, pad + w, pad + h), radius=14, fill=paper)
        d.rounded_rectangle((pad + 8, pad + 8, pad + w - 8, pad + h - 8), radius=10, outline=dark, width=3)
    return outline(layer, INK, 3)


def registration_mark(d, cx, cy, r=12, color=(40, 30, 22, 220)):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=2)
    d.line((cx - r - 6, cy, cx + r + 6, cy), fill=color, width=2)
    d.line((cx, cy - r - 6, cx, cy + r + 6), fill=color, width=2)


def hatch(d, x0, y0, x1, y1, gaps=7, color=(40, 30, 22, 150)):
    """手绘排线（版画阴影线）。"""
    for i in range(0, x1 - x0, gaps):
        d.line((x0 + i, y0, x0 + i + (y1 - y0) // 2, y1), fill=color, width=2)


# ==================== 背景：旧报刊书页底纹 ====================
bg = cover(load("magazine-old.jpg", POP).convert("RGB"), (W, H))
bg = Image.blend(bg, Image.new("RGB", (W, H), (222, 200, 158)), 0.34)
news = cover(load("newspaper-times.jpg", POP).convert("RGB"), (W, H))
news = ImageEnhance.Contrast(news).enhance(1.2)
bg = Image.blend(bg, news, 0.22)
stain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(stain)
rnd = random.Random(9)
for _ in range(80):
    x, y = rnd.randint(0, W), rnd.randint(0, H)
    r = rnd.randint(40, 170)
    sd.ellipse((x - r, y - r, x + r, y + r), fill=(118, 72, 34, rnd.randint(5, 16)))
stain = stain.filter(ImageFilter.GaussianBlur(26))
bg = Image.alpha_composite(bg.convert("RGBA"), stain)
noise = Image.effect_noise((W, H), 26).convert("L")
grain = Image.merge("RGBA", (noise, noise, noise, noise.point(lambda a: int(a * 0.10))))
bg = Image.alpha_composite(bg, grain)
bg = Image.alpha_composite(bg, halftone((W, H), cell=9, dot=2, color=(74, 46, 24, 34)))
canvas = bg

# ==================== 底层：高饱和撕边撞色块 ====================
place(canvas, color_block(400, 300, BURGUNDY, 41, amp=11), 160, 620, -9)
place(canvas, color_block(340, 250, PETROL, 42, amp=10), 770, 960, 8)
place(canvas, color_block(400, 230, MUSTARD, 43, amp=10), 460, 1280, 6)
place(canvas, color_block(220, 210, RUST, 44, amp=9), 110, 1330, -7)

# ==================== 底层报刊残页剪报（文字可辨） ====================
u1 = scrap("magazine-old.jpg", POP, 270, seed=71, amp=8)
u1.putalpha(u1.getchannel("A").point(lambda a: int(a * 0.55)))
place(canvas, u1, 780, 1400, 9)
u2 = scrap("american-retro-02.jpg", RETRO, 250, seed=72, amp=8, alpha=170)
place(canvas, u2, 120, 950, -8)
# 竖条报纸剪报（底层，压在照片位之下）
strip = scrap("newspaper-times.jpg", POP, 112, seed=73, amp=5, alpha=220)
strip = strip.rotate(90, Image.BICUBIC, expand=True)
place(canvas, strip, 452, 630, -4)

# ==================== 与前端 DEFAULT_SLOTS 完全一致的大照片位 ====================
photos = [
    ("torn",     245,  560, 340, 320, -8, 1),
    ("polaroid", 655,  700, 350, 285,  7, 2),
    ("rounded",  258, 1045, 330, 330,  6, 3),
    ("frame",    660, 1135, 345, 310, -7, 4),
]
for shape, cx, cy, w, h, ang, seed in photos:
    place(canvas, photo_slot(shape, w, h, seed), cx, cy, ang)

# ==================== 碎片化人像 / 分离式肢体局部（放空隙，脸完整露出） ====================
# 羽毛头饰坐姿女（顶部左，芥末套印）
f3 = portrait("american-retro-20.jpg", RETRO, 152,
              (0.16, 0.05, 0.86, 0.82), (58, 34, 14), (240, 202, 124), 13, keep=0.14)
place(canvas, f3, 118, 328, -9, misreg=True)
# 黄衣女星（顶部右，高饱和插画+纪实混合）
f4 = portrait("poster-red-lips.jpg", POP, 146,
              (0.20, 0.04, 0.86, 0.52), (54, 20, 16), (244, 196, 116), 15, keep=0.42, amp=6)
place(canvas, f4, 802, 318, 8, misreg=True)
# 礼帽托腮女（左下，酒红套印）
f1 = portrait("american-retro-18.jpg", RETRO, 196,
              (0.05, 0.04, 0.92, 0.66), (46, 18, 16), (232, 176, 118), 11, keep=0.10)
place(canvas, f1, 196, 1405, -10, misreg=True)
# 短发妆容女面部特写（中下，石油蓝套印）
f2 = portrait("american-retro-16.jpg", RETRO, 178,
              (0.16, 0.24, 0.94, 0.66), (16, 40, 44), (188, 216, 196), 12, keep=0.12)
place(canvas, f2, 628, 1418, 9, misreg=True)
# 分离式手局部（中部横带）
hand = portrait("american-retro-18.jpg", RETRO, 126,
                (0.14, 0.48, 0.72, 0.68), (52, 22, 18), (236, 182, 126), 14, keep=0.16, amp=5)
place(canvas, hand, 452, 792, 12)

# ==================== 标语条（空隙，避开照片内容区） ====================
place(canvas, slogan_bar(248, 54, "CUT & PASTE", BURGUNDY, 51, fsize=27), 252, 852, -4)
place(canvas, slogan_bar(212, 46, "EST. 1926", MUSTARD, 53, fsize=24, fg=(40, 28, 20, 250)), 672, 892, 5)
place(canvas, slogan_bar(244, 48, "AVANT-GARDE", PETROL, 52, fsize=25), 410, 1478, -3)

# ==================== 绘制装饰：套色十字 / 手绘排线 / 星芒 / 圆点 / 胶带 ====================
d = ImageDraw.Draw(canvas)
for mx, my in [(48, 430), (852, 560), (56, 1120), (848, 1440), (60, 790), (452, 380)]:
    registration_mark(d, mx, my, r=12)
hatch(d, 44, 948, 108, 1008, gaps=8)
hatch(d, 806, 1010, 868, 1070, gaps=8)

def star(d, cx, cy, r, color, seed):
    rnd = random.Random(seed)
    pts = []
    for i in range(8):
        a = i * math.pi / 4
        rr = r if i % 2 == 0 else r * rnd.uniform(0.24, 0.36)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=color, outline=INK)
    d.line(pts + [pts[0]], fill=INK, width=3, joint="curve")

star(d, 88, 640, 20, MUSTARD[:3] + (245,), 1)
star(d, 830, 1060, 20, BURGUNDY[:3] + (245,), 2)
star(d, 452, 920, 15, PETROL[:3] + (245,), 3)
for cx, cy, col in [(836, 742, BURGUNDY), (74, 1280, PETROL), (452, 1560, MUSTARD)]:
    for dx, dy in [(-18, 0), (0, 0), (18, 0), (-9, -16), (9, 16)]:
        d.ellipse((cx + dx - 4, cy + dy - 4, cx + dx + 4, cy + dy + 4), fill=col[:3] + (225,))

def tape(x, y, w, h, ang, color=(206, 176, 118, 165)):
    t = Image.new("RGBA", (w, h), color)
    td = ImageDraw.Draw(t)
    for i in range(0, w, 7):
        td.line((i, 0, i, h), fill=(250, 238, 208, 70), width=1)
    place(canvas, t, x, y, ang)

tape(150, 392, 72, 22, -20)
tape(612, 566, 70, 22, 14)
tape(158, 872, 68, 22, -14)
tape(586, 968, 70, 22, 12)

# ==================== 文字（最上层，大标题 + 文案） ====================
title = text_layer("MONTAGE", FONT_IMPACT, 92, (246, 230, 192, 252), rot=-3, stroke=5, spacing=2)
place(canvas, title, 420, 106, misreg=True)
title2 = text_layer("复古蒙太奇", FONT_CN, 44, (216, 158, 40, 252), rot=-2, stroke=3)
place(canvas, title2, 448, 198)
cn_sub = text_layer("剪报 · 拼贴 · 先锋艺术", FONT_CN, 23, (244, 228, 194, 246), rot=-1, stroke=1)
place(canvas, cn_sub, 448, 252)
foot = text_layer("CUT · PASTE · REIMAGINE — A PAPER COLLAGE", FONT_EN_B, 18, (40, 30, 22, 245), rot=-1)
place(canvas, foot, 450, 1572)

final = canvas.convert("RGB")
final.save(OUT, quality=92)
print("saved", OUT, final.size)
