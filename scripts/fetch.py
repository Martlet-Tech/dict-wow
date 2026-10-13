# -*- coding: utf-8 -*-
"""TurtleDB 列表页爬虫。

用法:
  python fetch.py [cat ...]        # 抓指定分类（默认全部）
产物:
  raw/<cat>/p0001.html             # 原始页面（断点续传）
  out/<cat>.json                   # 解析后的结构化词条
"""
import os
import re
import sys
import json
import time
import random
import threading
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

import parse as P

BASE = 'https://db.turtletail.net/index.php'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
HEADERS = {
    'User-Agent': UA,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://db.turtletail.net/index.php',
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'raw')      # 原始 HTML 缓存（.gitignore）
OUT = os.path.join(ROOT, 'data')     # 解析后的结构化数据

# 分类 -> 页数（None = 单页，抓一次）
CATS = ['items', 'npcs', 'quests', 'objects', 'spells', 'zones', 'factions']

_print_lock = threading.Lock()


def log(*a):
    with _print_lock:
        print(*a, flush=True)


def get(url, retries=5):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            last = f'HTTP {e.code}'
            if e.code in (403, 429, 503):
                time.sleep(2.0 * (i + 1) + random.random())
                continue
            if e.code == 404:
                return None
            time.sleep(1.0 * (i + 1))
        except Exception as e:  # noqa
            last = repr(e)
            time.sleep(1.5 * (i + 1) + random.random())
    raise RuntimeError(f'GET failed after {retries}: {url} ({last})')


def total_pages(html):
    m = re.search(r'共 \d+ 条记录\s+\d+/(\d+) 页', html)
    return int(m.group(1)) if m else 1


def page_url(cat, page):
    return f'{BASE}?{cat}&page={page}'


def fetch_page(cat, page, force=False):
    d = os.path.join(RAW, cat)
    os.makedirs(d, exist_ok=True)
    fp = os.path.join(d, f'p{page:04d}.html')
    if not force and os.path.exists(fp) and os.path.getsize(fp) > 2000:
        return fp, False
    html = get(page_url(cat, page))
    if html is None:
        raise RuntimeError(f'404 {page_url(cat, page)}')
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(html)
    return fp, True


def fetch_cat(cat, workers=5, delay=0.15):
    t0 = time.time()
    os.makedirs(os.path.join(RAW, cat), exist_ok=True)
    first = get(page_url(cat, 1))
    with open(os.path.join(RAW, cat, 'p0001.html'), 'w', encoding='utf-8') as f:
        f.write(first)
    n = total_pages(first)
    log(f'[{cat}] 共 {n} 页，开始抓取…')

    todo = list(range(2, n + 1))
    done = [1]
    failed = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {}
        for p in todo:
            time.sleep(delay)
            futs[ex.submit(fetch_page, cat, p)] = p
        for fu in as_completed(futs):
            p = futs[fu]
            try:
                fu.result()
                done.append(p)
            except Exception as e:  # noqa
                failed.append((p, repr(e)))
            if len(done) % 25 == 0:
                log(f'[{cat}] {len(done)}/{n}  ({(time.time()-t0):.0f}s)')
    log(f'[{cat}] 抓取完成 {len(done)}/{n} 页，失败 {len(failed)}，用时 {time.time()-t0:.0f}s')
    if failed:
        log(f'[{cat}] 失败页: {failed[:10]}')
    return n, failed


def build(cat):
    d = os.path.join(RAW, cat)
    files = sorted(f for f in os.listdir(d) if f.endswith('.html'))
    rows = []
    seen = set()
    for fn in files:
        html = open(os.path.join(d, fn), encoding='utf-8').read()
        for r in P.parse(cat, html):
            rid = r.get('id')
            key = (cat, rid, r.get('name') or r.get('name_cn'))
            if key in seen:
                continue
            seen.add(key)
            r['_cat'] = cat
            r['_page'] = fn
            rows.append(r)
    os.makedirs(OUT, exist_ok=True)
    fp = os.path.join(OUT, f'{cat}.json')
    with open(fp, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    log(f'[{cat}] 解析 {len(rows)} 条 -> {fp}')
    return rows


def main():
    cats = sys.argv[1:] or CATS
    for cat in cats:
        try:
            fetch_cat(cat)
        except Exception as e:  # noqa
            log(f'[{cat}] 抓取异常: {e!r}')
    log('=== 解析 ===')
    for cat in cats:
        try:
            build(cat)
        except Exception as e:  # noqa
            log(f'[{cat}] 解析异常: {e!r}')


if __name__ == '__main__':
    main()
