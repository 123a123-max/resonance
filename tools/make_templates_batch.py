# -*- coding: utf-8 -*-
"""批量生成 11 种风格的 9:16 拼贴模板（清新绿调/波普都市/科技磨砂已单独完成）。

策略：程序绘制为主 + 复用现有免费授权素材（paper/fern/stamp/label/grain 等）。
每个风格都遵循用户强约定：照片位大、摆放随意自由（错落+倾斜）、矩形系不裁内容、配大标题。
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops
import template_common as C

W, H = C.W, C.H

# 4 个大照片位（中心 x,y / 宽高 / 角度 / 形状）—— 与 templateStyles.ts 的 DEFAULT_SLOTS 一致
SLOTS = [
    (245, 560, 340, 320, -8, 'torn'),
    (655, 700, 350, 285, 7, 'polaroid'),
    (258, 1045, 330, 330, 6, 'rounded'),
    (660, 1135, 345, 310, -7, 'frame'),
]


def add_slots(canvas, doc_color=(248, 247, 243)):
    for i, (x, y, w, h, ang, shape) in enumerate(SLOTS, 1):
        C.place(canvas, C.photo_slot(shape, w, h, seed=i, num=i, doc_color=doc_color), x, y, ang)


def washi_tape(canvas, x, y, w=70, h=20, ang=0, color=(210, 205, 190)):
    """和纸胶带。"""
    layer = Image.new("RGBA", (w, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    col = color + (185,)
    d.rectangle((0, 0, w, h), fill=col)
    rnd = random.Random(int(x + y))
    for i in range(0, w, 6):
        d.line((i, 0, i, h), fill=(255, 255, 255, 40), width=1)
        d.line((i + 2, h, i + 2, h + 4), fill=col, width=2)
    layer = layer.rotate(ang, expand=True)
    canvas.alpha_composite(layer, (int(x - layer.width / 2), int(y - layer.height / 2)))


def sticker_label(canvas, x, y, text, w=190, h=52, ang=-6, bg=(255, 253, 246), fg=(90, 84, 76)):
    """复古英文/中文小标签。"""
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=6, fill=bg + (245,), outline=(180, 172, 160, 220), width=2)
    d.text((12, h // 2 - 12), text, font=C.FONT_EN_S, fill=fg + (250,))
    layer = layer.rotate(ang, expand=True)
    canvas.alpha_composite(layer, (int(x - layer.width / 2), int(y - layer.height / 2)))


def draw_plant_sprig(canvas, x, y, scale=1.0, color=(120, 140, 110), ang=0, seed=0):
    """程序绘制手绘枝叶。"""
    layer = Image.new("RGBA", (int(180 * scale), int(220 * scale)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(seed)
    sx, sy = layer.width / 2, layer.height
    C.jline(d, [(sx, sy - 4), (sx + rnd.randint(-10, 10), sy - 90 * scale),
                (sx + rnd.randint(-16, 16), sy - 190 * scale)], color + (200,), 3, 3, seed)
    for i in range(7):
        ly = sy - (25 + i * 24) * scale
        side = -1 if i % 2 else 1
        lx = sx + side * (8 + i * 2) * scale
        L = (26 + rnd.randint(-6, 8)) * scale
        d.ellipse((lx if side > 0 else lx - L, ly - 8 * scale,
                   lx + L if side > 0 else lx, ly + 8 * scale), fill=color + (150,))
    layer = layer.rotate(ang, expand=True)
    canvas.alpha_composite(layer, (int(x - layer.width / 2), int(y - layer.height / 2)))


def draw_flower(canvas, x, y, r=22, color=(230, 190, 200), petals=6, seed=0):
    """程序绘制小碎花。"""
    d = ImageDraw.Draw(canvas)
    rnd = random.Random(seed)
    for i in range(petals):
        a = 2 * math.pi * i / petals
        cx = x + int(r * 0.6 * math.cos(a))
        cy = y + int(r * 0.6 * math.sin(a))
        d.ellipse((cx - r // 2, cy - r // 2, cx + r // 2, cy + r // 2), fill=color + (220,))
    d.ellipse((x - r // 3, y - r // 3, x + r // 3, y + r // 3), fill=(245, 220, 150, 240))


def draw_bow(canvas, x, y, size=26, color=(240, 190, 200)):
    d = ImageDraw.Draw(canvas)
    d.ellipse((x - size, y - size // 2, x - 3, y + size // 2), fill=color + (230,))
    d.ellipse((x + 3, y - size // 2, x + size, y + size // 2), fill=color + (230,))
    d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(255, 240, 235, 250))


def draw_star(canvas, x, y, r, color):
    C.star(ImageDraw.Draw(canvas), x, y, r, color + (220,), width=3)


# ============================================================
# 1. INS 极简留白高级拼贴
# ============================================================
def make_ins_minimal():
    canvas = C.gradient_bg([(0, (243, 240, 234)), (0.5, (236, 233, 227)), (1, (228, 224, 216))],
                           glows=[(700, 300, 380, (255, 255, 255), 0.3)])
    d = ImageDraw.Draw(canvas)
    # 莫兰迪色块（克制）
    d.rectangle((60, 90, 230, 260), fill=(206, 198, 186, 120))
    d.ellipse((720, 1180, 860, 1320), fill=(188, 178, 166, 90))
    # 细线条
    d.line((90, 300, 340, 300), fill=(150, 142, 130, 160), width=2)
    d.line((560, 1380, 820, 1380), fill=(150, 142, 130, 160), width=2)
    # 手绘植物（风干植物，简笔）
    draw_plant_sprig(canvas, 760, 520, 1.1, (150, 148, 132), -8, 11)
    draw_plant_sprig(canvas, 120, 1180, 0.9, (156, 150, 136), 12, 12)
    # 陶瓷器皿剪影
    d = ImageDraw.Draw(canvas)
    d.ellipse((735, 600, 835, 690), fill=(212, 206, 196, 170))
    d.rectangle((752, 660, 818, 720), fill=(212, 206, 196, 170))
    C.add_grain(canvas, amount=4, alpha=12, seed=1)
    C.draw_title(canvas, "留 白", 70, 120, C.FONT_CN, (78, 74, 68, 240),
                 sub="克制 · 松弛 · 高级", en="LESS IS MORE / INS STYLE")
    add_slots(canvas, doc_color=(250, 248, 243))
    d = ImageDraw.Draw(canvas)
    d.text((70, 1510), "SLOW LIVING · 2026", font=C.FONT_EN_S, fill=(150, 142, 132, 220))
    return C.save_out(canvas, "template-ins-minimal.jpg")


# ============================================================
# 2. 日系盐系胶片拼贴
# ============================================================
def make_japanese_salt():
    canvas = C.gradient_bg([(0, (222, 228, 226)), (0.5, (208, 218, 216)), (1, (196, 208, 206))])
    C.add_paper_fibers(canvas, (150, 158, 150), count=700, alpha=22, seed=2)
    C.add_grain(canvas, amount=8, alpha=20, seed=3)
    C.add_vignette(canvas, strength=0.3, color=(90, 96, 92))
    d = ImageDraw.Draw(canvas)
    # 手撕纸片（复用纸张素材）
    paper = C.load("", "paper-4.jpg")
    if paper:
        p = C.fit(paper, 300)
        p = C.torn_edges(p.convert("RGBA"), seed=4, amp=9)
        C.place(canvas, p, 700, 440, 8)
    # 绿植枝叶
    draw_plant_sprig(canvas, 130, 570, 1.0, (110, 132, 112), -10, 21)
    draw_plant_sprig(canvas, 780, 1290, 0.95, (116, 136, 116), 14, 22)
    C.draw_title(canvas, "盐 系 日 常", 66, 112, C.FONT_CN, (62, 74, 70, 235),
                 sub="安静 · 治愈 · 清冷", en="JAPANESE SALT / FILM")
    add_slots(canvas, doc_color=(246, 245, 238))
    washi_tape(canvas, 190, 430, 68, 20, -18, (172, 182, 172))
    washi_tape(canvas, 720, 950, 72, 20, 14, (180, 190, 178))
    sticker_label(canvas, 740, 760, "coffee & light", 190, 50, -7, (246, 244, 234), (96, 106, 98))
    d = ImageDraw.Draw(canvas)
    d.text((70, 1510), "small moments, quietly kept", font=C.FONT_EN_S, fill=(100, 112, 104, 220))
    return C.save_out(canvas, "template-japanese-salt.jpg")


# ============================================================
# 3. 美式复古杂志拼贴
# ============================================================
def make_american_retro():
    canvas = C.gradient_bg([(0, (222, 200, 158)), (0.5, (214, 188, 142)), (1, (204, 174, 128))])
    C.add_halftone(canvas, (120, 80, 50), cell=10, dot_max=2.4, alpha=36, seed=5)
    C.add_grain(canvas, amount=10, alpha=22, seed=6)
    d = ImageDraw.Draw(canvas)
    # 撞色块
    d.rectangle((0, 0, 280, 200), fill=(178, 52, 46, 230))
    d.rounded_rectangle((650, 380, 890, 560), radius=8, fill=(44, 78, 136, 220))
    d.polygon([(40, 900), (220, 850), (180, 1050)], fill=(214, 150, 60, 200))
    # 老杂志碎片（复用标签/纸张）
    for folder, name, x, y, w, ang in [
        ("", "label-herbarium-14.jpg", 700, 900, 180, 9),
        ("", "paper-7.jpg", 120, 620, 200, -7),
    ]:
        im = C.load(folder, name)
        if im:
            p = C.torn_edges(C.fit(im, w).convert("RGBA"), seed=int(x), amp=9)
            C.place(canvas, p, x, y, ang)
    C.draw_title(canvas, "RETRO", 60, 82, C.FONT_EN, (250, 244, 226, 250))
    d = ImageDraw.Draw(canvas)
    d.text((66, 140), "MAGAZINE COLLAGE", font=C.FONT_EN_S, fill=(250, 240, 220, 240))
    d.text((66, 176), "复古杂志 · 年代复刻", font=C.FONT_CN_M, fill=(250, 238, 214, 235))
    add_slots(canvas, doc_color=(250, 242, 224))
    d = ImageDraw.Draw(canvas)
    d.text((70, 1510), "VINTAGE · BOLD · FREE", font=C.FONT_EN_S, fill=(90, 60, 40, 230))
    return C.save_out(canvas, "template-american-retro.jpg")


# ============================================================
# 4. 奶油马卡龙青春拼贴
# ============================================================
def make_macaron():
    canvas = C.gradient_bg([(0, (252, 238, 236)), (0.35, (250, 244, 228)),
                            (0.7, (232, 244, 236)), (1, (238, 232, 248))],
                           glows=[(450, 300, 420, (255, 255, 255), 0.3)])
    C.add_grain(canvas, amount=3, alpha=9, seed=7)
    d = ImageDraw.Draw(canvas)
    # 柔和色块
    d.ellipse((720, 120, 860, 260), fill=(246, 196, 206, 150))
    d.ellipse((40, 1260, 180, 1400), fill=(196, 226, 206, 150))
    # 碎花与蝴蝶结
    for (x, y, col) in [(130, 430, (244, 190, 202)), (780, 720, (198, 214, 244)),
                        (150, 980, (246, 218, 166)), (800, 1300, (222, 194, 240))]:
        draw_flower(canvas, x, y, 24, col, 6, seed=int(x))
    draw_bow(canvas, 770, 470, 30, (244, 190, 202))
    draw_bow(canvas, 140, 1220, 26, (200, 216, 246))
    # 星星
    for (x, y, col) in [(720, 980, (250, 214, 150)), (110, 700, (250, 214, 150))]:
        draw_star(canvas, x, y, 22, col)
    C.draw_title(canvas, "甜 心 小 记", 64, 106, C.FONT_CN, (120, 92, 106, 240),
                 sub="软乎乎 · 清新治愈", en="MACARON DREAM")
    add_slots(canvas, doc_color=(255, 252, 250))
    d = ImageDraw.Draw(canvas)
    d.text((70, 1510), "sweet & soft · everyday", font=C.FONT_EN_S, fill=(150, 120, 132, 220))
    return C.save_out(canvas, "template-macaron.jpg")


# ============================================================
# 6. 文艺宣纸书香拼贴
# ============================================================
def make_xuan_paper():
    canvas = C.gradient_bg([(0, (240, 232, 216)), (0.5, (234, 224, 204)), (1, (224, 212, 190))])
    C.add_paper_fibers(canvas, (150, 132, 104), count=1000, alpha=26, seed=8)
    C.add_grain(canvas, amount=6, alpha=14, seed=9)
    d = ImageDraw.Draw(canvas)
    # 淡墨晕染
    d.ellipse((680, 1080, 880, 1320), fill=(150, 140, 124, 40))
    d.ellipse((60, 360, 200, 520), fill=(150, 140, 124, 32))
    # 水墨花枝
    draw_plant_sprig(canvas, 760, 560, 1.15, (90, 84, 72), 8, 31)
    draw_plant_sprig(canvas, 140, 1280, 1.0, (96, 88, 76), -10, 32)
    # 火漆印章
    d.ellipse((720, 1420, 800, 1500), fill=(158, 62, 52, 220))
    d.ellipse((730, 1430, 790, 1490), outline=(196, 100, 86, 240), width=2)
    d.text((744, 1448), "印", font=C.FONT_CN_S, fill=(250, 230, 220, 240))
    # 古籍碎片（竖排文字块）
    d.rectangle((60, 700, 150, 860), fill=(230, 218, 194, 200), outline=(180, 160, 128, 180), width=1)
    for i in range(5):
        d.line((74, 720 + i * 26, 136, 720 + i * 26), fill=(120, 104, 80, 160), width=2)
    C.draw_title(canvas, "书 卷 气", 60, 100, C.FONT_CN, (72, 64, 52, 240),
                 sub="东方诗意 · 安静雅致", en="INK & PAPER / CLASSIC")
    add_slots(canvas, doc_color=(246, 238, 220))
    d = ImageDraw.Draw(canvas)
    d.text((70, 1510), "诗书 · 水墨 · 旧时光", font=C.FONT_CN_S, fill=(110, 96, 76, 220))
    return C.save_out(canvas, "template-xuan-paper.jpg")


# ============================================================
# 7. 街头极简潮流涂鸦拼贴
# ============================================================
def make_street_graffiti():
    canvas = C.solid_bg((26, 25, 24))
    d = ImageDraw.Draw(canvas)
    C.add_grain(canvas, amount=5, alpha=14, seed=10)
    # 荧光色块
    d.rectangle((0, 0, 180, 130), fill=(240, 224, 60, 235))
    d.ellipse((720, 1200, 880, 1400), fill=(244, 70, 92, 220))
    d.rectangle((740, 380, 880, 460), fill=(60, 200, 220, 220))
    # 粗黑手绘线条 + 涂鸦元素
    C.jline(d, [(80, 340), (260, 300), (400, 350)], (250, 250, 250, 230), 5, 6, 41)
    C.jline(d, [(620, 920), (820, 880)], (250, 250, 250, 230), 5, 6, 42)
    # 闪电
    d.polygon([(760, 600), (810, 540), (790, 620), (840, 610), (770, 720), (790, 640)],
              fill=(250, 220, 70, 240))
    # 星星与极简小卡通
    draw_star(canvas, 130, 1220, 34, (250, 220, 70))
    draw_star(canvas, 790, 1000, 26, (250, 100, 120))
    d.ellipse((110, 640, 170, 700), outline=(255, 255, 255, 220), width=4)
    d.ellipse((126, 656, 136, 666), fill=(255, 255, 255, 240))
    d.ellipse((146, 656, 156, 666), fill=(255, 255, 255, 240))
    C.draw_title(canvas, "STREET", 60, 76, C.FONT_EN, (250, 250, 250, 250))
    d = ImageDraw.Draw(canvas)
    d.text((66, 130), "涂鸦 · 潮流 · 克制", font=C.FONT_CN_M, fill=(244, 224, 70, 240))
    add_slots(canvas, doc_color=(250, 250, 248))
    d = ImageDraw.Draw(canvas)
    d.text((70, 1510), "URBAN · BOLD · MINIMAL", font=C.FONT_EN_S, fill=(220, 220, 220, 220))
    return C.save_out(canvas, "template-street-graffiti.jpg")


# ============================================================
# 8. 时光日历日记拼贴
# ============================================================
def make_calendar_diary():
    canvas = C.gradient_bg([(0, (246, 234, 214)), (0.5, (240, 226, 204)), (1, (232, 216, 192))])
    C.add_paper_fibers(canvas, (170, 150, 120), count=600, alpha=20, seed=11)
    C.add_grain(canvas, amount=5, alpha=13, seed=12)
    d = ImageDraw.Draw(canvas)
    # 方格日历底纹
    for gx in range(40, 900, 60):
        d.line((gx, 0, gx, H), fill=(190, 168, 136, 55), width=1)
    for gy in range(0, H, 60):
        d.line((0, gy, W, gy), fill=(190, 168, 136, 55), width=1)
    # 日期印章
    d.ellipse((730, 110, 850, 230), outline=(178, 84, 64, 210), width=4)
    d.text((760, 145), "24", font=C.FONT_EN, fill=(178, 84, 64, 230))
    d.text((752, 190), "NOV", font=C.FONT_EN_S, fill=(178, 84, 64, 220))
    # 邮票 + 邮戳（复用素材）
    for name, x, y, ang in [("stamp-2.jpg", 720, 930, 8), ("stamp-5.jpg", 120, 1320, -9)]:
        im = C.load("", name)
        if im:
            C.place(canvas, C.fit(im, 120).convert("RGBA"), x, y, ang)
    C.draw_title(canvas, "时 光 日 记", 60, 96, C.FONT_CN, (96, 78, 60, 240),
                 sub="温暖 · 私密 · 纪实", en="DAILY CALENDAR")
    add_slots(canvas, doc_color=(252, 246, 234))
    washi_tape(canvas, 700, 660, 70, 20, 12, (214, 190, 156))
    sticker_label(canvas, 730, 1200, "dear diary", 180, 48, -6, (252, 246, 230), (120, 96, 72))
    d = ImageDraw.Draw(canvas)
    d.text((70, 1510), "every day, a little memory", font=C.FONT_EN_S, fill=(130, 108, 84, 220))
    return C.save_out(canvas, "template-calendar-diary.jpg")


# ============================================================
# 9. 旅行复古手账拼贴
# ============================================================
def make_travel_journal():
    canvas = C.gradient_bg([(0, (226, 204, 168)), (0.5, (218, 192, 152)), (1, (206, 176, 134))])
    C.add_paper_fibers(canvas, (150, 120, 80), count=800, alpha=24, seed=13)
    C.add_grain(canvas, amount=9, alpha=20, seed=14)
    d = ImageDraw.Draw(canvas)
    # 地图线（虚线路径）
    C.jline(d, [(80, 420), (220, 380), (360, 460), (520, 400)], (140, 100, 66, 140), 3, 5, 51)
    C.jline(d, [(600, 1200), (740, 1160), (840, 1240)], (140, 100, 66, 140), 3, 5, 52)
    # 机票/票根（程序绘制）
    def ticket(x, y, w, h, ang, label):
        L = Image.new("RGBA", (w, h + 10), (0, 0, 0, 0))
        dd = ImageDraw.Draw(L)
        dd.rounded_rectangle((0, 0, w, h), radius=6, fill=(248, 238, 214, 240), outline=(170, 130, 90, 220), width=2)
        dd.line((w - 40, 6, w - 40, h - 6), fill=(180, 140, 100, 200), width=2)
        dd.text((12, h // 2 - 10), label, font=C.FONT_EN_S, fill=(120, 86, 56, 240))
        L = L.rotate(ang, expand=True)
        C.place(canvas, L, x, y)
    ticket(730, 520, 170, 70, 9, "BOARDING")
    ticket(140, 1290, 170, 70, -8, "TICKET")
    # 邮戳（复用）
    im = C.load("", "stamp-5.jpg")
    if im:
        C.place(canvas, C.fit(im, 110).convert("RGBA"), 760, 900, 12)
    C.draw_title(canvas, "旅 途 纪 念", 60, 96, C.FONT_CN, (90, 66, 44, 240),
                 sub="旧明信片 · 旅途碎片", en="TRAVEL JOURNAL")
    add_slots(canvas, doc_color=(250, 240, 218))
    washi_tape(canvas, 180, 620, 72, 20, -14, (196, 168, 126))
    d = ImageDraw.Draw(canvas)
    d.text((70, 1510), "collect moments, keep memories", font=C.FONT_EN_S, fill=(120, 92, 62, 220))
    return C.save_out(canvas, "template-travel-journal.jpg")


# ============================================================
# 11. 四季叙事手账长卷拼贴（9:16 竖版四段）
# ============================================================
def make_four_seasons():
    canvas = C.gradient_bg([(0, (248, 232, 234)), (0.25, (232, 242, 224)),
                            (0.5, (232, 238, 220)), (0.75, (246, 230, 210)),
                            (1, (232, 234, 240))])
    C.add_grain(canvas, amount=4, alpha=11, seed=15)
    d = ImageDraw.Draw(canvas)
    # 四段分色带
    bands = [(0, 400, (244, 200, 210, 55)), (400, 800, (198, 226, 190, 55)),
             (800, 1200, (242, 206, 168, 55)), (1200, 1600, (206, 212, 224, 55))]
    for y0, y1, col in bands:
        d.rectangle((0, y0, W, y1), fill=col)
    # 四季装饰
    draw_flower(canvas, 140, 380, 20, (244, 186, 200), 5, seed=61)      # 春
    draw_plant_sprig(canvas, 780, 780, 0.8, (120, 156, 104), 8, 62)      # 夏
    # 秋叶
    d.ellipse((700, 1080, 760, 1120), fill=(214, 146, 78, 200))
    d.ellipse((760, 1110, 820, 1150), fill=(226, 166, 88, 200))
    # 冬雪点
    for i in range(14):
        x = 80 + (i * 57) % 760
        y = 1240 + (i * 83) % 300
        d.ellipse((x, y, x + 5, y + 5), fill=(255, 255, 255, 200))
    C.draw_title(canvas, "四 季 长 卷", 60, 76, C.FONT_CN, (86, 80, 74, 240),
                 sub="春 · 夏 · 秋 · 冬", en="FOUR SEASONS / A YEAR")
    add_slots(canvas, doc_color=(252, 250, 244))
    d = ImageDraw.Draw(canvas)
    d.text((70, 1510), "a year in moments", font=C.FONT_EN_S, fill=(120, 116, 108, 220))
    return C.save_out(canvas, "template-four-seasons.jpg")


# ============================================================
# 13. 复古蒙太奇拼贴
# ============================================================
def make_vintage_montage():
    canvas = C.gradient_bg([(0, (214, 196, 164)), (0.5, (204, 184, 148)), (1, (192, 168, 132))])
    C.add_halftone(canvas, (92, 66, 44), cell=8, dot_max=2.6, alpha=44, seed=16)
    C.add_grain(canvas, amount=11, alpha=24, seed=17)
    d = ImageDraw.Draw(canvas)
    # 剪报碎片（复用素材，撕边 + 高对比）
    for folder, name, x, y, w, ang in [
        ("", "label-herbarium-16.jpg", 740, 460, 180, -9),
        ("", "paper-5.jpg", 130, 700, 190, 8),
        ("", "hand-1.jpg", 760, 1180, 160, 11),
    ]:
        im = C.load(folder, name)
        if im:
            im = ImageEnhance.Contrast(im).enhance(1.4)
            p = C.torn_edges(C.fit(im, w).convert("RGBA"), seed=int(x + y), amp=10)
            C.place(canvas, p, x, y, ang)
    # 撞色块
    d.rectangle((0, 0, 240, 180), fill=(166, 52, 44, 220))
    d.rectangle((720, 1400, 900, 1600), fill=(48, 72, 124, 210))
    C.draw_title(canvas, "MONTA", 60, 74, C.FONT_EN, (250, 240, 220, 250))
    d = ImageDraw.Draw(canvas)
    d.text((66, 130), "复古蒙太奇 · 剪报艺术", font=C.FONT_CN_M, fill=(250, 238, 214, 235))
    add_slots(canvas, doc_color=(248, 238, 216))
    d = ImageDraw.Draw(canvas)
    d.text((70, 1510), "CUT · PASTE · REIMAGINE", font=C.FONT_EN_S, fill=(90, 64, 44, 230))
    return C.save_out(canvas, "template-vintage-montage.jpg")


# ============================================================
# 14. 极简风格拼贴
# ============================================================
def make_minimal_photo():
    canvas = C.gradient_bg([(0, (246, 242, 234)), (0.5, (240, 236, 228)), (1, (232, 228, 218))])
    C.add_grain(canvas, amount=3, alpha=8, seed=18)
    d = ImageDraw.Draw(canvas)
    # 极简细线网格
    for gx in range(70, 900, 130):
        d.line((gx, 60, gx, 1540), fill=(190, 184, 172, 45), width=1)
    # 细白边框装饰
    d.rectangle((56, 56, 844, 1544), outline=(255, 255, 255, 200), width=2)
    d.text((70, 1510), "01 / 04", font=C.FONT_EN_S, fill=(150, 144, 134, 200))
    C.draw_title(canvas, "极 简 相 册", 70, 82, C.FONT_CN, (72, 68, 62, 235),
                 sub="米白 · 浅灰 · 暖棕", en="MINIMAL ALBUM")
    # 极简风格照片位用统一间距的细框
    add_slots(canvas, doc_color=(250, 248, 244))
    return C.save_out(canvas, "template-minimal-photo.jpg")


MAKERS = [
    ("INS极简留白", make_ins_minimal),
    ("日系盐系胶片", make_japanese_salt),
    ("美式复古杂志", make_american_retro),
    ("奶油马卡龙", make_macaron),
    ("文艺宣纸书香", make_xuan_paper),
    ("街头极简涂鸦", make_street_graffiti),
    ("时光日历日记", make_calendar_diary),
    ("旅行复古手账", make_travel_journal),
    ("四季叙事长卷", make_four_seasons),
    ("复古蒙太奇", make_vintage_montage),
    ("极简风格", make_minimal_photo),
]

if __name__ == "__main__":
    for name, fn in MAKERS:
        print("=== generating:", name, "===")
        try:
            fn()
        except Exception as e:
            print("  FAILED:", name, repr(e))
    print("DONE")
