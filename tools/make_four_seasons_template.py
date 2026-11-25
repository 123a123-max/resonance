# -*- coding: utf-8 -*-
"""「四季叙事手账长卷拼贴」照片模板（9:16）—— 专项训练版。

严格对照用户提示词：
- 纵向超长卷时间轴（9:16 竖版内做流动叙事），春夏秋冬四段式分区。
- 四季专属低饱和柔色：春淡粉 / 夏嫩绿 / 秋暖橙 / 冬浅灰，背景四段平滑渐变。
- 轻薄细腻手账纸纹理，平整干净，轻微柔光。
- 四季花草随拍贴纸、彩色便签、细线条手绘、手写感悟、简约贴纸。
- 避雷：无杂乱撞色、无强对比、无粗超大字体、无密集爆炸图案。

照片位为纵向四段各一个（左右交错，流动叙事），坐标同步 templateStyles.ts 的
four-seasons 自定义 slots。素材来自 pexels/four-seasons/（SOURCES.json 有授权）。
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops

random.seed(2026)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "public", "assets", "collage", "pexels", "four-seasons")
OUT = os.path.join(ROOT, "public", "assets", "collage", "template-four-seasons.jpg")
W, H = 900, 1600

# ---- 四季低饱和柔色（背景渐变节点）----
SPRING = (250, 231, 233)   # 春 淡粉
SUMMER = (226, 240, 218)   # 夏 嫩绿
AUTUMN = (247, 228, 204)   # 秋 暖橙
WINTER = (231, 233, 237)   # 冬 浅灰
INK     = (110, 104, 98)   # 柔灰墨（正文，非纯黑）
INK_L   = (150, 144, 138)
SEASON_C = {
    "spring": (214, 150, 166),
    "summer": (128, 172, 128),
    "autumn": (206, 146, 96),
    "winter": (140, 148, 162),
}

F_KAI = "C:/Windows/Fonts/STKAITI.TTF"      # 行楷（手写感悟）
F_SONG = "C:/Windows/Fonts/simsun.ttc"      # 宋体（季节标题）
F_EN = "C:/Windows/Fonts/georgia.ttf"       # 英文衬线
F_EN_I = "C:/Windows/Fonts/georgiai.ttf"

# 纵向四段：每段一个照片位（cx, cy, w, h, angle, shape, seed）
SEASONS = [
    ("spring", "春", "SPRING", "春风有信，花开有期。",  280, 430, 340, 300, -6, "polaroid", 1),
    ("summer", "夏", "SUMMER", "绿荫渐浓，万物生长。",  620, 750, 350, 285,  5, "rounded",  2),
    ("autumn", "秋", "AUTUMN", "一叶知秋，岁月温柔。",  280, 1075, 340, 300, -5, "torn",     3),
    ("winter", "冬", "WINTER", "白雪初临，静待春归。",  620, 1400, 350, 280,  6, "frame",    4),
]


# ================= 基础工具 =================
def lerp(c1, c2, t):
    return tuple(int(c1[k] * (1 - t) + c2[k] * t) for k in range(3))


def load(name):
    return Image.open(os.path.join(ASSETS, name)).convert("RGB")


def cover(im, size, focus=(0.5, 0.5)):
    tw, th = size
    s = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x = max(0, min(im.width - tw, int((im.width - tw) * focus[0])))
    y = max(0, min(im.height - th, int((im.height - th) * focus[1])))
    return im.crop((x, y, x + tw, y + th))


def soft_pastel(im, tint, strength=0.4):
    """季节随拍：轻度去饱和 + 染当季柔色，柔和通透。"""
    im = ImageEnhance.Color(im).enhance(0.75)
    im = ImageEnhance.Contrast(im).enhance(0.92)
    tinted = Image.blend(im.convert("RGB"), Image.new("RGB", im.size, tint), strength * 0.35)
    return tinted


def _odd(n):
    n = int(n)
    return n if n % 2 == 1 else n + 1


def place(canvas, layer, cx, cy, ang=0, shadow=False):
    if ang:
        layer = layer.rotate(ang, Image.BICUBIC, expand=True)
    x = int(cx - layer.width / 2)
    y = int(cy - layer.height / 2)
    if shadow:
        a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(5))
        sh = Image.new("RGBA", layer.size, (90, 84, 78, 55))
        sh.putalpha(a)
        canvas.alpha_composite(sh, (x + 4, y + 6))
    canvas.alpha_composite(layer, (x, y))


def torn_edges(layer, seed=0, amp=6, step=13):
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


# ================= 背景：四季四段平滑渐变 =================
bg = Image.new("RGB", (W, H))
bd = ImageDraw.Draw(bg)
# 四段中心色，段间在边界带内平滑过渡
stops = [(0.0, SPRING), (0.25, SPRING), (0.5, SUMMER), (0.75, AUTUMN), (1.0, WINTER)]
# 用关键点渐变：春→夏→秋→冬，边界处 120px 过渡带
segs = [
    (0, 360, SPRING, SPRING),
    (360, 520, SPRING, SUMMER),   # 春→夏过渡
    (520, 840, SUMMER, SUMMER),
    (840, 1000, SUMMER, AUTUMN),  # 夏→秋过渡
    (1000, 1320, AUTUMN, AUTUMN),
    (1320, 1480, AUTUMN, WINTER), # 秋→冬过渡
    (1480, H, WINTER, WINTER),
]
for y0, y1, c0, c1 in segs:
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0)
        bd.line((0, y, W, y), fill=lerp(c0, c1, t))

canvas = bg.convert("RGBA")

# 轻微柔光（中心亮、四周柔暗）
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gm = Image.new("L", (W, H), 0)
gd = ImageDraw.Draw(gm)
gd.ellipse((W * 0.1, H * 0.1, W * 0.9, H * 0.92), fill=26)
gm = gm.filter(ImageFilter.GaussianBlur(150))
glow = Image.new("RGBA", (W, H), (255, 255, 255, 0))
glow.putalpha(gm)
canvas.alpha_composite(glow)

# 手账纸纹理：细横纹 + 细颗粒
rnd = random.Random(5)
fib = Image.new("RGBA", (W, H), (0, 0, 0, 0))
fd = ImageDraw.Draw(fib)
for _ in range(1800):
    x, y = rnd.randint(0, W), rnd.randint(0, H)
    fd.line((x, y, x + rnd.randint(3, 13), y), fill=(140, 134, 128, rnd.randint(6, 14)), width=1)
canvas.alpha_composite(fib)
grain = Image.effect_noise((W, H), 12).convert("L")
g = Image.merge("RGBA", (grain, grain, grain, grain.point(lambda a: int(a * 0.028))))
canvas.alpha_composite(g)

# ==== 时间轴主骨架：贯穿全图的柔和竖线（左偏 x=120）+ 四季节点 ====
d = ImageDraw.Draw(canvas)
AXIS_X = 118
d.line((AXIS_X, 210, AXIS_X, H - 90), fill=(168, 160, 152, 150), width=3)
# 虚线点缀
for y in range(220, H - 100, 26):
    d.line((AXIS_X, y, AXIS_X, y + 12), fill=(188, 180, 172, 170), width=3)


# ================= 照片位（四季柔色贴纸，严格对齐 SEASONS 槽位） =================
def photo_slot(shape, w, h, season, seed):
    rnd = random.Random(seed)
    pad = 16
    L = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    paper = (253, 251, 246, 255)
    bx = (pad, pad, pad + w, pad + h)
    if shape == "torn":
        pts = []
        for x in range(pad, pad + w + 1, 12):
            pts.append((x, pad + rnd.randint(-3, 3)))
        for y in range(pad, pad + h + 1, 12):
            pts.append((pad + w + rnd.randint(-3, 3), y))
        for x in range(pad + w, pad - 1, -12):
            pts.append((x, pad + h + rnd.randint(-3, 3)))
        for y in range(pad + h, pad - 1, -12):
            pts.append((pad + rnd.randint(-3, 3), y))
        d.polygon(pts, fill=paper)
        d.rectangle((pad + 4, pad + 4, pad + w - 4, pad + h - 4), fill=(249, 246, 239, 255))
    elif shape == "polaroid":
        d.rectangle((pad - 2, pad - 2, pad + w + 2, pad + h + 22), fill=paper)
        d.rectangle(bx, fill=(248, 245, 238, 255))
    elif shape == "rounded":
        d.rounded_rectangle((pad, pad, pad + w, pad + h), radius=22, fill=paper)
        d.rounded_rectangle((pad + 4, pad + 4, pad + w - 4, pad + h - 4), radius=18,
                            fill=(248, 245, 238, 255))
    else:  # frame
        d.rectangle((pad - 3, pad - 3, pad + w + 3, pad + h + 3), fill=paper)
        d.rectangle(bx, fill=(248, 245, 238, 255))
    # 极细季节色描边（柔和不抢眼）
    d.rectangle((pad - 1, pad - 1, pad + w + 1, pad + h + 1),
                outline=SEASON_C[season] + (90,), width=2)
    return L


for (season, cn, en, poem, cx, cy, w, h, ang, shape, seed) in SEASONS:
    place(canvas, photo_slot(shape, w, h, season, seed), cx, cy, ang, shadow=True)


# ================= 季节随拍贴纸（白边）+ 三种遮挡关系 =================
def snap_sticker(name, side, tint, seed, focus=(0.5, 0.5)):
    im = soft_pastel(cover(load(name), (side, side), focus), tint, 0.42)
    b = 9
    L = Image.new("RGBA", (side + b * 2, side + b * 2), (255, 255, 255, 255))
    L.alpha_composite(im.convert("RGBA"), (b, b))
    return torn_edges(L, seed=seed, amp=5, step=12)


# 独立：春樱花贴纸（右上空白，不碰照片）
place(canvas, snap_sticker("four-seasons-08.jpg", 120, SEASON_C["spring"], 11), 742, 350, 7, shadow=True)
# 被照片压：夏绿园贴纸放照片2左上，仅边角被压（主体露出 >70%）
place(canvas, snap_sticker("four-seasons-15.jpg", 104, SEASON_C["summer"], 12), 412, 648, -6, shadow=False)
# 压在照片上：秋橙叶贴纸压照片3右上角一角
place(canvas, snap_sticker("four-seasons-06.jpg", 116, SEASON_C["autumn"], 13), 424, 966, 6, shadow=True)
# 独立：冬雪景贴纸（左下空白）
place(canvas, snap_sticker("four-seasons-18.jpg", 118, SEASON_C["winter"], 14), 176, 1420, -5, shadow=True)


# ================= 季节标题 / 手写感悟 / 细线手绘 / 便签 =================
d = ImageDraw.Draw(canvas)
f_season = ImageFont.truetype(F_SONG, 58)
f_en = ImageFont.truetype(F_EN, 24)
f_poem = ImageFont.truetype(F_KAI, 26)
f_note = ImageFont.truetype(F_KAI, 22)

# 时间轴四季节点：圆点在竖线 x=118 上；季节标题放在照片对侧空白，避免被照片纸压住
node_y = {"spring": 250, "summer": 570, "autumn": 890, "winter": 1210}
title_pos = {
    "spring": (600, 232),   # 春照片在左 -> 标题放右上
    "summer": (150, 630),   # 夏照片在右 -> 标题放左上
    "autumn": (600, 948),   # 秋照片在左 -> 标题放右上
    "winter": (600, 1310),  # 冬照片在右 -> 标题放右上空白（避开竖线与照片纸）
}

for (season, cn, en, poem, cx, cy, w, h, ang, shape, seed) in SEASONS:
    ny = node_y[season]
    c = SEASON_C[season]
    d.ellipse((AXIS_X - 11, ny - 11, AXIS_X + 11, ny + 11), fill=(255, 255, 255, 255))
    d.ellipse((AXIS_X - 7, ny - 7, AXIS_X + 7, ny + 7), fill=c + (255,))
    tx, ty = title_pos[season]
    d.text((tx, ty - 34), cn, font=f_season, fill=c + (235,))
    d.text((tx + 68, ty - 2), en, font=f_en, fill=INK_L + (220,))

# 手写感悟（各段，放在照片对侧留白）
d.text((640, 452), "春风有信", font=f_poem, fill=INK + (200,))
d.text((640, 488), "花开有期", font=f_poem, fill=INK + (200,))
d.text((150, 700), "绿荫渐浓", font=f_poem, fill=INK + (200,))
d.text((150, 736), "万物生长", font=f_poem, fill=INK + (200,))
d.text((640, 1108), "一叶知秋", font=f_poem, fill=INK + (200,))
d.text((640, 1144), "岁月温柔", font=f_poem, fill=INK + (200,))
d.text((150, 1520), "白雪初临", font=f_poem, fill=INK + (200,))
d.text((560, 1520), "静待春归", font=f_poem, fill=INK + (200,))


def note(cx, cy, w, h, color, seed, lines):
    """彩色便签（低饱和）+ 手绘细线。"""
    N = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    nd = ImageDraw.Draw(N)
    nd.rectangle((0, 0, w - 1, h - 1), fill=color + (235,), outline=(255, 255, 255, 220), width=2)
    for i, line in enumerate(lines):
        nd.text((14, 12 + i * 30), line, font=f_note, fill=INK + (215,))
    N = N.rotate(seed, Image.BICUBIC, expand=True)
    canvas.alpha_composite(N, (int(cx - N.width / 2), int(cy - N.height / 2)))


note(790, 490, 140, 88, (250, 224, 228), 5, ["三月的风", "很温柔"])       # 春便签（右移避开手写感悟）
note(168, 900, 150, 92, (222, 238, 216), -4, ["夏日悠长", "绿意满"])      # 夏便签
note(792, 1030, 140, 86, (250, 228, 204), 6, ["秋色渐染", "正好"])        # 秋便签（秋段右侧中部，避开冬标题）
note(470, 1340, 150, 92, (230, 232, 238), -5, ["等一场雪", "落满窗"])     # 冬便签

# 细线条手绘装饰（季节色小花草/叶片，克制）
def sprig(cx, cy, scale, color, seed):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(canvas)
    d.line((cx, cy, cx + 40 * scale, cy - 46 * scale), fill=color + (170,), width=3)
    for k in range(3):
        x = cx + (8 + k * 13) * scale
        y = cy - (10 + k * 15) * scale
        d.ellipse((x - 7 * scale, y - 4 * scale, x + 7 * scale, y + 4 * scale),
                  fill=color + (130,))


sprig(820, 610, 1.0, SEASON_C["spring"], 31)
sprig(120, 1010, 1.0, SEASON_C["summer"], 32)
sprig(830, 1180, 1.0, SEASON_C["autumn"], 33)
sprig(200, 1300, 1.0, SEASON_C["winter"], 34)

# 顶部大标题（柔和，非粗大）
d.text((170, 40), "四季 · 生活长卷", font=ImageFont.truetype(F_KAI, 54), fill=INK + (225,))
d.text((176, 108), "A YEAR IN PAGES", font=f_en, fill=INK_L + (215,))
d.text((404, 110), "/  春夏秋冬", font=ImageFont.truetype(F_KAI, 24), fill=INK_L + (215,))

# ================= 收尾：触边检测 + 保存 =================
from PIL import Image as _Im
final = canvas.convert("RGB")
for (season, cn, en, poem, cx, cy, w, h, ang, shape, seed) in SEASONS:
    sl = photo_slot(shape, w, h, season, seed).rotate(ang, Image.BICUBIC, expand=True)
    x0 = int(cx - sl.width / 2)
    y0 = int(cy - sl.height / 2)
    assert x0 > 0 and y0 > 0 and x0 + sl.width < W and y0 + sl.height < H, "照片位触边: %s" % season

final.save(OUT, quality=94)
print("saved:", OUT, final.size)
