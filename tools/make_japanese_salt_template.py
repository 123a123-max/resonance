# -*- coding: utf-8 -*-
"""日系盐系胶片拼贴 9:16 模板：随性松散、生活化碎片、冷柔褪色胶片感。

灰蓝 + 浅草绿低饱和冷柔主色，整体轻微褪色、干净寡淡；
粗糙复古和纸底纹 + 全覆盖胶片褪色颗粒 + 四周柔和暗角 + 哑光复古；
不规则手撕纸边、细款和纸胶带、路边生活快照、咖啡杯、绿植枝叶、复古旧相机；
小巧手写体文字，无规整印刷字。
禁止：高饱和艳色、夸张卡通、厚重涂鸦、元素密密麻麻、强对比。
照片位坐标/角度与 src/collage/templateStyles.ts 的 japanese-salt slots 一致（全 torn）。
素材来自 public/assets/collage/pexels 各目录（授权见 pexels/SOURCES.json）。
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

random.seed(512)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "public", "assets", "collage")
PEX = os.path.join(ASSETS, "pexels")
JS = os.path.join(PEX, "japanese-salt")
GF = os.path.join(PEX, "green-fresh")
INS = os.path.join(PEX, "ins-minimal")
OUT = os.path.join(ASSETS, "template-japanese-salt.jpg")
W, H = 900, 1600

FONT_HAND = "C:/Windows/Fonts/segoesc.ttf"
FONT_KAI = "C:/Windows/Fonts/STXINGKA.TTF"
FONT_YOU = "C:/Windows/Fonts/SIMYOU.TTF"

# 日系盐系低饱和冷柔色
BLUE_GRAY = (126, 148, 160, 255)
SAGE = (154, 174, 148, 255)
PAPER = (232, 230, 220, 255)
INK = (96, 104, 104, 235)


def load(folder, name):
    return Image.open(os.path.join(folder, name)).convert("RGBA")


def fit(im, w):
    h = im.height * w / im.width
    return im.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)


def cover(im, size):
    iw, ih = im.size
    sw, sh = size
    s = max(sw / iw, sh / ih)
    im = im.resize((int(iw * s) + 1, int(ih * s) + 1), Image.LANCZOS)
    x = (im.width - sw) // 2
    y = (im.height - sh) // 2
    return im.crop((x, y, x + sw, y + sh))


def torn_edges(im, seed=0, amp=6, step=11):
    """不规则手撕纸边。"""
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


def faded(im, strength=0.55, tint=(214, 220, 214)):
    """胶片褪色：降饱和 + 轻微灰蓝灰绿罩色，干净寡淡。"""
    im = ImageEnhance.Color(im).enhance(strength)
    im = ImageEnhance.Contrast(im).enhance(0.92)
    return Image.blend(im, Image.new("RGB", im.size, tint), 0.12)


def paste(canvas, layer, cx, cy, angle=0, shadow=False):
    if angle:
        layer = layer.rotate(angle, Image.BICUBIC, expand=True)
    x = int(cx - layer.width / 2)
    y = int(cy - layer.height / 2)
    if shadow:
        a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(6))
        sh = Image.new("RGBA", layer.size, (86, 92, 92, 34))
        sh.putalpha(a)
        canvas.alpha_composite(sh, (x + 2, y + 3))
    canvas.alpha_composite(layer, (x, y))
    return layer


def snap(folder, name, width, seed, angle=0, tint=(214, 220, 214)):
    """生活快照剪片：褪色 + 手撕边，干净无粗描边。"""
    im = load(folder, name).convert("RGB")
    im = faded(im, 0.52, tint)
    im = fit(im, width).convert("RGBA")
    return torn_edges(im, seed=seed, amp=6)


def snap_crop(folder, name, w, h, seed, tint=(214, 220, 214), focus=(0.5, 0.5)):
    """按目标画幅裁剪素材（居中或偏向主体），褪色 + 撕边。
    focus=(fx,fy)：0~1，裁剪窗口在原图相对位置，用于把主体（脸/器物）留在框内。"""
    im = load(folder, name).convert("RGB")
    im = faded(im, 0.52, tint)
    im = cover_focus(im, (w, h), focus)
    im = im.convert("RGBA")
    return torn_edges(im, seed=seed, amp=5)


def cover_focus(im, size, focus=(0.5, 0.5)):
    """cover 裁切到 size，按 focus 决定保留原图哪个区域。"""
    iw, ih = im.size
    sw, sh = size
    s = max(sw / iw, sh / ih)
    nw, nh = int(iw * s), int(ih * s)
    im = im.resize((nw, nh), Image.LANCZOS)
    max_x, max_y = nw - sw, nh - sh
    x = int(max_x * focus[0])
    y = int(max_y * focus[1])
    return im.crop((x, y, x + sw, y + sh))


def text_layer(txt, font_path, size, color, rot=0, spacing=0):
    f = ImageFont.truetype(font_path, size)
    if spacing:
        widths = [f.getlength(ch) for ch in txt]
        total = sum(widths) + spacing * (len(txt) - 1)
        im = Image.new("RGBA", (int(total) + 24, size + 30), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        x = 12
        for ch, wch in zip(txt, widths):
            d.text((x, 10), ch, font=f, fill=color)
            x += wch + spacing
    else:
        box = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), txt, font=f)
        im = Image.new("RGBA", (box[2] - box[0] + 24, box[3] - box[1] + 30), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.text((12 - box[0], 10 - box[1]), txt, font=f, fill=color)
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    return im


def paper_tape(canvas, x, y, w, h, angle, color=(198, 200, 188, 150)):
    """细款和纸胶带：半透明、细纤维纹、无厚边。"""
    t = Image.new("RGBA", (w, h), color)
    d = ImageDraw.Draw(t)
    for i in range(0, w, 5):
        d.line((i, 0, i + 2, h), fill=(236, 236, 228, 40), width=1)
    for i in range(0, h, 4):
        d.line((0, i, w, i + 1), fill=(160, 164, 156, 30), width=1)
    # 撕端
    t = torn_edges(t, seed=int(x + y), amp=2, step=4)
    paste(canvas, t, x, y, angle, shadow=False)


def coffee_cup(canvas, cx, cy, scale=1.0, angle=0):
    """手绘简约咖啡杯线稿（小巧、不夸张）。"""
    layer = Image.new("RGBA", (int(150 * scale), int(130 * scale)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = (112, 122, 120, 205)
    W1 = lambda v: int(v * scale)
    # 杯身
    d.arc((W1(28), W1(18), W1(104), W1(96)), 0, 180, fill=c, width=max(1, W1(3)))
    d.line((W1(28), W1(57), W1(34), W1(96)), fill=c, width=max(1, W1(3)))
    d.line((W1(104), W1(57), W1(98), W1(96)), fill=c, width=max(1, W1(3)))
    d.arc((W1(34), W1(88), W1(98), W1(102)), 0, 180, fill=c, width=max(1, W1(3)))
    # 杯口椭圆
    d.ellipse((W1(28), W1(48), W1(104), W1(68)), outline=c, width=max(1, W1(3)))
    # 把手
    d.arc((W1(99), W1(40), W1(133), W1(80)), -80, 90, fill=c, width=max(1, W1(3)))
    # 碟子
    d.ellipse((W1(14), W1(102), W1(118), W1(116)), outline=c, width=max(1, W1(2)))
    # 热气
    for k, ox in enumerate((52, 72, 90)):
        d.arc((W1(ox - 6), W1(6 + k * 3), W1(ox + 6), W1(28 + k * 3)), 200, 340,
              fill=(150, 158, 152, 150), width=max(1, W1(2)))
    paste(canvas, layer, cx, cy, angle, shadow=False)


def photo_slot(w, h, seed):
    """手撕纸边大照片位：和纸米白 + 淡灰蓝细框，不规则毛边。"""
    pad = 16
    rnd = random.Random(seed)
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pts = []
    for x in range(pad, pad + w + 1, 13):
        pts.append((x, pad + rnd.randint(-5, 5)))
    for y in range(pad, pad + h + 1, 13):
        pts.append((pad + w + rnd.randint(-5, 5), y))
    for x in range(pad + w, pad - 1, -13):
        pts.append((x, pad + h + rnd.randint(-5, 5)))
    for y in range(pad + h, pad - 1, -13):
        pts.append((pad + rnd.randint(-5, 5), y))
    d.polygon(pts, fill=(236, 233, 224, 255))
    d.rectangle((pad + 7, pad + 7, pad + w - 7, pad + h - 7), outline=(160, 172, 170, 190), width=2)
    # 轻微做旧颗粒
    return torn_edges(layer, seed=seed + 90, amp=3)


# ==================== 背景：粗糙和纸 + 褪色 + 暗角 ====================
bg = Image.new("RGB", (W, H), (224, 228, 220))
bd = ImageDraw.Draw(bg)
# 和纸纤维：细短横线，低对比
rnd = random.Random(31)
for _ in range(2600):
    x = rnd.randint(0, W)
    y = rnd.randint(0, H)
    ln = rnd.randint(3, 16)
    c = rnd.choice([(212, 218, 210), (234, 236, 228), (206, 214, 210)])
    bd.line((x, y, x + ln, y + rnd.randint(-1, 1)), fill=c, width=1)
# 冷柔渐变（灰蓝 -> 浅草绿）
ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
od = ImageDraw.Draw(ov)
for y in range(H):
    t = y / H
    c = (int(196 - 22 * t), int(212 - 16 * t), int(214 - 22 * t), 70)
    od.line((0, y, W, y), fill=c)
bg = Image.alpha_composite(bg.convert("RGBA"), ov)
# 全覆盖胶片褪色颗粒
noise = Image.effect_noise((W, H), 30).convert("L")
grain = Image.merge("RGBA", (noise, noise, noise, noise.point(lambda a: int(a * 0.11))))
bg = Image.alpha_composite(bg, grain)
# 四周柔和暗角
vig = Image.new("L", (W // 8, H // 8), 0)
vd = ImageDraw.Draw(vig)
for i in range(26):
    inset = i * 2
    a = int(2 + i * 0.9)
    vd.ellipse((-inset * 3, -inset * 5, W // 8 + inset * 3, H // 8 + inset * 5), outline=a, width=1)
vig = vig.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(60))
dark = Image.new("RGBA", (W, H), (78, 86, 86, 0))
dark.putalpha(vig.point(lambda a: min(90, a)))
bg = Image.alpha_composite(bg, dark)
canvas = bg

# ==================== 底层生活碎片（原始版：全部 snap 等比剪片、画在照片下层） ====================
# 街景快照
paste(canvas, snap(JS, "japanese-salt-06.jpg", 232, 1), 786, 386, 6, shadow=True)
paste(canvas, snap(JS, "japanese-salt-05.jpg", 176, 2), 120, 486, -8, shadow=True)
# 绿植枝叶（褪色、低对比）
paste(canvas, snap(GF, "green-fresh-05.jpg", 176, 3, tint=(206, 216, 204)), 104, 856, 9)
paste(canvas, snap(GF, "green-fresh-06.jpg", 168, 4, tint=(206, 216, 204)), 806, 1188, -7)
# 复古旧相机 + 人像
paste(canvas, snap(JS, "japanese-salt-01.jpg", 150, 6, tint=(206, 214, 216)), 208, 1330, -9, shadow=True)
paste(canvas, snap(JS, "japanese-salt-10.jpg", 120, 7, tint=(212, 216, 216)), 742, 1492, 8)

# ==================== 大照片位（坐标/角度与前端 japanese-salt slots 一致，全撕边） ====================
photos = [
    (245,  560, 340, 320, -8),
    (655,  700, 350, 285,  7),
    (258, 1045, 330, 330,  6),
    (660, 1135, 345, 310, -7),
]
for i, (cx, cy, pw, ph, ang) in enumerate(photos):
    paste(canvas, photo_slot(pw, ph, i + 1), cx, cy, ang, shadow=True)

# 小熊静物：画在照片上层，覆盖在右上照片下缘一点点（只露部分、不遮主体）
paste(canvas, snap(INS, "ins-minimal-03.jpg", 150, 5), 780, 852, 7, shadow=True)

# ==================== 细和纸胶带 ====================
paper_tape(canvas, 150, 398, 84, 16, -20)
paper_tape(canvas, 604, 566, 78, 16, 14)
paper_tape(canvas, 154, 872, 76, 16, -12)
paper_tape(canvas, 596, 978, 80, 16, 12)
paper_tape(canvas, 430, 1350, 74, 16, -8)

# ==================== 手绘小物：咖啡杯 / 手写标注 / 细线 ====================
coffee_cup(canvas, 452, 918, scale=1.05, angle=-5)
d = ImageDraw.Draw(canvas)
# 细手绘线（轻盈、不厚重）
for i in range(4):
    d.line((74, 1190 + i * 9, 150 - i * 8, 1186 + i * 9), fill=(140, 150, 148, 150), width=2)
for i in range(3):
    d.line((760, 660 + i * 11, 834 + i * 3, 654 + i * 11), fill=(140, 150, 148, 140), width=2)
# 小圆点
for px, py in [(452, 372), (836, 1020), (86, 1320), (452, 1460)]:
    d.ellipse((px - 3, py - 3, px + 3, py + 3), fill=(140, 152, 150, 170))

# ==================== 小巧手写体文字（非规整印刷字） ====================
t1 = text_layer("slow days", FONT_HAND, 72, (110, 126, 128, 235), rot=-4, spacing=1)
paste(canvas, t1, 402, 116, shadow=False)
t2 = text_layer("日系盐系 · 生活碎片", FONT_KAI, 34, (108, 120, 118, 230), rot=-2)
paste(canvas, t2, 430, 192, shadow=False)
t3 = text_layer("quiet · gentle · everyday", FONT_HAND, 30, (132, 142, 140, 225), rot=-2)
paste(canvas, t3, 434, 244, shadow=False)
foot = text_layer("a little film, a little calm", FONT_HAND, 26, (120, 132, 130, 225), rot=-1)
paste(canvas, foot, 448, 1554, shadow=False)

# 收尾：再叠一层极轻褪色颗粒，统一胶片感
noise2 = Image.effect_noise((W, H), 34).convert("L")
grain2 = Image.merge("RGBA", (noise2, noise2, noise2, noise2.point(lambda a: int(a * 0.05))))
canvas = Image.alpha_composite(canvas, grain2)

final = canvas.convert("RGB")
final.save(OUT, quality=92)
print("saved", OUT, final.size)
