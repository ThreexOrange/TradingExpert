# TradingExpert

独立交易员 Skills：Serenity（@aleabitoreddit）与 Ansem（@blknoiz06），分别保留来源、方法归属和独立执行规则。

## Skills

| Skill | 研究重点 | 入口 |
| --- | --- | --- |
| Serenity | 供应链瓶颈、催化、每股经济与交易执行 | [serenity-trading-desk](skills/serenity-trading-desk/SKILL.md) |
| Ansem | 喊单/配图与历史 K 线对齐、区间突破、假跌破、相对强弱与轮动 | [Ansem](skills/ansem/SKILL.md) |
| Ansem TA 法则 | 纯技术交易法则：阶段、比值选强、关键位、S1–S4 形态、失效止损与分级止盈 | [ansem-ta-system](skills/ansem-ta-system/SKILL.md) |

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
