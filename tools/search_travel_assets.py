# -*- coding: utf-8 -*-
"""旅行复古手账：从 Wikimedia Commons 搜索旧明信片/机票/地图/邮戳/牛皮纸等免费素材。"""
import os
import json
import time
import urllib.parse
import urllib.request
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(ROOT, "temp_asset_search", "travel")
os.makedirs(TMP, exist_ok=True)
API = "https://commons.wikimedia.org/w/api.php"
UA = "CollageTemplateBot/1.0 (educational use)"

QUERIES = [
    "vintage postcard city",
    "old postcard travel",
    "vintage airline ticket",
    "antique city map",
    "vintage postmark cancellation",
    "vintage train ticket",
    "kraft paper texture",
    "old paper texture aged",
    "vintage luggage label travel",
    "old street photograph city",
]


def api_get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.loads(r.read().decode("utf-8"))


def search(term, limit=9):
    params = {
        "action": "query", "generator": "search", "gsrsearch": term,
        "gsrnamespace": 6, "gsrlimit": limit,
        "prop": "imageinfo", "iiprop": "url|extmetadata",
        "iiurlwidth": 460, "format": "json",
    }
    try:
        data = api_get(params)
    except Exception as e:
        print("  search failed:", str(e)[:60], flush=True)
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
            "desc": ii.get("descriptionurl", ""),
        })
    return out


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = r.read()
    with open(path, "wb") as f:
        f.write(data)


all_items = []
for q in QUERIES:
    print("searching:", q, flush=True)
    items = search(q)
    print("  got", len(items), flush=True)
    for it in items:
        it["query"] = q
    all_items.extend(items)
    time.sleep(0.3)

seen = set()
uniq = []
for it in all_items:
    if it["url"] in seen:
        continue
    seen.add(it["url"])
    uniq.append(it)

records = []
fails = 0
for i, it in enumerate(uniq):
    path = os.path.join(TMP, "cand_%03d.jpg" % i)
    try:
        download(it["thumb"], path)
        im = Image.open(path)
        if im.width < 60 or im.height < 60:
            os.remove(path)
            continue
        records.append((i, it, path))
        fails = 0
    except Exception as e:
        if os.path.exists(path):
            os.remove(path)
        fails += 1
        print("  dl fail", i, str(e)[:50], flush=True)
        if fails >= 8:
            print("too many failures, stop downloading", flush=True)
            break
    time.sleep(0.15)

COLS = 6
TW, TH = 200, 178
rows = max(1, (len(records) + COLS - 1) // COLS)
sheet = Image.new("RGB", (COLS * TW, rows * TH), (238, 234, 224))
d = ImageDraw.Draw(sheet)
for n, (idx, it, path) in enumerate(records):
    im = Image.open(path).convert("RGB")
    im.thumbnail((TW - 8, TH - 42))
    x = (n % COLS) * TW + (TW - im.width) // 2
    y = (n // COLS) * TH + 36
    sheet.paste(im, (x, y))
    d.text(((n % COLS) * TW + 4, (n // COLS) * TH + 4),
           "%03d %s" % (idx, it["license"][:12]), fill=(0, 0, 0))

sheet_path = os.path.join(ROOT, "temp_asset_search", "travel_contact.jpg")
sheet.save(sheet_path)
with open(os.path.join(TMP, "candidates.json"), "w", encoding="utf-8") as f:
    json.dump([{"idx": i, **it, "file": p} for i, it, p in records], f, ensure_ascii=False, indent=2)
print("DONE candidates:", len(records), "sheet:", sheet_path, flush=True)
