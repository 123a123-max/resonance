# -*- coding: utf-8 -*-
"""「街头极简潮流涂鸦拼贴」照片模板（9:16）—— 专项训练版。

设计要点（严格对照用户提示词）：
- 克制简约街头海报版式，元素精简、不堆砌。
- 高饱和潮流撞色：近黑哑光底 + 荧光黄绿/荧光粉/荧光青 点缀。
- 轻微街头喷漆颗粒，平整哑光；无老旧斑驳、无报纸肌理、无网点。
- 利落粗黑手绘线条 + 闪电 / 星星 / 笑脸 / 爱心 极简涂鸦；贴纸带标准白边。
- 松弛酷感、青年潮流、都市活力；大标题 + 英文标语。

照片位与 src/collage/templateStyles.ts 的 DEFAULT_SLOTS 完全一致（street-graffiti 风格使用默认槽位）：
  (245,560,340,320,-8,torn) (655,700,350,285,7,polaroid)
  (258,1045,330,330,6,rounded) (660,1135,345,310,-7,frame)
素材来自 pexels/street-graffiti/（授权见该目录 SOURCES.json）。
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops

random.seed(2026)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "public", "assets", "collage", "pexels", "street-graffiti")
OUT = os.path.join(ROOT, "public", "assets", "collage", "template-street-graffiti.jpg")
W, H = 900, 1600

# ---- 荧光撞色体系（黑底 + 荧光点缀） ----
BG      = (18, 18, 21)      # 近黑哑光基底
INK     = (12, 12, 14)      # 利落粗黑线条
LIME    = (214, 255, 0)     # 荧光黄绿
PINK    = (255, 46, 149)    # 荧光粉
CYAN    = (0, 238, 255)     # 荧光青
ORANGE  = (255, 94, 0)      # 荧光橙
WHITE   = (250, 250, 247)   # 标准白边 / 正文
GREY    = (150, 150, 156)

F_IMPACT = "C:/Windows/Fonts/impact.ttf"
F_ARIAL  = "C:/Windows/Fonts/arialbd.ttf"
F_HEI    = "C:/Windows/Fonts/simhei.ttf"


# ================= 基础工具 =================
def load(name):
    return Image.open(os.path.join(ASSETS, name)).convert("RGB")


def cover(im, size, focus=(0.5, 0.5)):
    """按 focus 位置把图裁成目标尺寸（居中裁切，可偏移取景）。"""
    tw, th = size
    s = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x = int((im.width - tw) * focus[0])
    y = int((im.height - th) * focus[1])
    x = max(0, min(im.width - tw, x))
    y = max(0, min(im.height - th, y))
    return im.crop((x, y, x + tw, y + th))


def _odd(n):
    n = int(n)
    return n if n % 2 == 1 else n + 1


def outline(layer, color=INK, width=4):
    """沿 alpha 外扩做一圈描边（细黑边，衬托白边贴纸）。"""
    a = layer.getchannel("A")
    grow = a.filter(ImageFilter.MaxFilter(_odd(width * 2 + 1)))
    inner = a.filter(ImageFilter.MaxFilter(_odd(max(1, width))))
    ring = ImageChops.subtract(grow, inner)
    r = Image.new("RGBA", layer.size, color + (255,))
    r.putalpha(ring)
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(r)
    out.alpha_composite(layer)
    return out


def place(canvas, layer, cx, cy, ang=0, shadow=False):
    if ang:
        layer = layer.rotate(ang, Image.BICUBIC, expand=True)
    x = int(cx - layer.width / 2)
    y = int(cy - layer.height / 2)
    if shadow:
        a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(5))
        sh = Image.new("RGBA", layer.size, (0, 0, 0, 120))
        sh.putalpha(a)
        canvas.alpha_composite(sh, (x + 5, y + 7))
    canvas.alpha_composite(layer, (x, y))


def txt_layer(text, font, size, color, maxw=None, stroke=0, stroke_fill=INK):
    f = ImageFont.truetype(font, size)
    if maxw:
        while f.getbbox(text)[2] - f.getbbox(text)[0] > maxw and size > 12:
            size -= 2
            f = ImageFont.truetype(font, size)
    box = f.getbbox(text)
    w = box[2] - box[0] + 28
    h = box[3] - box[1] + 28
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((14 - box[0], 14 - box[1]), text, font=f, fill=color,
                            stroke_width=stroke, stroke_fill=stroke_fill)
    return im


# ================= 背景：近黑哑光 + 极轻喷漆颗粒 =================
canvas = Image.new("RGBA", (W, H), BG + (255,))

# 轻微喷漆颗粒（细噪点、低强度，平整不斑驳）
grain = Image.effect_noise((W, H), 16).convert("L")
g = Image.merge("RGBA", (grain, grain, grain, grain.point(lambda a: int(a * 0.045))))
canvas.alpha_composite(g)

dd = ImageDraw.Draw(canvas)

# 顶部荧光色块（标题衬底，克制的一块）
dd.rectangle((0, 0, 250, 92), fill=LIME + (255,))
# 侧边荧光细条（少量点缀）
dd.rectangle((0, 0, 12, H), fill=INK + (255,))
dd.rectangle((0, 1500, W, 1506), fill=INK + (255,))


# ================= 涂鸦素材贴纸（带标准白边） =================
def sticker(name, side, focus=(0.5, 0.5), seed=0):
    """把素材裁成方形贴纸：白边 + 细黑描边。"""
    im = cover(load(name), (side, side), focus)
    im = ImageEnhance.Color(im).enhance(1.18)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    b = 11  # 标准白边宽度
    layer = Image.new("RGBA", (side + b * 2, side + b * 2), WHITE + (255,))
    layer.alpha_composite(im.convert("RGBA"), (b, b))
    return outline(layer, INK, 3)


# 关系一：独立素材（画在照片下层，不与照片接触）
s_a = sticker("street-graffiti-19.jpg", 150, (0.5, 0.5), 1)   # 蓝底白字涂鸦
place(canvas, s_a, 772, 252, -6, shadow=True)

# 关系二：照片压素材（画在照片下层，边角被照片位压住）
s_c = sticker("street-graffiti-04.jpg", 132, (0.5, 0.5), 2)   # 彩色字母涂鸦墙
place(canvas, s_c, 258, 800, 4, shadow=False)


# ================= 照片位（与 DEFAULT_SLOTS 严格对齐、带白边贴纸） =================
def photo_slot(shape, w, h, seed):
    rnd = random.Random(seed)
    pad = 15
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bx = (pad, pad, pad + w, pad + h)
    if shape == "torn":
        # 手撕白边：细密小锯齿，利落不夸张
        pts = []
        for x in range(pad, pad + w + 1, 12):
            pts.append((x, pad + rnd.randint(-2, 2)))
        for y in range(pad, pad + h + 1, 12):
            pts.append((pad + w + rnd.randint(-2, 2), y))
        for x in range(pad + w, pad - 1, -12):
            pts.append((x, pad + h + rnd.randint(-2, 2)))
        for y in range(pad + h, pad - 1, -12):
            pts.append((pad + rnd.randint(-2, 2), y))
        white = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        ImageDraw.Draw(white).polygon(pts, fill=WHITE + (255,))
        layer.alpha_composite(white)
        # 规整的照片内框，避免撕边纸看起来像云团
        d = ImageDraw.Draw(layer)
        d.rectangle((pad + 5, pad + 5, pad + w - 5, pad + h - 5), fill=(238, 238, 234, 255))
    elif shape == "polaroid":
        d.rectangle((pad - 2, pad - 2, pad + w + 2, pad + h + 24), fill=WHITE + (255,))
        d.rectangle(bx, fill=(238, 238, 234, 255))
    elif shape == "rounded":
        d.rounded_rectangle((pad, pad, pad + w, pad + h), radius=26, fill=WHITE + (255,))
        d.rounded_rectangle((pad + 3, pad + 3, pad + w - 3, pad + h - 3), radius=23,
                            fill=(238, 238, 234, 255))
    else:  # frame
        d.rectangle((pad - 3, pad - 3, pad + w + 3, pad + h + 3), fill=WHITE + (255,))
        d.rectangle(bx, fill=(236, 236, 232, 255))
    return outline(layer, INK, 3)


# DEFAULT_SLOTS：x, y, w, h, angle, shape
photos = [
    (245, 560, 340, 320, -8, "torn", 1),
    (655, 700, 350, 285,  7, "polaroid", 2),
    (258, 1045, 330, 330, 6, "rounded", 3),
    (660, 1135, 345, 310, -7, "frame", 4),
]
for cx, cy, w, h, ang, shape, seed in photos:
    place(canvas, photo_slot(shape, w, h, seed), cx, cy, ang, shadow=True)


# 关系三：素材压照片（画在照片上层，压住槽4底部一角，带阴影）
s_b = sticker("street-graffiti-09.jpg", 140, (0.5, 0.5), 3)   # 荧光绿涂鸦墙
place(canvas, s_b, 720, 1372, 5, shadow=True)


# ================= 程序手绘涂鸦装饰（利落粗黑线条 + 极简图案，带白边） =================
dd = ImageDraw.Draw(canvas)


def star4(cx, cy, r, color, width=5):
    pts = []
    for i in range(8):
        a = i * math.pi / 4
        rr = r if i % 2 == 0 else r * 0.26
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    # 白边
    dd.polygon(pts, fill=WHITE)
    wpts = [(cx + (x - cx) * 1.16, cy + (y - cy) * 1.16) for x, y in pts]
    dd.line(wpts + [wpts[0]], fill=INK, width=2, joint="curve")
    inner = [(cx + (x - cx) * 0.82, cy + (y - cy) * 0.82) for x, y in pts]
    dd.polygon(inner, fill=color)
    dd.line(pts + [pts[0]], fill=INK, width=width, joint="curve")


def bolt(cx, cy, scale=1.0, color=LIME):
    pts = [(cx, cy - 42), (cx - 20, cy + 6), (cx - 3, cy + 6),
           (cx - 14, cy + 46), (cx + 25, cy - 6), (cx + 6, cy - 6)]
    pts = [(cx + (x - cx) * scale, cy + (y - cy) * scale) for x, y in pts]
    dd.polygon(pts, fill=WHITE)
    dd.line(pts + [pts[0]], fill=INK, width=5, joint="curve")
    inner = [(cx + (x - cx) * 0.78, cy + (y - cy) * 0.78) for x, y in pts]
    dd.polygon(inner, fill=color)
    dd.line(inner + [inner[0]], fill=INK, width=2, joint="curve")


def smiley(cx, cy, r, color=PINK):
    # 白边圆
    dd.ellipse((cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5), fill=WHITE)
    dd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color, outline=INK, width=3)
    # 眼睛 + 笑嘴（利落黑线）
    e = r * 0.34
    dd.ellipse((cx - r * 0.45 - e / 2, cy - r * 0.25 - e / 2,
                cx - r * 0.45 + e / 2, cy - r * 0.25 + e / 2), fill=INK)
    dd.ellipse((cx + r * 0.45 - e / 2, cy - r * 0.25 - e / 2,
                cx + r * 0.45 + e / 2, cy - r * 0.25 + e / 2), fill=INK)
    dd.arc((cx - r * 0.5, cy - r * 0.1, cx + r * 0.5, cy + r * 0.65),
           start=15, end=165, fill=INK, width=4)


def heart(cx, cy, s, color=PINK):
    top = cy - s * 0.3
    pts = [(cx, cy + s * 0.7)]
    for t in [i * math.pi / 16 for i in range(17)]:
        pts.append((cx + s * 0.5 * math.sin(t) + s * 0.5 * math.sin(t) ** 2 * 0,
                    top - s * 0.5 * math.cos(t)))
    # 用两圆+三角的稳画法
    dd.ellipse((cx - s * 0.5, cy - s * 0.55, cx, cy - s * 0.05), fill=WHITE)
    dd.ellipse((cx, cy - s * 0.55, cx + s * 0.5, cy - s * 0.05), fill=WHITE)
    dd.polygon([(cx - s * 0.5, cy - s * 0.2), (cx + s * 0.5, cy - s * 0.2), (cx, cy + s * 0.6)], fill=WHITE)
    dd.ellipse((cx - s * 0.42, cy - s * 0.5, cx - s * 0.04, cy - s * 0.12), fill=color)
    dd.ellipse((cx + s * 0.04, cy - s * 0.5, cx + s * 0.42, cy - s * 0.12), fill=color)
    dd.polygon([(cx - s * 0.44, cy - s * 0.2), (cx + s * 0.44, cy - s * 0.2), (cx, cy + s * 0.52)], fill=color)


def squiggle(pts, color=WHITE, width=5):
    dd.line(pts, fill=INK, width=width + 5, joint="curve")
    dd.line(pts, fill=color, width=width, joint="curve")


# 闪电（右上、左下）
bolt(520, 150, 0.85, LIME)
bolt(150, 1400, 0.7, CYAN)

# 四角星（少量，散落空隙）
star4(648, 168, 26, PINK)
star4(120, 812, 20, CYAN)
star4(452, 1330, 22, LIME)
star4(820, 630, 18, PINK)

# 笑脸 / 爱心（极简小卡通，放空隙）
smiley(825, 452, 30, LIME)
heart(118, 1470, 46, PINK)

# 利落手绘线条（随性划线，避开照片区主体）
squiggle([(60, 372), (150, 358), (250, 372), (340, 356)], LIME, 5)
squiggle([(470, 928), (530, 916), (600, 930), (660, 918)], PINK, 5)
squiggle([(700, 1322), (760, 1312), (820, 1324)], CYAN, 5)

# 荧光小圆点（克制的散点）
for (x, y, c) in [(80, 470, LIME), (860, 900, CYAN), (420, 820, PINK), (860, 1180, LIME)]:
    dd.ellipse((x - 6, y - 6, x + 6, y + 6), fill=WHITE)
    dd.ellipse((x - 4, y - 4, x + 4, y + 4), fill=c)


# ================= 大标题 + 文案 =================
t = txt_layer("STREET", F_IMPACT, 88, INK, stroke=0)  # 黑字压荧光块
place(canvas, t, 128, 47, 0, shadow=False)

head = txt_layer("街头 · 潮流 · 克制", F_HEI, 40, WHITE, stroke=5, stroke_fill=INK)
place(canvas, head, 300, 128, -2, shadow=False)

sub = txt_layer("URBAN STREET / BOLD & MINIMAL", F_ARIAL, 22, CYAN, stroke=3, stroke_fill=INK)
place(canvas, sub, 330, 182, -1, shadow=False)

# 底部标语条
dd.rectangle((16, 1520, W - 16, 1582), fill=INK + (255,))
slogan = txt_layer("STAY BOLD  ·  KEEP IT SIMPLE  ·  2026", F_ARIAL, 26, LIME, stroke=0)
place(canvas, slogan, 450, 1551, 0, shadow=False)

# ================= 收尾：四边检测 + 保存 =================
final = canvas.convert("RGB")
# 检测照片位纸样是否触边（应无）
for cx, cy, w, h, ang, shape, seed in photos:
    sl = photo_slot(shape, w, h, seed).rotate(ang, Image.BICUBIC, expand=True)
    x0 = int(cx - sl.width / 2)
    y0 = int(cy - sl.height / 2)
    assert x0 > 0 and y0 > 0 and x0 + sl.width < W and y0 + sl.height < H, \
        "照片位触边: %s" % (shape,)

final.save(OUT, quality=94)
print("saved:", OUT, final.size)
