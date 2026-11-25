# -*- coding: utf-8 -*-
"""美式复古杂志拼贴 9:16 模板：60-70年代欧美时尚杂志内页、多层剪贴叠加。

焦糖/正红/宝蓝撞色、泛黄牛皮纸底、复古网点印刷、老式颗粒；
复古人像 + 老广告 + 英文复古标语 + 超大粗体标题；撕纸毛边、粗轮廓。
照片位矩形系（撕边/拍立得/细框/圆角）尺寸大、随性错落倾斜、不裁内容；
所有装饰素材与文字位于照片上层，保证展露不被遮挡。
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops

random.seed(33)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "public", "assets", "collage")
POP = os.path.join(ASSETS, "popart")
OUT = os.path.join(ASSETS, "template-american-retro.jpg")
W, H = 900, 1600

FONT_IMPACT = "C:/Windows/Fonts/impact.ttf"
FONT_EN_B = "C:/Windows/Fonts/arialbd.ttf"
FONT_EN_I = "C:/Windows/Fonts/georgiai.ttf"
FONT_EN = "C:/Windows/Fonts/georgia.ttf"
FONT_CN = "C:/Windows/Fonts/simhei.ttf"

CARAMEL = (172, 96, 46, 255)
RED = (184, 40, 34, 255)
BLUE = (36, 58, 132, 255)
CREAM = (240, 224, 188, 255)
INK = (54, 34, 22, 245)
BLACK = (26, 22, 18, 255)


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


def torn_edges(im, seed=0, amp=6, step=13):
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
    m = m.filter(ImageFilter.GaussianBlur(0.6))
    out = im.copy()
    out.putalpha(Image.composite(out.getchannel("A"), Image.new("L", (w, h), 0), m))
    return out


def outline(layer, color=BLACK, width=4):
    """粗黑轮廓（波普剪贴感）。"""
    a = layer.getchannel("A")
    grow = a.filter(ImageFilter.MaxFilter(width * 2 + 1))
    inner_w = width if width % 2 == 1 else max(1, width - 1)
    inner = a.filter(ImageFilter.MaxFilter(inner_w))
    ring = ImageChops.subtract(grow, inner)
    r = Image.new("RGBA", layer.size, color)
    r.putalpha(ring)
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(r)
    out.alpha_composite(layer)
    return out


def drop_shadow(layer, blur=7, alpha=82):
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new("RGBA", layer.size, (52, 34, 18, alpha))
    sh.putalpha(a)
    return sh


def place(canvas, layer, cx, cy, angle=0, shadow=True):
    if angle:
        layer = layer.rotate(angle, Image.BICUBIC, expand=True)
    x = int(cx - layer.width / 2)
    y = int(cy - layer.height / 2)
    if shadow:
        canvas.alpha_composite(drop_shadow(layer), (x + 5, y + 7))
    canvas.alpha_composite(layer, (x, y))
    return layer


def text_layer(txt, font_path, size, color, rot=0, stroke=0, spacing=0):
    f = ImageFont.truetype(font_path, size)
    if spacing:
        widths = [f.getlength(ch) for ch in txt]
        total = sum(widths) + spacing * (len(txt) - 1)
        im = Image.new("RGBA", (int(total) + 20, size + 28), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        x = 10
        for ch, wch in zip(txt, widths):
            d.text((x, 10), ch, font=f, fill=color,
                   stroke_width=stroke, stroke_fill=BLACK)
            x += wch + spacing
    else:
        box = d0 = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), txt, font=f)
        w = box[2] - box[0] + 20
        h = box[3] - box[1] + 28
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.text((10 - box[0], 10 - box[1]), txt, font=f, fill=color,
               stroke_width=stroke, stroke_fill=BLACK)
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    return im


def halftone(size, cell=8, dot=2, color=(60, 40, 24, 46)):
    ly = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ly)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            d.ellipse((x, y, x + dot, y + dot), fill=color)
    return ly


def color_block(w, h, color, seed, amp=7):
    """撕边撞色块。"""
    rnd = random.Random(seed)
    blk = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(blk)
    pts = []
    for x in range(0, w + 1, 18):
        pts.append((x, rnd.randint(0, amp)))
    for y in range(0, h + 1, 18):
        pts.append((w - rnd.randint(0, amp), y))
    for x in range(w, -1, -18):
        pts.append((x, h - rnd.randint(0, amp)))
    for y in range(h, -1, -18):
        pts.append((rnd.randint(0, amp), y))
    d.polygon(pts, fill=color)
    return blk


def retro_portrait(name, width, folder, tint, seed, cut=None, desat=0.62):
    """复古人像剪贴：低饱和做旧泛黄 + 网点 + 撕边 + 粗轮廓。"""
    im = load(name, folder).convert("RGB")
    if cut:
        iw, ih = im.size
        im = im.crop((int(iw * cut[0]), int(iw * cut[1]), int(iw * cut[2]), int(ih * cut[3])))
    im = ImageEnhance.Color(im).enhance(desat)
    im = ImageEnhance.Contrast(im).enhance(1.12)
    im = Image.blend(im, Image.new("RGB", im.size, tint), 0.16)
    im = fit(im, width).convert("RGBA")
    im.alpha_composite(halftone((im.width, im.height), cell=7, dot=2, color=(52, 34, 20, 34)))
    im = torn_edges(im, seed=seed, amp=6)
    return outline(im, BLACK, 4)


def retro_ad(name, width, seed, folder=None):
    """老广告/杂志封面碎片：做旧 + 网点 + 撕边 + 粗轮廓。"""
    im = load(name, folder).convert("RGB")
    im = ImageEnhance.Color(im).enhance(0.82)
    im = Image.blend(im, Image.new("RGB", im.size, (214, 186, 138)), 0.14)
    im = fit(im, width).convert("RGBA")
    im.alpha_composite(halftone((im.width, im.height), cell=6, dot=2, color=(60, 40, 22, 30)))
    im = torn_edges(im, seed=seed, amp=5)
    return outline(im, BLACK, 3)


def slogan_bar(w, h, text, bg, seed, fsize=26):
    """英文复古标语条：撞色底 + 粗体字 + 撕边 + 粗轮廓。"""
    bar = color_block(w, h, bg, seed, amp=4)
    d = ImageDraw.Draw(bar)
    f = ImageFont.truetype(FONT_IMPACT, fsize)
    bb = d.textbbox((0, 0), text, font=f)
    tw = bb[2] - bb[0]
    d.text(((w - tw) / 2, (h - fsize) / 2 - 3), text, font=f, fill=(248, 236, 208, 245))
    return outline(bar, BLACK, 3)


def photo_slot(shape, w, h, seed):
    """矩形系照片位：撕边/拍立得/细框/圆角，泛黄做旧，不裁内容。"""
    rnd = random.Random(seed)
    pad = 18
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    paper = (240, 226, 196, 255)
    edge = (150, 108, 64, 200)
    dark = (110, 74, 42, 200)
    if shape == "torn":
        pts = []
        for x in range(pad, pad + w + 1, 14):
            pts.append((x, pad + rnd.randint(-5, 5)))
        for y in range(pad, pad + h + 1, 14):
            pts.append((pad + w + rnd.randint(-5, 5), y))
        for x in range(pad + w, pad - 1, -14):
            pts.append((x, pad + h + rnd.randint(-5, 5)))
        for y in range(pad + h, pad - 1, -14):
            pts.append((pad + rnd.randint(-5, 5), y))
        d.polygon(pts, fill=paper)
        d.rectangle((pad + 9, pad + 9, pad + w - 9, pad + h - 9), outline=edge, width=2)
    elif shape == "polaroid":
        d.rectangle((pad, pad, pad + w, pad + h), fill=paper)
        d.rectangle((pad + 10, pad + 10, pad + w - 10, pad + h - 46), outline=dark, width=2)
        d.text((pad + 14, pad + h - 40), "a lovely day", font=ImageFont.truetype(FONT_EN_I, 16), fill=(120, 78, 44, 210))
    elif shape == "frame":
        d.rectangle((pad, pad, pad + w, pad + h), fill=paper)
        d.rectangle((pad + 6, pad + 6, pad + w - 6, pad + h - 6), outline=dark, width=4)
        d.rectangle((pad + 13, pad + 13, pad + w - 13, pad + h - 13), outline=edge, width=1)
    elif shape == "rounded":
        d.rounded_rectangle((pad, pad, pad + w, pad + h), radius=16, fill=paper)
        d.rounded_rectangle((pad + 8, pad + 8, pad + w - 8, pad + h - 8), radius=11, outline=dark, width=3)
    return outline(layer, BLACK, 3)


def tape(canvas, x, y, w, h, angle, color=(196, 158, 92, 150)):
    t = Image.new("RGBA", (w, h), color)
    d = ImageDraw.Draw(t)
    for i in range(0, w, 7):
        d.line((i, 0, i, h), fill=(255, 244, 216, 60), width=1)
    place(canvas, t, x, y, angle, shadow=False)


# ============ 背景：泛黄牛皮纸 + 斑驳 + 颗粒 + 网点 ============
bg = cover(load("paper-4.jpg").convert("RGB"), (W, H))
bg = Image.blend(bg, Image.new("RGB", (W, H), (214, 184, 132)), 0.40)
stain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(stain)
rnd = random.Random(7)
for _ in range(70):
    x, y = rnd.randint(0, W), rnd.randint(0, H)
    r = rnd.randint(40, 160)
    sd.ellipse((x - r, y - r, x + r, y + r), fill=(122, 80, 40, rnd.randint(5, 16)))
stain = stain.filter(ImageFilter.GaussianBlur(24))
bg = Image.alpha_composite(bg.convert("RGBA"), stain)
# 老式印刷颗粒
noise = Image.new("L", (W // 3, H // 3))
noise.putdata([random.randint(88, 160) for _ in range(noise.width * noise.height)])
noise = noise.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.4))
grain = Image.merge("RGBA", (noise, noise, noise, Image.new("L", (W, H), 28)))
bg = Image.alpha_composite(bg, grain)
# 全覆盖网点印刷
bg = Image.alpha_composite(bg, halftone((W, H), cell=9, dot=2, color=(74, 48, 24, 34)))
canvas = bg

# ============ 撞色色块（多层剪贴底层） ============
b1 = color_block(430, 300, CARAMEL, 41, amp=10)
place(canvas, b1, 150, 470, -9, shadow=False)
b2 = color_block(360, 250, BLUE, 42, amp=9)
place(canvas, b2, 790, 660, 8, shadow=False)
b3 = color_block(400, 210, RED, 43, amp=9)
place(canvas, b3, 470, 1180, 6, shadow=False)
b4 = color_block(230, 230, BLUE, 44, amp=8)
place(canvas, b4, 170, 1420, -7, shadow=False)

# ============ 底层旧纸片（叠层次） ============
under = torn_edges(fit(load("newspaper-times.jpg", POP), 300), seed=71, amp=8)
under.putalpha(under.getchannel("A").point(lambda a: int(a * 0.42)))
place(canvas, under, 748, 1320, 9, shadow=False)
under2 = torn_edges(fit(load("magazine-old.jpg", POP), 260), seed=72, amp=7)
under2.putalpha(under2.getchannel("A").point(lambda a: int(a * 0.46)))
place(canvas, under2, 132, 900, -8, shadow=False)

# ============ 照片位：大、随性错落 ============
photos = [
    ("torn",     224, 420, 350, 410, -14, 1),
    ("polaroid", 676, 405, 390, 290,  11, 2),
    ("rounded",  250, 995, 362, 385,   9, 3),
    ("frame",    668, 990, 352, 415, -12, 4),
]
for shape, cx, cy, w, h, ang, seed in photos:
    place(canvas, photo_slot(shape, w, h, seed), cx, cy, ang)

# ============ 复古人像剪贴（主角，完整露出） ============
# 墨镜西装男（港风）
man = retro_portrait("magazine-cover.jpg", 230, POP, (196, 158, 108), 12,
                     cut=(0.18, 0.02, 0.82, 0.72))
place(canvas, man, 152, 720, -8)
# 黄衣女星（复古广告感，强降饱和做旧）
woman = retro_portrait("poster-red-lips.jpg", 205, POP, (202, 166, 118), 13,
                       cut=(0.20, 0.10, 0.80, 0.78), desat=0.42)
place(canvas, woman, 762, 900, 8)

# ============ 老广告 / 杂志封面碎片 ============
# 城市街景快照（都市复古，替换深蓝书本块的突兀感）
ad1 = retro_ad("city-chicago.jpg", 158, 14, POP)
place(canvas, ad1, 786, 250, 7)
ad2 = retro_ad("label-herbarium-14.jpg", 165, 15)
place(canvas, ad2, 120, 1210, -9)
chicago = retro_ad("chicago-neon.jpg", 158, 16, POP)
place(canvas, chicago, 796, 1390, 8)

# ============ 英文复古标语条 ============
sg1 = slogan_bar(300, 62, "THE GOOD LIFE", RED, 51, fsize=30)
place(canvas, sg1, 470, 660, -4)
sg2 = slogan_bar(280, 58, "VINTAGE 1968", BLUE, 52, fsize=28)
place(canvas, sg2, 470, 1350, 5)
sg3 = slogan_bar(210, 50, "STYLE & GRACE", CARAMEL, 53, fsize=23)
place(canvas, sg3, 700, 1200, -7)

# ============ 邮票 / 标签小碎片 ============
st1 = torn_edges(fit(load("stamp-2.jpg"), 78), seed=17, amp=3)
place(canvas, st1, 820, 520, 12)
lab = torn_edges(fit(load("label-herbarium-16.jpg"), 128), seed=18, amp=4)
place(canvas, lab, 130, 1090, 6)

# ============ 胶带（贴合照片边角） ============
tape(canvas, 156, 236, 80, 24, -22)
tape(canvas, 600, 240, 76, 24, 15)
tape(canvas, 150, 800, 74, 22, -14)
tape(canvas, 586, 830, 76, 22, 12)

# ============ 绘制装饰：星芒 / 速度线 / 圆点 ============
d = ImageDraw.Draw(canvas)
for sx, sy, sr in [(84, 560, 12), (838, 760, 10), (96, 1330, 9), (846, 1100, 11)]:
    for a in (0, math.pi / 2, math.pi / 4, -math.pi / 4):
        rr = sr if a % math.pi < 0.1 else sr * 0.55
        d.line((sx - rr * math.cos(a), sy - rr * math.sin(a),
                sx + rr * math.cos(a), sy + rr * math.sin(a)), fill=(58, 38, 24, 200), width=3)
for i in range(4):
    y = 1430 + i * 14
    d.line((70, y, 150 - i * 7, y - 6), fill=(58, 38, 24, 200), width=4)
for i in range(3):
    y = 340 + i * 16
    d.line((772, y, 836 + i * 4, y - 8), fill=(58, 38, 24, 200), width=4)
for x, y in [(470, 810), (520, 826), (570, 810), (620, 826)]:
    d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(184, 40, 34, 200))

# ============ 文字（最上层） ============
# 超大粗体美式标题
title = text_layer("MODERN", FONT_IMPACT, 108, (238, 222, 184, 250), rot=-3, stroke=5, spacing=3)
place(canvas, title, 448, 118, shadow=False)
title2 = text_layer("LIFE", FONT_IMPACT, 116, (184, 40, 34, 250), rot=-2, stroke=5, spacing=4)
place(canvas, title2, 470, 232, shadow=False)
# 中文副标题
cn = text_layer("复古新时代", FONT_CN, 34, (246, 230, 196, 245), rot=-2, stroke=2)
place(canvas, cn, 452, 320, shadow=False)
# 底部标语
foot = text_layer("A MAGAZINE OF STYLE & TASTE", FONT_EN_B, 20, (240, 224, 190, 235), rot=-1)
place(canvas, foot, 452, 1536, shadow=False)

canvas.convert("RGB").save(OUT, quality=92)
print("saved", OUT, canvas.size)
