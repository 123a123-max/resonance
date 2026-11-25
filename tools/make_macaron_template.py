# -*- coding: utf-8 -*-
"""奶油马卡龙青春拼贴 9:16 模板：柔光治愈、圆润无棱角、低饱和少女感。

马卡龙渐变底（淡粉/奶黄/薄荷绿/浅紫）+ 哑光奶油纸质感（平整细腻、无破损），
圆角贴纸照片位（大、随性错落、无尖锐），蝴蝶结/糖果/碎花/星星手绘贴纸，
少女感人像 + 甜品小物，随性手写字体，低对比柔光。
禁止：暗沉、高对比、粗硬线条、破旧撕纸肌理 —— 全程不用撕边/网点/黑粗描边。
照片位坐标/角度/形状与 src/collage/templateStyles.ts 中 macaron 的 slots 一致（全 rounded）。
素材来自 public/assets/collage/pexels/macaron（授权见该目录 SOURCES.json）。
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

random.seed(618)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "public", "assets", "collage")
MAC = os.path.join(ASSETS, "pexels", "macaron")
OUT = os.path.join(ASSETS, "template-macaron.jpg")
W, H = 900, 1600

FONT_HAND = "C:/Windows/Fonts/segoesc.ttf"       # 英文手写
FONT_HAND_B = "C:/Windows/Fonts/segoescb.ttf"    # 英文手写加粗
FONT_YOU = "C:/Windows/Fonts/SIMYOU.TTF"         # 中文幼圆
FONT_KAI = "C:/Windows/Fonts/STXINGKA.TTF"       # 中文行楷

# 马卡龙低饱和色
PINK = (250, 199, 210)
YELLOW = (252, 233, 176)
MINT = (196, 232, 214)
LILAC = (219, 205, 238)
CREAM = (255, 250, 246)
INK = (110, 92, 104)  # 柔和深藕色，不用纯黑


def load(name, folder=None):
    return Image.open(os.path.join(folder or MAC, name)).convert("RGBA")


def fit(im, w, h=None):
    if h is None:
        h = im.height * w / im.width
    s = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


def cover(im, size):
    iw, ih = im.size
    sw, sh = size
    s = max(sw / iw, sh / ih)
    im = im.resize((int(iw * s) + 1, int(ih * s) + 1), Image.LANCZOS)
    x = (im.width - sw) // 2
    y = (im.height - sh) // 2
    return im.crop((x, y, x + sw, y + sh))


def paste(canvas, layer, cx, cy, angle=0, soft_shadow=True):
    """圆润贴放：可选极淡柔光投影（非硬边、非立体）。"""
    if angle:
        layer = layer.rotate(angle, Image.BICUBIC, expand=True)
    x = int(cx - layer.width / 2)
    y = int(cy - layer.height / 2)
    if soft_shadow:
        a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(9))
        sh = Image.new("RGBA", layer.size, (168, 146, 160, 46))
        sh.putalpha(a)
        canvas.alpha_composite(sh, (x + 2, y + 5))
    canvas.alpha_composite(layer, (x, y))
    return layer


def soft_portrait(name, width, crop, seed, tint):
    """少女感人像贴纸：柔光提亮、降对比、圆角白贴纸边，无版画无网点。"""
    im = load(name).convert("RGB")
    iw, ih = im.size
    im = im.crop((int(iw * crop[0]), int(ih * crop[1]), int(iw * crop[2]), int(ih * crop[3])))
    im = fit(im, width).convert("RGBA")
    rgb = im.convert("RGB")
    d = ImageDraw.Draw(rgb)
    # 柔光提亮
    from PIL import ImageEnhance
    rgb = ImageEnhance.Brightness(rgb).enhance(1.05)
    rgb = ImageEnhance.Contrast(rgb).enhance(0.90)
    im = rgb.convert("RGBA")
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=30, fill=255)
    im.putalpha(m)
    out = Image.new("RGBA", (im.width + 18, im.height + 18), (0, 0, 0, 0))
    od = ImageDraw.Draw(out)
    od.rounded_rectangle((0, 0, out.width - 1, out.height - 1), radius=36, fill=CREAM, outline=tint, width=3)
    out.alpha_composite(im, (9, 9))
    return out


def round_sticker(name, size, seed, tint):
    """甜品/小物圆形贴纸：柔光、圆贴纸白边。"""
    im = load(name).convert("RGB")
    im = cover(im, (size, size))
    from PIL import ImageEnhance
    im = ImageEnhance.Brightness(im).enhance(1.04)
    im = ImageEnhance.Contrast(im).enhance(0.92)
    im = im.convert("RGBA")
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).ellipse((0, 0, size - 1, size - 1), fill=255)
    im.putalpha(m)
    pad = 9
    out = Image.new("RGBA", (size + pad * 2, size + pad * 2), (0, 0, 0, 0))
    od = ImageDraw.Draw(out)
    od.ellipse((0, 0, out.width - 1, out.height - 1), fill=CREAM, outline=tint, width=3)
    out.alpha_composite(im, (pad, pad))
    return out


def photo_slot(w, h, seed, tint):
    """大圆角贴纸照片位：奶白圆角纸 + 柔和彩色描边 + 内细线，无尖锐棱角。"""
    pad = 20
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((pad - 6, pad - 6, pad + w + 6, pad + h + 6), radius=42,
                        fill=CREAM, outline=tint, width=4)
    d.rounded_rectangle((pad + 4, pad + 4, pad + w - 4, pad + h - 4), radius=32,
                        outline=(238, 222, 228, 210), width=2)
    # 顶部小圆点装饰
    d.ellipse((pad + w / 2 - 6, pad - 11, pad + w / 2 + 6, pad + 1), fill=tint)
    return layer


def text_layer(txt, font_path, size, color, rot=0, stroke=2, spacing=0):
    f = ImageFont.truetype(font_path, size)
    if spacing:
        widths = [f.getlength(ch) for ch in txt]
        total = sum(widths) + spacing * (len(txt) - 1)
        im = Image.new("RGBA", (int(total) + 30, size + 34), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        x = 15
        for ch, wch in zip(txt, widths):
            d.text((x, 14), ch, font=f, fill=color, stroke_width=stroke, stroke_fill=CREAM)
            x += wch + spacing
    else:
        box = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), txt, font=f)
        im = Image.new("RGBA", (box[2] - box[0] + 30, box[3] - box[1] + 34), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.text((15 - box[0], 14 - box[1]), txt, font=f, fill=color,
               stroke_width=stroke, stroke_fill=CREAM)
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    return im


def bow(canvas, cx, cy, size, color, angle=0):
    """手绘小蝴蝶结：圆润双耳 + 结心 + 飘带。"""
    layer = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = color
    dark = tuple(max(0, int(v * 0.86)) for v in c[:3]) + (255,)
    cx0, cy0 = size, size
    # 左右圆润耳朵
    d.ellipse((cx0 - int(size * 0.92), cy0 - int(size * 0.50),
               cx0 - int(size * 0.06), cy0 + int(size * 0.34)), fill=c, outline=CREAM, width=3)
    d.ellipse((cx0 + int(size * 0.06), cy0 - int(size * 0.50),
               cx0 + int(size * 0.92), cy0 + int(size * 0.34)), fill=c, outline=CREAM, width=3)
    # 飘带
    d.polygon([(cx0 - size // 5, cy0), (cx0 - size // 8, cy0 + int(size * 0.9)),
               (cx0 + size // 14, cy0 + int(size * 0.62)), (cx0, cy0)], fill=c)
    d.polygon([(cx0 + size // 5, cy0), (cx0 + size // 8, cy0 + int(size * 0.9)),
               (cx0 - size // 14, cy0 + int(size * 0.62)), (cx0, cy0)], fill=dark)
    # 结心
    d.ellipse((cx0 - size // 6, cy0 - size // 6, cx0 + size // 6, cy0 + size // 6),
              fill=tuple(min(255, int(v * 1.06)) for v in c[:3]) + (255,), outline=CREAM, width=2)
    paste(canvas, layer, cx, cy, angle, soft_shadow=False)


def flower(d, cx, cy, r, petal, center):
    """圆润碎花：5 瓣椭圆花瓣 + 暖色花心。"""
    for i in range(5):
        a = i * 2 * math.pi / 5 - math.pi / 2
        px = cx + r * 0.62 * math.cos(a)
        py = cy + r * 0.62 * math.sin(a)
        d.ellipse((px - r * 0.52, py - r * 0.52, px + r * 0.52, py + r * 0.52),
                  fill=petal, outline=CREAM, width=2)
    d.ellipse((cx - r * 0.34, cy - r * 0.34, cx + r * 0.34, cy + r * 0.34), fill=center)


def star(d, cx, cy, r, color):
    """圆润五角星贴纸：用圆滑多边形 + 柔白描边。"""
    pts = []
    for i in range(10):
        a = i * math.pi / 5 - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.52
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=color)
    d.line(pts + [pts[0]], fill=CREAM, width=4, joint="curve")


def lollipop(canvas, cx, cy, r, color, angle=0):
    """棒棒糖：圆糖面 + 螺旋 + 细杆。"""
    layer = Image.new("RGBA", (r * 4, r * 5), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ox, oy = r * 2, r * 2
    d.line((ox, oy, ox, oy + r * 2), fill=(226, 210, 216, 255), width=7)
    d.ellipse((ox - r, oy - r, ox + r, oy + r), fill=color, outline=CREAM, width=4)
    # 螺旋
    pts = []
    for i in range(72):
        t = i / 71 * math.pi * 4.2
        rr = r * 0.86 * (1 - i / 95)
        pts.append((ox + rr * math.cos(t), oy + rr * math.sin(t)))
    d.line(pts, fill=CREAM, width=4, joint="curve")
    paste(canvas, layer, cx, cy, angle, soft_shadow=False)


# ==================== 背景：马卡龙柔光渐变 + 哑光奶油纸 ====================
stops = [
    (0.00, (253, 231, 237)),
    (0.32, (253, 244, 221)),
    (0.62, (225, 243, 232)),
    (0.84, (232, 222, 246)),
    (1.00, (250, 228, 238)),
]
bg = Image.new("RGBA", (W, H), (255, 255, 255, 255))
bd = ImageDraw.Draw(bg)
for y in range(H):
    t = y / (H - 1)
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        if p0 <= t <= p1:
            k = (t - p0) / (p1 - p0)
            col = tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(3)) + (255,)
            bd.line((0, y, W, y), fill=col)
            break
# 柔光光晕
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
for gx, gy, gr, gc in [(140, 380, 260, (255, 255, 255, 40)),
                       (760, 940, 300, (255, 250, 235, 42)),
                       (420, 1420, 280, (250, 240, 255, 40))]:
    gd.ellipse((gx - gr, gy - gr, gx + gr, gy + gr), fill=gc)
glow = glow.filter(ImageFilter.GaussianBlur(80))
bg = Image.alpha_composite(bg, glow)
# 细腻哑光颗粒（极轻，非破损粗糙）
noise = Image.effect_noise((W, H), 10).convert("L")
grain = Image.merge("RGBA", (noise, noise, noise, noise.point(lambda a: int(a * 0.035))))
bg = Image.alpha_composite(bg, grain)
canvas = bg

# ==================== 背景柔色圆点（低对比装饰） ====================
d = ImageDraw.Draw(canvas)
for _ in range(26):
    x = random.randint(30, W - 30)
    y = random.randint(60, H - 60)
    r = random.randint(6, 26)
    col = random.choice([PINK, YELLOW, MINT, LILAC])[:3] + (70,)
    d.ellipse((x - r, y - r, x + r, y + r), fill=col)

# ==================== 大圆角贴纸照片位（坐标/角度/形状与前端 macaron slots 一致） ====================
photos = [
    (245,  560, 340, 320, -8, PINK),
    (655,  700, 350, 285,  7, MINT),
    (258, 1045, 330, 330,  6, LILAC),
    (660, 1135, 345, 310, -7, YELLOW),
]
for cx, cy, pw, ph, ang, tint in photos:
    paste(canvas, photo_slot(pw, ph, 0, tint), cx, cy, ang)

# ==================== 少女感人像贴纸（放空隙，脸完整露出） ====================
p1 = soft_portrait("macaron-13.jpg", 186, (0.10, 0.04, 0.90, 0.58), 1, PINK)
paste(canvas, p1, 792, 300, 8)
p2 = soft_portrait("macaron-07.jpg", 176, (0.00, 0.04, 0.60, 0.52), 2, LILAC)
paste(canvas, p2, 122, 1326, -9)

# ==================== 甜品 / 小物圆形贴纸 ====================
s1 = round_sticker("macaron-11.jpg", 112, 1, PINK)     # 粉色糖果球
paste(canvas, s1, 458, 862, -6)
s2 = round_sticker("macaron-03.jpg", 96, 2, YELLOW)    # 彩色糖珠
paste(canvas, s2, 806, 906, 7)
s3 = round_sticker("macaron-16.jpg", 104, 3, MINT)     # 蛋白糖
paste(canvas, s3, 104, 646, -9)
s4 = round_sticker("macaron-05.jpg", 92, 4, LILAC)     # 甜甜圈
paste(canvas, s4, 806, 1428, 8)

# ==================== 手绘装饰：蝴蝶结 / 碎花 / 星星 / 棒棒糖 ====================
bow(canvas, 118, 470, 52, PINK, -14)
bow(canvas, 758, 1010, 46, LILAC, 12)
bow(canvas, 452, 1352, 40, MINT, -8)

d = ImageDraw.Draw(canvas)
for fx, fy, fr, fp, fc in [
    (78, 1090, 22, (252, 205, 218, 235), YELLOW),
    (844, 560, 20, (206, 228, 246, 235), PINK),
    (452, 410, 18, (220, 208, 242, 235), CREAM),
    (96, 1490, 16, (252, 224, 180, 235), PINK),
    (838, 780, 17, (204, 234, 218, 235), YELLOW),
]:
    flower(d, fx, fy, fr, fp, fc)

for sx, sy, sr, sc in [
    (820, 470, 17, YELLOW),
    (86, 840, 15, LILAC),
    (452, 990, 14, PINK),
    (790, 1180, 16, MINT),
    (452, 1520, 13, LILAC),
]:
    star(d, sx, sy, sr, sc[:3] + (235,))

lollipop(canvas, 452, 768, 30, PINK, -8)
lollipop(canvas, 830, 1280, 24, MINT, 10)

# ==================== 手写字体：大标题 + 文案 ====================
t = text_layer("Sweet Days", FONT_HAND_B, 96, (232, 150, 172, 255), rot=-4, stroke=3, spacing=1)
paste(canvas, t, 424, 112, soft_shadow=False)
t2 = text_layer("奶油马卡龙", FONT_YOU, 52, (172, 148, 196, 255), rot=-2, stroke=2, spacing=2)
paste(canvas, t2, 446, 206, soft_shadow=False)
t3 = text_layer("软乎乎的青春手账", FONT_KAI, 30, (168, 152, 162, 250), rot=-1, stroke=1)
paste(canvas, t3, 448, 258, soft_shadow=False)
foot = text_layer("sweet · soft · lovely", FONT_HAND, 34, (170, 148, 176, 250), rot=-2, stroke=1)
paste(canvas, foot, 448, 1550, soft_shadow=False)

final = canvas.convert("RGB")
final.save(OUT, quality=92)
print("saved", OUT, final.size)
