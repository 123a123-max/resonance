# -*- coding: utf-8 -*-
"""极简风格拼贴 9:16 模板。

低饱和米白/浅灰/暖棕，整齐网格 + 错落大小，统一间距，留白充足；
轻微纸张纹理 + 细腻磨砂颗粒；少量细白边框照片位 + 极简编号；
点缀克制（一小枝干花），标题纤细不夸张，无复杂装饰/密集贴纸/撞色/厚重阴影。

照片位坐标与 src/collage/templateStyles.ts 中 minimal-photo 的 slots 完全一致。
"""
import os
import random
from PIL import Image, ImageDraw, ImageChops
import template_common as C

random.seed(7)
W, H = C.W, C.H
OUT = os.path.join(C.OUT_DIR, "template-minimal-photo.jpg")

# 纤细字体
F_EN_L = C.font("C:/Windows/Fonts/segoeuil.ttf", 30)
F_EN_S = C.font("C:/Windows/Fonts/segoeuil.ttf", 20)
F_NUM = C.font("C:/Windows/Fonts/segoeuil.ttf", 22)
F_CN = C.font(["C:/Windows/Fonts/Deng.ttf", "C:/Windows/Fonts/msyh.ttc"], 22)

INK = (104, 97, 87, 225)       # 暖棕灰
INK_L = (150, 143, 132, 205)   # 浅暖灰
LINE = (206, 200, 190, 185)    # 极细分隔线

# (x, y, w, h) —— 中心点与尺寸；2×2 网格，对角大小错落，间距统一
SLOTS = [
    (245, 510, 380, 400),
    (655, 510, 350, 365),
    (245, 945, 350, 365),
    (655, 945, 380, 400),
]


def right_text(d, x_right, y, text, fnt, fill):
    w = d.textlength(text, font=fnt)
    d.text((x_right - w, y), text, font=fnt, fill=fill)


def cut_white(im, lo=232, hi=255):
    """白底转透明（纯 PIL，避开 template_common.white_to_alpha 的环境兼容问题）。"""
    rgb = im.convert("RGB")
    r, g, b = rgb.split()
    v = ImageChops.darker(ImageChops.darker(r, g), b)
    lut = [255 if x <= lo else (0 if x >= hi else int(255 * (hi - x) / (hi - lo))) for x in range(256)]
    alpha = v.point(lut)
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def cut_by_saturation(im, lo=8, hi=24):
    """按 HSV 饱和度抠图：灰白背景(S≤5)转透明，暖棕主体(S≥20)保留。"""
    rgb = im.convert("RGB")
    s = rgb.convert("HSV").split()[1]
    lut = [0 if x <= lo else (255 if x >= hi else int(255 * (x - lo) / (hi - lo))) for x in range(256)]
    alpha = s.point(lut)
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def draw_handdrawn_accent(canvas):
    """底部手绘小图案：几颗纤细四角星芒 + 一条淡手绘弧线，纯线条、克制。"""
    d = ImageDraw.Draw(canvas)
    col = INK_L
    cx, cy = 450, 1300
    # 星芒错落（中间高、两侧一高一低），大小有别
    C.star(d, cx - 6, cy - 4, 18, col, width=2)
    C.star(d, cx - 84, cy + 16, 8, col, width=2)
    C.star(d, cx + 76, cy + 6, 10, col, width=2)
    C.star(d, cx + 30, cy + 24, 5, col, width=2)
    # 一条平缓的极淡手绘短线（不作笑脸弧度）
    C.jline(d, [(cx - 108, cy + 30), (cx - 40, cy + 33),
                (cx + 34, cy + 31), (cx + 104, cy + 29)],
            col, width=2, wobble=1, seed=9)


def main():
    # 暖米白 -> 浅灰暖棕 极轻渐变
    canvas = C.gradient_bg([
        (0.0, (248, 245, 239)),
        (0.5, (243, 240, 232)),
        (1.0, (237, 233, 224)),
    ])
    # 轻微纸张纤维 + 细腻磨砂颗粒
    C.add_paper_fibers(canvas, (176, 168, 156), count=260, alpha=13, seed=6)
    C.add_grain(canvas, amount=4, alpha=12, seed=5)

    # ---- 顶部纤细标题（克制，不夸张）----
    d = ImageDraw.Draw(canvas)
    d.text((90, 116), "M I N I M A L   A L B U M", font=F_EN_L, fill=INK)
    d.text((90, 166), "极简相册 · 留白日常", font=F_CN, fill=INK_L)
    d.line((90, 216, 810, 216), fill=LINE, width=2)

    # ---- 照片位：细白边框 + 框外左上角极简编号 ----
    for i, (x, y, w, h) in enumerate(SLOTS, 1):
        frame = C.photo_slot("frame", w, h)
        C.place(canvas, frame, x, y, 0)
        d = ImageDraw.Draw(canvas)
        left = int(x - w / 2)
        top = int(y - h / 2)
        d.text((left, top - 32), "%02d" % i, font=F_NUM, fill=INK_L)

    # ---- 底部点缀：程序手绘小图案（纤细星芒 + 淡弧线，克制不抢镜）----
    draw_handdrawn_accent(canvas)

    # ---- 底部小字（纤细、克制）----
    d = ImageDraw.Draw(canvas)
    d.line((90, 1440, 810, 1440), fill=LINE, width=2)
    d.text((90, 1462), "Collected moments, quietly kept.", font=F_EN_S, fill=INK_L)
    right_text(d, 810, 1462, "01 - 04", F_EN_S, INK_L)

    C.save_out(canvas, "template-minimal-photo.jpg")
    print("slots:", SLOTS)


if __name__ == "__main__":
    main()
