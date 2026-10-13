# -*- coding: utf-8 -*-
"""TurtleDB 页面解析器：从列表页 HTML 中提取结构化词条。"""
import re
import json


def extract_json_array(html, key='data: ['):
    """从 `new Listview({... data: [ ... ] ...})` 中括号匹配提取 JSON 数组。"""
    i = html.find(key)
    if i < 0:
        return None
    j = i + len(key) - 1  # '[' 的位置
    depth = 0
    instr = False
    esc = False
    for k in range(j, len(html)):
        c = html[k]
        if instr:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    return json.loads(html[j:k + 1])
    return None


def parse_items(html):
    """items 是服务端渲染的 HTML 表格，逐行解析。"""
    rows = []
    for tr in re.findall(r'<tr>(.*?)</tr>', html, re.S):
        m = re.search(r'href="\?item=(\d+)"', tr)
        if not m:
            continue
        iid = int(m.group(1))
        nm = re.search(r'<a class="q(\d)" href="\?item=\d+"[^>]*>(.*?)</a>', tr, re.S)
        if not nm:
            continue
        quality = int(nm.group(1))
        raw_name = re.sub(r'<[^>]+>', '', nm.group(2)).strip()
        parts = re.split(r'\s*<br>\s*', nm.group(2), maxsplit=1)
        name_cn = re.sub(r'<[^>]+>', '', parts[0]).strip()
        name_en = re.sub(r'<[^>]+>', '', parts[1]).strip() if len(parts) > 1 else ''
        # 后续 <td> 里的等级/类型
        tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)
        plain = [re.sub(r'<[^>]+>', '', t).strip() for t in tds]
        # 品质列 title
        qm = re.search(r'href="\?items&amp;quality=\d+"[^>]*title="([^"]*)"', tr)
        rows.append({
            'id': iid,
            'name_cn': name_cn,
            'name_en': name_en,
            'quality': quality,
            'quality_cn': qm.group(1) if qm else '',
            'cells': plain,
        })
    return rows


def parse_listview(html):
    """npcs/quests/objects/spells/zones/factions 走内嵌 JSON。"""
    return extract_json_array(html) or []


CATS = {
    'items':    {'kind': 'items',    'url': 'items'},
    'npcs':     {'kind': 'json',     'url': 'npcs'},
    'quests':   {'kind': 'json',     'url': 'quests'},
    'objects':  {'kind': 'json',     'url': 'objects'},
    'spells':   {'kind': 'json',     'url': 'spells'},
    'zones':    {'kind': 'json',     'url': 'zones'},
    'factions': {'kind': 'json',     'url': 'factions'},
}


def parse(cat, html):
    if CATS[cat]['kind'] == 'items':
        return parse_items(html)
    return parse_listview(html)


if __name__ == '__main__':
    import sys
    fn = sys.argv[1] if len(sys.argv) > 1 else 'idx_items.html'
    cat = sys.argv[2] if len(sys.argv) > 2 else 'items'
    data = parse(cat, open(fn, encoding='utf-8').read())
    print(f'{fn} [{cat}] -> {len(data)} 条')
    for d in data[:3]:
        print(json.dumps(d, ensure_ascii=False))
