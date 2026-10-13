# dict-wow

魔兽世界**乌龟服（Turtle WoW / 水豚乐园）**中文专有词库。

数据抓取自 [TurtleDB](https://db.turtletail.net/)（乌龟服中文数据库），生成可直接用于 Rime / iuv 的拼音词库。

## 词库

`dict/turtledb.dict.yaml` —— **26270 条**专有词，格式为 Rime 风格的 `词<TAB>带空格拼音<TAB>权重`：

```
冰点岩	bing dian yan	6000
雷管大师手套	lei guan da shi shou tao	4000
永恒牺牲之冠	yong heng xi sheng zhi guan	4000
```

收录范围：通用词库（rime-frost 的 base/ext/others/8105）里**没有**的魔兽专名 —— 包括乌龟服自定义内容与玩家同样要打的原版专名。通用输入法本就能出的词一律剔除，避免污染。

## 数据来源

| 分类 | 条数 | 分类 | 条数 |
|---|---:|---|---:|
| items 物品 | 23929 | objects 物体 | 21057 |
| spells 技能 | 27946 | npcs NPC | 13233 |
| quests 任务 | 6073 | zones 地区 | 112 |
| factions 阵营 | 51 | **合计** | **92401** |

> spells 分类含中文的条目 100% 为 `@` 开头的内部占位/附魔效果名，对词库无价值，已整体过滤。

## 目录结构

```
dict/    最终词库 turtledb.dict.yaml
data/    各分类解析后的结构化 JSON（抓取产物）
scripts/ 抓取 / 解析 / 注音 / 生成脚本
raw/     原始 HTML 缓存（运行时生成，不纳入版本控制）
```

## 复现

```bash
# 1. 抓取（约 1670 页，10 分钟；支持断点续传）
python scripts/fetch.py

# 2. 生成词库（离线注音 + 过滤）
python scripts/gen_dict.py
```

注音依赖本机 rime-frost 词库目录，用环境变量指定：

```bash
RIME_DICT_DIR=/path/to/rime-frost/cn_dicts python scripts/gen_dict.py
```

## 实现要点

- **绕过 Cloudflare**：站点对根路径 `/` 带 query 的请求返回 CF JS 挑战（403），但走 `/index.php?items` 可正常访问；官方 JSON 接口 `/api/tooltip_item.php?id=N` 不受影响。
- **两种渲染方式**：`items` 是服务端渲染的 HTML 表格，其余分类是内嵌在 `new Listview({... data: [...] })` 里的 JSON 数组。
- **离线注音**：不依赖 pypinyin，改用 rime-frost 的 `8105.dict.yaml`（通用规范汉字表）作单字拼音表，已有词直接取 base/ext 词库读音。
- **筛选策略**：原版基准站 `db.nfuwow.com` 已下线，无法做原版差集；改用「通用词库缺失」作为等价信号。

## 已知问题

- 6 个生僻字缺注音：`呣 嚢 營 盜 矽 虛`
- 多音字专名可能存在少量错标，待人工校对
- 权重为分类经验值（2000–6000），可按需调整

## 声明

数据版权归 Blizzard Entertainment 及 Turtle WoW 所有，本项目仅作输入法词库用途。
