# -*- coding: utf-8 -*-
"""「城市拼贴·波普艺术海报」照片模板（9:16）。

撞色色块 + 半色调网点 + 撕边剪贴 + 粗黑轮廓 + 爆炸对话框 + 大标题。
照片位为矩形系、随性错落、不裁内容。
素材来自 public/assets/collage/popart/（授权见该目录 SOURCES.json）。
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance

random.seed(2026)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "public", "assets", "collage", "popart")
OUT = os.path.join(ROOT, "public", "assets", "collage", "template-popart-city.jpg")
W, H = 900, 1600

# 波普四色 + 黑
YELLOW = (255, 214, 0)
RED = (237, 28, 36)
BLUE = (0, 102, 255)
ORANGE = (255, 122, 0)
BLACK = (20, 18, 16)
CREAM = (255, 248, 225)
F_IMPACT = "C:/Windows/Fonts/impact.ttf"
F_ARIAL = "C:/Windows/Fonts/arialbd.ttf"
F_HEI = "C:/Windows/Fonts/simhei.ttf"


# ---------------- 基础工具 ----------------
def load(name):
    return Image.open(os.path.join(ASSETS, name)).convert("RGB")


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


def halftone(src, cell=7, dot_max=3.2, angle=0, colorize=None, threshold=225):
    """把图转成半色调网点（本戴点）图，可指定单色着色。"""
    g = src.convert("L")
    if angle:
        g = g.rotate(angle, Image.BILINEAR, expand=True, fillcolor=255)
    w, h = g.size
    px = g.load()
    base = colorize or (255, 255, 255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            # 取块内平均暗度
            vals = []
            for dy in range(0, cell, 2):
                for dx in range(0, cell, 2):
                    if x + dx < w and y + dy < h:
                        vals.append(px[x + dx, y + dy])
            v = sum(vals) / len(vals) if vals else 255
            darkness = max(0.0, min(1.0, (threshold - v) / threshold))
            r = darkness * dot_max
            if r < 0.7:
                continue
            cx, cy = x + cell / 2, y + cell / 2
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=base + (255,))
    if angle:
        out = out.rotate(-angle, Image.BILINEAR, expand=True, fillcolor=(0, 0, 0, 0))
        # 裁回原尺寸中心
        x = (out.width - w) // 2
        y = (out.height - h) // 2
        out = out.crop((x, y, x + w, y + h))
    return out


def halftone_bg(size, cell=9, r=1.7, color=(0, 0, 0), alpha=45):
    """整幅半色调网点背景层。"""
    w, h = size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            d.ellipse((x - r, y - r, x + r, y + r), fill=color + (alpha,))
    return layer


def posterize(im, bits=2):
    return im.point(lambda p: int(p / (256 / (2 ** bits))) * (256 // (2 ** bits)))


def high_contrast(im, cut=(55, 200)):
    im = ImageEnhance.Contrast(im).enhance(1.5)
    lo, hi = cut
    lut = [0 if x < lo else (255 if x > hi else int((x - lo) * 255 / (hi - lo))) for x in range(256)]
    return im.point(lut * 3)


def torn_edges(im, seed=0, amp=9, color=None):
    """撕边剪贴：把图裁成边缘毛糙的形状，可选白色撕边。"""
    rnd = random.Random(seed)
    w, h = im.size
    pad = 12
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    # 白纸底（撕边留白）
    if color:
        base = Image.new("RGBA", (w + pad * 2, h + pad * 2), color)
        layer = base
    mask = Image.new("L", (w + pad * 2, h + pad * 2), 0)
    md = ImageDraw.Draw(mask)
    pts = []
    step = 11
    for x in range(pad, pad + w + 1, step):
        pts.append((x, pad + rnd.randint(-amp, amp)))
    for y in range(pad, pad + h + 1, step):
        pts.append((pad + w + rnd.randint(-amp, amp), y))
    for x in range(pad + w, pad - 1, -step):
        pts.append((x, pad + h + rnd.randint(-amp, amp)))
    for y in range(pad + h, pad - 1, -step):
        pts.append((pad + rnd.randint(-amp, amp), y))
    md.polygon(pts, fill=255)
    content = im.convert("RGBA")
    layer.alpha_composite(content, (pad, pad))
    layer.putalpha(Image.composite(layer.getchannel("A"), Image.new("L", layer.size, 0), mask))
    return layer


def _odd(n):
    n = int(n)
    return n if n % 2 == 1 else n + 1


def outline(layer, color=BLACK, width=5):
    """给图层加粗黑轮廓。"""
    a = layer.getchannel("A")
    grow = a.filter(ImageFilter.MaxFilter(_odd(width * 2 + 1)))
    inner = a.filter(ImageFilter.MaxFilter(_odd(max(1, width))))
    diff = ImageChops.subtract(grow, inner)
    ring = Image.new("RGBA", layer.size, color + (255,))
    ring.putalpha(diff)
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(ring)
    out.alpha_composite(layer)
    return out


def place(canvas, layer, cx, cy, angle=0, shadow=True):
    if angle:
        layer = layer.rotate(angle, Image.BICUBIC, expand=True)
    x = int(cx - layer.width / 2)
    y = int(cy - layer.height / 2)
    if shadow:
        a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(4))
        sh = Image.new("RGBA", layer.size, BLACK + (90,))
        sh.putalpha(a)
        canvas.alpha_composite(sh, (x + 6, y + 8))
    canvas.alpha_composite(layer, (x, y))


def burst(cx, cy, rx, ry, points=12, seed=0):
    """爆炸/星芒对话框多边形点。"""
    rnd = random.Random(seed)
    pts = []
    for i in range(points * 2):
        a = i * math.pi / points - math.pi / 2
        rr = 1.0 if i % 2 == 0 else rnd.uniform(0.72, 0.85)
        pts.append((cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a)))
    return pts


def txt_layer(text, font, size, color, maxw=None, stroke=0, stroke_fill=BLACK):
    f = ImageFont.truetype(font, size)
    if maxw:
        # 自动缩字号适应宽度
        while f.getbbox(text)[2] - f.getbbox(text)[0] > maxw and size > 12:
            size -= 2
            f = ImageFont.truetype(font, size)
    box = f.getbbox(text)
    w = box[2] - box[0] + 24
    h = box[3] - box[1] + 24
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((12 - box[0], 12 - box[1]), text, font=f, fill=color,
           stroke_width=stroke, stroke_fill=stroke_fill)
    return im


# ================= 画布背景：撞色色块分割 =================
canvas = Image.new("RGBA", (W, H), YELLOW + (255,))
d = ImageDraw.Draw(canvas)

# 大色块（不规则几何分割）
d.polygon([(0, 0), (W, 0), (W, 470), (520, 430), (330, 520), (0, 450)], fill=BLUE + (255,))
d.polygon([(0, 450), (330, 520), (520, 430), (600, 760), (250, 800), (0, 720)], fill=RED + (255,))
d.polygon([(0, 720), (250, 800), (600, 760), (W, 720), (W, 1180), (430, 1240), (0, 1160)], fill=YELLOW + (255,))
d.polygon([(0, 1160), (430, 1240), (W, 1180), (W, H), (0, H)], fill=BLUE + (255,))
# 橙色斜带
d.polygon([(0, 300), (W, 200), (W, 275), (0, 375)], fill=ORANGE + (255,))
d.polygon([(0, 980), (W, 900), (W, 975), (0, 1055)], fill=ORANGE + (255,))

# 背景半色调网点
canvas.alpha_composite(halftone_bg((W, H), cell=10, r=1.9, color=BLACK, alpha=40))

# 油墨错位斑驳：噪点
noise = Image.effect_noise((W, H), 28).convert("L")
noise_col = Image.merge("RGBA", (noise, noise, noise, noise.point(lambda a: int(a * 0.10))))
canvas.alpha_composite(noise_col)

# ================= 城市剪影条（半色调处理） =================
def city_strip(name, width, height, color, seed):
    """城市剪影：原色照片 + 保留天空的剪影感 + 网点叠加。"""
    im = load(name)
    im = cover(im, (width, height))
    # 适度对比，保留建筑轮廓与天空
    im = ImageEnhance.Contrast(im).enhance(1.35)
    im = ImageEnhance.Color(im).enhance(1.2)
    strip = im.convert("RGBA")
    # 只在暗部叠网点，增加印刷感但不盖掉画面
    ht = halftone(im, cell=6, dot_max=2.4, colorize=color, threshold=150)
    strip.alpha_composite(ht)
    strip = torn_edges(strip, seed=seed, amp=7)
    return outline(strip, BLACK, 4)


city1 = city_strip("city-chicago.jpg", 470, 150, BLACK, 11)
place(canvas, city1, 300, 470, -4)

city2 = city_strip("city-ny-1.jpg", 430, 130, BLUE, 12)
place(canvas, city2, 660, 700, 5)

city3 = city_strip("city-fog.jpg", 400, 170, BLACK, 13)
place(canvas, city3, 260, 1120, -3)

# ================= 潮流人像（半色调波普化） =================
def pop_portrait(name, width, height, color, seed, cut=(70, 195)):
    """波普人像：保留人物原有鲜艳色彩，仅在暗部叠半色调网点。"""
    im = load(name)
    im = cover(im, (width, height))
    im = ImageEnhance.Contrast(im).enhance(1.3)
    im = ImageEnhance.Color(im).enhance(1.3)
    layer = im.convert("RGBA")
    # 暗部网点（threshold 低，只作用在阴影），增加印刷质感而保住色彩
    ht = halftone(im, cell=6, dot_max=2.2, colorize=color, threshold=135)
    layer.alpha_composite(ht)
    layer = torn_edges(layer, seed=seed, amp=8)
    return outline(layer, BLACK, 5)


# 黄衣女性封面（鲜艳，做主视觉）
pop1 = pop_portrait("poster-red-lips.jpg", 300, 400, BLACK, 21, cut=(60, 200))
place(canvas, pop1, 760, 470, 7)

# （第二张人像碎片已移除，避免被照片位遮挡露出半张脸）

# ================= 杂志/印刷碎片 =================
def scrap(name, box, seed, angle, color=None):
    im = load(name)
    im = im.crop(box)
    im = fit(im, 200)
    im = ImageEnhance.Contrast(im).enhance(1.2)
    im = ImageEnhance.Color(im).enhance(1.25)
    # 叠一层浅网点增加印刷感，不压黑原图
    ht = halftone(im, cell=6, dot_max=2.0, colorize=BLACK, threshold=140)
    im = im.convert("RGBA")
    im.alpha_composite(ht)
    layer = torn_edges(im, seed=seed, amp=8)
    return outline(layer, BLACK, 4)


scrap1 = scrap("magazine-old.jpg", (0, 0, 520, 300), 31, 0)
place(canvas, scrap1, 470, 150, -9)

scrap2 = scrap("newspaper-times.jpg", (0, 0, 520, 400), 32, 0)
place(canvas, scrap2, 160, 200, 8)

# scrap3 人像碎片已移除，避免露出半张脸

# 纯红纸块碎片
red_block = torn_edges(Image.new("RGBA", (150, 110), RED + (255,)), seed=34, amp=10)
place(canvas, outline(red_block, BLACK, 4), 800, 1240, 12)

# 纯蓝纸块碎片
blue_block = torn_edges(Image.new("RGBA", (130, 90), BLUE + (255,)), seed=35, amp=10)
place(canvas, outline(blue_block, BLACK, 4), 90, 640, -14)

# ================= 照片位（矩形系、随性错落、不裁内容） =================
def photo_slot(shape, w, h, seed):
    rnd = random.Random(seed)
    pad = 16
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    paper = CREAM + (255,)
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
    elif shape == "polaroid":
        d.rectangle((pad, pad, pad + w, pad + h), fill=paper)
    elif shape == "frame":
        d.rectangle((pad, pad, pad + w, pad + h), fill=paper)
        d.rectangle((pad + 6, pad + 6, pad + w - 6, pad + h - 6), outline=BLACK + (255,), width=4)
    else:
        d.rounded_rectangle((pad, pad, pad + w, pad + h), radius=16, fill=paper)
    # 粗黑轮廓
    return outline(layer, BLACK, 5)


photos = [
    ("torn",     195, 690, 290, 305, -13, 1),
    ("polaroid", 595, 895, 330, 255,  11, 2),
    ("frame",    298, 1045, 305, 325,   9, 3),
    ("torn",     685, 1295, 290, 310, -12, 4),
]
for shape, cx, cy, w, h, ang, seed in photos:
    place(canvas, photo_slot(shape, w, h, seed), cx, cy, ang)

# ================= 绘制版波普装饰元素 =================
dd = ImageDraw.Draw(canvas)

# 四角星芒（波普闪光）
def star4(d, cx, cy, r, color, width=6, seed=0):
    rnd = random.Random(seed)
    pts = []
    for i in range(8):
        a = i * math.pi / 4
        rr = r if i % 2 == 0 else r * rnd.uniform(0.22, 0.34)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=color, outline=BLACK)
    d.line(pts + [pts[0]], fill=BLACK, width=width, joint="curve")


star4(dd, 95, 640, 34, YELLOW, seed=1)
star4(dd, 820, 880, 28, RED, seed=2)
star4(dd, 470, 1380, 30, YELLOW, seed=3)

# 圆点阵装饰（三颗一组）
def dots(d, cx, cy, color, r=7, gap=26):
    for dx, dy in [(-gap, 0), (0, 0), (gap, 0), (-gap / 2, -gap), (gap / 2, gap)]:
        d.ellipse((cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r),
                  fill=color, outline=BLACK, width=2)


dots(dd, 800, 1000, YELLOW)
dots(dd, 100, 1190, BLUE)

# 速度线（放射短线）— 避开文字区
for i in range(4):
    y = 1400 + i * 16
    dd.line((70, y, 130 - i * 6, y - 6), fill=BLACK, width=5)
for i in range(4):
    y = 560 + i * 18
    dd.line((770, y, 830 + i * 5, y - 8), fill=BLACK, width=5)

# 闪电
def bolt(d, cx, cy, scale=1.0):
    pts = [(cx, cy - 40), (cx - 18, cy + 4), (cx - 2, cy + 4),
           (cx - 12, cy + 42), (cx + 22, cy - 8), (cx + 4, cy - 8)]
    pts = [(cx + (x - cx) * scale, cy + (y - cy) * scale) for x, y in pts]
    d.polygon(pts, fill=YELLOW, outline=BLACK)
    d.line(pts + [pts[0]], fill=BLACK, width=4, joint="curve")


bolt(dd, 830, 620, 0.9)
bolt(dd, 90, 1080, 0.75)

# ================= 爆炸对话框 + 大标题 =================
# 爆炸框 1
bp = burst(470, 600, 150, 92, points=13, seed=41)
dlg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dd = ImageDraw.Draw(dlg)
dd.polygon(bp, fill=YELLOW + (255,), outline=BLACK + (255,))
# 重新描粗边
dd.line(bp + [bp[0]], fill=BLACK + (255,), width=7, joint="curve")
canvas.alpha_composite(dlg)

t = txt_layer("WOW!", F_IMPACT, 74, RED, stroke=3)
place(canvas, t, 470, 585, -6, shadow=False)

# 爆炸框 2
bp2 = burst(690, 1120, 118, 74, points=11, seed=42)
dlg2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dd2 = ImageDraw.Draw(dlg2)
dd2.polygon(bp2, fill=RED + (255,), outline=BLACK + (255,))
dd2.line(bp2 + [bp2[0]], fill=BLACK + (255,), width=6, joint="curve")
canvas.alpha_composite(dlg2)
t2 = txt_layer("POP!", F_IMPACT, 52, CREAM, stroke=2)
place(canvas, t2, 690, 1112, 5, shadow=False)

# 大标题（顶部，粗体描边）
title = txt_layer("CITY", F_IMPACT, 150, YELLOW, stroke=8, stroke_fill=BLACK)
place(canvas, title, 210, 175, -3, shadow=False)
title2 = txt_layer("POP! 波普都市", F_HEI, 58, CREAM, stroke=5, stroke_fill=BLACK)
place(canvas, title2, 430, 285, -2, shadow=False)

# 副标题条
d = ImageDraw.Draw(canvas)
d.rectangle((60, 1490, 840, 1560), fill=BLACK + (255,))
sub = txt_layer("URBAN COLLAGE  ·  VIVID  ·  BOLD  ·  2026", F_ARIAL, 26, YELLOW)
place(canvas, sub, 450, 1525, 0, shadow=False)

# 小标签文字
tag = txt_layer("流行 · 撞色 · 都市", F_HEI, 26, BLACK)
place(canvas, tag, 250, 1330, -4, shadow=False)

# 收尾：轻微颗粒
final = canvas.convert("RGB")
grain = Image.effect_noise((W, H), 12).convert("L")
gr = Image.merge("RGB", (grain, grain, grain))
final = Image.blend(final, gr, 0.05)
final.save(OUT, quality=93)
print("saved:", OUT, final.size)
