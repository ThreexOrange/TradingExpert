# TradingExpert

基于 Serenity（@aleabitoreddit）公开研究方法的交易员 Skill，包含独立添加的技术分析与执行规则。

## Skill

完整目录：[skills/serenity-trading-desk](skills/serenity-trading-desk)。入口：[SKILL.md](skills/serenity-trading-desk/SKILL.md)。

- 跟踪公开发言与观点变化，区分原帖、镜像、摘要和公司披露。
- 研究供应链瓶颈、催化剂、融资稀释及每股收益兑现。
- 制定多、空、等待情景，结合相对强弱、KC、期权与风险管理。

## 使用

将 `skills/serenity-trading-desk` 整个目录导入支持 Skill 的工具，保留 `references/`、`agents/` 和 `assets/` 的相对路径。也可以让其他 AI 先读取 `SKILL.md`，再按任务读取它引用的资料。

示例：

> 使用 serenity-trading-desk，核查 Serenity 最近七天的公开发言，比较旧观点与新证据，说明哪些变化会改变交易条件。

> 使用 serenity-trading-desk，分析指定标的的产业驱动、每股经济、相对强弱与多空交易情景。数据不足时列出待核条件。

## 方法归属与更新

本 Skill 不代表 Serenity 本人，不确认其真实持仓。KC、期权计算、仓位公式和宏观执行规则是独立扩展。

来源台账核查至 2026-10-10，是历史快照；具体行情、政策、公司披露及最新观点仍须实时验证。仓库中的副本不会自动同步 ChatGPT 内的后续更新。
