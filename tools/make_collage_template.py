# -*- coding: utf-8 -*-
"""用免费授权素材合成「清新绿调森系手账拼贴」照片模板（9:16）。

照片位一律保持矩形系（撕边/拍立得/圆角/细框），不裁切照片内容；
另行手绘一批线条涂鸦填补留白。
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

random.seed(7)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "public", "assets", "collage")
OUT = os.path.join(ASSETS, "template-forest-green.jpg")
W, H = 900, 1600
FONT_CN = "C:/Windows/Fonts/STKAITI.TTF"
FONT_EN = "C:/Windows/Fonts/georgia.ttf"
FONT_EN_I = "C:/Windows/Fonts/georgiai.ttf"
INK = (92, 108, 86, 165)


def load(name):
    return Image.open(os.path.join(ASSETS, name)).convert("RGBA")


def cover(im, size):
    iw, ih = im.size
    sw, sh = size
    s = max(sw / iw, sh / ih)
    im = im.resize((int(iw * s) + 1, int(ih * s) + 1), Image.LANCZOS)
    x = (im.width - sw) // 2
    y = (im.height - sh) // 2
    return im.crop((x, y, x + sw, y + sh))


def white_to_alpha(im, lo=222, hi=252):
    """把白底转透明，保留墨线与色彩。"""
    px = list(im.getdata())
    out = []
    for r, g, b, a in px:
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        if lum >= hi:
            na = 0
        elif lum <= lo:
            na = a
        else:
            na = int(a * (hi - lum) / (hi - lo))
        out.append((r, g, b, na))
    im.putdata(out)
    return im


def fit(im, w, h=None):
    if h is None:
        h = im.height * w / im.width
    s = min(w / im.width, h / im.height)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)


def cut_by_channel(im, channel, low, high, feather=0.7, invert=False):
    """按 HSV 的 V（亮度）或 S（饱和度）通道抠出植物主体，去掉米色纸底。

    蕨叶等深色标本用 'V'（暗的留下）；彩色花朵用 'S'（鲜艳的留下）。
    low/high 之间做软过渡，feather 轻微羽化边缘。
    """
    rgb = im.convert("RGB")
    ch = rgb.convert("HSV").split()[0 if channel == "V" else 1]
    if invert:
        lut = [255 if x <= low else (0 if x >= high else int(255 * (x - low) / (high - low)))
               for x in range(256)]
    else:
        lut = [0 if x <= low else (255 if x >= high else int(255 * (x - low) / (high - low)))
               for x in range(256)]
    a = ch.point(lut).filter(ImageFilter.GaussianBlur(feather))
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out


def trim_transparent(im, margin=6):
    """裁掉周围透明区域，只留主体。"""
    bb = im.getchannel("A").getbbox()
    if not bb:
        return im
    l, t, r, b = bb
    return im.crop((max(0, l - margin), max(0, t - margin),
                    min(im.width, r + margin), min(im.height, b + margin)))


def round_crop(im, radius):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1),
                                           radius=radius, fill=255)
    alpha = im.getchannel("A")
    im.putalpha(Image.composite(alpha, Image.new("L", im.size, 0), mask))
    return im


def drop_shadow(layer, blur=9, alpha=70):
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new("RGBA", layer.size, (78, 72, 58, alpha))
    sh.putalpha(a)
    return sh


def place(canvas, layer, cx, cy, angle=0, shadow=True):
    if angle:
        layer = layer.rotate(angle, Image.BICUBIC, expand=True)
    x = int(cx - layer.width / 2)
    y = int(cy - layer.height / 2)
    if shadow:
        canvas.alpha_composite(drop_shadow(layer), (x + 6, y + 9))
    canvas.alpha_composite(layer, (x, y))


def photo_slot(shape, w, h, seed):
    """矩形系照片位：撕边 / 拍立得 / 圆角 / 细框，均不裁切照片内容。"""
    rnd = random.Random(seed)
    pad = 18
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    paper = (252, 250, 243, 255)
    edge = (214, 210, 196, 110)
    if shape == "torn":
        pts = []
        for x in range(pad, pad + w + 1, 15):
            pts.append((x, pad + rnd.randint(-5, 5)))
        for y in range(pad, pad + h + 1, 15):
            pts.append((pad + w + rnd.randint(-5, 5), y))
        for x in range(pad + w, pad - 1, -15):
            pts.append((x, pad + h + rnd.randint(-5, 5)))
        for y in range(pad + h, pad - 1, -15):
            pts.append((pad + rnd.randint(-5, 5), y))
        d.polygon(pts, fill=paper)
        d.rectangle((pad + 10, pad + 10, pad + w - 10, pad + h - 10), outline=edge, width=1)
    elif shape == "polaroid":
        d.rectangle((pad, pad, pad + w, pad + h), fill=paper)
        d.rectangle((pad + 12, pad + 12, pad + w - 12, pad + h - 46), outline=edge, width=1)
    elif shape == "rounded":
        d.rounded_rectangle((pad, pad, pad + w, pad + h), radius=20, fill=paper)
        d.rounded_rectangle((pad + 10, pad + 10, pad + w - 10, pad + h - 10),
                            radius=14, outline=edge, width=1)
    elif shape == "frame":
        d.rectangle((pad, pad, pad + w, pad + h), fill=paper)
        d.rectangle((pad + 8, pad + 8, pad + w - 8, pad + h - 8), outline=(176, 172, 156, 150), width=2)
        d.rectangle((pad + 14, pad + 14, pad + w - 14, pad + h - 14), outline=edge, width=1)
    return layer


def washi(canvas, x, y, w, h, angle, color=(126, 156, 118, 130)):
    t = Image.new("RGBA", (w, h), color)
    d = ImageDraw.Draw(t)
    for i in range(0, w, 7):
        d.line((i, 0, i, h), fill=(255, 255, 255, 45), width=1)
    place(canvas, t, x, y, angle, shadow=False)


def text_layer(txt, font_path, size, color, rot=0):
    f = ImageFont.truetype(font_path, size)
    box = f.getbbox(txt)
    w = box[2] - box[0] + 12
    h = box[3] - box[1] + 12
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((6 - box[0], 6 - box[1]), txt, font=f, fill=color)
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    return im


# ---------- 手绘线条涂鸦 ----------
def jline(d, pts, fill=INK, width=2, jitter=1.6, seed=0):
    """带轻微抖动的线段，模拟手绘。"""
    rnd = random.Random(seed)
    out = []
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 11))
        for k in range(n):
            t = k / n
            out.append((x1 + (x2 - x1) * t + rnd.uniform(-jitter, jitter),
                        y1 + (y2 - y1) * t + rnd.uniform(-jitter, jitter)))
    out.append(pts[-1])
    d.line(out, fill=fill, width=width, joint="curve")


def d_arrow(d, x, y, length, angle, seed=0):
    a = math.radians(angle)
    ex, ey = x + length * math.cos(a), y + length * math.sin(a)
    mx, my = x + length * 0.55 * math.cos(a - 0.18), y + length * 0.55 * math.sin(a - 0.18)
    jline(d, [(x, y), (mx, my), (ex, ey)], seed=seed)
    for da in (2.55, -2.55):
        jline(d, [(ex, ey), (ex + 22 * math.cos(a + da), ey + 22 * math.sin(a + da))],
              width=2, seed=seed + 1)


def d_star(d, x, y, r=13, seed=0):
    for a in (0, math.pi / 2, math.pi / 4, -math.pi / 4):
        rr = r if a % (math.pi) < 0.1 else r * 0.62
        jline(d, [(x - rr * math.cos(a), y - rr * math.sin(a)),
                  (x + rr * math.cos(a), y + rr * math.sin(a))],
              width=2, jitter=1.1, seed=seed)
    d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=INK)


def d_wave(d, x, y, w, amp=6, seed=0, width=2):
    pts = [(x + i, y + amp * math.sin(i / 13.0)) for i in range(0, w, 9)]
    jline(d, pts, width=width, jitter=0.9, seed=seed)


def d_loop(d, x, y, rx, ry, seed=0):
    pts = [(x + rx * math.cos(a), y + ry * math.sin(a))
           for a in [i * 2 * math.pi / 24 for i in range(25)]]
    jline(d, pts, width=2, jitter=1.8, seed=seed)


def d_dotted(d, pts, seed=0, step=13):
    rnd = random.Random(seed)
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        n = int(math.hypot(x2 - x1, y2 - y1) / step)
        for k in range(n):
            t = (k + 0.4) / n
            x = x1 + (x2 - x1) * t + rnd.uniform(-1.5, 1.5)
            y = y1 + (y2 - y1) * t + rnd.uniform(-1.5, 1.5)
            d.ellipse((x - 1.6, y - 1.6, x + 1.6, y + 1.6), fill=INK)


def d_sprig(d, x, y, scale=1.0, seed=0):
    """手绘小枝叶。"""
    jline(d, [(x, y + 70 * scale), (x - 3 * scale, y + 35 * scale), (x + 2 * scale, y)],
          width=2, seed=seed)
    for i, fy in enumerate([0.72, 0.54, 0.36, 0.2]):
        ly = y + 70 * scale * fy
        for side in (-1, 1):
            lx = x + side * (16 + i * 2) * scale
            jline(d, [(x, ly), (lx, ly - 9 * scale)], width=2, seed=seed + i * 2 + (side + 1))
            jline(d, [(lx, ly - 9 * scale), (lx + side * 9 * scale, ly - 14 * scale)],
                  width=2, seed=seed + i * 2 + side)
            jline(d, [(lx, ly - 9 * scale), (lx + side * 6 * scale, ly - 1 * scale)],
                  width=2, seed=seed + i * 3 + side)


def d_heart(d, x, y, r=11, seed=0):
    pts = []
    for a in [i * 2 * math.pi / 40 for i in range(41)]:
        px = 16 * math.sin(a) ** 3
        py = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        pts.append((x + px * r / 16, y + py * r / 16))
    jline(d, pts, width=2, jitter=0.9, seed=seed)


# ---------- 背景纸 ----------
bg = load("paper-7.jpg").convert("RGB")
bg = cover(bg, (W, H))
bg = Image.blend(bg, Image.new("RGB", (W, H), (230, 231, 216)), 0.62)
glow = Image.new("L", (W, H), 0)
gd = ImageDraw.Draw(glow)
gd.ellipse((-180, -120, W + 180, H + 120), fill=210)
glow = glow.filter(ImageFilter.GaussianBlur(190))
bg = Image.composite(Image.new("RGB", (W, H), (247, 246, 236)), bg, glow)
canvas = bg.convert("RGBA")

grain = load("grain-5.jpg").convert("L").resize((W, H))
grain = Image.blend(Image.new("L", (W, H), 128), grain, 0.16)
gn = Image.merge("RGB", (grain, grain, grain))
canvas = Image.blend(canvas.convert("RGB"), gn, 0.10).convert("RGBA")

# 活页孔
hd = ImageDraw.Draw(canvas)
for y in [140, 430, 720, 1010, 1300, 1480]:
    hd.ellipse((14, y - 15, 44, y + 15), fill=(188, 186, 172, 255))
    hd.ellipse((18, y - 11, 40, y + 11), fill=(150, 148, 136, 255))
    hd.arc((18, y - 11, 40, y + 11), 200, 340, fill=(238, 237, 227, 200), width=2)

# ---------- 照片位：矩形系，随性错落，不裁内容 ----------
photos = [
    ("torn",     228, 322, 345, 410, -16, 1),   # 撕边竖版：左上、左倾（收进画布）
    ("polaroid", 672, 340, 380, 280,  14, 2),   # 拍立得横版：右上、右倾（收进画布）
    ("rounded",  224, 888, 360, 380,  12, 3),   # 圆角方版：左下、右倾
    ("frame",    665, 872, 350, 410, -16, 4),   # 细框竖版：右下、左倾
]
for shape, cx, cy, w, h, ang, seed in photos:
    place(canvas, photo_slot(shape, w, h, seed), cx, cy, ang)

# ---------- 素材：形状多变，放上层确保展露 ----------
# 蕨叶：fern-1 印在深色残旧纸上、纸底分不开，改从 fern-2 裁一支清晰的单叶
# 叶片是深绿色、纸底灰白，用饱和度通道抠可完全去纸底
fern_src = load("fern-2.jpg").crop((28, 18, 112, 480))
fern1 = cut_by_channel(fern_src, "S", 45, 100)
fern1 = fit(trim_transparent(fern1), 112)
place(canvas, fern1, 100, 528, -15)

# 第二片蕨叶：四支并列标本，同样按饱和度抠掉纸底
fern2 = cut_by_channel(load("fern-2.jpg"), "S", 45, 100)
fern2 = fit(trim_transparent(fern2), 150)
place(canvas, fern2, 815, 585, 10)

# 百合：橙色花朵，按饱和度抠出花形轮廓（S 通道，鲜艳保留）
lily = cut_by_channel(load("lily-2.jpg"), "S", 55, 145)
lily = fit(trim_transparent(lily), 205)
place(canvas, lily, 818, 1290, 9)

# 雏菊：花很小且偏顶部，先裁到花的区域、增强对比与色彩，再按饱和度抠
from PIL import ImageEnhance
daisy_src = load("daisy-2.jpg").crop((190, 20, 375, 150)).convert("RGB")
daisy_src = ImageEnhance.Color(daisy_src).enhance(1.8)
daisy_src = ImageEnhance.Contrast(daisy_src).enhance(1.5)
daisy = cut_by_channel(daisy_src, "S", 22, 78)
daisy = fit(trim_transparent(daisy), 140)
place(canvas, daisy, 122, 1332, -9)

lab1 = round_crop(fit(load("label-herbarium-14.jpg"), 345), 10)
place(canvas, lab1, 300, 115, -3)

lab2 = round_crop(fit(load("label-herbarium-16.jpg"), 300), 12)
place(canvas, lab2, 665, 1370, 4)

st1 = white_to_alpha(load("stamp-2.jpg"), 232, 252)
st1 = fit(st1, 170)
place(canvas, st1, 755, 118, 9)

st2 = white_to_alpha(load("stamp-5.jpg"), 232, 252)
st2 = fit(st2, 140)
place(canvas, st2, 168, 1495, -8)

# 金属夹
clip = Image.new("RGBA", (96, 34), (0, 0, 0, 0))
cd = ImageDraw.Draw(clip)
cd.rounded_rectangle((2, 2, 94, 32), radius=15, outline=(120, 124, 120, 255), width=4)
cd.rounded_rectangle((14, 10, 82, 24), radius=7, fill=(198, 202, 196, 255))
cd.ellipse((30, 13, 42, 25), fill=(150, 154, 150, 255))
cd.ellipse((54, 13, 66, 25), fill=(150, 154, 150, 255))
place(canvas, clip, 450, 34, 0)

# 胶带（压在照片角上，展露）
washi(canvas, 160, 172, 80, 24, -24)
washi(canvas, 360, 528, 72, 22, 16)
washi(canvas, 540, 232, 76, 24, 14)
washi(canvas, 795, 475, 70, 22, -14)
washi(canvas, 148, 672, 74, 22, -16)
washi(canvas, 360, 1015, 72, 22, 18)
washi(canvas, 520, 668, 74, 22, 12)
washi(canvas, 805, 1030, 70, 22, -16)

# ---------- 手绘涂鸦层（填补留白，不压照片主体） ----------
doodle = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(doodle)
# 顶部
d_arrow(d, 552, 150, 105, -25, seed=1)
d_wave(d, 462, 182, 120, seed=2)
d_star(d, 838, 222, 12, seed=3)
# 照片缝隙与边缘
d_dotted(d, [(452, 288), (458, 520), (445, 700), (452, 1040)], seed=4)
d_star(d, 452, 590, 10, seed=5)
d_star(d, 450, 742, 8, seed=6)
d_loop(d, 795, 258, 34, 52, seed=7)
d_sprig(d, 84, 430, 0.75, seed=8)
d_wave(d, 818, 748, 62, seed=9)
d_arrow(d, 128, 700, 78, 38, seed=10)
# 文字区
d_wave(d, 58, 1145, 340, amp=3, seed=11, width=2)
d_wave(d, 58, 1202, 275, amp=3, seed=12, width=2)
d_heart(d, 432, 1178, 10, seed=13)
d_star(d, 452, 1242, 9, seed=14)
d_wave(d, 90, 1272, 410, amp=4, seed=15)
d_sprig(d, 470, 1425, 0.85, seed=16)
d_sprig(d, 822, 1465, 0.7, seed=17)
d_dotted(d, [(360, 1505), (430, 1490), (470, 1508)], seed=18, step=11)
d_wave(d, 468, 1565, 300, amp=3, seed=19, width=2)
d_star(d, 832, 1520, 10, seed=20)
canvas.alpha_composite(doodle)

# ---------- 文字（最上层，确保展露） ----------
t1 = text_layer("林间散步 · 风里有青草的味道", FONT_CN, 30, (74, 86, 66, 240), -2)
place(canvas, t1, 225, 1112, 0, shadow=False)

t2 = text_layer("把秋天收进本子里", FONT_CN, 32, (74, 86, 66, 240), -2)
place(canvas, t2, 170, 1172, 0, shadow=False)

t3 = text_layer("FOREST NOTES  ·  DAILY LIFE", FONT_EN_I, 20, (104, 112, 92, 230), -1)
place(canvas, t3, 300, 1240, 0, shadow=False)

t4 = text_layer("日子慢慢过，也挺甜", FONT_CN, 28, (74, 86, 66, 240), -2)
place(canvas, t4, 610, 1530, 0, shadow=False)

# 柔光收尾
final = canvas.convert("RGB")
soft = final.filter(ImageFilter.GaussianBlur(22))
final = Image.blend(final, soft, 0.10)
final.save(OUT, quality=92)
print("saved:", OUT, final.size)
