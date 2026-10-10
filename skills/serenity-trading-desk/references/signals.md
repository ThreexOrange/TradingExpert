# 发言解码：把一条帖子变成信号

本文件从 2025-07 至 2026-09 的公开帖子样本中抽取本人的**措辞习惯**，用于判断一条帖子在交易上意味着什么。它描述的是“怎么读”，不是“该买什么”；具体标的、价位和持仓随时变化，必须重新联网核验。日期为 UTC。

## 先分类，再谈交易

对每条已核身份的帖子填写：

| 字段 | 取值 |
| --- | --- |
| 信号类型 | 披露建仓 / 加仓 / 交易点子 / 仅论点 / 明确无仓位 / 重申持有 / 减仓或退出 / 回避警告 / 兑现庆祝 / 宏观状态 / 新闻摘要 / 互动帖 |
| 持仓状态 | 已持有 / 新增 / 明确无仓位 / 未知 |
| 信念层级 | S 明确核心持仓 / A 明确高信念 / B 交易点子 / C 观察名单 / U 未知；另列原话和分类依据 |
| 新颖度 | 首次提及 / 强化 / 削弱 / 重复 / 反转 / 待核；首次指当前可访问样本中的首次 |
| 已发生涨跌 | 自发帖时点、自首次提及以来的涨跌幅 |

将信号类型、持仓状态、信念和证据强度分别判断。S/A/B/C/U 是本 Skill 的阅读分类，不是本人评级、胜率、建议仓位或交易方向。仅在本人明确说是核心/最大持仓或最高信念时给 S/A；只有建仓、股数或长论点时，信念可仍为 U。披露只证明其当时自述，不证明当前持有；资料不足就写未知，不用未发卖出帖补全仓位。

## 措辞对照

| 本人措辞（示例） | 含义 | 样本 |
| --- | --- | --- |
| “I've initiated a position in $X ($___M MC)” | 披露建仓；信念先记 U，再核全文，不能自动给 A | [OSS，2026-01-07](https://x.com/aleabitoreddit/status/2008910857003221451) |
| “I went long…”“took a sizable position ~€43” | 披露建仓，常给价位 | SOI 等 |
| “Fun Trade Idea: Long $X” / “Trade Idea:” | B 类交易点子；期限、持仓和催化另核，不能仅靠标签推断短线 | [RPI，2026-02-16](https://x.com/aleabitoreddit/status/2023415224372756782)；[Hammond，2026-04-06](https://x.com/aleabitoreddit/status/2041168871168545115) |
| “Random ___ names I like”“just some random ideas” | C 级观察名单，常无仓位 | [CPO 名单，2026-05-12](https://x.com/aleabitoreddit/status/2054076086452162675) |
| “(disclosure: I own…)”/“(disclosure: I don't own…)”/“I have no positions in” | 明确的持仓标注，优先于推断 | [2026-06-05](https://x.com/aleabitoreddit/status/2062744101393715325)、[2026-08-30](https://x.com/aleabitoreddit/status/2094027369648681284) |
| “one of my largest holdings”“top holdings”“million+ share position” | 前两者支持当时自述核心持仓；百万股只给股数，不足以推断账户权重或 S 级 | [SIVE，2026-06-26](https://x.com/aleabitoreddit/status/2070444675337503166) |
| “Nothing's changed with $X… looks like a buying opportunity” | 下跌中重申持有，是其对回撤的惯常反应；不等于你该加仓 | [AAOI，2026-03-12](https://x.com/aleabitoreddit/status/2032181937784389759) |
| “I trimmed / cut some concentration / to go off margin” | 减仓，多因杠杆或宏观，不一定是论点失效；常事后才说 | [2026-03-28](https://x.com/aleabitoreddit/status/2037804702797287444) |
| “I sold out of…” + 理由 | 明确当时自述退出；再区分论点失效、估值、流动性、杠杆或换仓，不自动归为基本面反转 | [新云整合，2025-10-25](https://x.com/aleabitoreddit/status/1981981029029298374)；[Sumitomo 出口管制后卖出光通信，2026-01-09](https://x.com/aleabitoreddit/status/2009561002958782514) |
| “not a fan of ATMs/dilution”“toxic financing” | 回避警告。本人自述“I don't short”（[2025-11-05](https://x.com/aleabitoreddit/status/1985898768836018244)），所以这是“不碰/等待”，**不是做空信号** | IREN、POET、AAOI 的 ATM 讨论 |
| “validated”“played out”“X% since I went long” | 兑现庆祝，涨幅通常已发生，**不是新入场信号** | [SOI，2026-05-28](https://x.com/aleabitoreddit/status/2059965358455619764) |
| “I don't give earnings up or down predictions” | 自述不预测财报涨跌；不能把所有财报前帖子都判成无方向观点，逐帖核全文 | [2026-08-10](https://x.com/aleabitoreddit/status/2086638639052955732) |
| 每月 “What's your #1 highest conviction stock?” | 互动帖，无信号 | [2026-08-09](https://x.com/aleabitoreddit/status/2086304269943419276) |
| “thesis tracking mode” | 自述以跟踪旧论点为主；不能据此推断实际开仓频率 | [2026-09-23](https://x.com/aleabitoreddit/status/2102793298561970218) |

## 本人自述的择时方式

[2026-04-25](https://x.com/aleabitoreddit/status/2048123597223579736) 本人概括过入场节奏：找到未被注意的关键公司 → 围绕 NVDA GTC、OFC 等催化安排建仓 → 关注实质性变化的新闻 → 在下跌中找入场点（“this is where your astrology TA's get used”）。另一类是新信息发现型（例如 ALRIB）。因此“催化前”的帖子与“新事实”帖子要分开处理：前者看事件日历，后者看事实能否独立核验。

## 解读规则

1. **按决策影响排序**：优先报告改变需求、合格产能、订单、利润、股数、融资或失效条件的新事实；退出和反证可比新建仓更重要。首次提及、热度和本人仓位仅作研究线索，不能替代事实核验。重申、庆祝帖中若包含实质新证据，仍按新证据处理。
2. **卖出很少实时公布**：本人自述大部分仓位未实现、很多从未卖出（[2026-05-15](https://x.com/aleabitoreddit/status/2055405163092066719)）。不能用“没说卖”推断“仍持有”，也不能用“仍看好产业”推断“仍持有该股”。
3. **长期产业判断 ≠ 今天的买点**：本人多次区分长期观点不变与短期入场点（例如 [2026-04-19 的 30 只名单复盘](https://x.com/aleabitoreddit/status/2045965735386820934)：“my long term opinion doesn't change… Short term entry points do though”）。
4. **本人入场价只作背景**：用用户当前可成交价格重算预期差和风险收益；不能假设跟随者总比本人买得贵，也不能沿用本人入场价作为自己的成本。
5. **免责声明是真的**：“I literally and legally can't give you advice”（[2026-08-07](https://x.com/aleabitoreddit/status/2085608520293154900)）。输出时把本人观点与本 Skill 的执行规则分开标注。
