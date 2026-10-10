# 证据、识图与时间对齐

## 身份与动作

从 @blknoiz06 原页和已核作者渠道追踪；展示名相同不验证身份，别名需交叉链接/原 ID 确认。保留原文、引用对象、回复、图片、撤销与后续。区分 idea、conditional_entry、self_reported_position、fill_record、add、reduce、exit、invalidate、celebration、watchlist。公开记录不自动等于完整经审计账户。

## 时间

保存原帖、事件、图表截止及访问时间；统一 UTC，显示北京时间及 IANA 交易所本地时区处理 DST。原始 X ID 可推候选时间 `ms=(int(id)>>22)+1288834974657`，字段必须为 `id_derived_unconfirmed`，与原帖/可信导出核验。编辑后的正文未必创建时可见。冲突时排除精确时点研究；日期粒度只给当日区间，不默认午夜入场。

分开决策、公开、读者观察和最早成交。只用 `bar_close_time <= decision_time` 已完成 bar；盘中数据要当时快照。信号在 bar 完成后产生，模拟用随后可成交报价；原帖时间不保证成交。日/周 close_time 取真实 session，不给美国日线硬加 86400 秒。

## 实际识图与数学校准

必须实际打开原图；核交易所/产品、周期、线性/对数轴、时区、指标参数、真实 candle/预测箭头与 volume 单位。OCR 后人工核对，看不清标范围。

线性轴两点 `P(y)=p1+(p2-p1)*(y-y1)/(y2-y1)`；对数轴 `ln P(y)=ln p1+(ln p2-ln p1)*(y-y1)/(y2-y1)`。像素误差 δy 传播为 δP，保留 ±δP；一个锚点不足以校准。TradingView 横轴通常按已交易 bar 排列，美股隔夜/周末不能等墙钟时间插值。用 candle 索引和日期标签匹配 OHLCV。

普通 volume 柱不能精确重建 volume profile；截图不能唯一恢复隐藏源码。预测箭头不是价格，不能捏造未来路径概率。

## 数据与出图

核同一 venue、pair 和价格类型；OHLC 合法、时间唯一、缺 bar、单位、拆股/除息与合约迁移。结构用当时未复权可交易尺度，长期回报另标复权/总回报，不混用。跨资产同步共同已完成 session，不能前向填充周末股票制造领先。

图上标原帖线/证据 ID、事前水平、信号与最早可执行时点；未来结果分隔为复盘。实际成交、自述与模拟分标签。无 OHLCV 不造 candle，可出明确标示的价位算术示意。

脚本 CSV 字段：open_time,close_time,open,high,low,close,volume；时间 ISO 且带时区，volume 可空。close_time 必须显式。脚本不负责下载、验证身份、确认成交或测 Alpha。

## 脚本调用

```bash
python scripts/analyze_chart.py bars.csv --asof 2024-04-19T12:00:00Z --output features.json --svg chart.svg
```

日期只是格式示例，不代表任何案例实际发帖时间。可选 `--window 20 --atr-period 14 --benchmark same_intervals.csv --levels levels.json --log`。levels 为数组，每项 `price,label,known_at`；必须事前已知。CSV 用实际 session 的 close_time。历史案例机器台账见 [cases.jsonl](cases.jsonl)，不能将其中候选时间当已核。脚本只画已完成行情，不绘未来结果。收回多bar状态、pivot确认、事件研究和回测须按数学/验证规则另行执行，脚本不自动实现这些研究。
