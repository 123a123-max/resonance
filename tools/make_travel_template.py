# -*- coding: utf-8 -*-
"""旅行复古手账拼贴 9:16 模板：牛皮纸做旧底 + 真实免费素材剪贴 + 绘制机票/地图/邮戳。

照片位为矩形系（撕边/拍立得/圆角/细框），尺寸大、随性错落倾斜，不裁切内容；
所有装饰素材与文字位于照片上层，保证展露不被遮挡。
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

random.seed(11)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "public", "assets", "collage")
OUT = os.path.join(ASSETS, "template-travel-journal.jpg")
POP = os.path.join(ASSETS, "popart")
W, H = 900, 1600

FONT_CN = "C:/Windows/Fonts/STKAITI.TTF"
FONT_CN_B = "C:/Windows/Fonts/simhei.ttf"
FONT_EN = "C:/Windows/Fonts/georgia.ttf"
FONT_EN_I = "C:/Windows/Fonts/georgiai.ttf"
FONT_EN_B = "C:/Windows/Fonts/arialbd.ttf"

INK = (86, 58, 36, 205)
INK_L = (120, 88, 58, 150)
CREAM = (244, 232, 208, 255)


def load(name, folder=None):
    d = folder or ASSETS
    return Image.open(os.path.join(d, name)).convert("RGBA")


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


def trim_transparent(im, margin=4):
    bb = im.getchannel("A").getbbox()
    if not bb:
        return im
    l, t, r, b = bb
    return im.crop((max(0, l - margin), max(0, t - margin),
                    min(im.width, r + margin), min(im.height, b + margin)))


def torn_edges(im, seed=0, amp=6, step=13):
    """给素材加手撕毛边（保留内容）。"""
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


def round_crop(im, radius):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1),
                                        radius=radius, fill=255)
    im.putalpha(Image.composite(im.getchannel("A"), Image.new("L", im.size, 0), m))
    return im


def drop_shadow(layer, blur=8, alpha=75):
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new("RGBA", layer.size, (74, 52, 32, alpha))
    sh.putalpha(a)
    return sh


def place(canvas, layer, cx, cy, angle=0, shadow=True):
    if angle:
        layer = layer.rotate(angle, Image.BICUBIC, expand=True)
    x = int(cx - layer.width / 2)
    y = int(cy - layer.height / 2)
    if shadow:
        canvas.alpha_composite(drop_shadow(layer), (x + 5, y + 8))
    canvas.alpha_composite(layer, (x, y))
    return layer


def text_layer(txt, font_path, size, color, rot=0):
    f = ImageFont.truetype(font_path, size)
    box = f.getbbox(txt)
    w = box[2] - box[0] + 14
    h = box[3] - box[1] + 14
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((7 - box[0], 7 - box[1]), txt, font=f, fill=color)
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    return im


def jline(d, pts, fill=INK, width=2, jitter=1.4, seed=0):
    rnd = random.Random(seed)
    out = []
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 10))
        for k in range(n):
            t = k / n
            out.append((x1 + (x2 - x1) * t + rnd.uniform(-jitter, jitter),
                        y1 + (y2 - y1) * t + rnd.uniform(-jitter, jitter)))
    out.append(pts[-1])
    d.line(out, fill=fill, width=width, joint="curve")


def photo_slot(shape, w, h, seed):
    """矩形系照片位：撕边/拍立得/圆角/细框，不裁切照片内容。"""
    rnd = random.Random(seed)
    pad = 18
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    paper = (246, 235, 213, 255)
    edge = (186, 160, 126, 150)
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
        d.rectangle((pad + 9, pad + 9, pad + w - 9, pad + h - 9), outline=edge, width=1)
    elif shape == "polaroid":
        d.rectangle((pad, pad, pad + w, pad + h), fill=paper)
        d.rectangle((pad + 11, pad + 11, pad + w - 11, pad + h - 44), outline=edge, width=1)
        d.text((pad + 16, pad + h - 38), "remember this trip", font=ImageFont.truetype(FONT_EN_I, 15), fill=(130, 104, 76, 170))
    elif shape == "rounded":
        d.rounded_rectangle((pad, pad, pad + w, pad + h), radius=18, fill=paper)
        d.rounded_rectangle((pad + 9, pad + 9, pad + w - 9, pad + h - 9), radius=12, outline=edge, width=1)
    elif shape == "frame":
        d.rectangle((pad, pad, pad + w, pad + h), fill=paper)
        d.rectangle((pad + 7, pad + 7, pad + w - 7, pad + h - 7), outline=(134, 104, 70, 170), width=2)
        d.rectangle((pad + 13, pad + 13, pad + w - 13, pad + h - 13), outline=edge, width=1)
    return layer


def tape(canvas, x, y, w, h, angle, color=(184, 152, 105, 120)):
    t = Image.new("RGBA", (w, h), color)
    d = ImageDraw.Draw(t)
    for i in range(0, w, 7):
        d.line((i, 0, i, h), fill=(255, 246, 224, 55), width=1)
    place(canvas, t, x, y, angle, shadow=False)


def vintage_ticket(w, h, code=" boarding pass ", frm="NYC", to="PAR", seed=1):
    """绘制复古机票：奶白纸、齿孔虚线、粗体编号。"""
    t = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=8, fill=(240, 226, 198, 255),
                        outline=(128, 96, 62, 210), width=2)
    d.line((int(w * 0.68), 6, int(w * 0.68), h - 6), fill=(154, 122, 84, 190), width=1)
    for y in range(8, h - 6, 12):
        d.ellipse((int(w * 0.68) - 2, y - 2, int(w * 0.68) + 2, y + 2), fill=(214, 196, 164, 255))
    f1 = ImageFont.truetype(FONT_EN_B, 14)
    f2 = ImageFont.truetype(FONT_EN_I, 17)
    f3 = ImageFont.truetype(FONT_EN, 12)
    d.text((12, 9), "AIR TICKET", font=f1, fill=INK)
    d.text((12, 30), frm + "  >  " + to, font=f2, fill=(110, 72, 42, 235))
    d.text((12, h - 24), code.strip().upper(), font=f3, fill=(120, 90, 60, 200))
    d.text((int(w * 0.68) + 12, 12), "NO.", font=f3, fill=INK_L)
    d.text((int(w * 0.68) + 12, 30), "0%d7" % seed, font=f1, fill=INK)
    return torn_edges(t, seed=seed + 30, amp=3, step=20)


def map_fragment(w, h, seed=2):
    """绘制城市地图碎片：网格路网 + 虚线路线 + X 标记。"""
    rnd = random.Random(seed)
    m = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(m)
    d.rectangle((0, 0, w - 1, h - 1), fill=(236, 222, 194, 248), outline=(140, 106, 70, 200), width=2)
    # 不规则路网
    for i in range(6):
        y = rnd.randint(10, h - 10)
        jline(d, [(rnd.randint(0, 12), y), (w - rnd.randint(0, 12), y + rnd.randint(-5, 5))],
              fill=(168, 138, 100, 150), width=1, jitter=1.2, seed=seed + i)
    for i in range(5):
        x = rnd.randint(10, w - 10)
        jline(d, [(x, rnd.randint(0, 10)), (x + rnd.randint(-5, 5), h - rnd.randint(0, 10))],
              fill=(168, 138, 100, 150), width=1, jitter=1.2, seed=seed + 20 + i)
    # 虚线路线
    pts = [(18, h - 22), (w * 0.35, h * 0.55), (w * 0.62, h * 0.68), (w - 20, 20)]
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        steps = int(math.hypot(x2 - x1, y2 - y1) / 9)
        for k in range(steps):
            t = k / steps
            d.ellipse((x1 + (x2 - x1) * t - 1.3, y1 + (y2 - y1) * t - 1.3,
                       x1 + (x2 - x1) * t + 1.3, y1 + (y2 - y1) * t + 1.3), fill=(164, 62, 42, 220))
    d.text((12, 7), "CITY MAP", font=ImageFont.truetype(FONT_EN_B, 11), fill=INK)
    d.line((w - 32, h - 18, w - 18, h - 32), fill=(164, 62, 42, 230), width=2)
    d.line((w - 18, h - 18, w - 32, h - 32), fill=(164, 62, 42, 230), width=2)
    return torn_edges(m, seed=seed + 40, amp=3, step=18)


def postmark(size=104, text="TRAVEL 2026", seed=3):
    """绘制复古邮戳：双圈 + 波浪注销线 + 年份文字。"""
    p = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(p)
    ink = (138, 56, 40, 165)
    c = size // 2
    d.ellipse((8, 8, size - 8, size - 8), outline=ink, width=3)
    d.ellipse((17, 17, size - 17, size - 17), outline=ink, width=1)
    f = ImageFont.truetype(FONT_EN_B, 13)
    bb = d.textbbox((0, 0), text, font=f)
    d.text((c - (bb[2] - bb[0]) / 2, c - 24), text, font=f, fill=ink)
    d.text((c - 26, c + 2), "POST", font=ImageFont.truetype(FONT_EN_B, 15), fill=ink)
    for i in range(3):
        y = c + 24 + i * 7
        pts = [(12 + k, y + 3 * math.sin(k / 7.0)) for k in range(0, size - 24, 5)]
        d.line(pts, fill=ink, width=2)
    return p.rotate(random.Random(seed).uniform(-18, 18), Image.BICUBIC, expand=True)


# ============ 背景：牛皮纸做旧 ============
bg = cover(load("paper-4.jpg").convert("RGB"), (W, H))
bg = Image.blend(bg, Image.new("RGB", (W, H), (203, 171, 124)), 0.42)
# 斑驳做旧
stain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(stain)
rnd = random.Random(5)
for _ in range(60):
    x, y = rnd.randint(0, W), rnd.randint(0, H)
    r = rnd.randint(35, 150)
    sd.ellipse((x - r, y - r, x + r, y + r), fill=(126, 88, 52, rnd.randint(4, 14)))
stain = stain.filter(ImageFilter.GaussianBlur(26))
bg = Image.alpha_composite(bg.convert("RGBA"), stain)
# 老式印刷颗粒
noise = Image.new("L", (W // 3, H // 3))
noise.putdata([random.randint(96, 158) for _ in range(noise.width * noise.height)])
noise = noise.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.4))
grain = Image.merge("RGBA", (noise, noise, noise, Image.new("L", (W, H), 26)))
bg = Image.alpha_composite(bg, grain)
canvas = bg

# ============ 淡化底层：旧纸片叠层 ============
under = load("paper-5.jpg")
under = torn_edges(fit(under, 430), seed=71, amp=9)
under.putalpha(under.getchannel("A").point(lambda a: int(a * 0.45)))
place(canvas, under, 120, 470, -8, shadow=False)
under2 = load("paper-7.jpg")
under2 = torn_edges(fit(under2, 300), seed=72, amp=8)
under2.putalpha(under2.getchannel("A").point(lambda a: int(a * 0.38)))
place(canvas, under2, 786, 1210, 9, shadow=False)

# ============ 照片位：大、随性错落 ============
photos = [
    ("torn",     226, 430, 340, 398, -13, 1),
    ("polaroid", 668, 415, 372, 272,  10, 2),
    ("rounded",  248, 965, 355, 372,   8, 3),
    ("frame",    676, 975, 345, 398, -12, 4),
]
for shape, cx, cy, w, h, ang, seed in photos:
    place(canvas, photo_slot(shape, w, h, seed), cx, cy, ang)

# ============ 装饰素材（照片上层） ============
# 复古 Chicago 海报碎片（旧明信片感）
post = torn_edges(fit(load("chicago-neon.jpg", POP), 168), seed=12, amp=5)
place(canvas, post, 758, 178, 8)

# 城市快照 → 旅行明信片小卡
postcard = round_crop(fit(load("city-ny-1.jpg", POP), 148), 6)
place(canvas, postcard, 116, 636, -9)

# 城市天际线 → 街景快照小卡
city = round_crop(fit(load("city-chicago.jpg", POP), 150), 8)
place(canvas, city, 782, 1310, 6)

# 复古标本标签 → 行李标签
lab = torn_edges(fit(load("label-herbarium-16.jpg"), 152), seed=14, amp=4)
place(canvas, lab, 126, 1265, -7)

# 邮票两枚（带齿孔感的旧邮票）
st1 = fit(load("stamp-2.jpg"), 88)
place(canvas, st1, 88, 152, -12)
st2 = fit(load("stamp-5.jpg"), 76)
place(canvas, st2, 828, 690, 13)

# 手写纸碎片（浅淡做底，避免压在照片上显脏）
hand = fit(load("hand-1.jpg"), 130)
hand.putalpha(hand.getchannel("A").point(lambda a: int(a * 0.34)))
place(canvas, torn_edges(hand, seed=15, amp=4), 806, 1210, -6, shadow=False)

# ============ 绘制装饰：机票 / 地图 / 邮戳 ============
ticket = vintage_ticket(272, 78, code="TRAVEL 07", frm="NYC", to="PAR", seed=4)
place(canvas, ticket, 462, 628, -4)

mfrag = map_fragment(146, 112, seed=5)
place(canvas, mfrag, 742, 652, 7)

pm = postmark(112, "TRAVEL 2026", seed=6)
place(canvas, pm, 300, 682, shadow=False)

pm2 = postmark(86, "JOURNEY", seed=8)
place(canvas, pm2, 800, 1470, shadow=False)

# 胶带：贴合照片边角
tape(canvas, 168, 268, 78, 22, -22)
tape(canvas, 596, 286, 74, 22, 16)
tape(canvas, 152, 802, 72, 20, -14)
tape(canvas, 574, 832, 76, 22, 12)

# ============ 手绘线条：路线、箭头、星 ============
d = ImageDraw.Draw(canvas)
# 虚线旅行路线
jline(d, [(92, 1100), (150, 1180), (120, 1290)], fill=(158, 72, 48, 150), width=2, seed=31)
for (x, y) in [(96, 1100), (150, 1180), (120, 1290)]:
    d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(158, 72, 48, 190))
# 箭头指向海报
jline(d, [(628, 196), (658, 182), (690, 190)], fill=INK_L, width=2, seed=32)
d.line((690, 190, 682, 182), fill=INK_L, width=2)
d.line((690, 190, 681, 197), fill=INK_L, width=2)
# 小星星
for sx, sy, sr in [(84, 470, 11), (842, 520, 9), (96, 930, 8), (840, 1150, 10)]:
    for a in (0, math.pi / 2, math.pi / 4, -math.pi / 4):
        rr = sr if a % math.pi < 0.1 else sr * 0.6
        d.line((sx - rr * math.cos(a), sy - rr * math.sin(a),
                sx + rr * math.cos(a), sy + rr * math.sin(a)), fill=(146, 86, 52, 160), width=2)

# ============ 文字（最上层） ============
# 大标题
title = text_layer("旅途手记", FONT_CN_B, 76, (92, 56, 32, 245), rot=-2)
place(canvas, title, 430, 112, shadow=False)
en = text_layer("TRAVEL NOTES  ·  MEMORY ALBUM", FONT_EN_I, 25, (128, 84, 50, 225), rot=-1)
place(canvas, en, 448, 172, shadow=False)
# 标题下手写小字
sub = text_layer("把路过的风景，都收进这本旧相册", FONT_CN, 27, (116, 76, 46, 220), rot=-1)
place(canvas, sub, 430, 224, shadow=False)

# 底部手写日记文字
note1 = text_layer("一路向西 · 风里有远方的味道", FONT_CN, 29, (104, 68, 42, 235), rot=-2)
place(canvas, note1, 392, 1392, shadow=False)
note2 = text_layer("Day 07  —  on the road again", FONT_EN_I, 22, (124, 84, 52, 220), rot=-1)
place(canvas, note2, 410, 1440, shadow=False)
note3 = text_layer("SOMEWHERE  ·  2026", FONT_EN_B, 18, (130, 90, 56, 200), rot=1)
place(canvas, note3, 400, 1520, shadow=False)

canvas.convert("RGB").save(OUT, quality=92)
print("saved", OUT, canvas.size)
