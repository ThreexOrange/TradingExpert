# TradingExpert

独立交易员 Skills：Serenity（@aleabitoreddit）与 Ansem（@blknoiz06），分别保留来源、方法归属和独立执行规则；另有三本交易书的方法 Skills（价格行为、订单流、威科夫 2.0），为 3xOrange Advanced System 提供结构、价位和触发层。

## Skills

| Skill | 研究重点 | 入口 |
| --- | --- | --- |
| Serenity | 供应链瓶颈、催化、每股经济与交易执行 | [serenity-trading-desk](skills/serenity-trading-desk/SKILL.md) |
| Ansem | 喊单/配图与历史 K 线对齐、区间突破、假跌破、相对强弱与轮动 | [Ansem](skills/ansem/SKILL.md) |
| 裸 K 线价格行为 | Pinbar 与吞没、关键水平位、假突破、2+5 信号评分、入场止损、金字塔加仓 | [price-action-pinbar](skills/price-action-pinbar/SKILL.md) |
| 订单流交易 | 足迹图、Delta、POC、失衡与堆积、被套交易者、大单微单、吸收；逐笔成交构建足迹 | [order-flow-trading](skills/order-flow-trading/SKILL.md) |
| 威科夫 2.0 | 结构定背景、成交量分布定价位（VA/POC/VWAP/HVN/LVN）、订单流定触发 | [wyckoff-2-0](skills/wyckoff-2-0/SKILL.md) |

### Serenity

完整目录：[skills/serenity-trading-desk](skills/serenity-trading-desk)。入口：[SKILL.md](skills/serenity-trading-desk/SKILL.md)。

- 跟踪公开发言与观点变化，区分原帖、镜像、摘要和公司披露。
- 研究供应链瓶颈、催化剂、融资稀释及每股收益兑现。
- 制定多、空、等待情景，结合相对强弱、KC、期权与风险管理。
- 解码建仓、重申、退出、观察名单和兑现庆祝；分别记录持仓自述、信念依据与事实核验程度。
- 对照旧模型、新证据和当前价格，检查盈利修正、放量时间、稀释及剩余预期差。
- 评估发帖后的成交风险，分列主题名义敞口、计划止损损失和压力情景损失。

## 使用

将 `skills/serenity-trading-desk` 整个目录导入支持 Skill 的工具，保留 `references/`、`agents/` 和 `assets/` 的相对路径。也可以让其他 AI 先读取 `SKILL.md`，再按任务读取它引用的资料。

示例：

> 使用 serenity-trading-desk，核查 Serenity 最近七天的公开发言，比较旧观点与新证据，说明哪些变化会改变交易条件。

> 使用 serenity-trading-desk，分析指定标的的产业驱动、每股经济、相对强弱与多空交易情景。数据不足时列出待核条件。

## 方法归属与更新

本 Skill 不代表 Serenity 本人，不确认其真实持仓。KC、期权计算、仓位公式和宏观执行规则是独立扩展。

来源台账核查至 2026-10-10，是历史快照；具体行情、政策、公司披露及最新观点仍须实时验证。仓库中的副本不会自动同步 ChatGPT 内的后续更新。

## 2026-10-10 更新

合入上传更新包的发言解码、平台身份线索、技术路线与日期修正、发帖冲击及主题共振分析。信念分类保留未知，不从建仓或股数直接推断重仓；涨幅提示不作为机械买卖阈值，风险预算不与名义敞口混用。新增“旧模型 → 新证据 → 新模型 → 当前价格”评估流程，平台认证按日期更新，第三方档案的抽检声明保留来源限制。


## Ansem（2026-10-11）

完整目录：[skills/ansem](skills/ansem)，界面显示名 **Ansem**，调用名 `$ansem`。

- 对齐原帖、配图、发帖时间与当时已完成的 K 线；分开观点、自述持仓与真实成交。
- 量化 ATR 标准化突破/刺穿、收回速度、实体影线、趋势效率、相对强弱与 Beta 残差；参数归属明确。
- 保存历史条件案例与来源缺口，分别检验加密和美股；包含反例、费用、发帖延迟和样本外要求。
- `scripts/analyze_chart.py` 从显式 open/close 时间的 OHLCV CSV 输出研究特征与带决策时点/事前水平的 SVG，排除未完成 bar 和未来水平。

将整个 `skills/ansem` 目录导入工具，保留相对路径。示例：

> 使用 $ansem，将给定原帖及原图对齐历史 K 线，先还原当时能知道的信息，再量化突破、假跌破及相对强弱，给出候选规则与反例。

初版来源有限，部分原帖/配图未读取，未取得连续同源 OHLCV；尚未完成历史回测或证明预测优势。数学模型与风控为独立扩展，不代表本人固定参数。两个 Skills 的方法不能混为一人观点，GitHub 副本与 ChatGPT 后续更新需分别同步。

## 三本书的方法 Skills（2026-11-18）

来源：许佳聪《裸K线交易法——价格行为（Price Action）全面详解》；Michael Valtos《订单流交易》（中译本）；鲁本·维拉赫莫萨《威科夫2.0：市场结构、成交量分布与订单流》（中译本）。Skill 是读书笔记与方法提炼，用自己的话重写，**不含原书正文、图表或书籍文件**；书中阈值和作者自述的胜率都标明出处，没有当作已验证的结果。

三者在 3xOrange Advanced System 里的分工：

| 层 | 来源 | 提供什么 |
| --- | --- | --- |
| 背景 | 威科夫 2.0 | 区间还是趋势、累积还是派发、哪一方控制 |
| 价位 | 威科夫 2.0（成交量分布）、价格行为（关键水平位） | 在哪里交易：价值区边界、POC、VWAP、HVN / LVN、拐点水平位 |
| 触发 | 订单流、价格行为 | 什么时候进：吸收 + 主动、控制 + 测试、被套交易者、大单微单；Pinbar / 吞没 + 2+5 评分 |
| 执行 | 三本书 | 止损单入场、结构性止损、目标（下一关键位、HVN、未回补 POC）、分批与金字塔 |

每个 Skill 都有可运行的脚本（只用标准库）：

```bash
python skills/order-flow-trading/scripts/footprint.py --selftest
python skills/price-action-pinbar/scripts/pa_signals.py --selftest
python skills/wyckoff-2-0/scripts/volume_profile.py --selftest
```

- `footprint.py`：从逐笔成交（例如币安 aggTrades）构建足迹 K 线，计算 Delta、POC 位置、斜对角失衡、堆积失衡区、大单 / 微单、被套交易者、吸收、订单流背离。
- `pa_signals.py`：从 OHLC 逐根计算 Pinbar / 吞没 / 双星、关键位（只用已确认拐点）、2+5 评分、入场止损目标和盈亏比。
- `volume_profile.py`：按会话或固定区间计算成交量分布、价值区域、HVN / LVN、P / b 形状、VWAP 与标准差带、未回补 POC。

每个 Skill 的 `references/quant-mapping.md` 列出了可计算定义、已经在 3xOrangeTradingTheory 检验过的结论（单独的假突破、K 线级主动买卖都没通过），以及还没检验、可以事先写定规则再测的项目。

