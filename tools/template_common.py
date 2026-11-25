# -*- coding: utf-8 -*-
"""拼贴模板通用绘制工具库（纯 PIL，无 numpy / OpenCV）。

被 tools/make_templates_batch.py 及各 make_*_template.py 复用。
画布统一 900×1600（9:16）；照片位统一矩形系，保证照片内容不被裁。
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops

W, H = 900, 1600

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_ROOT = os.path.join(ROOT, "public", "assets", "collage")
OUT_DIR = os.path.join(ROOT, "public", "assets", "collage")


# ---------------- 字体 ----------------
def font(cn_path, size):
    """按给定路径加载字体，退化到系统默认。"""
    for p in cn_path if isinstance(cn_path, (list, tuple)) else [cn_path]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


FONT_CN = font(["C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/simhei.ttf"], 96)
FONT_CN_M = font(["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"], 34)
FONT_CN_S = font(["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"], 24)
FONT_EN = font(["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/calibrib.ttf"], 40)
FONT_EN_S = font(["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/calibri.ttf"], 24)
FONT_SERIF = font(["C:/Windows/Fonts/georgia.ttf", "C:/Windows/Fonts/times.ttf"], 44)


def load(folder, name):
    """从风格素材目录载入图片。name 含扩展名。找不到时返回 None。"""
    p = os.path.join(ASSET_ROOT, folder, name)
    if not os.path.exists(p):
        p2 = os.path.join(ASSET_ROOT, name)
        if not os.path.exists(p2):
            return None
    return Image.open(p).convert("RGB")


def fit(im, w, h=None):
    if h is None:
        h = im.height * w / im.width
    s = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


def cover(im, size):
    tw, th = size
    s = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    x = (im.width - tw) // 2
    y = (im.height - th) // 2
    return im.crop((x, y, x + tw, y + th))


# ---------------- 背景与纹理 ----------------
def gradient_bg(stops, glows=()):
    """垂直渐变 + 可选柔和光晕。stops=[(0~1, (r,g,b)), ...]"""
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    for i in range(len(stops) - 1):
        y0, c0 = stops[i]
        y1, c1 = stops[i + 1]
        a, b = int(y0 * H), int(y1 * H)
        for y in range(a, b):
            t = (y - a) / max(1, b - a)
            c = tuple(int(c0[k] * (1 - t) + c1[k] * t) for k in range(3))
            d.line((0, y, W, y), fill=c)
    bg = bg.convert("RGBA")
    for cx, cy, r, col, strength in glows:
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).ellipse((cx - r, cy - r, cx + r, cy + r), fill=int(255 * strength))
        mask = mask.filter(ImageFilter.GaussianBlur(r * 0.4))
        glow = Image.new("RGBA", (W, H), col + (0,))
        glow.putalpha(mask)
        bg.alpha_composite(glow)
    return bg


def solid_bg(color):
    return Image.new("RGBA", (W, H), color + (255,))


def add_grain(canvas, amount=6, alpha=16, seed=1):
    """细腻颗粒（很轻，避免粗糙噪点）。"""
    rnd = random.Random(seed)
    g = Image.new("L", (W, H))
    g.putdata([rnd.randint(128 - amount, 128 + amount) for _ in range(W * H)])
    g = g.filter(ImageFilter.GaussianBlur(0.4))
    layer = Image.merge("RGBA", (g, g, g, Image.new("L", (W, H), alpha)))
    canvas.alpha_composite(layer)


def add_halftone(canvas, color, cell=9, dot_max=3, alpha=40, seed=2):
    """半色调网点（波普/复古印刷感）。"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(seed)
    for gy in range(0, H, cell):
        for gx in range(0, W, cell):
            r = rnd.uniform(0.5, dot_max)
            d.ellipse((gx, gy, gx + r * 2, gy + r * 2), fill=color + (alpha,))
    canvas.alpha_composite(layer)


def add_paper_fibers(canvas, color, count=900, alpha=28, seed=3):
    """宣纸/和纸纤维纹理：随机短线。"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(seed)
    for _ in range(count):
        x = rnd.randint(0, W)
        y = rnd.randint(0, H)
        ln = rnd.randint(4, 22)
        ang = rnd.uniform(-0.5, 0.5)
        x2 = x + int(ln * math.cos(ang))
        y2 = y + int(ln * math.sin(ang))
        d.line((x, y, x2, y2), fill=color + (rnd.randint(alpha // 2, alpha),), width=1)
    canvas.alpha_composite(layer)


def add_vignette(canvas, strength=0.22, color=(60, 55, 50)):
    """四周柔和暗角。"""
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    steps = 26
    for i in range(steps):
        v = int(255 * strength * (i / steps) ** 2)
        m = 18 * i
        d.rectangle((m, m, W - m, H - m), outline=255 - v, width=1)
    # 用渐变椭圆近似暗角
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    for i in range(40):
        inset = int(i * 9)
        v = int(255 * strength * (1 - i / 40) ** 1.6)
        if W - 2 * inset <= 0 or H - 2 * inset <= 0:
            break
        d.rectangle((inset, inset, W - inset, H - inset), outline=v, width=9)
    mask = mask.filter(ImageFilter.GaussianBlur(60))
    vg = Image.new("RGBA", (W, H), color + (0,))
    vg.putalpha(mask)
    canvas.alpha_composite(vg)


# ---------------- 图层变换 ----------------
def place(canvas, layer, cx, cy, ang=0):
    if ang:
        layer = layer.rotate(ang, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def white_to_alpha(im, lo=225, hi=252):
    """白/浅色背景转透明（保留彩色主体）。"""
    rgb = im.convert("RGB")
    v = min(rgb.split())
    lut = [0 if x <= lo else (255 if x >= hi else int(255 * (x - lo) / (hi - lo))) for x in range(256)]
    # 取三通道最小值做遮罩：任一通道偏暗即保留
    a = v.point(lambda x: 255 - lut[x])
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out


def cut_by_channel(im, channel, lo, hi, invert=False):
    """按 HSV 的 V/S 通道抠图（古籍植物素材有效）。"""
    rgb = im.convert("RGB")
    ch = rgb.convert("HSV").split()[0 if channel == "V" else 1]
    if invert:
        lut = [255 if x <= lo else (0 if x >= hi else int(255 * (hi - x) / (hi - lo))) for x in range(256)]
    else:
        lut = [0 if x <= lo else (255 if x >= hi else int(255 * (x - lo) / (hi - lo))) for x in range(256)]
    a = ch.point(lut).filter(ImageFilter.GaussianBlur(0.7))
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out


def trim_transparent(im):
    bb = im.getchannel("A").getbbox()
    return im.crop(bb) if bb else im


def torn_edges(layer, seed=0, amp=7, color=None):
    """给矩形图层做手撕毛边。"""
    w, h = layer.size
    rnd = random.Random(seed)
    m = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(m)
    step = 12
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
    m = m.filter(ImageFilter.GaussianBlur(1))
    if color:
        base = Image.new("RGBA", (w, h), color + (255,))
        base.alpha_composite(layer)
        base.putalpha(ImageChops.multiply(base.getchannel("A"), m))
        return base
    out = layer.copy()
    out.putalpha(ImageChops.multiply(out.getchannel("A"), m))
    return out


def outline(layer, color=(28, 26, 24), width=5):
    """粗轮廓（MaxFilter 需奇数尺寸）。"""
    a = layer.getchannel("A")
    k = width * 2 + 1
    if k % 2 == 0:
        k += 1
    grow = a.filter(ImageFilter.MaxFilter(k))
    inner = a.filter(ImageFilter.MaxFilter(max(1, width)))
    ring = ImageChops.subtract(grow, inner)
    r = Image.new("RGBA", layer.size, color + (255,))
    r.putalpha(ring)
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(r)
    out.alpha_composite(layer)
    return out


# ---------------- 照片位 ----------------
def photo_slot(shape, w, h, seed=1, num=None, doc_color=(248, 247, 243)):
    """矩形系照片位（不裁照片内容），返回 RGBA 图层。"""
    pad = 16
    L = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    bx = (pad, pad, pad + w, pad + h)
    if shape == "torn":
        white = Image.new("RGBA", L.size, (255, 255, 255, 0))
        wd = ImageDraw.Draw(white)
        wd.rectangle(bx, fill=(255, 255, 255, 255))
        white = torn_edges(white, seed=seed, amp=8)
        L.alpha_composite(white)
        d = ImageDraw.Draw(L)
        d.rectangle((pad + 6, pad + 6, pad + w - 6, pad + h - 6),
                    fill=doc_color + (255,), outline=(210, 205, 196, 220), width=2)
    elif shape == "polaroid":
        paper_h = int(h * 1.16)
        d.rounded_rectangle((pad, pad, pad + w, pad + paper_h), radius=3,
                            fill=(255, 255, 255, 255))
        d.rectangle((pad + 8, pad + 8, pad + w - 8, pad + h + 8),
                    fill=doc_color + (255,), outline=(214, 210, 202, 230), width=2)
    elif shape == "rounded":
        d.rounded_rectangle((pad, pad, pad + w, pad + h), radius=26,
                            fill=doc_color + (255,), outline=(255, 255, 255, 240), width=3)
        d.rounded_rectangle((pad + 5, pad + 5, pad + w - 5, pad + h - 5), radius=22,
                            outline=(206, 202, 194, 200), width=1)
    elif shape == "frame":
        d.rectangle(bx, fill=doc_color + (255,), outline=(255, 255, 255, 245), width=4)
        d.rectangle((pad + 4, pad + 4, pad + w - 4, pad + h - 4),
                    outline=(198, 194, 186, 210), width=1)
    else:  # frost
        d.rounded_rectangle(bx, radius=18, fill=(250, 253, 255, 205),
                            outline=(255, 255, 255, 245), width=3)
        d.rounded_rectangle((pad + 6, pad + 6, pad + w - 6, pad + h - 6), radius=13,
                            fill=(246, 248, 250, 245))
    if num is not None:
        d.text((pad + 10, pad + 8), "%02d" % num, font=FONT_EN_S, fill=(150, 146, 138, 200))
    return L


def draw_title(canvas, text, x, y, fnt=FONT_CN, color=(40, 38, 36, 245),
               sub=None, sub_color=(110, 104, 96, 230), en=None):
    """绘制大标题 + 可选中文副标 + 英文标签。"""
    d = ImageDraw.Draw(canvas)
    d.text((x, y), text, font=fnt, fill=color)
    if sub:
        d.text((x + 4, y + fnt.size + 14), sub, font=FONT_CN_M, fill=sub_color)
    if en:
        d.text((x + 4, y + fnt.size + (58 if sub else 16)), en, font=FONT_EN_S, fill=sub_color)


def jline(d, pts, color, width=2, wobble=2, seed=0):
    """手绘抖动线条。"""
    rnd = random.Random(seed)
    jittered = [(x + rnd.randint(-wobble, wobble), y + rnd.randint(-wobble, wobble)) for x, y in pts]
    d.line(jittered, fill=color, width=width, joint="curve")


def star(d, cx, cy, r, color, width=3):
    """手绘四角星芒。"""
    d.line((cx - r, cy, cx + r, cy), fill=color, width=width)
    d.line((cx, cy - r, cx, cy + r), fill=color, width=width)
    d.line((cx - r // 2, cy - r // 2, cx + r // 2, cy + r // 2), fill=color, width=width - 1)
    d.line((cx + r // 2, cy - r // 2, cx - r // 2, cy + r // 2), fill=color, width=width - 1)


def save_out(canvas, name):
    path = os.path.join(OUT_DIR, name)
    canvas.convert("RGB").save(path, quality=94)
    print("saved:", path)
    return path
