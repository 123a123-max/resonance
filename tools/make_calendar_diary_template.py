# -*- coding: utf-8 -*-
"""时光日历日记拼贴 9:16 模板。

方格日历做固定骨架（背景网格 + 日期数字），碎片化日记式错落排版；
温暖浅色暖调（暖米/浅杏）、哑光书写纸轻微做旧；
拍立得照片位（大、错落倾斜）、复古邮票、邮戳、日期印章、手写日记文字、
小众便签、迷你贴纸、细和纸胶带。装饰克制、全部位于照片上层保证展露。
无撞色/夸张涂鸦/超大粗标题/拥挤杂乱。

照片位坐标与 src/collage/templateStyles.ts 中 calendar-diary 的 slots 一致。
"""
import os
import math
import random
import calendar
from datetime import date
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import template_common as C

random.seed(17)

# ---- 当前日期（所有文字/数字随系统时间自动变化）----
TODAY = date.today()
DAY = TODAY.day
MON_ABBR = TODAY.strftime("%b").upper()          # NOV
MON_FULL = TODAY.strftime("%B").upper()          # NOVEMBER
MON_CN = "%d月" % TODAY.month                    # 11月
WEEK_EN = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][TODAY.weekday()]
DAYS_IN_MONTH = calendar.monthrange(TODAY.year, TODAY.month)[1]

W, H = C.W, C.H
OUT = os.path.join(C.OUT_DIR, "template-calendar-diary.jpg")

# ---- 字体 ----
F_CN_KAI = C.font("C:/Windows/Fonts/STKAITI.TTF", 30)      # 行楷（手写日记）
F_CN_XIN = C.font("C:/Windows/Fonts/STXINGKA.TTF", 62)     # 书法标题
F_EN = C.font("C:/Windows/Fonts/georgia.ttf", 40)
F_EN_I = C.font("C:/Windows/Fonts/georgiai.ttf", 26)
F_EN_B = C.font("C:/Windows/Fonts/arialbd.ttf", 22)
F_EN_S = C.font("C:/Windows/Fonts/georgia.ttf", 18)

# ---- 暖调配色 ----
PAPER = (247, 239, 224, 255)
GRID = (223, 207, 181, 120)
INK = (138, 104, 74, 220)
INK_L = (172, 143, 112, 175)
SEAL = (168, 88, 68, 180)       # 柔和砖红（印章/邮戳）
NOTE = (250, 233, 192, 255)
EDGE = (192, 166, 132, 190)

# 照片位 (x, y, w, h, angle)
SLOTS = [
    (245, 520, 350, 330, -7),
    (658, 630, 340, 315, 6),
    (252, 1035, 340, 320, 5),
    (650, 1150, 352, 325, -6),
]


def place(layer, cx, cy, ang=0):
    if ang:
        layer = layer.rotate(ang, resample=Image.BICUBIC, expand=True)
    return layer, (int(cx - layer.width / 2), int(cy - layer.height / 2))


def photo_slot_polaroid(w, h, caption):
    """拍立得照片位：照片区严格 w×h 居中于图层（照片区中心=图层中心，与前端槽位对齐）。"""
    pad = 20
    L = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.rectangle((pad, pad, pad + w, pad + h), fill=PAPER, outline=EDGE, width=2)
    d.rectangle((pad + 7, pad + 7, pad + w - 7, pad + h - 7), outline=(206, 186, 156, 150), width=1)
    d.text((pad + 12, pad + h + 2), caption, font=F_EN_S, fill=(150, 120, 88, 190))
    return L


def draw_calendar_grid(canvas):
    """方格日历骨架：淡杏色方格 + 星期 + 日期数字，作为底层骨架。"""
    d = ImageDraw.Draw(canvas)
    left, top = 48, 250
    col_w, row_h = 115, 148
    # 方格
    for i in range(8):
        x = left + i * col_w
        d.line((x, top, x, min(H - 40, top + 9 * row_h)), fill=GRID, width=1)
    for j in range(10):
        y = top + j * row_h
        if y > H - 40:
            break
        d.line((left, y, left + 7 * col_w, y), fill=GRID, width=1)
    # 星期
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    for i, day in enumerate(days):
        d.text((left + i * col_w + 8, top - 30), day, font=F_EN_S,
               fill=(176, 148, 116, 165))
    # 日期数字（1~当月天数），淡色若隐若现；当天用砖红高亮
    num = 1
    for j in range(9):
        for i in range(7):
            if num > DAYS_IN_MONTH:
                break
            x = left + i * col_w + 9
            y = top + j * row_h + 8
            if y > H - 60:
                break
            col = (198, 172, 140, 135)
            if num == DAY:
                col = SEAL
            d.text((x, y), "%02d" % num, font=F_EN_S, fill=col)
            num += 1


def postage_stamp(w=78, h=94):
    """齿孔邮票：暖米底 + 齿孔边 + 简约图案 + 面值。"""
    s = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    d.rectangle((5, 5, w - 6, h - 6), fill=(243, 226, 196, 255), outline=EDGE, width=1)
    # 齿孔
    for x in range(5, w - 5, 10):
        d.ellipse((x - 3, 0, x + 3, 9), fill=(247, 239, 224, 255))
        d.ellipse((x - 3, h - 10, x + 3, h - 1), fill=(247, 239, 224, 255))
    for y in range(5, h - 5, 10):
        d.ellipse((0, y - 3, 9, y + 3), fill=(247, 239, 224, 255))
        d.ellipse((w - 10, y - 3, w - 1, y + 3), fill=(247, 239, 224, 255))
    # 简约图案：小房子
    d.rectangle((22, 30, 56, 60), outline=(150, 104, 76, 210), width=2)
    d.polygon([(18, 30), (39, 16), (60, 30)], outline=(150, 104, 76, 210))
    d.line((18, 30, 60, 30), fill=(150, 104, 76, 210), width=2)
    d.text((10, 10), "POSTAGE", font=C.font("C:/Windows/Fonts/arial.ttf", 9), fill=(150, 112, 80, 200))
    d.text((w - 26, h - 22), "%02d" % DAY, font=C.font("C:/Windows/Fonts/arialbd.ttf", 12), fill=(150, 112, 80, 220))
    return s


def postmark(size=112, text=None, seed=3):
    if text is None:
        text = "%s %02d %d" % (MON_ABBR, DAY, TODAY.year)
    """复古邮戳：双圈 + 波浪注销线 + 文字，柔和砖红。"""
    p = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(p)
    ink = SEAL
    c = size // 2
    d.ellipse((8, 8, size - 8, size - 8), outline=ink, width=3)
    d.ellipse((17, 17, size - 17, size - 17), outline=ink, width=1)
    f = C.font("C:/Windows/Fonts/arialbd.ttf", 11)
    bb = d.textbbox((0, 0), text, font=f)
    d.text((c - (bb[2] - bb[0]) / 2, c - 20), text, font=f, fill=ink)
    d.text((c - 12, c + 2), "POST", font=C.font("C:/Windows/Fonts/arialbd.ttf", 12), fill=ink)
    for i in range(3):
        y = c + 24 + i * 7
        pts = [(12 + k, y + 3 * math.sin(k / 7.0)) for k in range(0, size - 24, 5)]
        d.line(pts, fill=ink, width=2)
    return p.rotate(random.Random(seed).uniform(-20, 20), Image.BICUBIC, expand=True)


def date_seal(size=140):
    """日期印章：双线方框 + 大号当天日期 + 月份 + 星期，跟随系统时间。"""
    s = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    d.rounded_rectangle((6, 6, size - 6, size - 6), radius=8, outline=SEAL, width=4)
    d.rounded_rectangle((14, 14, size - 14, size - 14), radius=5, outline=SEAL, width=1)
    f_m = C.font("C:/Windows/Fonts/arial.ttf", 13 if len(MON_FULL) <= 8 else 10)
    mb = d.textbbox((0, 0), MON_FULL, font=f_m)
    d.text(((size - (mb[2] - mb[0])) / 2, 16), MON_FULL, font=f_m, fill=SEAL)
    f_d = C.font("C:/Windows/Fonts/georgia.ttf", 56)
    db = d.textbbox((0, 0), "%02d" % DAY, font=f_d)
    d.text(((size - (db[2] - db[0])) / 2, 36), "%02d" % DAY, font=f_d, fill=SEAL)
    f_w = C.font("C:/Windows/Fonts/arial.ttf", 12)
    wb = d.textbbox((0, 0), WEEK_EN, font=f_w)
    d.text(((size - (wb[2] - wb[0])) / 2, size - 26), WEEK_EN, font=f_w, fill=SEAL)
    return s.rotate(-8, Image.BICUBIC, expand=True)


def sticky_note(w=196, h=170):
    """便签：浅黄小方纸 + 手写小字 + 折角。"""
    n = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(n)
    d.rectangle((0, 0, w - 1, h - 1), fill=NOTE, outline=(214, 190, 150, 200), width=1)
    d.polygon([(w - 30, h), (w, h - 30), (w, h)], fill=(232, 210, 170, 255))
    lines = ["今天的风很轻，", "阳光刚好落在窗台。", "把这一刻，", "好好收进日记里。"]
    for i, t in enumerate(lines):
        d.text((18, 20 + i * 34), t, font=C.font("C:/Windows/Fonts/STKAITI.TTF", 20),
               fill=(128, 96, 68, 225))
    return n


def handwriting(canvas, lines, x, y, angle=-4):
    """斜向手写日记文字（真实行楷小字 + 淡手绘衬线）。"""
    layer = Image.new("RGBA", (560, 240), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = C.font("C:/Windows/Fonts/STKAITI.TTF", 27)
    for i, t in enumerate(lines):
        d.text((10, i * 52), t, font=f, fill=(140, 106, 76, 205))
    layer = layer.rotate(angle, Image.BICUBIC, expand=True)
    canvas.alpha_composite(layer, (x, y))


def mini_stickers(canvas):
    """迷你贴纸：少量小圆点、小星、小爱心，暖色克制。"""
    d = ImageDraw.Draw(canvas)
    # 小星
    C.star(d, 812, 460, 11, (168, 120, 84, 190), width=2)
    C.star(d, 120, 880, 9, (168, 120, 84, 170), width=2)
    C.star(d, 470, 1380, 8, (168, 120, 84, 160), width=2)
    # 小圆点
    for (x, y, r) in [(800, 900, 4), (110, 700, 4), (520, 700, 3), (830, 1300, 4)]:
        d.ellipse((x - r, y - r, x + r, y + r), fill=(178, 132, 96, 170))
    # 小爱心（双圆 + 三角近似）
    for (x, y) in [(430, 1480), (760, 470)]:
        d.ellipse((x - 9, y - 9, x, y), fill=(168, 92, 72, 175))
        d.ellipse((x, y - 9, x + 9, y), fill=(168, 92, 72, 175))
        d.polygon([(x - 9, y - 2), (x + 9, y - 2), (x, y + 12)], fill=(168, 92, 72, 175))


def tape(canvas, x, y, w, h, angle, color=(206, 180, 142, 120)):
    t = Image.new("RGBA", (w, h), color)
    d = ImageDraw.Draw(t)
    for i in range(0, w, 7):
        d.line((i, 0, i, h), fill=(252, 240, 214, 55), width=1)
    layer, pos = place(t, x, y, angle)
    canvas.alpha_composite(layer, pos)


def main():
    # 暖米到浅杏渐变 + 书写纸纤维 + 轻颗粒 + 轻微做旧斑
    canvas = C.gradient_bg([
        (0.0, (250, 243, 230)),
        (0.5, (247, 238, 222)),
        (1.0, (242, 231, 211)),
    ])
    C.add_paper_fibers(canvas, (198, 176, 146), count=520, alpha=15, seed=5)
    C.add_grain(canvas, amount=3, alpha=9, seed=4)
    # 做旧茶渍
    stain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stain)
    rnd = random.Random(8)
    for _ in range(10):
        cx, cy = rnd.randint(0, W), rnd.randint(0, H)
        r = rnd.randint(60, 150)
        sd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(196, 160, 110, 12))
    stain = stain.filter(ImageFilter.GaussianBlur(28))
    canvas.alpha_composite(stain)

    # 方格日历骨架
    draw_calendar_grid(canvas)

    # 顶部标题（纤细，不夸张）
    d = ImageDraw.Draw(canvas)
    d.text((60, 74), TODAY.strftime("%B"), font=F_EN, fill=INK)
    d.text((62, 128), "%s · 时光日记" % MON_CN, font=F_CN_KAI, fill=INK_L)
    d.line((60, 180, 470, 180), fill=(200, 176, 142, 150), width=2)

    # 4 个拍立得照片位（大、错落、倾斜）；照片区中心=图层中心，与槽位对齐
    caps = ["%02d %s" % (DAY, MON_ABBR), "AUTUMN DAYS", "MOMENTS", "KEEP THIS"]
    for (x, y, w, h, ang), cap in zip(SLOTS, caps):
        frame = photo_slot_polaroid(w, h, cap)
        layer, pos = place(frame, x, y, ang)
        canvas.alpha_composite(layer, pos)

    # ---- 装饰（全部在照片上层，保证展露）----
    # 日期印章：放在照片1与照片3之间的横向空隙（y705-855），不压日历星期行
    seal = date_seal(126)
    layer, pos = place(seal, 250, 785, 8)
    canvas.alpha_composite(layer, pos)

    # 邮票：顶部右侧空隙，往左移避免贴边
    st = postage_stamp(70, 84).rotate(6, Image.BICUBIC, expand=True)
    canvas.alpha_composite(st, (774, 214))

    # 邮戳：压在邮票下方，稍往左，不贴边
    pm = postmark(96, "%s %02d" % (MON_ABBR, DAY), seed=6)
    layer, pos = place(pm, 790, 332, 0)
    canvas.alpha_composite(layer, pos)

    # 便签（右下，照片4下方空隙）
    note = sticky_note(190, 164).rotate(-5, Image.BICUBIC, expand=True)
    canvas.alpha_composite(note, (630, 1362))
    tape(canvas, 724, 1364, 52, 20, -5)

    # 手写日记文字（左侧下空隙，照片3下方）
    handwriting(canvas, ["清晨的光，", "落在旧日历上。"], 72, 1288, -4)

    # 迷你贴纸
    mini_stickers(canvas)

    # 胶带贴在照片角（少量）
    tape(canvas, 180, 360, 54, 18, -18)
    tape(canvas, 828, 486, 50, 18, 14)

    # 底部小字署名
    d = ImageDraw.Draw(canvas)
    d.text((62, 1544), "a little diary of ordinary days", font=F_EN_I, fill=(160, 130, 100, 180))

    C.save_out(canvas, "template-calendar-diary.jpg")
    print("slots:", SLOTS)


if __name__ == "__main__":
    main()
