# dict-wow

魔兽世界**乌龟服（Turtle WoW / 水豚乐园）**中文专有词库，可直接用于 Rime / iuv 等拼音输入法。

乌龟服有大量自定义的物品、NPC、任务、地名，通用输入法（QQ、搜狗、微软拼音等）都没有覆盖。本词库专门补上这部分，让你能直接打出「雷管大师手套」「永恒牺牲之冠」「仇恨熔炉采石场」。

## 词库

`dict/turtledb.dict.yaml` —— **26270 条**，Rime 风格，每行 `词<TAB>带空格拼音<TAB>权重`：

```
冰点岩	bing dian yan	6000
雷管大师手套	lei guan da shi shou tao	4000
永恒牺牲之冠	yong heng xi sheng zhi guan	4000
```

收录原则：只收通用词库里**没有**的魔兽专名 —— 既包括乌龟服自定义内容，也包括玩家同样要打的原版专名（如「影牙城堡」）。通用输入法本来就能打出的词一律剔除，避免污染日常输入。

## 使用

**Rime**：把 `turtledb.dict.yaml` 放进用户配置目录，然后在方案的 `.dict.yaml` 里导入：

```yaml
import_tables:
  - turtledb
```

**iuv**：放进 `data/rime-frost/cn_dicts/`，安装链会自动合并编译。

## 数据覆盖

| 分类 | 条数 | 分类 | 条数 |
|---|---:|---|---:|
| items 物品 | 23929 | objects 物体 | 21057 |
| spells 技能 | 27946 | npcs NPC | 13233 |
| quests 任务 | 6073 | zones 地区 | 112 |
| factions 阵营 | 51 | **合计** | **92401** |

词条抓取自乌龟服中文数据库 [TurtleDB](https://db.turtletail.net/)。

## 目录结构

```
dict/    最终词库 turtledb.dict.yaml
data/    各分类的结构化数据
scripts/ 抓取 / 解析 / 注音 / 生成脚本
raw/     原始页面缓存（运行时生成，不纳入版本控制）
```

## 重新生成

```bash
python scripts/fetch.py      # 抓取（约 10 分钟，支持断点续传）
python scripts/gen_dict.py   # 过滤 + 注音 + 生成词库
```

注音依赖本机 rime-frost 词库目录，可用环境变量指定：

```bash
RIME_DICT_DIR=/path/to/rime-frost/cn_dicts python scripts/gen_dict.py
```

## 已知问题

- 6 个生僻字缺注音：`呣 嚢 營 盜 矽 虛`
- 多音字专名可能存在少量错标，待人工校对
- 权重为分类经验值（2000–6000），可按需调整

## 声明

数据版权归 Blizzard Entertainment 及 Turtle WoW 所有，本项目仅作输入法词库用途。
