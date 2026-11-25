# -*- coding: utf-8 -*-
"""从 Wikimedia Commons 搜索波普艺术风格免费素材，下载缩略候选并生成联系表。"""
import os
import json
import time
import urllib.parse
import urllib.request
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(ROOT, "temp_asset_search", "popart")
os.makedirs(TMP, exist_ok=True)
API = "https://commons.wikimedia.org/w/api.php"
UA = "CollageTemplateBot/1.0 (educational use)"

# 搜索关键词：城市街景、人像、老杂志、波普元素
QUERIES = [
    "New York City skyline skyscraper",
    "Chicago skyline building",
    "vintage fashion woman portrait 1960s",
    "pop art portrait painting",
    "halftone newspaper print texture",
    "vintage magazine cover 1960",
    "comic book explosion graphic",
    "art deco building facade",
]


def api_get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def search(term, limit=12):
    params = {
        "action": "query", "generator": "search", "gsrsearch": term,
        "gsrnamespace": 6, "gsrlimit": limit,
        "prop": "imageinfo", "iiprop": "url|extmetadata",
        "iiurlwidth": 420, "format": "json",
    }
    try:
        data = api_get(params)
    except Exception as e:
        print("  search failed:", e)
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
            "title": page.get("title", ""),
            "license": lic,
            "thumb": thumb,
            "url": ii.get("url", ""),
            "desc": ii.get("descriptionurl", ""),
        })
    return out


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    with open(path, "wb") as f:
        f.write(data)


all_items = []
for q in QUERIES:
    print("searching:", q)
    items = search(q)
    print("  got", len(items))
    for it in items:
        it["query"] = q
    all_items.extend(items)
    time.sleep(0.4)

# 去重
seen = set()
uniq = []
for it in all_items:
    key = it["url"]
    if key in seen:
        continue
    seen.add(key)
    uniq.append(it)

# 下载缩略图
records = []
for i, it in enumerate(uniq):
    ext = ".jpg"
    path = os.path.join(TMP, "cand_%03d%s" % (i, ext))
    try:
        download(it["thumb"], path)
        im = Image.open(path)
        if im.width < 60 or im.height < 60:
            os.remove(path)
            continue
        records.append((i, it, path))
    except Exception as e:
        if os.path.exists(path):
            os.remove(path)
        print("  dl fail", i, str(e)[:60])
    time.sleep(0.25)

# 生成联系表
COLS = 6
TW, TH = 200, 175
rows = (len(records) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * TW, rows * TH), (238, 238, 234))
d = ImageDraw.Draw(sheet)
for n, (idx, it, path) in enumerate(records):
    im = Image.open(path).convert("RGB")
    im.thumbnail((TW - 8, TH - 40))
    x = (n % COLS) * TW + (TW - im.width) // 2
    y = (n // COLS) * TH + 34
    sheet.paste(im, (x, y))
    label = "%03d %s" % (idx, it["license"][:12])
    d.text(((n % COLS) * TW + 4, (n // COLS) * TH + 4), label, fill=(0, 0, 0))

sheet_path = os.path.join(ROOT, "temp_asset_search", "popart_contact.jpg")
sheet.save(sheet_path)
with open(os.path.join(TMP, "candidates.json"), "w", encoding="utf-8") as f:
    json.dump([{"idx": i, **it, "file": p} for i, it, p in records], f, ensure_ascii=False, indent=2)
print("DONE candidates:", len(records), "sheet:", sheet_path)
