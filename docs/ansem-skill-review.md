# Ansem Skill 对比评审：`ansem`（现有）与 `ansem-ta-system`（新建）

评审日期：2026-10-11

## 1. 两个 skill 的定位

| 维度 | `ansem`（现有） | `ansem-ta-system`（新建） |
| --- | --- | --- |
| 本质 | 研究和审计框架：怎么核证据、怎么对齐时间、怎么做统计 | 交易法则：拿来就能写交易卡 |
| 主周期 | 4H（美股 1H），20 根区间 | 周线和日线定位，LTF 只放失效位 |
| 形态 | A 突破、B 回踩，都只做多 | S1 突破、S2 收复、S3 二元判定（可做空）、S4 比值轮动 |
| 离场 | 固定 3R，第 12 根时间退出，最长持有 30 根 | 到下一个 HTF 位减仓，趋势里按结构跟踪，抛物线三推离场，比值走出更低高点就换仓 |
| 本人依据 | 约 8 个来源，多数还没核实；规则主体是独立量化参数 | 约 25 条原话或二手转述，每条规则标【A】【A+】【补】 |
| 篇幅 | 约 52KB，12 个文件 | 约 31KB，6 个文件 |

结论：两者不是替代关系。现有 skill 的强项是**研究的严谨性**，但它的"交易系统"部分其实是一个通用的 4H 突破策略，Ansem 本人的成分很少。新 skill 把交易规则补到了 Ansem 自己说过的内容上。建议的分工见 §4。

## 2. 现有 skill 值得保留的部分

- 只用决策当时已收盘的 K 线、冻结关键位、pivot 有确认延迟，这些防前视偏差的规则（SKILL.md 第 3 步，evidence.md）。
- 动作类型的区分：idea、conditional_entry、fill_record……，以及"发帖时的市价不等于本人入场价"。
- 同一根 K 线同时碰到止损和目标时先按止损算，跳空止损按第一个可成交价算（manual-system.md §7.4）。
- 统计口径：R0 冻结、Wilson 区间、block bootstrap、样本外留出（validation.md）。
- `case-schema.json` 和 `cases.jsonl` 的台账格式，以及 `analyze_chart.py` 的 point-in-time 特征计算。

## 3. 问题和改进建议（按优先级）

### P0：和 Ansem 本人的方法有冲突

1. **周期错位。** `manual-system.md:37` 用 4H 前 20 根 K 线定义区间，只有大约 3.3 天。Ansem 说的是"sideways for several months"、"100 day+ consolidation"、"key weekly resistance"、"high timeframe"。`SKILL.md:36` 默认 15m/30m 作为执行层，而他明确说过看 15m 会过度交易（Q-TF1）。
   → 改成周线和日线定位，LTF 只放失效位。
2. **离场规则方向相反。** `manual-system.md:52-55` 是固定 3R 全部止盈、第 12 根 K 线时间退出、最长持有 30 根 4H（约 5 天）。Ansem 说按浮盈交易"always end up taking profits too early"（Q-PNL），还说山寨的跑赢期有 4–6 个月。
   → 改成 T1 到下一个 HTF 位减仓，剩余仓位按结构跟踪；再补上抛物线三推离场（T-PARA）和"短期涨出几倍就激进止盈"（Q-1K）这两种例外。3R 版本可以留下来做对照。
3. **市场过滤和他的阶段论不一致。** `manual-system.md:35` 要求 BTC 在 EMA20 之上并且 EMA20 ≥ EMA50。Ansem 最核心的阶段判断是"BTC 横盘、山寨补涨"（S2，C2），这时 BTC 的 EMA 常常是缠绕的，这个过滤会把他最想参与的阶段排除掉。
   → 改用 R1、R2、R3 三个阶段（新 rules.md §2）。
4. **用 RS 的变化率代替比值图结构。** `manual-system.md:36` 的 RS20 > 0、RS5 > 0 是收益率之差。Ansem 实际看的是 ALT/BTC、ALT/ETH、ALT/L1 比值图上的区间突破、收复前低和更低高点（N-Q4、L-SOL、Q-ZEC）。
   → 在比值图上用和价格图一样的结构规则。

### P1：漏掉了本人明确说过的规则

| 遗漏 | 本人证据 | 现有处理 |
| --- | --- | --- |
| 收复和假跌破（S2） | B1、Q-WIF、L-SOL、L-PUMP | `manual-system.md:67` 只作为"观察标签" |
| 做空，以及二元判定（S3） | Q-W1、C1、C-W | `manual-system.md:15` 只做多 |
| 配对和比值轮动（S4） | T-PAIR、T-ROT、Q-ZEC | 没有 |
| 方向倾向区和单笔止损分两层 | Q-HYPE 25–30、Q-WIF 0.75–0.80 | 没有 |
| "止损不往远处挪"、失效位用当日低点 | Q-INV | 只有 ATR 公式 |
| S1/S2 阶段和"必须在场" | Q-RH | 没有 |
| 账户分离、计价资产、利润滚动 | Q-TF1、Q-1K | 没有（只有 70/30） |
| 在区间高点设提醒、不盯盘 | Q-RH、Q-TF1 | 没有 |

### P2：精简

1. **免责和归属说明重复太多。** "独立 / 不归本人"之类的表述在 SKILL.md 里出现 6 次，manual-system.md 9 次，technical-math.md 3 次。
   → 只在 SKILL.md 保留一段"归属"说明，规则里用【A】【A+】【补】三个标签就够了，新 skill 已经这样改。
2. **研究部分的四个文件有重叠。** evidence.md、technical-math.md、validation.md、execution.md 都在讲"不能用未来数据、要扣成本、要样本外检验"。
   → 合并成一个 `research.md`，大约能减 40%。
3. **SKILL.md 的"核心流程"共 9 步，每一步都很长。** 交易场景用不到其中第 1、2、7 步（核身份、建台账、发帖冲击）。
   → 交易模式和研究模式分开加载。
4. **frontmatter 的 description 太偏研究。** 它写的是"还原……数学分析……"，用户说"按 Ansem 方法帮我做 SOL 的计划"时，可能不会触发这个 skill。

### P3：错误和证据缺口

1. **Bug：** `skills/ansem/agents/openai.yaml` 引用了 `assets/icon.svg`，但这个文件不存在。新 skill 已经带了自己的 icon。
2. **案例台账可以升级。** C1、C2 现在标的是"媒体二手"。这次在搜索索引里看到原帖 2061445183305052615 的标题文字是"65k & then 60k if bitcoin cant get back above"，6 月还有 Q-W1、Q-INV、C-W，可以组成一条完整的决策链（见新 skill 的 `case-btc-2026-06.md`）。建议把这些补进 `cases.jsonl`，并把 C1 的来源等级提高一级（仍然需要打开原帖核对）。
3. **sources.md 只有 8 条。** 新 skill 的 `quotes.md` 多出大约 20 条，可以直接合并过去。
4. **`analyze_chart.py` 只做描述统计。** 下一步可以加一个日线扫描器（S1、S2 触发检查）和逐根回放的回测器，复用现有的数据校验逻辑。

## 4. 建议的分工（迭代方案）

```
skills/
  ansem/                 研究模式：核证据、案例台账、时间对齐、统计验证、analyze_chart.py
    SKILL.md             精简到大约 30 行，交易规则部分直接指向 ansem-ta-system
    references/
      research.md        由 evidence + technical-math + validation + execution 合并
      sources.md         合并 quotes.md 的新增来源
      cases.jsonl        补上 2026-06 BTC 决策链
      quant-variant-A.md 由 manual-system.md 的规则 A/B 改名，作为"S1 的 4H 量化变体"
  ansem-ta-system/       交易模式：法则、交易卡、案例
```

## 5. 迭代路线

| 版本 | 内容 | 完成标准 |
| --- | --- | --- |
| v1.0 | 本次交付：法则 + 原话索引 + 案例 + 交易卡 | 已完成 |
| v1.1 | 用浏览器或用户导出逐条核对 quotes.md 中的原帖，补上发帖时间和配图 | 每条标"已核"或"未核" |
| v1.2 | 在 2020–2026 年 BTC 和前 30 山寨的日线上回放 S1，比较 S1a 和 S1b | 每个变体 ≥ 60 笔，扣费后的期望 R |
| v1.3 | 加入 S2，做消融测试：比较带和不带 §2 阶段过滤 | 阶段过滤是否提高期望 |
| v1.4 | S4 比值轮动和 §7 的离场变体（3R 对比结构跟踪） | 决定默认离场方式 |
| v2.0 | 前瞻模拟 30 笔，达到门槛后再上小额实盘 | 用 validation.md 的门槛 |
