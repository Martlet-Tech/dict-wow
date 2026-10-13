# -*- coding: utf-8 -*-
"""汇总 TurtleDB 各分类词条 -> 生成 Rime 风格 .dict.yaml。

筛选策略（计划 §3 的离线近似）：
  - 只留中文词条，长度 2~6，剔除占位/测试/纯英文条目
  - 剔除「已存在于通用词库(base/ext/others/8105)」的词 —— 这些通用输入法本就能出，
    真正需要补充的是专名，等价于「乌龟服独有」的实用近似
输出: out/turtledb.dict.yaml
"""
import os
import re
import json
import sys
from collections import Counter

import annotate as A

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data')      # 输入：解析后的 JSON
DICT_OUT = os.path.join(ROOT, 'dict')  # 输出：最终词库

CATS = ['zones', 'factions', 'items', 'npcs', 'quests', 'objects', 'spells']

# 分类权重（可调；越大越优先）
WEIGHTS = {
    'zones': 6000,
    'factions': 5000,
    'npcs': 5000,
    'items': 4000,
    'quests': 3000,
    'objects': 2000,
    'spells': 1500,
}

BAD_RE = re.compile(
    r'\[PH\]|\(DND\)|^@|UNUSED|unused|未使用|未实装|测试|Test|Deprecated|'
    r'^zz|^ZZ|placeholder|Placeholder|占位|^Old |^old ', re.I)
CJK_RE = re.compile(r'[\u4e00-\u9fff]')
ONLY_CJK = re.compile(r'^[\u4e00-\u9fff]+$')


def clean(s):
    if not s:
        return ''
    s = re.sub(r'<[^>]+>', '', s)
    s = s.replace('\u00a0', ' ').strip()
    return s


def main():
    ann = A.Annotator()
    general = set(ann.words.keys())          # 通用词库已有词
    for ch in ann.chars:
        general.add(ch)

    kept = {}          # word -> dict(pinyin, cats, ids)
    stat = Counter()
    for cat in CATS:
        fp = os.path.join(OUT, f'{cat}.json')
        if not os.path.exists(fp):
            continue
        for r in json.load(open(fp, encoding='utf-8')):
            raw = r.get('name') or r.get('name_cn') or ''
            name = clean(raw)
            if not name:
                continue
            stat[f'{cat}:总'] += 1
            if not CJK_RE.search(name):
                continue
            if not ONLY_CJK.match(name):
                # 允许中文里带少量符号/数字的专名，但先只收纯中文，保证干净
                continue
            if BAD_RE.search(name):
                continue
            if not (2 <= len(name) <= 6):
                continue
            if name in general:
                stat[f'{cat}:通用库已有'] += 1
                continue
            py = ann.pinyin(name)
            if not py:
                stat[f'{cat}:无注音'] += 1
                continue
            stat[f'{cat}:收录'] += 1
            e = kept.get(name)
            if e is None:
                kept[name] = {'pinyin': py, 'cats': {cat}, 'ids': {r.get('id')}}
            else:
                e['cats'].add(cat)
                e['ids'].add(r.get('id'))

    # 输出
    lines = []
    for name, e in kept.items():
        cats = sorted(e['cats'])
        w = max(WEIGHTS.get(c, 2000) for c in cats)
        lines.append((name, e['pinyin'], w, cats, sorted(str(i) for i in e['ids'])))
    lines.sort(key=lambda x: (-x[2], x[0]))

    os.makedirs(DICT_OUT, exist_ok=True)
    fp = os.path.join(DICT_OUT, 'turtledb.dict.yaml')
    with open(fp, 'w', encoding='utf-8') as f:
        f.write('# Rime dictionary\n')
        f.write('# encoding: utf-8\n')
        f.write('#\n')
        f.write('# 魔兽世界乌龟服(Turtle WoW)专有词条 —— 抓自 TurtleDB https://db.turtletail.net/\n')
        f.write('# 由 tmp/turtledb 下的抓取/注音脚本生成，注音基于 rime-frost 8105 字表离线生成。\n')
        f.write('# 生成时间: 见文件系统\n')
        f.write('---\n')
        f.write('name: turtledb\n')
        f.write('version: "1"\n')
        f.write('sort: by_weight\n')
        f.write('...\n')
        for name, py, w, cats, ids in lines:
            f.write(f'{name}\t{py}\t{w}\n')

    print(f'收录 {len(lines)} 个专有词 -> {fp}')
    print('--- 统计 ---')
    for k in sorted(stat):
        print(f'  {k}: {stat[k]}')
    if ann.miss:
        print(f'缺注音字 {len(ann.miss)}: {"".join(sorted(ann.miss))[:150]}')


if __name__ == '__main__':
    main()
