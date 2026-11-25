# -*- coding: utf-8 -*-
"""增量补充 Pexels 免费商用素材到素材库，并新增 handdrawn / cartoon 两类。

- 只追加新文件，不覆盖已有素材（编号从目录内最大编号+1 开始）。
- 合并保留原 SOURCES.json 的全部记录，追加新记录的授权来源。
- Pexels License: 免费商用、无需署名、可修改（https://www.pexels.com/license/）。
"""
import os
import json
import time
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_ROOT = os.path.join(ROOT, "public", "assets", "collage", "pexels")
UA = "CollageTemplateBot/1.0 (free commercial asset collection)"

# 各风格新搜到的图片 ID（来自 Pexels 搜索页，免费商用；已排除与现有重复的 ID）
SETS = {
    "ins-minimal": [18278210, 7303773, 7307623, 7302751, 7302748, 5825574,
                    7214789, 6739705, 6962803, 6692149, 9304500, 7302683],
    "japanese-salt": [30228562, 30228556, 30979556, 21274274, 30979278, 30979279,
                      30979271, 30228564, 30228551, 39299520, 7949554, 140221],
    "american-retro": [7966867, 17323760, 11866393, 34763358, 9086765, 9200153,
                       17314081, 13081133, 2058495, 9086775, 5010877, 12753702],
    "macaron": [16365469, 5890119, 5469214, 7033662, 6823746, 7002967,
                7123120, 6942169, 5469039, 8964282, 5469037, 8669984],
    "tech-frost": [19299040, 14731533, 35541195, 35930150, 6486617, 13141665,
                   36343601, 36296930],
    "xuan-paper": [9478287, 30899526, 5907795, 6026345, 37605548, 9276214,
                   6391523, 37605547, 9478275, 9478289, 2147872, 39388943],
    "street-graffiti": [20640206, 11538192, 28936742, 27852730, 38973829, 17569308,
                        8363069, 36390526, 16819660, 30526030, 14137976, 1055845],
    "travel-journal": [7368310, 8372639, 8372624, 18799888, 4645982, 7368308,
                       5405598, 7368300, 8372663, 5863541, 7966751, 7966691],
    "green-fresh": [38359336, 26756518, 29199485, 37860926, 9907270, 36180519,
                    35332022, 34886564],
    "four-seasons": [33158, 12496783, 34612582, 5727778, 31672968, 19185454,
                     40425616, 4520496, 36065631, 9138175],
    # 新增：手绘涂鸦/素描素材
    "handdrawn": [932262, 35597616, 18372231, 1707581, 8716097, 20772152, 1643964,
                  35665055, 7411984, 8434764, 37462202, 37461253, 15100360, 1707579,
                  1707577, 11135903, 7078970, 35812597, 7078960, 20358821],
    # 新增：卡通画/可爱角色素材（已排除蝙蝠侠、马里奥等有版权角色）
    "cartoon": [33568904, 37548192, 187069, 36907038, 20704974, 31500187, 37248155,
                34047976, 34051779, 36949801, 36323152, 31593307, 31756353,
                37248149, 34723571, 31365104, 37248189, 36611244],
}

# 合并已有授权记录
sources_path = os.path.join(OUT_ROOT, "SOURCES.json")
if os.path.exists(sources_path):
    with open(sources_path, encoding="utf-8") as f:
        sources = json.load(f)
else:
    sources = []
existing_ids = {str(s.get("photo_id")) for s in sources}

total_ok = 0
for style, ids in SETS.items():
    d = os.path.join(OUT_ROOT, style)
    os.makedirs(d, exist_ok=True)
    # 从目录内最大编号+1 开始，避免覆盖
    nums = [int(m.group(1)) for fn in os.listdir(d)
            for m in [re.match(r"%s-(\d+)\.jpg" % style, fn)] if m]
    start = max(nums) + 1 if nums else 1
    ok = 0
    n = start
    for pid in ids:
        if str(pid) in existing_ids:
            continue
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
            existing_ids.add(str(pid))
            ok += 1
            total_ok += 1
            n += 1
        except Exception as e:
            print("FAIL", style, pid, str(e)[:70])
        time.sleep(0.1)
    print("DONE", style, ok, "new")

with open(sources_path, "w", encoding="utf-8") as f:
    json.dump(sources, f, ensure_ascii=False, indent=2)
print("TOTAL NEW", total_ok, "SOURCES TOTAL", len(sources))
