# -*- coding: utf-8 -*-
"""INS 极简留白高级拼贴 9:16 模板：莫兰迪米白/浅灰/裸棕、哑光纸感、大量留白。

照片位矩形系（细白框/圆角）尺寸大、轻微错落倾斜、不裁内容；
装饰稀疏（局部人像、干花标本、程序绘制陶瓷器皿），均带细白描边、极淡阴影；
文字为纤细无衬线极小字 + 纤细大标题，无粗体无夸张涂鸦。
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops

random.seed(21)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "public", "assets", "collage")
POP = os.path.join(ASSETS, "popart")
OUT = os.path.join(ASSETS, "template-ins-minimal.jpg")
W, H = 900, 1600

# 纤细无衬线
F_THIN = "C:/Windows/Fonts/segoeuil.ttf"
F_THIN_I = "C:/Windows/Fonts/calibril.ttf"
F_EN = "C:/Windows/Fonts/calibri.ttf"
F_EN_B = "C:/Windows/Fonts/arial.ttf"
F_CN = "C:/Windows/Fonts/Deng.ttf"

INK = (108, 104, 96, 210)      # 莫兰迪深灰
INK_L = (140, 136, 128, 165)
WHITE = (255, 255, 255, 255)


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
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)


def white_outline(layer, width=3):
    """给贴纸加细白描边（轻柔，不厚重）。"""
    a = layer.getchannel("A")
    grow = a.filter(ImageFilter.MaxFilter(width * 2 + 1))
    inner_w = width if width % 2 == 1 else max(1, width - 1)
    inner = a.filter(ImageFilter.MaxFilter(inner_w))
    ring = ImageChops.subtract(grow, inner)
    wh = Image.new("RGBA", layer.size, WHITE)
    wh.putalpha(ring)
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(wh)
    out.alpha_composite(layer)
    return out


def soft_shadow(layer, blur=12, alpha=20):
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new("RGBA", layer.size, (96, 92, 84, alpha))
    sh.putalpha(a)
    return sh


def place(canvas, layer, cx, cy, angle=0, shadow=True):
    if angle:
        layer = layer.rotate(angle, Image.BICUBIC, expand=True)
    x = int(cx - layer.width / 2)
    y = int(cy - layer.height / 2)
    if shadow:
        canvas.alpha_composite(soft_shadow(layer), (x + 3, y + 6))
    canvas.alpha_composite(layer, (x, y))
    return layer


def text_layer(txt, font_path, size, color, rot=0, spacing=0):
    f = ImageFont.truetype(font_path, size)
    if spacing:
        # 手动字距（纤细大标题用）
        widths = [f.getlength(ch) for ch in txt]
        total = sum(widths) + spacing * (len(txt) - 1)
        im = Image.new("RGBA", (int(total) + 14, size + 24), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        x = 7
        for ch, wch in zip(txt, widths):
            d.text((x, 8), ch, font=f, fill=color)
            x += wch + spacing
    else:
        box = f.getbbox(txt)
        w = box[2] - box[0] + 14
        h = box[3] - box[1] + 14
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.text((7 - box[0], 7 - box[1]), txt, font=f, fill=color)
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    return im


def photo_slot(shape, w, h, seed):
    """细白框/圆角照片位：奶白底 + 细描边，不裁切照片内容。"""
    pad = 16
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    paper = (250, 249, 246, 255)
    edge = (206, 203, 196, 200)
    if shape == "frame":
        d.rectangle((pad, pad, pad + w, pad + h), fill=paper)
        d.rectangle((pad + 6, pad + 6, pad + w - 6, pad + h - 6), outline=edge, width=2)
    elif shape == "rounded":
        d.rounded_rectangle((pad, pad, pad + w, pad + h), radius=16, fill=paper)
        d.rounded_rectangle((pad + 6, pad + 6, pad + w - 6, pad + h - 6),
                            radius=11, outline=edge, width=2)
    return layer


def ceramic_vase(w, h, body, seed=1):
    """程序绘制简约陶瓷器皿：莫兰迪纯色 + 细白描边。"""
    rnd = random.Random(seed)
    v = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(v)
    cx = w / 2
    # 花瓶轮廓：半径随高度变化（口窄-颈细-肚圆-底收）
    prof = [(0.00, 0.20), (0.06, 0.22), (0.14, 0.13), (0.28, 0.20),
            (0.45, 0.42), (0.62, 0.46), (0.78, 0.34), (0.92, 0.22), (1.00, 0.20)]
    right, left = [], []
    for t, r in prof:
        y = t * h
        right.append((cx + r * w, y))
        left.append((cx - r * w, y))
    pts = left + right[::-1]
    d.polygon(pts, fill=body)
    # 瓶口椭圆
    ry = 0.045 * h
    d.ellipse((cx - 0.20 * w, -ry, cx + 0.20 * w, ry), fill=body)
    d.ellipse((cx - 0.20 * w, -ry, cx + 0.20 * w, ry), outline=(255, 255, 255, 150), width=2)
    # 细白描边
    d.line(pts + [pts[0]], fill=(255, 255, 255, 210), width=2, joint="curve")
    # 高光（极淡）
    hi = [(cx - 0.30 * w, 0.42 * h), (cx - 0.26 * w, 0.58 * h), (cx - 0.22 * w, 0.70 * h)]
    d.line(hi, fill=(255, 255, 255, 90), width=5, joint="curve")
    return white_outline(v, 2)


def ceramic_bowl(w, h, body):
    b = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)
    d.ellipse((0, h * 0.18, w, h * 0.95), fill=body)
    d.ellipse((0, h * 0.06, w, h * 0.46), fill=tuple(min(255, c + 16) for c in body[:3]) + (255,))
    d.ellipse((0, h * 0.06, w, h * 0.46), outline=(255, 255, 255, 190), width=2)
    d.arc((0, h * 0.18, w, h * 0.95), 10, 170, fill=(255, 255, 255, 170), width=2)
    return white_outline(b, 2)


def dried_plant(name, width):
    """干花标本：降饱和成灰绿/裸棕，裁掉多余纸底，细白描边小卡。"""
    im = load(name).convert("RGB")
    im = ImageEnhance.Color(im).enhance(0.42)
    im = ImageEnhance.Brightness(im).enhance(1.06)
    im = fit(im, width).convert("RGBA")
    # 细白描边小卡
    pad = 10
    card = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (247, 246, 242, 255))
    card.alpha_composite(im, (pad, pad))
    d = ImageDraw.Draw(card)
    d.rectangle((0, 0, card.width - 1, card.height - 1), outline=(228, 225, 216, 220), width=2)
    return white_outline(card, 2)


def portrait_crop(width):
    """局部人像实拍：裁人物面部/上身局部，强降饱和成莫兰迪裸棕调，细白描边。"""
    im = load("poster-red-lips.jpg", POP).convert("RGB")
    # 人物在画面中部偏左，裁脸部区域
    iw, ih = im.size
    crop = im.crop((int(iw * 0.24), int(ih * 0.16), int(iw * 0.72), int(ih * 0.62)))
    crop = ImageEnhance.Color(crop).enhance(0.10)
    crop = ImageEnhance.Contrast(crop).enhance(0.86)
    crop = ImageEnhance.Brightness(crop).enhance(1.08)
    # 叠一层裸棕色统一色调（强制压成莫兰迪）
    crop = Image.blend(crop, Image.new("RGB", crop.size, (190, 178, 166)), 0.52)
    crop = fit(crop, width).convert("RGBA")
    pad = 9
    card = Image.new("RGBA", (crop.width + pad * 2, crop.height + pad * 2), (248, 247, 243, 255))
    card.alpha_composite(crop, (pad, pad))
    return white_outline(card, 3)


def handdoodle_layer():
    """极简手绘涂鸦层：纤细莫兰迪线条，稀疏落在留白缝隙，克制不堆砌。"""
    ly = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ly)
    G = (166, 164, 156, 130)   # 米灰
    S = (158, 172, 158, 125)   # 灰绿
    T = (182, 166, 152, 130)   # 裸棕

    def star(x, y, r, c):
        for k in range(4):
            a = k * math.pi / 2
            d.line((x, y, x + math.cos(a) * r, y + math.sin(a) * r), fill=c, width=2)

    def ring(x, y, r, c):
        pts = []
        for i in range(34):
            a = 2 * math.pi * i / 40 - 0.7
            rr = r + random.uniform(-1.2, 1.2)
            pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
        d.line(pts, fill=c, width=2, joint="curve")

    def wave(x, y, w, c, amp=3.5):
        pts = [(x + t * w / 24, y + math.sin(t * math.pi / 3) * amp + random.uniform(-0.6, 0.6))
               for t in range(25)]
        d.line(pts, fill=c, width=2, joint="curve")

    def heart(x, y, s, c):
        pts = []
        for i in range(41):
            t = 2 * math.pi * i / 40
            hx = 16 * math.sin(t) ** 3
            hy = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
            pts.append((x + hx * s / 16, y - hy * s / 16 + random.uniform(-0.5, 0.5)))
        d.line(pts, fill=c, width=2, joint="curve")

    def sprig(x, y, s, c, rot=0):
        ca, sa = math.cos(rot), math.sin(rot)
        def P(px, py):
            return (x + px * ca - py * sa, y + px * sa + py * ca)
        d.line([P(0, s * 0.5), P(0, -s * 0.5)], fill=c, width=2)
        for k in range(3):
            py = s * (0.28 - k * 0.28)
            for side in (-1, 1):
                d.line([P(0, py), P(side * s * 0.18, py + s * 0.02),
                        P(side * s * 0.30, py - s * 0.12)], fill=c, width=2, joint="curve")

    def arrow(x, y, c):
        pts = [(x, y), (x + 18, y - 7), (x + 40, y - 5), (x + 54, y + 5)]
        d.line(pts, fill=c, width=2, joint="curve")
        d.line((x + 54, y + 5, x + 45, y + 3), fill=c, width=2)
        d.line((x + 54, y + 5, x + 50, y - 4), fill=c, width=2)

    def dotted(x, y, c):
        for i in range(6):
            px, py = x + i * 11, y + math.sin(i * 0.9) * 5
            d.ellipse((px - 1.5, py - 1.5, px + 1.5, py + 1.5), fill=c)

    # 标题周围
    star(150, 150, 11, G)
    ring(766, 158, 14, T)
    wave(240, 292, 90, S)
    # 右上照片上方留白
    sprig(650, 352, 34, S, rot=-0.3)
    # 中部横向通道（避开两侧标本卡）
    arrow(360, 772, T)
    heart(560, 782, 16, G)
    ring(686, 790, 10, S)
    # 两列照片之间的竖缝
    dotted(452, 884, G)
    # 底部横向通道
    wave(220, 1300, 96, S)
    star(400, 1312, 9, T)
    # 底部留白（避开落款与陶瓷）
    sprig(300, 1430, 30, S, rot=0.2)
    heart(486, 1440, 14, T)
    return ly


# ============ 背景：米白哑光纸 + 淡颗粒（不厚重斑驳） ============
bg = Image.new("RGBA", (W, H), (243, 241, 236, 255))
# 极淡暖灰渐变
gd = ImageDraw.Draw(bg)
for y in range(H):
    t = y / H
    c = (int(244 - 5 * t), int(242 - 5 * t), int(237 - 6 * t), 255)
    gd.line((0, y, W, y), fill=c)
# 细腻纸纹（paper-5 强淡化）
tex = cover(load("paper-5.jpg").convert("RGB"), (W, H))
tex = Image.blend(Image.new("RGB", (W, H), (243, 241, 236)), tex, 0.12)
bg = Image.alpha_composite(bg, tex.convert("RGBA"))
# 淡胶片颗粒
noise = Image.new("L", (W // 3, H // 3))
noise.putdata([random.randint(120, 138) for _ in range(noise.width * noise.height)])
noise = noise.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.4))
grain = Image.merge("RGBA", (noise, noise, noise, Image.new("L", (W, H), 12)))
bg = Image.alpha_composite(bg, grain)
canvas = bg

# ============ 大标题（纤细，非粗体） ============
title = text_layer("SLOW LIVING", F_THIN, 66, (112, 108, 100, 225), spacing=10)
place(canvas, title, 452, 150, shadow=False)
title_cn = text_layer("慢 生 活", F_CN, 30, (128, 124, 116, 205), spacing=6)
place(canvas, title_cn, 452, 214, shadow=False)
# 极小英文标签
tag = text_layer("a quiet moment  ·  no. 07", F_THIN_I, 17, INK_L)
place(canvas, tag, 452, 258, shadow=False)

# ============ 照片位：大、错落、疏朗、小角度 ============
photos = [
    ("frame",   252, 500, 358, 430, -4, 1),
    ("rounded", 668, 585, 330, 300,  5, 2),
    ("rounded", 258, 1035, 348, 375,  4, 3),
    ("frame",   672, 1160, 328, 395, -5, 4),
]
for shape, cx, cy, w, h, ang, seed in photos:
    place(canvas, photo_slot(shape, w, h, seed), cx, cy, ang)

# ============ 稀疏装饰：干花 / 陶瓷 / 局部人像 ============
# 干花标本（放留白边缘，不压照片）
plant1 = dried_plant("fern-3.jpg", 118)
place(canvas, plant1, 96, 700, -6)
plant2 = dried_plant("fern-2.jpg", 108)
place(canvas, plant2, 796, 705, 7)
# 局部人像（左下）
port = portrait_crop(150)
place(canvas, port, 120, 960, -5)
# 陶瓷器皿（程序绘制，缩小、放底部留白、不压照片）
vase = ceramic_vase(96, 138, (198, 186, 172, 255), seed=3)
place(canvas, vase, 780, 1500, 2)
bowl = ceramic_bowl(92, 60, (214, 206, 195, 255))
place(canvas, bowl, 690, 1530, -3)

# ============ 手绘涂鸦（留白缝隙，细线条，不压照片文字） ============
canvas = Image.alpha_composite(canvas, handdoodle_layer())

# ============ 极小纤细文字 ============
d = ImageDraw.Draw(canvas)
d.text((96, 320), "less, but better", font=ImageFont.truetype(F_THIN_I, 18), fill=INK_L)
d.text((742, 340), "01", font=ImageFont.truetype(F_THIN, 15), fill=INK_L)
d.text((742, 760), "02", font=ImageFont.truetype(F_THIN, 15), fill=INK_L)
d.text((700, 1010), "03", font=ImageFont.truetype(F_THIN, 15), fill=INK_L)
# 底部落款（居中偏左，避开右下陶瓷）
foot = text_layer("collect moments, not things", F_THIN_I, 18, INK_L)
place(canvas, foot, 385, 1544, shadow=False)
d.text((96, 1542), "INS", font=ImageFont.truetype(F_THIN, 14), fill=INK_L)

canvas.convert("RGB").save(OUT, quality=93)
print("saved", OUT, canvas.size)
