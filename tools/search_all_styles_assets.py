# -*- coding: utf-8 -*-
"""批量搜索 11 种拼贴风格所需素材，下载缩略候选并生成联系表。
授权筛选：Public domain / CC0 / CC BY。原图会 429，统一用 thumburl。
"""
import os
import json
import time
import urllib.parse
import urllib.request
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(ROOT, "temp_asset_search", "allstyles")
os.makedirs(TMP, exist_ok=True)
API = "https://commons.wikimedia.org/w/api.php"
UA = "CollageTemplateBot/1.0 (educational use)"

# 覆盖 11 种风格的素材关键词
QUERIES = [
    # INS 极简留白
    "minimal ceramic vase still life", "dried flower branch still life",
    "fashion editorial portrait woman",
    # 日系盐系胶片
    "coffee cup cafe photo", "vintage film camera", "green plant leaves photo",
    # 美式复古杂志
    "vintage magazine advertisement 1960", "retro woman portrait 1970",
    "vintage newspaper page",
    # 奶油马卡龙
    "pastel candy sweets", "pastel flowers bouquet", "cute cake dessert pastel",
    # 文艺宣纸书香
    "chinese calligraphy ink painting", "ancient chinese book page",
    "ink painting plum blossom", "chinese seal stamp red",
    # 街头涂鸦（主要程序绘制，找少量涂鸦参考）
    "graffiti street art lettering",
    # 时光日历
    "vintage rubber stamp postmark", "vintage postcard letter",
    # 旅行复古手账
    "vintage train ticket", "vintage postcard city travel", "old map vintage",
    # 四季叙事
    "spring cherry blossom branch", "autumn maple leaves", "winter snow branch",
    # 复古蒙太奇
    "vintage collage magazine portrait", "old newspaper clipping portrait",
    # 极简风格
    "minimal still life beige",
]


def api_get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def search(term, limit=8):
    params = {
        "action": "query", "generator": "search", "gsrsearch": term,
        "gsrnamespace": 6, "gsrlimit": limit,
        "prop": "imageinfo", "iiprop": "url|extmetadata",
        "iiurlwidth": 440, "format": "json",
    }
    try:
        data = api_get(params)
    except Exception as e:
        print("  search failed:", str(e)[:60])
        return []
    out = []
    for page in data.get("query", {}).get("pages", {}).values():
        ii = page.get("imageinfo", [{}])[0]
        meta = ii.get("extmetadata", {})
        lic = meta.get("LicenseShortName", {}).get("value", "")
        thumb = ii.get("thumburl") or ii.get("url")
        if not thumb:
            continue
        out.append({
            "title": page.get("title", ""), "license": lic,
            "thumb": thumb, "url": ii.get("url", ""),
            "desc": ii.get("descriptionurl", ""), "query": term,
        })
    return out


all_items = []
for q in QUERIES:
    print("searching:", q)
    items = search(q)
    print("  got", len(items))
    all_items.extend(items)
    time.sleep(0.5)

seen, uniq = set(), []
for it in all_items:
    if it["url"] in seen:
        continue
    seen.add(it["url"])
    uniq.append(it)

records = []
for i, it in enumerate(uniq):
    path = os.path.join(TMP, "cand_%03d.jpg" % i)
    try:
        req = urllib.request.Request(it["thumb"], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        with open(path, "wb") as f:
            f.write(data)
        im = Image.open(path)
        if im.width < 60 or im.height < 60:
            os.remove(path)
            continue
        records.append((i, it, path))
    except Exception as e:
        if os.path.exists(path):
            os.remove(path)
        print("  dl fail", i, str(e)[:50])
    time.sleep(0.2)

COLS, TW, TH = 6, 195, 172
rows = (len(records) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * TW, rows * TH), (238, 239, 240))
d = ImageDraw.Draw(sheet)
for n, (idx, it, path) in enumerate(records):
    im = Image.open(path).convert("RGB")
    im.thumbnail((TW - 8, TH - 38))
    x = (n % COLS) * TW + (TW - im.width) // 2
    y = (n // COLS) * TH + 34
    sheet.paste(im, (x, y))
    d.text(((n % COLS) * TW + 3, (n // COLS) * TH + 3),
           "%03d %s" % (idx, it["license"][:10]), fill=(0, 0, 0))

sheet_path = os.path.join(ROOT, "temp_asset_search", "allstyles_contact.jpg")
sheet.save(sheet_path)
with open(os.path.join(TMP, "candidates.json"), "w", encoding="utf-8") as f:
    json.dump([{"idx": i, **it, "file": p} for i, it, p in records], f,
              ensure_ascii=False, indent=2)
print("DONE candidates:", len(records), "sheet:", sheet_path)
