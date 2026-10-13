# -*- coding: utf-8 -*-
"""用 rime-frost 词库给 TurtleDB 词条离线注音（替代 pypinyin）。

- 单字表: 8105.dict.yaml（《通用规范汉字表》）
- 词表:   base/ext/others/41448 —— 已有词直接取其拼音，比逐字拼更准
输出: out/<cat>.dict.yaml 风格的行  `词\t拼音\t权重`
"""
import os
import re
import json
import sys

# 通用词库目录（rime-frost cn_dicts）。可用环境变量 RIME_DICT_DIR 覆盖。
DICT_DIR = os.environ.get(
    'RIME_DICT_DIR', r'D:/Projects/input-method/iuvim/data/rime-frost/cn_dicts')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data')

CHAR_FILE = '8105.dict.yaml'
WORD_FILES = ['base.dict.yaml', 'ext.dict.yaml', 'others.dict.yaml', '41448.dict.yaml']

PY_RE = re.compile(r'^[a-z]+$')
PYSP_RE = re.compile(r'^[a-z]+( [a-z]+)*$')
CJK_RE = re.compile(r'[\u4e00-\u9fff]')


def _rows(fn):
    fp = os.path.join(DICT_DIR, fn)
    if not os.path.exists(fp):
        return
    for line in open(fp, encoding='utf-8'):
        line = line.rstrip('\n').rstrip('\r')
        if not line or line.startswith('#') or line.startswith('---') or line.startswith('...'):
            continue
        p = line.split('\t')
        if len(p) < 2:
            continue
        yield p


def load_char_table():
    """char -> [(pinyin, weight)]，按权重降序。"""
    m = {}
    for p in _rows(CHAR_FILE):
        w = p[0]
        py = p[1]
        if len(w) == 1 and PY_RE.match(py):
            wt = int(p[2]) if len(p) > 2 and p[2].isdigit() else 0
            m.setdefault(w, []).append((py, wt))
    for k in m:
        m[k].sort(key=lambda x: -x[1])
    return m


def load_word_table():
    """word -> pinyin（空格分隔）。"""
    m = {}
    for fn in WORD_FILES:
        for p in _rows(fn):
            w, py = p[0], p[1]
            if not w or w not in m and PYSP_RE.match(py):
                if PYSP_RE.match(py):
                    m.setdefault(w, py)
    return m


class Annotator:
    def __init__(self):
        self.chars = load_char_table()
        self.words = load_word_table()
        self.miss = set()

    def pinyin(self, word):
        """返回空格分隔拼音；有字无注音则返回 None。"""
        if word in self.words:
            return self.words[word]
        out = []
        for ch in word:
            if not CJK_RE.match(ch):
                return None  # 含非中文字符，跳过
            lst = self.chars.get(ch)
            if not lst:
                self.miss.add(ch)
                return None
            out.append(lst[0][0])
        return ' '.join(out)

    def clean(self, s):
        """清洗词条：去掉标记、括号补充、占位符等。"""
        if not s:
            return ''
        s = re.sub(r'<[^>]+>', '', s)
        s = s.replace('\u00a0', ' ').strip()
        return s


def iter_entries(cat):
    fp = os.path.join(OUT, f'{cat}.json')
    if not os.path.exists(fp):
        return
    for r in json.load(open(fp, encoding='utf-8')):
        name = r.get('name') or r.get('name_cn') or ''
        yield r.get('id'), name


def main():
    cats = sys.argv[1:] or ['items', 'npcs', 'quests', 'objects', 'spells', 'zones', 'factions']
    a = Annotator()
    total = ok = 0
    lines = []
    seen = set()
    for cat in cats:
        for rid, raw in iter_entries(cat):
            name = a.clean(raw)
            if not name or name in seen:
                continue
            if not CJK_RE.search(name):
                continue  # 纯英文/数字跳过
            if len(name) > 8:
                continue  # 过长多半是句子/占位
            total += 1
            py = a.pinyin(name)
            if not py:
                continue
            seen.add(name)
            ok += 1
            lines.append((name, py, cat, rid))
    lines.sort(key=lambda x: (x[0], x[2]))
    fp = os.path.join(OUT, 'annotated.tsv')
    with open(fp, 'w', encoding='utf-8') as f:
        for name, py, cat, rid in lines:
            f.write(f'{name}\t{py}\t{cat}\t{rid}\n')
    print(f'候选中文词 {total}，成功注音 {ok} -> {fp}')
    if a.miss:
        ms = ''.join(sorted(a.miss))
        print(f'缺注音的字 ({len(a.miss)}): {ms[:200]}')


if __name__ == '__main__':
    main()
