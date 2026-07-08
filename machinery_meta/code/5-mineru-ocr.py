# -*- coding: utf-8 -*-
"""用 MinerU API (v4) 批量OCR原始文献PDF -> markdown。

输入：/root/data/Paper/农机Meta/文献筛选-中文、文献筛选-英文(两个子文件夹)
输出：data/fulltext_md/<稿件名>.md ；状态缓存 data/mineru_state.json
已完成的文件自动跳过，可反复重跑续传。
"""
import glob
import json
import os
import re
import time
import zipfile
import io

import requests

TOKEN = os.environ.get("MINERU_TOKEN", "").strip()
assert TOKEN, "请通过环境变量 MINERU_TOKEN 提供 API key"

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "/root/data/Paper/农机Meta"
OUT = os.path.join(BASE, "data", "fulltext_md")
STATE_F = os.path.join(BASE, "data", "mineru_state.json")
os.makedirs(OUT, exist_ok=True)

API = "https://mineru.net/api/v4"
HDR = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

pdfs = sorted(
    glob.glob(os.path.join(SRC, "文献筛选-中文", "*.pdf"))
    + glob.glob(os.path.join(SRC, "文献筛选-英文", "*", "*.pdf")))
print(f"共 {len(pdfs)} 个PDF")

state = json.load(open(STATE_F)) if os.path.exists(STATE_F) else {}


def slug(path):
    s = os.path.splitext(os.path.basename(path))[0]
    return re.sub(r"[^\w一-鿿.-]+", "_", s)[:120]


todo = [p for p in pdfs if not os.path.exists(os.path.join(OUT, slug(p) + ".md"))]
print(f"待处理 {len(todo)} 个")

BATCH = 20
for i in range(0, len(todo), BATCH):
    chunk = todo[i:i + BATCH]
    names = [slug(p) + ".pdf" for p in chunk]
    is_cn = ["文献筛选-中文" in p for p in chunk]
    files_req = [{"name": n, "is_ocr": True, "data_id": n} for n in names]
    lang = "ch"  # 混合批次用ch，MinerU可自动处理英文
    r = requests.post(f"{API}/file-urls/batch", headers=HDR, json={
        "enable_formula": False, "enable_table": True,
        "language": lang, "files": files_req}, timeout=60)
    j = r.json()
    assert j.get("code") == 0, j
    batch_id = j["data"]["batch_id"]
    urls = j["data"]["file_urls"]
    for p, u in zip(chunk, urls):
        with open(p, "rb") as f:
            up = requests.put(u, data=f, timeout=300)
        up.raise_for_status()
        print("uploaded", os.path.basename(p), flush=True)
    state[batch_id] = names
    json.dump(state, open(STATE_F, "w"), ensure_ascii=False, indent=1)

    # 轮询该批次直到全部完成
    pending = set(names)
    t0 = time.time()
    while pending and time.time() - t0 < 3600:
        time.sleep(20)
        rr = requests.get(f"{API}/extract-results/batch/{batch_id}",
                          headers=HDR, timeout=60)
        jj = rr.json()
        if jj.get("code") != 0:
            print("poll error", jj, flush=True)
            continue
        for item in jj["data"]["extract_result"]:
            name, st = item.get("file_name"), item.get("state")
            if name in pending and st == "done":
                z = requests.get(item["full_zip_url"], timeout=300)
                zf = zipfile.ZipFile(io.BytesIO(z.content))
                mdname = [n for n in zf.namelist() if n.endswith("full.md")]
                md = zf.read(mdname[0]).decode("utf-8", "ignore") if mdname else ""
                with open(os.path.join(OUT, name[:-4] + ".md"), "w",
                          encoding="utf-8") as f:
                    f.write(md)
                pending.discard(name)
                print(f"done {name}  (剩{len(pending)})", flush=True)
            elif name in pending and st == "failed":
                print(f"FAILED {name}: {item.get('err_msg')}", flush=True)
                with open(os.path.join(OUT, name[:-4] + ".md"), "w") as f:
                    f.write(f"[MINERU FAILED] {item.get('err_msg')}\n")
                pending.discard(name)
    print(f"batch {batch_id} 完成", flush=True)

print("全部完成:", len(glob.glob(os.path.join(OUT, "*.md"))), "个md")
