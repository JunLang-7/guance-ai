# 山东企业模拟案例包

本目录包含 5 家山东企业的模拟营销决策案例，覆盖智能家电、啤酒、商用车动力、滋补健康和宠物食品五个行业。每个案例包含：

- `reports/<slug>.md`：至少一万字的过程性报告（含图表）。
- `projects/<slug>.json`：可导入观策AI的模拟项目数据。
- `charts/<slug>/`：封面、信号结构、预算、计划 vs 实际、指标对比、可信度图。
- `data/<slug>-signals.csv`：信号清单。
- `data/<slug>-channels.csv`：渠道计划与模拟实际数据。

## 案例列表

| 企业 | 行业 | 模拟预算 | 报告 | 项目数据 |
| --- | --- | --- | --- | --- |
| 海尔智家股份有限公司 | 智能家电与全屋智能 | 120 万 | reports/haier-smart-home.md | projects/haier-smart-home.json |
| 青岛啤酒股份有限公司 | 啤酒与高端饮品 | 80 万 | reports/tsingtao-premium-beer.md | projects/tsingtao-premium-beer.json |
| 潍柴动力股份有限公司 | 商用车动力与高端装备 | 60 万 | reports/weichai-powertrain.md | projects/weichai-powertrain.json |
| 东阿阿胶股份有限公司 | 滋补健康与中式养生 | 50 万 | reports/dongee-ejiao.md | projects/dongee-ejiao.json |
| 乖宝宠物食品集团股份有限公司 | 宠物食品与宠物消费 | 40 万 | reports/gambol-pet-food.md | projects/gambol-pet-food.json |

## 怎么用

1. 打开观策AI桌面端。
2. 设置 → 模拟案例库 → 选择案例 → 导入为演示项目。
3. 在市场情报、策略、复盘页查看信号、主题、方案、审批和复盘。
4. 对照 `reports/<slug>.md` 阅读过程材料。

也可以在设置→项目与备份→导入项目 JSON 中手动选择 `projects/<slug>.json`。

## 重要声明

所有消费者语句、竞品观察、渠道数据、复盘结果和“企业满意度”均为模拟；企业名称和业务方向来自公开资料，但不代表企业真实意见、真实广告效果或真实经营数据。任何对外使用前，必须由企业市场、法务、合规和数据负责人复核。

## 相关文档

- [方法与可信度](methodology.md)
- [可信度对比](credibility-summary.md)
- [迭代记录](iteration-log.md)
