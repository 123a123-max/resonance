# -*- coding: utf-8 -*-
"""清透AI科技磨砂拼贴 —— 9:16 模板生成脚本。
冷调浅色渐变 + 半透明磨砂玻璃 + 柔和几何圆环 + 实拍低透明叠层。
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "public", "assets", "collage", "tech")
OUT = os.path.join(ROOT, "public", "assets", "collage", "template-tech-frost.jpg")
W, H = 900, 1600

# ---------- 冷调色板 ----------
INK = (74, 96, 112)
INK_SOFT = (112, 136, 152)
FROST = (250, 253, 255)
CYAN = (150, 205, 214)
BLUE = (158, 190, 226)
GRAY = (198, 212, 220)


def font(paths, size):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


F_TITLE = font(["C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/simhei.ttf"], 104)
F_SUB = font(["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"], 30)
F_SMALL = font(["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"], 22)
F_EN = font(["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/calibrib.ttf"], 34)
F_EN_S = font(["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/calibri.ttf"], 22)
F_NUM = font(["C:/Windows/Fonts/arialbd.ttf"], 20)


def load(name):
    return Image.open(os.path.join(ASSETS, name)).convert("RGB")


def cover(im, size):
    tw, th = size
    s = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    x = (im.width - tw) // 2
    y = (im.height - th) // 2
    return im.crop((x, y, x + tw, y + th))


def gradient_bg():
    """冷调三段渐变 + 柔和径向光晕（纯 PIL）。"""
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    stops = [(0.0, (235, 241, 245)), (0.42, (211, 230, 236)), (1.0, (223, 233, 246))]
    for i in range(len(stops) - 1):
        y0, c0 = stops[i]
        y1, c1 = stops[i + 1]
        a, b = int(y0 * H), int(y1 * H)
        for y in range(a, b):
            t = (y - a) / max(1, b - a)
            c = tuple(int(c0[k] * (1 - t) + c1[k] * t) for k in range(3))
            d.line((0, y, W, y), fill=c)
    bg = bg.convert("RGBA")
    for cx, cy, r, col, strength in [
        (230, 380, 430, (255, 255, 255), 0.42),
        (700, 1180, 500, (206, 232, 242), 0.38),
        (640, 180, 300, (214, 226, 246), 0.28),
    ]:
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).ellipse((cx - r, cy - r, cx + r, cy + r), fill=int(255 * strength))
        mask = mask.filter(ImageFilter.GaussianBlur(r * 0.38))
        glow = Image.new("RGBA", (W, H), col + (0,))
        glow.putalpha(mask)
        bg.alpha_composite(glow)
    return bg


def frost_layer(name, size, opacity, blur=7, desat=0.35, tint=(214, 233, 240), tint_mix=0.34, feather=70):
    """实拍素材 → 朦胧冷调半透明叠层，边缘羽化融入背景（虚实叠加里的“虚”）。"""
    im = cover(load(name), size)
    im = ImageEnhance.Color(im).enhance(desat)
    im = ImageEnhance.Brightness(im).enhance(1.22)
    im = im.filter(ImageFilter.GaussianBlur(blur))
    im = Image.blend(im, Image.new("RGB", size, tint), tint_mix)
    layer = im.convert("RGBA")
    # 边缘羽化蒙版：越靠边越透明，消除矩形硬边
    mask = Image.new("L", size, 255)
    md = ImageDraw.Draw(mask)
    for i in range(feather):
        v = int(255 * i / feather)
        md.rectangle((i, i, size[0] - 1 - i, size[1] - 1 - i), outline=v, width=1)
    a = Image.new("L", size, int(255 * opacity))
    layer.putalpha(ImageChops.multiply(a, mask))
    return layer


def soft_ring(canvas, cx, cy, r, width, color, alpha, blur=0, start=None, end=None):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    box = (int(cx - r), int(cy - r), int(cx + r), int(cy + r))
    if start is None:
        d.ellipse(box, outline=color + (alpha,), width=width)
    else:
        d.arc(box, start, end, fill=color + (alpha,), width=width)
    if blur:
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(layer)


def soft_line(canvas, pts, color, alpha, width=2, blur=0):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.line(pts, fill=color + (alpha,), width=width, joint="curve")
    if blur:
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(layer)


def place(canvas, layer, cx, cy, ang=0):
    if ang:
        layer = layer.rotate(ang, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def photo_slot(shape, w, h, seed, num):
    """矩形系磨砂玻璃照片位：半透明底 + 细白边 + 浅色照片区，不裁内容。"""
    pad = 14
    L = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    bx = (pad, pad, pad + w, pad + h)
    if shape == "frame":
        d.rectangle(bx, fill=(252, 254, 255, 150), outline=(255, 255, 255, 220), width=2)
        d.rectangle((pad + 4, pad + 4, pad + w - 4, pad + h - 4), outline=(176, 200, 214, 150), width=1)
        inner = (pad + 10, pad + 10, pad + w - 10, pad + h - 10)
    elif shape == "soft":
        d.rounded_rectangle(bx, radius=30, fill=(250, 253, 255, 165), outline=(255, 255, 255, 225), width=2)
        inner = (pad + 8, pad + 8, pad + w - 8, pad + h - 8)
        d.rounded_rectangle(inner, radius=24, outline=(188, 210, 222, 140), width=1)
    else:  # frost / glass
        d.rounded_rectangle(bx, radius=18, fill=(250, 253, 255, 170), outline=(255, 255, 255, 235), width=2)
        inner = (pad + 7, pad + 7, pad + w - 7, pad + h - 7)
        d.rounded_rectangle(inner, radius=13, fill=(246, 251, 254, 235))
    if shape != "frame":
        d.rounded_rectangle(inner, radius=13 if shape != "soft" else 24, fill=(247, 252, 255, 240))
    # 斜向高光（玻璃感）
    hl = Image.new("RGBA", L.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.polygon([(pad, pad + int(h * 0.42)), (pad + int(w * 0.55), pad),
                (pad + int(w * 0.78), pad), (pad, pad + int(h * 0.78))], fill=(255, 255, 255, 13))
    hl = hl.filter(ImageFilter.GaussianBlur(16))
    L.alpha_composite(hl)
    # 角标编号（科技感）
    d = ImageDraw.Draw(L)
    d.text((pad + 12, pad + 10), "%02d" % num, font=F_NUM, fill=(158, 182, 198, 210))
    return L


def centered_text(canvas, text, cx, y, fnt, color, spacing=6):
    """逐字绘制并水平居中（避免 PIL 中文对齐问题）。"""
    widths = [fnt.getlength(ch) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = cx - total / 2
    d = ImageDraw.Draw(canvas)
    for ch, cw in zip(text, widths):
        d.text((x, y), ch, font=fnt, fill=color)
        x += cw + spacing


# ================= 画布 =================
canvas = gradient_bg()

# ---- 实拍叠层（低透明、朦胧，虚的部分）----
canvas.alpha_composite(frost_layer("crystal-bokeh-1.jpg", (900, 620), 0.22, blur=6,
                                   desat=0.55, tint=(210, 230, 240), tint_mix=0.38), (0, 60))
canvas.alpha_composite(frost_layer("crystal-bokeh-3.jpg", (760, 560), 0.20, blur=7,
                                   desat=0.55, tint=(212, 230, 242), tint_mix=0.38), (110, 900))
canvas.alpha_composite(frost_layer("glass-ice.jpg", (520, 350), 0.22, blur=4,
                                   desat=0.55, tint=(212, 233, 242), tint_mix=0.38), (300, 1120))
canvas.alpha_composite(frost_layer("glass-building-1.jpg", (330, 250), 0.26, blur=3,
                                   desat=0.5, tint=(216, 233, 242), tint_mix=0.40), (40, 1330))
canvas.alpha_composite(frost_layer("glass-building-3.jpg", (360, 220), 0.24, blur=3,
                                   desat=0.5, tint=(214, 232, 242), tint_mix=0.40), (520, 60))

# ---- 柔和几何圆环 / 曲面 / 线条（实的部分）----
soft_ring(canvas, 690, 330, 205, 3, CYAN, 95, blur=1)
soft_ring(canvas, 690, 330, 232, 1, BLUE, 70)
soft_ring(canvas, 200, 1250, 150, 2, CYAN, 80, blur=1)
soft_ring(canvas, 200, 1250, 178, 1, GRAY, 70)
soft_ring(canvas, 820, 1020, 96, 2, BLUE, 65, start=200, end=70)
soft_ring(canvas, 120, 470, 80, 2, CYAN, 60, start=40, end=300)
# 曲面几何：几条平滑弧线
soft_ring(canvas, 470, 640, 355, 2, (176, 206, 220), 45, start=200, end=345, blur=1)
soft_ring(canvas, 470, 640, 390, 1, (186, 214, 226), 40, start=205, end=340)
# 极简直线与点阵
soft_line(canvas, [(110, 300), (300, 300)], GRAY, 90, 2)
soft_line(canvas, [(600, 1435), (800, 1435)], GRAY, 90, 2)
for i in range(6):
    for j in range(3):
        d = ImageDraw.Draw(canvas)
        d.ellipse((772 + i * 16, 1180 + j * 16, 775 + i * 16, 1183 + j * 16),
                  fill=(150, 180, 198, 90))
for x, y in [(140, 860), (760, 730), (320, 1470)]:
    d = ImageDraw.Draw(canvas)
    d.line((x - 9, y, x + 9, y), fill=INK_SOFT + (110,), width=2)
    d.line((x, y - 9, x, y + 9), fill=INK_SOFT + (110,), width=2)

# ---- 大标题 ----
d = ImageDraw.Draw(canvas)
d.text((112, 132), "幻 境", font=F_TITLE, fill=INK)
d.text((120, 258), "DIGITAL  /  FROSTED", font=F_EN, fill=INK_SOFT)
d.line((120, 310, 540, 310), fill=GRAY + (150,), width=2)
d.text((120, 322), "虚 实 叠 加  ·  清 透 数 字 空 间", font=F_SMALL, fill=INK_SOFT)

# ---- 照片位（4 张，随性错落、不裁内容）----
photos = [
    ("frost", 245, 555, 340, 320, -9, 1),
    ("glass", 655, 700, 355, 285, 7, 2),
    ("frame", 255, 1040, 330, 330, 6, 3),
    ("soft", 665, 1135, 350, 310, -8, 4),
]
for shape, cx, cy, w, h, ang, num in photos:
    place(canvas, photo_slot(shape, w, h, num, num), cx, cy, ang)

# ---- 底部装饰几何 + 副标题 ----
soft_ring(canvas, 738, 1415, 62, 1, CYAN, 60, start=185, end=345)
soft_line(canvas, [(70, 1452), (250, 1452)], GRAY, 110, 2)
soft_line(canvas, [(560, 1452), (620, 1452)], GRAY, 110, 2)
d = ImageDraw.Draw(canvas)
d.text((60, 1496), "VIRTUAL × REAL", font=F_EN_S, fill=INK_SOFT)
d.text((640, 1496), "2026", font=F_EN_S, fill=INK_SOFT)

# ---- 全局细腻磨砂颗粒（很轻）----
rnd = random.Random(7)
noise_img = Image.new("L", (W, H))
noise_img.putdata([rnd.randint(112, 144) for _ in range(W * H)])
noise_img = noise_img.filter(ImageFilter.GaussianBlur(0.4))
grain = Image.merge("RGBA", (noise_img, noise_img, noise_img, Image.new("L", (W, H), 14)))
canvas.alpha_composite(grain)

canvas.convert("RGB").save(OUT, quality=94)
print("saved:", OUT, canvas.size)
