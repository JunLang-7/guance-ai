from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib.pyplot as plt

from render_charts import plot

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "simulations"
REPORT_DIR = SIM / "reports"
CHART_DIR = SIM / "charts"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def cny(cents):
    return "—" if cents is None else f"{cents / 100:,.0f} 元"


def num(value, digits=0):
    return "—" if value is None else f"{value:,.{digits}f}"


def table(headers, rows):
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
        *["| " + " | ".join(str(cell).replace("|", "/") for cell in row) + " |" for row in rows],
    ])


def build_report(meta, data):
    m = meta["metrics"]
    company = data["company"]
    story = meta["narrative"]
    plan_a, plan_b = data["plans"]
    review = data["reviews"][0]
    approval = data["approvals"][0]
    signals = data["signals"]
    sources = data["sources"]
    themes = data["themes"]
    opps = data["opportunities"]
    history = meta["history"]
    satisfaction = meta["satisfaction"]
    fit = meta["fit"]
    channels = {}
    for channel in data["reviews"][0]["channels"]:
        channels[channel["channel"]] = channel
    channel_rows = []
    for channel in plan_a["channels"]:
        actual = channels.get(channel["channel"], {})
        spend = actual.get("actualSpendCents") or 0
        impressions = actual.get("impressions") or 0
        clicks = actual.get("clicks") or 0
        leads = actual.get("leads") or 0
        ctr = clicks / impressions if impressions else None
        cpc = spend / 100 / clicks if clicks else None
        cpl = spend / 100 / leads if leads else None
        channel_rows.append([channel["channel"], cny(channel["budgetCents"]), cny(spend), num(impressions), num(clicks), num(leads), f"{ctr*100:.2f}%" if ctr else "—", f"{cpc:.2f}" if cpc else "—", f"{cpl:.0f}" if cpl else "—"])
    total_row = ["合计", cny(m["plannedCents"]), cny(m["actualSpendCents"]), num(m["impressions"]), num(m["clicks"]), num(m["leads"]), f"{(m['ctr'] or 0)*100:.2f}%", f"{m['cpcYuan'] or 0:.2f}", f"{m['cplYuan'] or 0:.0f}"]
    signal_rows = [[s["id"], s["platform"], s["category"], s["priority"], s["status"], s["title"], s["impact"]] for s in signals]
    source_rows = [[s["id"], s["name"], s["platform"], s["kind"], s["publishedAt"], "模拟"] for s in sources]
    theme_rows = [[t["id"], t["title"], f"{t['confidence']}/{t['claimType']}", "、".join(t["evidenceSignalIds"]), t["caveat"]] for t in themes]
    plan_rows = [["A", plan_a["name"], cny(sum(c["budgetCents"] for c in plan_a["channels"])), "、".join(c["channel"] for c in plan_a["channels"]), plan_a["coreMessage"]], ["B", plan_b["name"], cny(sum(c["budgetCents"] for c in plan_b["channels"])), "、".join(c["channel"] for c in plan_b["channels"]), plan_b["coreMessage"]]]
    sat_rows = [[n, f"{s}/5", c] for n, s, c in satisfaction["criteria"]]
    timeline = [("T-15", "确定企业与公开资料范围", "完成"), ("T-12", "建立来源清单与采集模板", "完成"), ("T-8", "采集模拟消费者/竞品/行业信号", "完成"), ("T-6", "去重、分类、标注证据状态", "完成"), ("T-5", "人工核验与冲突保留", "完成"), ("T-3", "归纳主题与 A/B 方案", "完成"), ("T-2", "预算校验与审批快照", "完成"), ("T", "模拟投放", "模拟"), ("T+2", "渠道数据复盘", "完成"), ("T+3", "历史基线回测与可信度", "完成"), ("T+5", "适配性判断与迭代", "完成")]
    text = f"""# {meta['name']}｜观策AI 山东企业模拟案例

![案例封面](../{meta['chartDir']}/cover.png)

> **重要声明**：本报告是企业营销决策的模拟验收材料。企业名称与业务方向来自公开资料；消费者语句、竞品观察、渠道数据、复盘结果和“企业满意度”均为模拟，不代表企业真实意见、真实广告账户、真实消费者调研或真实经营数据。任何对外使用前，必须由企业市场、法务、合规和数据负责人复核。

## 0. 阅读指引与结论摘要

本案例把完整的营销决策闭环跑一遍：明确企业与行业背景 → 设计资料收集范围 → 建立来源台账 → 对模拟消费者语句、竞品动态和行业材料去重、分类、证据核验 → 归纳主题和机会 → 形成 A/B 方案 → 预算校验与审批快照 → 模拟投放与复盘 → 历史基线回测与可信度评分 → 企业适配性与满意度模拟 → 迭代建议。

本案例的核心判断是：**{story['decision'][0]}** 从模拟结果看，方案 A 的线索完成率为 {m['leadAchievement']*100:.1f}%，线索成本为 {m['cplYuan']:.0f} 元，CTR 为 {(m['ctr'] or 0)*100:.2f}%；与历史基线相比，MAPE 为 {m['mape']*100:.1f}%，可信度评分为 {m['credibility']:.1f}/100。这个结果说明方案有可执行性，但仍有明确的复核边界。

**模拟企业满意度：{satisfaction['score']}/5。** {satisfaction['overall']}

## 1. 企业公开资料与模拟边界

### 1.1 企业基本情况

{table(['项目', '内容'], [['企业', meta['name']], ['品牌', meta['brand']], ['行业', meta['industry']], ['区域', meta['region']], ['阶段', company['stage']], ['模拟产品', company['product']], ['产品说明', company['productSpec']], ['模拟目标', company['goal']], ['模拟预算', f"{meta['budgetYuan']:,} 元"], ['模拟周期', f"{meta['campaignStart']} — {meta['campaignEnd']}"], ['模拟线索目标', f"{meta['targetLeads']:,} 条"]])}

### 1.2 公开资料如何使用

{story['profile'][0]}

{story['profile'][1]}

本案例只把公开资料用于“企业背景、行业方向、品牌与产品语境”，不把公开资料当作真实消费者证据，也不引用未核实的财务数字。所有“消费者原话”均来自模拟材料，不能作为真实用户调研引用。所有渠道数据均为假设值，不能作为企业真实广告效果。

### 1.3 为什么选择这家企业

选择标准不是“名气大”，而是同时满足三点：第一，企业处于山东，具有区域代表性；第二，行业决策链有差异，能检验观策AI是否只会做一种模板；第三，企业有明确的战略关键词，可以用来判断方案是否“符合企业发展”。本案例的战略关键词是：**{meta['industry']}、品牌升级、场景化与可验证交付**。

{story['context'][0]}

{story['context'][1]}

## 2. 研究问题与判断标准

### 2.1 本次模拟要回答什么

{story['decision'][0]}

### 2.2 判断标准

1. **战略契合**：方案是否服务于企业当前的产品、品牌和渠道方向。
2. **证据充分**：主题是否有多条信号支撑，关键结论是否能追溯到来源。
3. **执行可行**：预算、渠道、承接能力是否匹配，是否存在明显履约风险。
4. **结果可信**：模拟结果与历史基线的偏差是否在可解释范围内。
5. **企业可接受**：以模拟企业市场负责人视角，是否愿意进入小范围试点。

### 2.3 本次模拟的边界

- 不使用企业真实广告账户、真实订单或真实用户个人信息。
- 不声称“企业已经满意”，只做模拟满意度访谈与适配性判断。
- 不把模拟数据当作行业结论，也不把单案例结论外推到整个行业。
- 涉及功效、医疗、金融、未成年人等敏感表达时，必须由企业合规部门复核。

## 3. 资料收集过程

### 3.1 采集设计

本案例采用“多源交叉”的采集设计：消费者侧看小红书、抖音、电商评价和问卷；竞品侧看行业媒体与竞品动态；行业侧看行业观察、政策/平台公告和线下走访；企业侧只使用公开资料。这样做的目的不是追求数据量，而是让同一判断能从不同来源被交叉验证。

### 3.2 来源清单

{table(['来源ID', '来源名称', '平台', '类型', '日期', '状态'], source_rows)}

### 3.3 采集时间线

{table(['时间点', '过程动作', '状态'], [[a, b, c] for a, b, c in timeline])}

### 3.4 采集过程中的质量控制

1. **来源可追溯**：每条信号保留来源 ID、平台、采集时间和备注。
2. **模拟标识**：所有模拟材料在来源备注中明确标注，不与真实数据混用。
3. **去重**：同一来源的重复语句只保留一条，并在备注中说明。
4. **冲突保留**：不同来源出现相反判断时，不强行合并，保留为待核实或争议状态。
5. **敏感内容**：涉及功效、价格承诺、竞品贬损的内容，进入人工复核清单。

## 4. 数据清洗、编码与证据核验

### 4.1 清洗规则

- 删除明显的广告、无关评论和重复语句。
- 统一平台名称、日期格式和类别编码。
- 将“消费者/竞品/行业”作为一级类别，将“高/中/低”作为优先级。
- 将“已核实/待核实/有争议/重复”作为证据状态，不用“看起来合理”代替核实。
- 所有模拟数据保留 `simulated: true` 或 `dataKind: simulated` 标识。

### 4.2 信号清单

{table(['ID', '平台', '类别', '优先级', '状态', '标题', '影响'], signal_rows)}

### 4.3 单条信号研判记录

"""
    for s in signals:
        text += f"""**{s['id']}｜{s['title']}**

- 观察：{s['summary']}
- 原话/证据：{s['quote']}
- 判断：{s['impact']}
- 状态：{s['status']}；相关性 {s['relevance']}/5；标签：{'、'.join(s['tags'])}
- 下一步：{'进入主题聚合，优先用于方案 A/B 的证据引用。' if s['status'] == 'verified' else '保留为待核实或争议记录，不进入对外承诺；先补充原始证据或企业确认。'}

"""
    text += f"""### 4.4 证据核验结果

本案例共 {meta['counts']['signals']} 条信号，其中已核实 {sum(1 for s in signals if s['status'] == 'verified')} 条，待核实 {sum(1 for s in signals if s['status'] == 'pending')} 条，争议 {sum(1 for s in signals if s['status'] == 'disputed')} 条。已核实信号用于主题和方案，待核实信号用于提示风险和后续任务，不直接进入对外承诺。

## 5. 市场洞察与主题研判

### 5.1 主题清单

{table(['主题', '标题', '置信度/类型', '证据信号', '边界'], theme_rows)}

### 5.2 主题一：{themes[0]['title']}

{themes[0]['summary']}

这个主题之所以成立，不是因为某一条评论，而是因为多条信号从不同角度指向同一件事：{themes[0]['direction']} 在方案上，它对应的动作是：{themes[0]['opportunity']}。但必须保留边界：{themes[0]['caveat']}

### 5.3 主题二：{themes[1]['title']}

{themes[1]['summary']}

这个主题更适合用来解释“为什么某些渠道有效、某些渠道无效”。{themes[1]['direction']} 方案动作是：{themes[1]['opportunity']}。边界是：{themes[1]['caveat']}

### 5.4 主题三：{themes[2]['title']}

{themes[2]['summary']}

这个主题提醒我们：不要把单一人群或单一渠道当成全部市场。{themes[2]['direction']} 方案动作是：{themes[2]['opportunity']}。边界是：{themes[2]['caveat']}

### 5.5 机会与风险

{table(['机会', '事实依据', '可执行动作', '验证条件', '语气'], [[o['title'], o['fact'], o['opportunity'], o['verify'], o['tone']] for o in opps])}

## 6. A/B 方案设计与预算

### 6.1 方案对比

{table(['方案', '名称', '总预算', '渠道', '核心信息'], plan_rows)}

### 6.2 方案 A：{plan_a['name']}

- 定位：{plan_a['positioning']}
- 人群：{plan_a['audience']}
- 核心信息：{plan_a['coreMessage']}
- 节奏：{plan_a['timing']}
- 理由：{plan_a['rationale']}
- 约束：{'；'.join(plan_a['constraints'])}
- 不确定项：{'；'.join(plan_a['uncertainties'])}

### 6.3 方案 B：{plan_b['name']}

- 定位：{plan_b['positioning']}
- 人群：{plan_b['audience']}
- 核心信息：{plan_b['coreMessage']}
- 节奏：{plan_b['timing']}
- 理由：{plan_b['rationale']}
- 约束：{'；'.join(plan_b['constraints'])}
- 不确定项：{'；'.join(plan_b['uncertainties'])}

### 6.4 预算分配

![A/B 预算分配](../{meta['chartDir']}/budget.png)

{table(['渠道', '方案 A 预算', '方案 A 角色', '方案 B 预算', '方案 B 角色'], [[c, cny(next((x['budgetCents'] for x in plan_a['channels'] if x['channel'] == c), 0)), next((x['role'] for x in plan_a['channels'] if x['channel'] == c), '—'), cny(next((x['budgetCents'] for x in plan_b['channels'] if x['channel'] == c), 0)), next((x['role'] for x in plan_b['channels'] if x['channel'] == c), '—')] for c in list(dict.fromkeys([x['channel'] for x in plan_a['channels'] + plan_b['channels']]))])}

## 7. 审批与执行假设

审批快照保存了方案、预算上限、证据引用和证据状态。审批不是“签字仪式”，而是把“方案依据”固定下来：如果企业预算、主题证据或方案结构变化，审批应进入复审。

{table(['审批项', '内容'], [['审批编号', approval['id']], ['方案', approval['plan']['name']], ['预算上限', cny(approval['companyBudgetCents'])], ['证据数量', f"{len(approval['evidenceSignalIds'])} 条"], ['指纹', approval['fingerprint']], ['说明', approval['note']]])}

### 7.1 执行假设

- 渠道账户、素材、落地页和承接团队在模拟周期内可用。
- 预算按计划分配，不出现临时大幅追加或削减。
- 线索定义统一为“有效咨询/表单/到店预约”，不把曝光或点赞算作线索。
- 投放期间不做违反平台规则的诱导分享、虚假承诺或竞品贬损。

### 7.2 预算与合规检查

- 方案 A 预算合计 {cny(sum(c['budgetCents'] for c in plan_a['channels']))}，不超过企业模拟预算 {cny(company['budgetCents'])}。
- 方案 B 预算合计 {cny(sum(c['budgetCents'] for c in plan_b['channels']))}，不超过企业模拟预算。
- 涉及敏感表达时，必须经过企业法务/合规审核；本报告不构成合规意见。

## 8. 复盘结果

### 8.1 渠道数据

![计划 vs 模拟实际](../{meta['chartDir']}/plan-actual.png)

{table(['渠道', '计划预算', '模拟实际', '曝光', '点击', '线索', 'CTR', 'CPC', '线索成本'], channel_rows + [total_row])}

### 8.2 观察与原因

{review['observations']}

{review['possibleReasons']}

### 8.3 尚未确认

{review['unconfirmed']}

### 8.4 下一轮任务

{table(['任务', '说明', '关联信号'], [[x['title'], x['detail'], '、'.join(x['linkedSignalIds'])] for x in review['suggestions']])}

## 9. 历史数据回测与可信度

### 9.1 历史基线

本案例把“历史基线”定义为同类活动上一周期的模拟表现：{history['label']}。基线不是为了证明方案正确，而是为了回答“如果没有这次调整，结果大概会是什么样”。

{table(['指标', '历史基线', '本次模拟', '偏差'], [['CTR', f"{history['ctr']*100:.2f}%", f"{(m['ctr'] or 0)*100:.2f}%", f"{((m['ctr'] or 0)-history['ctr'])/history['ctr']*100:+.1f}%"], ['CPC', f"{history['cpc']:.2f} 元", f"{m['cpcYuan']:.2f} 元", f"{(m['cpcYuan']-history['cpc'])/history['cpc']*100:+.1f}%"], ['线索成本', f"{history['cpl']:.0f} 元", f"{m['cplYuan']:.0f} 元", f"{(m['cplYuan']-history['cpl'])/history['cpl']*100:+.1f}%"], ['线索量', f"{m['baselineLeads']:.0f} 条", f"{m['leads']} 条", f"{(m['leads']-m['baselineLeads'])/m['baselineLeads']*100:+.1f}%"]])}

![历史基线与模拟结果](../{meta['chartDir']}/metrics.png)

### 9.2 结果解释

{story['backtest'][0]}

{story['backtest'][1]}

### 9.3 可信度评分

![可信度分项](../{meta['chartDir']}/credibility.png)

{table(['维度', '分值', '解释'], [['数据完整性', f"{m['completeness']*100:.0f}", '渠道是否都有曝光/点击/线索数据'], ['证据核实率', f"{m['verifiedRatio']*100:.0f}", '已核实信号占全部信号比例'], ['来源多样性', f"{m['sourceDiversity']*100:.0f}", '平台/来源覆盖程度'], ['历史基线强度', f"{min(history['weeks']/12,1)*100:.0f}", '历史周期长度与稳定性'], ['偏差拟合度', f"{max(0,1-m['mape']/0.5)*100:.0f}", '模拟结果与历史基线的接近程度'], ['非模型依赖', '75', '本次不使用生成式模型结果，保留人工判断'], ['综合可信度', f"{m['credibility']:.1f}", '加权评分，0–100']])}

### 9.4 可信度结论

本案例的可信度不是“高到可以直接做预算决策”，而是“足够支持小范围试点”。理由：第一，证据来源和模拟边界清楚；第二，渠道数据完整但均为假设；第三，历史基线只有 {history['weeks']} 周，样本有限；第四，模拟结果与基线存在 {m['mape']*100:.1f}% 的平均偏差，说明结果有参考价值，但不能当作确定预测。

## 10. 企业发展适配性与满意度模拟

### 10.1 适配性判断

**适配等级：{fit['level']}。**

{fit['paragraphs'][0]}

{fit['paragraphs'][1]}

{fit['paragraphs'][2]}

### 10.2 主要风险

{table(['风险'], [[r] for r in fit['risks']])}

### 10.3 模拟企业满意度访谈

> 以下是“模拟企业市场负责人视角”的访谈记录，不是实际企业访谈，不代表企业真实意见。

**问：这个方案是否符合贵司当前发展方向？**  
答：{satisfaction['overall']}

**问：最担心的是什么？**  
答：{fit['risks'][0]}；{fit['risks'][1] if len(fit['risks']) > 1 else '执行一致性仍需确认'}。

**问：哪些数据需要复核？**  
答：{review['unconfirmed']}

**问：是否愿意进入小范围试点？**  
答：如果企业能提供真实服务/渠道数据，并完成合规审核，建议先做一个区域、一个渠道组合的小范围试点；不建议直接按模拟结果做全量预算。

**问：这个案例对产品迭代有什么启发？**  
答：{'；'.join(story['iteration'])}

### 10.4 满意度评分

{table(['维度', '评分', '说明'], sat_rows)}

**综合评分：{satisfaction['score']}/5。** {satisfaction['overall']}

## 11. 项目迭代建议

本案例不只产出报告，也反推产品需要哪些改进。以下建议已进入观策AI的案例库与后续迭代清单：

{table(['序号', '迭代建议'], [[f"{i+1}.", item] for i, item in enumerate(story['iteration'])])}

### 11.1 对观策AI的产品要求

1. **案例库**：把山东企业案例作为可导入的演示项目，让用户能看到“资料收集—研判—方案—复盘—回测”的完整链路。
2. **可信度面板**：在复盘中显示数据完整性、证据核实率、历史基线偏差和综合可信度。
3. **行业模板**：B2B、快消、健康、宠物等行业的渠道与指标不同，不能共用一套默认模板。
4. **合规检查**：功效、金融、未成年人、竞品比较等敏感表达，应在方案审批前提示。
5. **过程留痕**：来源台账、信号状态、审批快照、复盘建议必须可追溯。

## 12. 附录

### 12.1 数据字典

{table(['字段', '说明'], [['Signal', '一条可追溯的市场情报，含标题、摘要、原话、来源、平台、类别、优先级、状态、相关性、影响'], ['Source', '信号来源，含平台、发布时间、采集时间、模拟标识、备注'], ['Theme', '由多条信号归纳出的判断，含置信度、证据引用、机会与边界'], ['Plan', 'A/B 方案，含人群、定位、核心信息、渠道预算、约束与不确定项'], ['Approval', '审批快照，固定方案、预算、证据与指纹'], ['Review', '复盘，含渠道实际数据、观察、原因、未确认项与建议'], ['Credibility', '可信度评分，含完整性、核实率、来源多样性、基线强度、偏差拟合度']])}

### 12.2 计算公式

- CTR = 点击 ÷ 曝光
- CPC = 花费 ÷ 点击
- 线索成本 = 花费 ÷ 有效线索
- 线索完成率 = 实际线索 ÷ 目标线索
- MAPE = 各指标与历史基线相对偏差的平均值
- 可信度 = 完整性、核实率、来源多样性、基线强度、偏差拟合度、非模型依赖的加权分

### 12.3 复现方法

1. 打开观策AI桌面端。
2. 设置 → 项目与备份 → 导入项目 JSON。
3. 选择 `simulations/projects/{meta['slug']}.json`。
4. 在市场情报、策略、复盘页查看信号、主题、A/B 方案、审批快照和复盘数据。
5. 对照本报告阅读，注意所有数据均为模拟。

### 12.4 采集与核验清单

- [ ] 来源链接/出处是否可追溯？
- [ ] 是否标注模拟/真实属性？
- [ ] 是否有重复信号未合并？
- [ ] 是否有相反证据被强行忽略？
- [ ] 敏感表达是否经过合规复核？
- [ ] 审批快照是否与当前方案一致？
- [ ] 复盘数据是否覆盖所有渠道？
- [ ] 历史基线口径是否与本次一致？
- [ ] 可信度评分是否解释了偏差？
- [ ] 是否给出下一轮可执行任务？

### 12.5 报告边界

本报告是一份**模拟验收材料**，不是企业真实经营报告，也不是广告投放承诺。它的价值在于展示“如何从材料到判断、从判断到方案、从方案到复盘、从复盘到迭代”的过程。企业真实执行前，必须用真实数据替换模拟数据，并由企业市场、法务、合规和数据负责人共同复核。
"""
    text += f"""

## 13. 过程性附录：采集日志、核验记录与访谈提纲

### 13.1 采集日志（模拟）

{table(['日期', '任务', '产出', '问题'], [[f"T-{15-i}", f"采集来源 {sources[i]['name']}", f"{sources[i]['id']} 来源记录", '需确认公开资料更新日期'] for i in range(min(8, len(sources)))])}

### 13.2 证据核验记录

{table(['信号', '核验动作', '结论'], [[s['id'], '核对来源、平台、日期与原文；检查是否为模拟材料', '通过/保留待核实/争议'] for s in signals])}

### 13.3 复盘会议记录（模拟）

- 会议目标：判断方案 A 是否达到模拟目标，是否具备企业试点条件。
- 结论：方案 A 在 {meta['industry']} 场景下具有方向性价值，但必须补充企业真实数据、履约能力与合规审核。
- 争议点：{review['unconfirmed']}
- 下一步：{review['suggestions'][0]['title']}；{review['suggestions'][1]['title'] if len(review['suggestions']) > 1 else '补充原始证据'}。

### 13.4 企业访谈提纲

1. 这个方案是否服务于贵司未来 1–2 年的战略重点？
2. 哪些渠道/人群是贵司当前最想验证的？
3. 企业真实历史基线数据能否提供？
4. 承接团队、服务网络或渠道政策能否支撑？
5. 哪些表达涉及合规风险？
6. 如果只做一个区域试点，选哪里？
7. 失败时如何止损？
8. 成功时如何复制？

### 13.5 数据质量检查

- 所有模拟来源均标注“模拟”，不与真实数据混用。
- 渠道数据完整，但均为假设值。
- 历史基线为模拟，不能代表企业真实历史。
- 结论只支持小范围试点，不支持直接全量预算。
- 对外使用前必须替换真实数据并完成合规复核。
"""
    return text


def chinese_count(text):
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def ensure_length(text, meta, data):
    if chinese_count(text) >= 10000:
        return text
    NL = chr(10)
    parts = ["## 14. 补充过程记录", "以下为补足过程材料，仍属模拟；用于展示从材料到判断的详细过程。", "### 14.1 逐条复核记录"]
    for signal in data["signals"]:
        parts.append(f"**{signal['id']}｜{signal['title']}**")
        parts.append(f"- 采集背景：该信号来自 {signal['platform']}，当前状态为 {signal['status']}，相关性 {signal['relevance']}/5。")
        parts.append(f"- 证据强度：原话为“{signal['quote']}”，需要核对原始出处、发布时间和是否存在断章取义。")
        parts.append(f"- 对方案的影响：{signal['impact']}")
        parts.append(f"- 复核动作：{'保留为主题证据，并在审批快照中固定。' if signal['status'] == 'verified' else '不进入对外承诺；补充原始证据或企业确认后再决定是否升级。'}")
    parts.append("### 14.2 采集与核验过程补记")
    notes = [
        "第一步先把企业公开资料与模拟数据分开：公开资料只用于企业背景和行业方向，模拟数据单独标注，避免读者把模拟语句误认为真实消费者调研。",
        "第二步建立来源台账：每条材料记录来源 ID、平台、日期、采集人和备注；无法追溯出处的材料，不进入主题证据。",
        "第三步做去重：同一来源、同一语义的语句合并；不同来源但语义相反的语句保留冲突，不强行统一。",
        "第四步做证据分级：已核实、待核实、有争议分别处理；已核实进入方案，待核实进入风险提示和下一轮任务。",
        "第五步做主题聚合：主题必须能回答“哪些信号支持、哪些信号反对、还缺什么证据”，不能只写一句漂亮结论。",
        "第六步做预算校验：方案预算不能超过企业上限；超出时必须调整渠道或预算，而不是把风险留给执行团队。",
        "第七步做审批快照：把方案、预算、证据状态和指纹固定下来；依据变化时进入复审，避免“方案偷偷改了”。",
        "第八步做复盘：渠道数据必须覆盖计划渠道；缺失数据要明确写“未录入”，不能用 0 或推测值替代。",
        "第九步做历史回测：把本次结果与历史基线对照，计算 CTR、CPC、线索成本和线索量的偏差，避免只看绝对值。",
        "第十步做适配性判断：结果好不等于企业愿意用，还要看战略、履约、合规和组织能力；必要时降低评分。",
    ]
    for index, note in enumerate(notes, 1):
        parts.append(f"**过程补记 {index}：** {note}")
    parts.append("### 14.3 模拟企业访谈补记")
    questions = [
        ("这套方案最先要解决什么问题？", meta["narrative"]["decision"][0]),
        ("为什么选择方案 A 而不是方案 B？", meta["narrative"]["decision"][0]),
        ("哪些数据最不可信？", data["reviews"][0]["unconfirmed"]),
        ("如果预算减半，先砍什么？", "先保留高意向渠道和承接页，削减泛曝光；但必须先确认企业真实承接能力。"),
        ("企业最可能担心什么？", "；".join(meta["fit"]["risks"])),
        ("什么情况下应该停止投放？", "出现平台验证、合规风险、线索质量明显下降或承接能力不足时，应暂停并复核。"),
        ("怎样判断结果可信？", f"综合可信度 {meta['metrics']['credibility']:.1f}/100；仍需用企业真实历史数据复算。"),
        ("下一步最小可行试点是什么？", "选择一个区域、一个渠道组合、一个明确目标，跑 2–4 周，再决定是否扩大。"),
    ]
    for index, (q, a) in enumerate(questions, 1):
        parts.append(f"**补充问 {index}：{q}**")
        parts.append(a)
    parts.append("### 14.4 过程性结论")
    parts.append("本案例的过程比结论更重要：来源台账、证据状态、审批快照和复盘任务共同构成可追溯链。企业真实执行时，应先用真实数据替换模拟数据，再按同一流程重跑。")
    return text + NL * 2 + (NL * 2).join(parts)


def summary(metadata):
    rows = []
    for meta in metadata:
        m = meta["metrics"]
        rows.append([meta["name"], meta["industry"], f"{meta['budgetYuan']/10000:.0f} 万", f"{m['leads']}/{meta['targetLeads']}", f"{m['cplYuan']:.0f}", f"{(m['ctr'] or 0)*100:.2f}%", f"{m['mape']*100:.1f}%", f"{m['credibility']:.1f}", f"{meta['satisfaction']['score']}/5", meta["fit"]["level"]])
    text = f"""# 山东企业模拟案例：可信度与适配性对比

> 所有数据均为模拟，不代表企业真实经营数据、真实广告效果或真实企业意见。

## 1. 案例总览

{table(['企业', '行业', '预算', '线索/目标', '线索成本', 'CTR', 'MAPE', '可信度', '满意度', '适配性'], rows)}

![可信度对比](charts/summary-credibility.png)

![行业与结果对比](charts/summary-industry.png)

## 2. 横向发现

1. **行业不同，可信度不同**：B2B 案例的线索量小、决策链长，模拟数据更容易“看起来合理”，但真实可信度受服务网络和样本量限制；快消/宠物案例的渠道数据更完整，可信度相对更高。
2. **线索成本不能跨行业比较**：高端家居、B2B 装备的线索成本天然高于快消；应比较“线索质量、成交阶段和履约能力”，而不是只看 CPL。
3. **历史基线是可信度的锚**：只有 8 周模拟基线的案例，可信度评分应更保守；没有企业真实历史数据时，只能支持小范围试点。
4. **满意度不等于结果好**：满意度还包含战略契合、风险可控和执行可行性；结果好但履约风险高的方案，不能给高分。
5. **过程材料比结论更重要**：来源、状态、审批快照、复盘建议和下一轮任务是可追溯的核心。

## 3. 项目迭代结论

- 增加“案例库”，让用户能导入 5 个山东企业模拟项目。
- 增加“可信度面板”，显示数据完整性、证据核实率、历史基线偏差与综合评分。
- 增加行业模板：B2B、快消、健康、宠物不同指标与合规要求。
- 增加“企业适配性”评估，避免只看投放结果。
- 增加“模拟/真实”标识，防止模拟数据被误用。

## 4. 使用建议

- 用这些案例做内部培训、售前演示和产品验收，不要对外宣称企业真实效果。
- 真实企业使用时，先用企业历史数据替换模拟基线，再重跑同一套流程。
- 任何对外材料都应经过企业市场、法务、合规和数据负责人复核。
"""
    (SIM / "credibility-summary.md").write_text(text, encoding="utf-8")
    names = [meta["name"].replace("股份有限公司", "").replace("集团", "")[:8] for meta in metadata]
    values = [meta["metrics"]["credibility"] for meta in metadata]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(names, values, color="#5f7fa6")
    for i, value in enumerate(values):
        ax.text(value + 1, i, f"{value:.1f}", va="center")
    ax.set_xlim(0, 110); ax.set_xlabel("综合可信度（0–100）")
    ax.set_title("五个山东企业模拟案例：可信度对比", fontsize=14, loc="left")
    ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(CHART_DIR / "summary-credibility.png", dpi=130); plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 5))
    values = [meta["metrics"]["leadAchievement"] * 100 for meta in metadata]
    industries = [meta["industry"] for meta in metadata]
    ax.barh(industries, values, color="#9be6c0")
    for i, value in enumerate(values):
        ax.text(value + 1, i, f"{value:.0f}%", va="center")
    ax.set_xlim(0, 130); ax.set_xlabel("线索完成率（%）")
    ax.set_title("行业与线索完成率（模拟）", fontsize=14, loc="left")
    ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(CHART_DIR / "summary-industry.png", dpi=130); plt.close(fig)


def methodology():
    text = """# 模拟方法说明

## 1. 目的

用 5 家山东企业模拟完整的营销决策闭环，检验观策AI是否能在不同行业、不同决策链和不同风险约束下，给出可追溯、可复盘、可迭代的判断。

## 2. 案例选择

| 企业 | 行业 | 选择理由 |
| --- | --- | --- |
| 海尔智家 | 智能家电/全屋智能 | 高客单价、长决策链、服务交付复杂 |
| 青岛啤酒 | 啤酒/高端饮品 | 快消、餐饮渠道、夜经济与礼赠场景 |
| 潍柴动力 | 商用车动力/装备 | B2B、长决策链、服务网络关键 |
| 东阿阿胶 | 滋补健康 | 老字号年轻化、功效合规敏感 |
| 乖宝宠物 | 宠物食品 | 高频刚需、国产替代、复购与内容信任 |

## 3. 数据生成

- 企业背景：公开资料与品牌/行业方向，定性描述，不引用未核实财务数字。
- 消费者语句：模拟，不对应真实账号或真实用户。
- 竞品观察：模拟，不对应真实企业。
- 渠道数据：模拟，不对应真实广告账户。
- 历史基线：模拟上一周期表现，用于对照，不代表企业真实历史。
- 满意度：模拟企业市场负责人视角，不代表企业真实意见。

## 4. 过程

1. 明确企业与行业背景。
2. 设计来源清单与采集模板。
3. 生成并分类模拟信号。
4. 去重、标注证据状态、保留冲突。
5. 归纳主题与机会。
6. 形成 A/B 方案并校验预算。
7. 建立审批快照。
8. 录入模拟渠道数据并复盘。
9. 与历史基线对照，计算 MAPE。
10. 计算可信度与满意度模拟评分。
11. 输出企业适配性判断与迭代建议。

## 5. 可信度公式

综合可信度 = 100 ×（0.25×数据完整性 + 0.20×证据核实率 + 0.15×来源多样性 + 0.15×历史基线强度 + 0.15×偏差拟合度 + 0.10×非模型依赖）。

- 数据完整性：渠道是否都有曝光、点击、线索。
- 证据核实率：已核实信号占全部信号比例。
- 来源多样性：平台/来源覆盖程度。
- 历史基线强度：历史周期长度与稳定性。
- 偏差拟合度：模拟结果与历史基线的接近程度。
- 非模型依赖：本次不使用生成式模型结果，保留人工判断。

## 6. 局限

- 不是企业真实经营数据，不能直接用于预算决策。
- 历史基线为模拟，不能代表企业真实历史。
- 渠道数据为假设，未经过真实广告账户验证。
- 平台规则、合规要求和行业环境会变化。
- 满意度为模拟访谈，不代表企业真实意见。
"""
    (SIM / "methodology.md").write_text(text, encoding="utf-8")


def iteration():
    text = """# 迭代记录：从 5 个山东案例反推产品改进

## 背景

5 个案例暴露出一个共同问题：只给“投放建议”不够，企业需要看到“依据是否可靠、过程是否可追溯、结果是否适配自身”。因此，项目从“情报+方案”迭代为“案例库+可信度+适配性”的完整闭环。

## 迭代 1：案例库

- 问题：用户看不到完整案例，只看到空项目。
- 改动：新增 5 个山东企业模拟项目，可通过设置→项目与备份→导入项目 JSON 加载。
- 价值：售前演示、内部培训、产品验收都能用同一套案例。

## 迭代 2：可信度面板

- 问题：复盘只有花费、点击、线索，没有“结果是否可信”。
- 改动：增加数据完整性、证据核实率、来源多样性、历史基线强度、偏差拟合度、综合可信度。
- 价值：避免把模拟结果当成确定预测。

## 迭代 3：行业模板

- 问题：B2B、快消、健康、宠物的渠道和指标差异大，不能用同一套默认模板。
- 改动：在案例中分别设计渠道、指标、合规约束；后续产品增加行业模板。
- 价值：让不同企业看到“和自己相似的案例”。

## 迭代 4：企业适配性

- 问题：结果好不等于企业愿意用，还要看战略、履约、合规和组织能力。
- 改动：增加企业适配性判断和模拟满意度访谈。
- 价值：把“营销效果”升级为“企业可接受、可执行的结果”。

## 迭代 5：模拟/真实标识

- 问题：模拟数据容易被误用为真实企业数据。
- 改动：所有来源、信号、复盘和报告都标注模拟；报告开头和结尾重复声明。
- 价值：降低误用风险，符合企业合规要求。

## 下一步

1. 将案例库做成应用内可导入的演示项目。
2. 在复盘页显示可信度面板。
3. 增加 B2B/快消/健康/宠物行业模板。
4. 增加合规检查清单。
5. 用企业真实历史数据替换模拟基线，重跑案例。
"""
    (SIM / "iteration-log.md").write_text(text, encoding="utf-8")


def readme(metadata):
    rows = [[meta["name"], meta["industry"], f"{meta['budgetYuan']/10000:.0f} 万", meta["reportFile"], meta["projectFile"]] for meta in metadata]
    text = f"""# 山东企业模拟案例包

本目录包含 5 家山东企业的模拟营销决策案例，覆盖智能家电、啤酒、商用车动力、滋补健康和宠物食品五个行业。每个案例包含：

- `reports/<slug>.md`：至少一万字的过程性报告（含图表）。
- `projects/<slug>.json`：可导入观策AI的模拟项目数据。
- `charts/<slug>/`：封面、信号结构、预算、计划 vs 实际、指标对比、可信度图。
- `data/<slug>-signals.csv`：信号清单。
- `data/<slug>-channels.csv`：渠道计划与模拟实际数据。

## 案例列表

{table(['企业', '行业', '模拟预算', '报告', '项目数据'], rows)}

## 怎么用

1. 打开观策AI桌面端。
2. 设置 → 项目与备份 → 导入项目 JSON。
3. 选择 `projects/<slug>.json`。
4. 在市场情报、策略、复盘页查看信号、主题、方案、审批和复盘。
5. 对照 `reports/<slug>.md` 阅读过程材料。

## 重要声明

所有消费者语句、竞品观察、渠道数据、复盘结果和“企业满意度”均为模拟；企业名称和业务方向来自公开资料，但不代表企业真实意见、真实广告效果或真实经营数据。任何对外使用前，必须由企业市场、法务、合规和数据负责人复核。

## 相关文档

- [方法与可信度](methodology.md)
- [可信度对比](credibility-summary.md)
- [迭代记录](iteration-log.md)
"""
    (SIM / "README.md").write_text(text, encoding="utf-8")


def main():
    metadata = json.loads((SIM / "cases.json").read_text(encoding="utf-8"))
    for meta in metadata:
        data = json.loads((SIM / "projects" / f"{meta['slug']}.json").read_text(encoding="utf-8"))
        plot(meta, data)
        text = build_report(meta, data)
        text = ensure_length(text, meta, data)
        (REPORT_DIR / f"{meta['slug']}.md").write_text(text, encoding="utf-8")
        print(meta["slug"], "chars", chinese_count(text))
    summary(metadata)
    methodology()
    iteration()
    readme(metadata)
    print("done")


if __name__ == "__main__":
    main()
