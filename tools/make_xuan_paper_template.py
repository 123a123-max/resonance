# -*- coding: utf-8 -*-
"""「文艺宣纸书香拼贴」照片模板（9:16）—— 专项训练版。

严格对照用户提示词：
- 雅致对称松弛排版，国风书卷式布局，元素错落雅致不杂乱。
- 中式复古低饱和：米白 / 浅赭石为主，淡墨点缀，温润素雅。
- 原生宣纸纤维 + 蜡染旧纸肌理，纸面自然温润、轻微做旧。
- 古籍残片、毛笔书法、古典古诗文字、金石拓片、水墨花枝、火漆印章；
  边缘自然晕染、轻微灼烧、自然撕裂效果。
- 避雷：无高饱和彩色、无现代涂鸦、无粗大字体、无卡通贴纸、无强烈撞色。

照片位与 src/collage/templateStyles.ts 的 DEFAULT_SLOTS 完全一致（xuan-paper 用默认槽位）。
素材来自 pexels/xuan-paper/ 与 pexels/green-fresh/（授权见各目录 SOURCES.json）。
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops

random.seed(2026)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_ROOT = os.path.join(ROOT, "public", "assets", "collage", "pexels")
OUT = os.path.join(ROOT, "public", "assets", "collage", "template-xuan-paper.jpg")
W, H = 900, 1600

# ---- 低饱和国风色 ----
PAPER   = (243, 235, 219)   # 米白宣纸
PAPER2  = (236, 225, 204)   # 浅赭旧纸
OCHRE   = (196, 166, 120)   # 浅赭石
INK     = (74, 68, 60)      # 淡墨
INK_L   = (120, 112, 100)   # 淡墨浅
SEAL    = (163, 76, 60)     # 朱砂印章（低饱和赭红）
BURN    = (150, 116, 78)    # 灼烧边

F_KAI  = "C:/Windows/Fonts/STKAITI.TTF"      # 楷体
F_XING = "C:/Windows/Fonts/STXINGKA.TTF"     # 行书
F_SONG = "C:/Windows/Fonts/simsun.ttc"       # 宋体
F_EN   = "C:/Windows/Fonts/georgia.ttf"


# ================= 基础工具 =================
def _odd(n):
    n = int(n)
    return n if n % 2 == 1 else n + 1


def load(folder, name):
    return Image.open(os.path.join(ASSET_ROOT, folder, name)).convert("RGB")


def cover(im, size, focus=(0.5, 0.5)):
    tw, th = size
    s = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x = max(0, min(im.width - tw, int((im.width - tw) * focus[0])))
    y = max(0, min(im.height - th, int((im.height - th) * focus[1])))
    return im.crop((x, y, x + tw, y + th))


def sepia(im, strength=0.55):
    """去饱和 + 米赭染色，做旧成温润古纸调。"""
    im = ImageEnhance.Color(im).enhance(0.28)
    im = ImageEnhance.Contrast(im).enhance(0.86)
    g = im.convert("L")
    tint = Image.new("RGB", im.size, PAPER)
    out = Image.blend(g.convert("RGB"), tint, strength * 0.45)
    return out


def place(canvas, layer, cx, cy, ang=0, shadow=False):
    if ang:
        layer = layer.rotate(ang, Image.BICUBIC, expand=True)
    x = int(cx - layer.width / 2)
    y = int(cy - layer.height / 2)
    if shadow:
        a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(6))
        sh = Image.new("RGBA", layer.size, (60, 50, 38, 70))
        sh.putalpha(a)
        canvas.alpha_composite(sh, (x + 4, y + 6))
    canvas.alpha_composite(layer, (x, y))


def torn_edges(layer, seed=0, amp=7, step=14):
    """自然撕裂毛边（不规则多边形 alpha）。"""
    w, h = layer.size
    rnd = random.Random(seed)
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    pts = []
    for x in range(0, w + step, step):
        pts.append((x, rnd.randint(0, amp)))
    for y in range(0, h + step, step):
        pts.append((w - rnd.randint(0, amp), y))
    for x in range(w, -step, -step):
        pts.append((x, h - rnd.randint(0, amp)))
    for y in range(h, -step, -step):
        pts.append((rnd.randint(0, amp), y))
    d.polygon(pts, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(0.8))
    out = layer.copy()
    out.putalpha(ImageChops.multiply(out.getchannel("A"), m))
    return out


def burn_edge(layer, color=BURN, width=5, seed=0):
    """轻微灼烧边：沿 alpha 外缘染一圈浅赭焦色。"""
    a = layer.getchannel("A")
    grow = a.filter(ImageFilter.MaxFilter(_odd(width * 2 + 1)))
    ring = ImageChops.subtract(grow, a)
    r = Image.new("RGBA", layer.size, color + (150,))
    r.putalpha(ring)
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(r)
    out.alpha_composite(layer)
    return out


# ================= 背景：宣纸纤维 + 蜡染做旧 =================
canvas = Image.new("RGBA", (W, H), PAPER + (255,))
d = ImageDraw.Draw(canvas)

# 垂直淡渐变（米白 -> 浅赭）
for y in range(H):
    t = y / H
    c = tuple(int(PAPER[k] * (1 - t * 0.5) + PAPER2[k] * (t * 0.5)) for k in range(3))
    d.line((0, y, W, y), fill=c + (255,))

# 蜡染旧纸：柔和斑驳色块（低对比，温润）
rnd = random.Random(7)
stain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(stain)
for _ in range(70):
    cx, cy = rnd.randint(0, W), rnd.randint(0, H)
    r = rnd.randint(60, 210)
    sd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=OCHRE + (rnd.randint(6, 16),))
stain = stain.filter(ImageFilter.GaussianBlur(40))
canvas.alpha_composite(stain)

# 宣纸纤维纹理：细短横纹
fib = Image.new("RGBA", (W, H), (0, 0, 0, 0))
fd = ImageDraw.Draw(fib)
for _ in range(2600):
    x, y = rnd.randint(0, W), rnd.randint(0, H)
    ln = rnd.randint(3, 16)
    fd.line((x, y, x + ln, y + rnd.randint(-1, 1)), fill=INK_L + (rnd.randint(8, 20),), width=1)
canvas.alpha_composite(fib)

# 细颗粒
grain = Image.effect_noise((W, H), 14).convert("L")
g = Image.merge("RGBA", (grain, grain, grain, grain.point(lambda a: int(a * 0.035))))
canvas.alpha_composite(g)

# 边缘自然晕染（四周淡墨扩散）
vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
vd = ImageDraw.Draw(vig)
for i in range(46):
    inset = int(i * 7)
    v = int(38 * (1 - i / 46) ** 1.5)
    if W - 2 * inset <= 0 or H - 2 * inset <= 0:
        break
    vd.rectangle((inset, inset, W - inset, H - inset), outline=INK_L + (v,), width=7)
vig = vig.filter(ImageFilter.GaussianBlur(26))
canvas.alpha_composite(vig)

# 淡墨晕染团（水墨感，若隐若现）
for cx, cy, r in [(110, 470, 120), (820, 900, 140), (180, 1330, 110), (760, 340, 90)]:
    ink = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    idr = ImageDraw.Draw(ink)
    idr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=INK + (16,))
    canvas.alpha_composite(ink.filter(ImageFilter.GaussianBlur(r * 0.5)))


# ================= 古籍 / 书法 / 印章 贴纸（做旧处理） =================
def frag(name, folder, w, h, cx, cy, focus, seed, angle, tone=0.6):
    """古籍残片：做旧 + 自然撕裂 + 轻微灼烧边。"""
    im = sepia(cover(load(folder, name), (w, h), focus), tone)
    layer = torn_edges(im.convert("RGBA"), seed=seed, amp=7, step=12)
    layer = burn_edge(layer, BURN, 4, seed)
    place(canvas, layer, cx, cy, angle, shadow=True)


# 关系一：独立素材（不接触照片）—— 放在顶部两侧留白与中缝
frag("xuan-paper-12.jpg", "xuan-paper", 210, 150, 150, 330, (0.5, 0.5), 11, -5, 0.5)  # 竹简毛笔字
frag("xuan-paper-16.jpg", "xuan-paper", 150, 190, 770, 300, (0.5, 0.5), 12, 6, 0.55)  # 书法字帖


# ================= 水墨花枝（程序手绘，淡墨） =================
d = ImageDraw.Draw(canvas)


def ink_branch(ox, oy, scale, ang, seed, color=INK):
    """手绘水墨梅枝：主枝 + 分叉 + 花朵（淡墨点瓣）。"""
    rnd = random.Random(seed)
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)

    def tr(x, y):
        return (ox + (x * ca - y * sa) * scale, oy + (x * sa + y * ca) * scale)

    # 主枝（弯曲折线）—— 淡墨但清晰可辨
    main = [(0, 0), (40, -18), (86, -12), (130, -40), (170, -52), (214, -84)]
    main = [tr(x, y) for x, y in main]
    lw = max(3, int(6 * scale))
    d.line(main, fill=color + (235,), width=lw, joint="curve")
    d.line([tr(40, -18), tr(70, 14), tr(112, 26)], fill=color + (215,), width=max(2, int(4 * scale)))
    d.line([tr(130, -40), tr(150, -6), tr(196, 8)], fill=color + (215,), width=max(2, int(4 * scale)))
    # 花（五瓣淡墨点 + 花心）—— 墨色花瓣，朱砂点蕊
    for (fx, fy) in [(86, -12), (170, -52), (112, 26), (196, 8), (40, -18)]:
        cx, cy = tr(fx, fy)
        r = 8 * scale
        for k in range(5):
            t = k * 2 * math.pi / 5
            px, py = cx + r * math.cos(t), cy + r * math.sin(t)
            d.ellipse((px - r * 0.6, py - r * 0.6, px + r * 0.6, py + r * 0.6),
                      fill=(150, 128, 106, 205))
        d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=SEAL + (220,))


# （花枝在照片位绘制之后再调用，避免被照片纸盖住 —— 见下方装饰层）


# ================= 照片位（宣纸撕边，严格对齐 DEFAULT_SLOTS） =================
def photo_slot(shape, w, h, seed):
    rnd = random.Random(seed)
    pad = 16
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    bx = (pad, pad, pad + w, pad + h)
    d = ImageDraw.Draw(layer)
    # 宣纸底纸
    if shape == "torn":
        pts = []
        for x in range(pad, pad + w + 1, 12):
            pts.append((x, pad + rnd.randint(-4, 4)))
        for y in range(pad, pad + h + 1, 12):
            pts.append((pad + w + rnd.randint(-4, 4), y))
        for x in range(pad + w, pad - 1, -12):
            pts.append((x, pad + h + rnd.randint(-4, 4)))
        for y in range(pad + h, pad - 1, -12):
            pts.append((pad + rnd.randint(-4, 4), y))
        d.polygon(pts, fill=PAPER + (255,))
        d.rectangle((pad + 5, pad + 5, pad + w - 5, pad + h - 5), fill=(238, 229, 211, 255))
    elif shape == "polaroid":
        d.rectangle((pad - 2, pad - 2, pad + w + 2, pad + h + 22), fill=PAPER + (255,))
        d.rectangle(bx, fill=(237, 228, 210, 255))
    elif shape == "rounded":
        d.rounded_rectangle((pad, pad, pad + w, pad + h), radius=24, fill=PAPER + (255,))
        d.rounded_rectangle((pad + 4, pad + 4, pad + w - 4, pad + h - 4), radius=20,
                            fill=(237, 228, 210, 255))
    else:  # frame
        d.rectangle((pad - 3, pad - 3, pad + w + 3, pad + h + 3), fill=PAPER + (255,))
        d.rectangle(bx, fill=(236, 227, 209, 255))
    # 淡墨细边
    d.rectangle((pad - 1, pad - 1, pad + w + 1, pad + h + 1), outline=INK_L + (110,), width=1)
    return layer


# DEFAULT_SLOTS: (cx, cy, w, h, angle, shape, seed)
photos = [
    (245, 560, 340, 320, -8, "torn", 1),
    (655, 700, 350, 285,  7, "polaroid", 2),
    (258, 1045, 330, 330, 6, "rounded", 3),
    (660, 1135, 345, 310, -7, "frame", 4),
]
for cx, cy, w, h, ang, shape, seed in photos:
    place(canvas, photo_slot(shape, w, h, seed), cx, cy, ang, shadow=True)


# 关系二：照片压素材 —— 素材放照片下层边角被压（绿植做淡墨花枝残片）
gf = sepia(cover(load("green-fresh", "green-fresh-06.jpg"), (130, 130)), 0.72)
gf_layer = torn_edges(gf.convert("RGBA"), seed=31, amp=8, step=12)
place(canvas, gf_layer, 690, 510, -5, shadow=False)  # 照片2上缘，底边被轻微压住（可见率>80%）

# 关系三：素材压照片 —— 画在照片上层压住右下照片一角
seal_frag = sepia(cover(load("xuan-paper", "xuan-paper-21.jpg"), (150, 118), (0.5, 0.55)), 0.58)
sf_layer = torn_edges(seal_frag.convert("RGBA"), seed=32, amp=7, step=12)
sf_layer = burn_edge(sf_layer, BURN, 4, 32)
place(canvas, sf_layer, 726, 1300, 7, shadow=True)


# ================= 水墨花枝（画在上层空隙，清晰可辨） =================
ink_branch(80, 1420, 1.3, -22, 21, INK)     # 左下空白向右上伸展
ink_branch(600, 905, 0.9, -26, 23, INK_L)   # 中右横缝淡枝
ink_branch(842, 560, 0.78, 148, 22, INK)    # 右侧中部小枝

# ================= 火漆印章 / 金石拓片（程序手绘） =================
d = ImageDraw.Draw(canvas)


def seal_stamp(cx, cy, r, text, seed):
    """朱砂火漆印章：不规则圆 + 篆字。"""
    s = Image.new("RGBA", (r * 2 + 20, r * 2 + 20), (0, 0, 0, 0))
    sd = ImageDraw.Draw(s)
    cc = r + 10
    pts = []
    rnd = random.Random(seed)
    for i in range(40):
        t = i * 2 * math.pi / 40
        rr = r + rnd.randint(-3, 3)
        pts.append((cc + rr * math.cos(t), cc + rr * math.sin(t)))
    sd.polygon(pts, fill=SEAL + (205,))
    sd.ellipse((cc - r + 8, cc - r + 8, cc + r - 8, cc + r - 8), outline=PAPER + (180,), width=2)
    f = ImageFont.truetype(F_SONG, int(r * 0.95))
    bb = sd.textbbox((0, 0), text, font=f)
    sd.text((cc - (bb[2] - bb[0]) / 2 - bb[0], cc - (bb[3] - bb[1]) / 2 - bb[1]),
            text, font=f, fill=PAPER + (235,))
    canvas.alpha_composite(s, (int(cx - cc), int(cy - cc)))


seal_stamp(810, 1210, 40, "印", 41)
seal_stamp(120, 880, 32, "藏", 42)


# 金石拓片：淡墨方形碑拓（黑色底 + 白字意象，低对比做旧）
tb = Image.new("RGBA", (150, 118), (0, 0, 0, 0))
td = ImageDraw.Draw(tb)
td.rectangle((4, 4, 146, 114), fill=(86, 80, 72, 215), outline=INK + (230,), width=2)
f = ImageFont.truetype(F_SONG, 26)
for row, line in enumerate(["風", "花", "雪", "月"]):
    td.text((16 + (row % 2) * 62, 12 + (row // 2) * 50), line, font=f, fill=PAPER + (200,))
tb = torn_edges(tb, seed=43, amp=6, step=11)
place(canvas, tb, 780, 1500, -4, shadow=False)


# ================= 古诗文字 + 大标题 =================
def vtext(text, x, y, fnt, color, gap=8):
    """竖排文字。"""
    d = ImageDraw.Draw(canvas)
    for i, ch in enumerate(text):
        d.text((x, y + i * (fnt.size + gap)), ch, font=fnt, fill=color)


f_poem = ImageFont.truetype(F_KAI, 30)
vtext("書香", 56, 250, f_poem, INK + (200,))
vtext("墨韵", 838, 620, f_poem, INK_L + (170,))

# 古诗（淡墨小字）
f_poem_s = ImageFont.truetype(F_KAI, 22)
poem = "窗竹影摇书案上\n野泉声入砚池中"
d.multiline_text((600, 20), poem, font=f_poem_s, fill=INK_L + (190,), spacing=8)

# 大标题（行书，淡墨，不做粗大）
title = ImageFont.truetype(F_XING, 84)
d.text((70, 60), "书卷气", font=title, fill=INK + (235,))
d.text((74, 158), "东方诗意 · 安静雅致", font=ImageFont.truetype(F_KAI, 30), fill=INK_L + (215,))
d.text((76, 200), "INK & PAPER / CLASSIC", font=ImageFont.truetype(F_EN, 20), fill=OCHRE + (220,))

# 底部落款
d.text((70, 1518), "诗书 · 水墨 · 旧时光", font=ImageFont.truetype(F_KAI, 26), fill=INK_L + (210,))

# ================= 收尾：触边检测 + 保存 =================
final = canvas.convert("RGB")
for cx, cy, w, h, ang, shape, seed in photos:
    sl = photo_slot(shape, w, h, seed).rotate(ang, Image.BICUBIC, expand=True)
    x0 = int(cx - sl.width / 2)
    y0 = int(cy - sl.height / 2)
    assert x0 > 0 and y0 > 0 and x0 + sl.width < W and y0 + sl.height < H, "照片位触边: %s" % shape

final.save(OUT, quality=94)
print("saved:", OUT, final.size)
