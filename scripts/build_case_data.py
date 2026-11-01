from __future__ import annotations

import csv
import json
import math
import sys
from collections import OrderedDict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from simulation_cases import CASES  # noqa: E402

SIM = ROOT / "simulations"
for folder in (SIM / "projects", SIM / "data"):
    folder.mkdir(parents=True, exist_ok=True)


def iso_date(value: str, days: int = 0, hour: int = 9) -> str:
    day = date.fromisoformat(value) + timedelta(days=days)
    return f"{day.isoformat()}T{hour:02d}:00:00+08:00"


def allocate(channels, budget_cents: int):
    rows = [{"channel": c, "role": role, "budgetCents": round(budget_cents * share / 100 / 100) * 100} for c, share, role in channels]
    remainder = budget_cents - sum(row["budgetCents"] for row in rows)
    for row in sorted(rows, key=lambda item: item["budgetCents"], reverse=True):
        if remainder <= 0:
            break
        step = min(remainder, 100)
        row["budgetCents"] += step
        remainder -= step
    return rows


def fnv1a(text: str) -> str:
    value = 0x811C9DC5
    for char in text:
        value ^= ord(char)
        value = (value * 0x01000193) & 0xFFFFFFFF
    return f"{value:08x}"


def snapshot_evidence(signals, evidence_ids):
    return [
        OrderedDict(
            id=signal["id"],
            priority=signal["priority"],
            status=signal["status"],
            relevance=signal["relevance"],
            content=json.dumps([signal["title"], signal["summary"], signal["quote"], signal["sourceId"], signal["impact"]], ensure_ascii=False, separators=(",", ":")),
        )
        for signal in sorted(signals, key=lambda item: item["id"])
        if signal["id"] in evidence_ids
    ]


def fingerprint(plan, budget_cents, evidence):
    plan_canonical = OrderedDict()
    for key in ("id", "code", "name", "positioning", "audience", "platforms", "formats", "coreMessage", "timing", "rationale", "constraints", "uncertainties"):
        plan_canonical[key] = plan[key]
    plan_canonical["channels"] = [[channel["channel"], channel["budgetCents"]] for channel in plan["channels"]]
    plan_canonical["themes"] = sorted(plan["evidenceThemeIds"])
    canonical = OrderedDict(budget=budget_cents, plan=plan_canonical, evidence=evidence)
    return f"fp_{fnv1a(json.dumps(canonical, ensure_ascii=False, separators=(',', ':')))}"


def build(seed):
    budget_cents = seed["budget_yuan"] * 100
    start, end = seed["start"], seed["end"]
    duration = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
    source_map = {row[0]: {"platform": row[2]} for row in seed["sources"]}
    sources = [
        {
            "id": row[0], "name": row[1], "platform": row[2], "kind": row[3],
            "publishedAt": (date.fromisoformat(start) - timedelta(days=15 - index)).isoformat(),
            "note": row[4], "simulated": True, "collectedAt": iso_date(start, -14 + index, 10), "origin": "demo",
        }
        for index, row in enumerate(seed["sources"])
    ]
    sid = lambda n: f"S-{n:02d}"
    signals = []
    for index, row in enumerate(seed["signals"]):
        title, summary, quote, source_key, category, priority, status, tags, impact = row
        signal = {
            "id": sid(index + 1), "title": title, "summary": summary, "quote": quote,
            "sourceId": source_key, "platform": source_map[source_key]["platform"],
            "category": category, "priority": priority, "status": status,
            "relevance": 5 if priority == "high" else 4 if priority == "medium" else 3,
            "impact": impact, "tags": [tag for tag in tags.split("|") if tag],
            "capturedAt": iso_date(start, -8 + index // 3, 9 + index % 6),
            "note": "人工核对：模拟材料，仅用于案例演示；执行前需复核真实来源。" if status == "verified" else "待核实：模拟材料，未获得原始证据；不得直接用于对外发布。",
        }
        if status == "verified":
            signal["verifiedAt"] = iso_date(start, -6, 16)
        signals.append(signal)
    themes = []
    for index, row in enumerate(seed["themes"]):
        title, summary, direction, opportunity, caveat, confidence, claim_type, numbers = row
        themes.append({
            "id": f"TH-{index + 1:02d}", "rank": index + 1, "title": title, "summary": summary,
            "mentionCount": len(numbers), "direction": direction, "confidence": confidence,
            "claimType": claim_type, "evidenceSignalIds": [sid(n) for n in numbers],
            "opportunity": opportunity, "caveat": caveat,
        })
    opps = []
    for index, row in enumerate(seed["opps"]):
        title, fact, opportunity, verify, tone, numbers = row
        opps.append({"id": f"OP-{index + 1:02d}", "title": title, "fact": fact, "opportunity": opportunity, "verify": verify, "evidenceSignalIds": [sid(n) for n in numbers], "tone": tone})
    def make_plan(config, code):
        channels = allocate(config["channels"], budget_cents)
        return {
            "id": f"PLAN-{code}", "code": code, "name": config["name"], "shortName": config["short"],
            "positioning": config["positioning"], "audience": config["audience"],
            "platforms": list(dict.fromkeys(channel["channel"] for channel in channels)),
            "formats": ["内容种草", "搜索承接", "私域/渠道承接"], "timing": config["timing"],
            "coreMessage": config["message"], "rationale": config["rationale"],
            "constraints": config["constraints"], "uncertainties": config["uncertainties"],
            "channels": channels, "evidenceThemeIds": [f"TH-{n:02d}" for n in config["themes"]],
            "updatedAt": iso_date(start, -2, 11),
        }
    plans = [make_plan(seed["plan_a"], "A"), make_plan(seed["plan_b"], "B")]
    approved = plans[0]
    evidence_ids = sorted({sid for theme in themes if theme["id"] in approved["evidenceThemeIds"] for sid in theme["evidenceSignalIds"]})
    evidence = snapshot_evidence(signals, evidence_ids)
    approval = {
        "id": "APR-01", "planId": approved["id"], "planCode": approved["code"],
        "approvedAt": iso_date(start, -1, 17),
        "reason": "模拟审批：方案预算、证据引用和风险约束已核对；所有效果均为模拟假设，执行前需企业真实复核。",
        "plan": json.loads(json.dumps(approved, ensure_ascii=False)), "companyBudgetCents": budget_cents,
        "fingerprint": fingerprint(approved, budget_cents, evidence), "evidenceSignalIds": evidence_ids,
        "evidence": evidence, "note": "审批快照保存方案、预算上限与关键证据状态；任一项变化需重新确认。",
    }
    review_channels = []
    for channel in approved["channels"]:
        actual = seed["review"]["channels"].get(channel["channel"])
        spend, impressions, clicks, leads = actual if actual else (channel["budgetCents"] // 100, None, None, None)
        review_channels.append({"channel": channel["channel"], "actualSpendCents": spend * 100, "impressions": impressions, "clicks": clicks, "leads": leads})
    review = {
        "id": "REV-01", "approvalId": approval["id"], "planId": approved["id"], "dataKind": "simulated",
        "note": "模拟复盘：渠道数据为假设值，不对应真实广告账户或真实订单。",
        "observations": seed["review"]["observations"], "possibleReasons": seed["review"]["reasons"],
        "unconfirmed": seed["review"]["unconfirmed"], "updatedAt": iso_date(end, 2, 15), "channels": review_channels,
        "suggestions": [{"id": f"SUG-{i + 1:02d}", "title": title, "detail": detail, "linkedSignalIds": [sid(n) for n in numbers]} for i, (title, detail, numbers) in enumerate(seed["review"]["suggestions"])],
    }
    feedback = [{"id": f"FT-{i + 1:02d}", "title": item["title"], "detail": item["detail"], "trigger": "来自模拟复盘 REV-01", "createdAt": iso_date(end, 3 + i, 9), "status": "open", "linkedSignalIds": item["linkedSignalIds"], "source": "review"} for i, item in enumerate(review["suggestions"])]
    data = {
        "schemaVersion": 4, "mode": "demo",
        "company": {"id": f"C-{seed['slug'].upper()}", "name": seed["name"], "brand": seed["brand"], "industry": seed["industry"], "region": seed["region"], "stage": seed["stage"], "product": seed["product"], "productSpec": seed["product_spec"], "goal": seed["goal"], "budgetCents": budget_cents, "campaignStart": start, "campaignEnd": end, "updatedAt": iso_date(start, -10, 10)},
        "sources": sources, "signals": signals, "themes": themes, "opportunities": opps, "plans": plans,
        "approvals": [approval], "reviews": [review], "feedbackTasks": feedback,
        "decision": {"status": "approved", "planId": approved["id"], "updatedAt": iso_date(start, -1, 18)},
        "activePlanId": approved["id"],
    }
    metrics = compute_metrics(data, seed, duration)
    meta = {
        "slug": seed["slug"], "name": seed["name"], "brand": seed["brand"], "industry": seed["industry"], "region": seed["region"],
        "product": seed["product"], "goal": seed["goal"], "budgetYuan": seed["budget_yuan"], "campaignStart": start, "campaignEnd": end,
        "targetLeads": seed["target_leads"], "history": seed["history"], "satisfaction": seed["satisfaction"], "fit": seed["fit"],
        "narrative": seed["narrative"], "projectFile": f"projects/{seed['slug']}.json", "reportFile": f"reports/{seed['slug']}.md",
        "chartDir": f"charts/{seed['slug']}", "counts": {"sources": len(sources), "signals": len(signals), "themes": len(themes), "plans": len(plans)},
        "metrics": metrics,
    }
    return data, meta


def compute_metrics(data, seed, duration):
    plan = data["plans"][0]
    channels = data["reviews"][0]["channels"]
    planned = sum(c["budgetCents"] for c in plan["channels"])
    spend = sum(c["actualSpendCents"] or 0 for c in channels)
    impressions = sum(c["impressions"] or 0 for c in channels)
    clicks = sum(c["clicks"] or 0 for c in channels)
    leads = sum(c["leads"] or 0 for c in channels)
    ctr = clicks / impressions if impressions else None
    cpc = (spend / 100) / clicks if clicks else None
    cpl = (spend / 100) / leads if leads else None
    baseline = seed["history"]
    baseline_leads = baseline["weekly_leads"] * duration / 7
    deviations = [abs((ctr or 0) - baseline["ctr"]) / baseline["ctr"], abs((cpc or 0) - baseline["cpc"]) / baseline["cpc"], abs((cpl or 0) - baseline["cpl"]) / baseline["cpl"], abs(leads - baseline_leads) / baseline_leads]
    mape = sum(deviations) / len(deviations)
    verified_ratio = sum(1 for s in data["signals"] if s["status"] == "verified") / len(data["signals"])
    platforms = len({s["platform"] for s in data["signals"]})
    source_diversity = min(platforms / 8, 1)
    completeness = 1.0 if all(c["impressions"] is not None and c["clicks"] is not None and c["leads"] is not None for c in channels) else 0.5
    baseline_strength = min(baseline["weeks"] / 12, 1)
    deviation_fit = max(0, 1 - mape / 0.5)
    credibility = 100 * (0.25 * completeness + 0.20 * verified_ratio + 0.15 * source_diversity + 0.15 * baseline_strength + 0.15 * deviation_fit + 0.10 * 0.75)
    return {
        "plannedCents": planned, "actualSpendCents": spend, "impressions": impressions, "clicks": clicks, "leads": leads,
        "ctr": ctr, "cpcYuan": cpc, "cplYuan": cpl, "targetLeads": seed["target_leads"],
        "leadAchievement": leads / seed["target_leads"] if seed["target_leads"] else None,
        "budgetUtilization": spend / (seed["budget_yuan"] * 100) if seed["budget_yuan"] else None,
        "baselineLeads": baseline_leads, "baselineCtr": baseline["ctr"], "baselineCpc": baseline["cpc"], "baselineCpl": baseline["cpl"],
        "mape": mape, "verifiedRatio": verified_ratio, "sourceDiversity": source_diversity, "completeness": completeness,
        "credibility": round(credibility, 1),
    }


def main():
    metadata = []
    for seed in CASES:
        data, meta = build(seed)
        (SIM / "projects" / f"{seed['slug']}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        with (SIM / "data" / f"{seed['slug']}-signals.csv").open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(["ID", "标题", "平台", "类别", "优先级", "状态", "相关性", "来源", "影响"])
            for signal in data["signals"]:
                writer.writerow([signal["id"], signal["title"], signal["platform"], signal["category"], signal["priority"], signal["status"], signal["relevance"], signal["sourceId"], signal["impact"]])
        with (SIM / "data" / f"{seed['slug']}-channels.csv").open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(["渠道", "计划预算(分)", "模拟实际花费(分)", "曝光", "点击", "线索"])
            actual = {c["channel"]: c for c in data["reviews"][0]["channels"]}
            for channel in data["plans"][0]["channels"]:
                row = actual.get(channel["channel"])
                writer.writerow([channel["channel"], channel["budgetCents"], row["actualSpendCents"] if row else "", row["impressions"] if row else "", row["clicks"] if row else "", row["leads"] if row else ""])
        metadata.append(meta)
        print(seed["slug"], meta["metrics"]["credibility"])
    (SIM / "cases.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
