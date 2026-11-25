# -*- coding: utf-8 -*-
"""批量下载 Pexels 免费商用素材，按风格分目录，并记录授权来源。

Pexels License: 免费商用、无需署名、可修改（https://www.pexels.com/license/）。
素材供后续各风格拼贴模板合成使用，不直接展示。
"""
import os
import json
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_ROOT = os.path.join(ROOT, "public", "assets", "collage", "pexels")
UA = "CollageTemplateBot/1.0 (free commercial asset collection)"

# 各风格挑选的图片 ID（来自 Pexels 搜索，免费商用）
SETS = {
    "ins-minimal": [7663201, 4203100, 6805521, 7185748, 13192756, 6801449,
                    7663203, 6952331, 9850116, 6952333, 10016635, 10348541,
                    7022650, 35075401, 7664163, 9055006, 32557003, 5957563],
    "japanese-salt": [20240938, 9566844, 33156934, 11048540, 33315259,
                      30228557, 30802659, 35089102, 33315150, 25149741, 12072175],
    "american-retro": [39213914, 38568366, 31666148, 15669745, 11669849,
                       13198553, 18663181, 7359593, 38772451, 17115450,
                       12182584, 13589785, 16208088, 18398581, 32897042,
                       31064369, 6003846, 35475561, 31881219, 24514217],
    "macaron": [7679940, 6086208, 7640058, 4016659, 6823675, 8126358,
                16077154, 7676078, 9743268, 1375811, 7232909, 16115229,
                4902634, 15972884, 27913837, 2808802],
    "tech-frost": [35872548, 5997209, 6609914, 6757692, 32402669, 36068814,
                   6485472, 15111793, 6615654, 6434772],
    "xuan-paper": [9016466, 6156193, 9016463, 2147866, 6213047, 9016475,
                   5788531, 9478265, 6061757],
    "street-graffiti": [1707640, 36895672, 35799119, 955798, 7951901,
                        35696485, 1738154, 32439576, 1366851, 8466681,
                        6188, 14754790, 19581966, 32745102, 11985451, 9858901],
    "travel-journal": [30568781, 5405597, 28464584, 7235901, 31315871,
                       7310015, 7967946, 3234893, 3927538, 5405596, 3490665,
                       37947892, 1906606, 3826581, 7790175, 31376933, 69866,
                       9260822],
    "green-fresh": [32937521, 28643077, 35626296, 33818374, 4799967,
                    14753429, 38658905],
    "four-seasons": [1029040, 805448, 36860728, 31913117, 37081338, 9424116,
                     479392, 31471798, 479386, 27452090, 14941834],
}

sources = []
total_ok = 0
for style, ids in SETS.items():
    d = os.path.join(OUT_ROOT, style)
    os.makedirs(d, exist_ok=True)
    ok = 0
    for n, pid in enumerate(ids, 1):
        url = ("https://images.pexels.com/photos/%d/pexels-photo-%d.jpeg"
               "?auto=compress&cs=tinysrgb&w=640" % (pid, pid))
        path = os.path.join(d, "%s-%02d.jpg" % (style, n))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = resp.read()
            if len(data) < 2000:
                print("SKIP small", style, pid, len(data))
                continue
            with open(path, "wb") as f:
                f.write(data)
            sources.append({
                "file": "pexels/%s/%s-%02d.jpg" % (style, style, n),
                "style": style,
                "photo_id": pid,
                "license": "Pexels License (free for commercial use)",
                "source": "https://www.pexels.com/photo/%d/" % pid,
                "download": url,
            })
            ok += 1
            total_ok += 1
        except Exception as e:
            print("FAIL", style, pid, str(e)[:70])
        time.sleep(0.12)
    print("DONE", style, ok, "/", len(ids))

with open(os.path.join(OUT_ROOT, "SOURCES.json"), "w", encoding="utf-8") as _sf:
    json.dump(sources, _sf, ensure_ascii=False, indent=2)
print("TOTAL OK", total_ok, "sources", len(sources))
