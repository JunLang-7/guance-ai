from __future__ import annotations

import csv
import json
import math
import os
import re
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "simulations"
CHART_DIR = SIM / "charts"
REPORT_DIR = SIM / "reports"
CHART_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

FONT = r"C:\Windows\Fonts\msyh.ttc"
if os.path.exists(FONT):
    font_manager.fontManager.addfont(FONT)
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
else:
    plt.rcParams["font.sans-serif"] = ["SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.facecolor"] = "#f7f9fb"
plt.rcParams["axes.facecolor"] = "#ffffff"
plt.rcParams["axes.edgecolor"] = "#d7dfe8"
plt.rcParams["text.color"] = "#172033"
plt.rcParams["axes.labelcolor"] = "#172033"
plt.rcParams["xtick.color"] = "#5f6d7e"
plt.rcParams["ytick.color"] = "#5f6d7e"
PALETTE = ["#243e63", "#5f7fa6", "#9be6c0", "#c58a5a", "#b7791f", "#8f9db0"]


def cny(cents):
    return "—" if cents is None else f"{cents / 100:,.0f} 元"


def num(value, digits=0):
    return "—" if value is None else f"{value:,.{digits}f}"


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("|", "/") for cell in row) + " |")
    return "\n".join(out)


def plot(meta, data):
    folder = CHART_DIR / meta["slug"]
    folder.mkdir(parents=True, exist_ok=True)
    metrics = meta["metrics"]
    plans = data["plans"]
    signals = data["signals"]
    # cover
    fig, ax = plt.subplots(figsize=(12, 6.4))
    ax.axis("off")
    fig.patch.set_facecolor("#f7f9fb")
    ax.text(0.06, 0.78, "观策AI · 山东企业模拟案例", fontsize=14, color="#5f6d7e")
    ax.text(0.06, 0.60, meta["name"], fontsize=27, color="#172033", weight="bold")
    ax.text(0.06, 0.49, meta["industry"] + "｜" + meta["region"], fontsize=14, color="#243e63")
    ax.text(0.06, 0.37, f"模拟周期 {meta['campaignStart']} — {meta['campaignEnd']}｜模拟预算 {meta['budgetYuan']/10000:.0f} 万元", fontsize=12, color="#5f6d7e")
    ax.text(0.06, 0.22, "公开资料 + 模拟消费者语句 + 模拟投放数据", fontsize=11, color="#b7791f")
    ax.text(0.06, 0.10, "本报告不代表真实企业意见、真实广告报表或真实消费者调研。", fontsize=10, color="#8f9db0")
    fig.savefig(folder / "cover.png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    # signals
    cats = ["consumer", "competitor", "industry"]
    labels = ["消费者", "竞品", "行业"]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    bottoms = [0] * 3
    for priority, color in [("high", "#243e63"), ("medium", "#5f7fa6"), ("low", "#9be6c0")]:
        values = [sum(1 for s in signals if s["category"] == cat and s["priority"] == priority) for cat in cats]
        ax.bar(labels, values, bottom=bottoms, label={"high": "高优先级", "medium": "中优先级", "low": "低优先级"}[priority], color=color)
        bottoms = [bottoms[i] + values[i] for i in range(3)]
    ax.set_title("情报结构：类别与优先级", fontsize=14, loc="left")
    ax.set_ylabel("条数")
    ax.legend(frameon=False, ncol=3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(folder / "signals.png", dpi=130)
    plt.close(fig)
    # budget
    channels = list(dict.fromkeys([c["channel"] for plan in plans for c in plan["channels"]]))
    fig, ax = plt.subplots(figsize=(10, 5.2))
    width = 0.36
    for index, plan in enumerate(plans):
        lookup = {c["channel"]: c["budgetCents"] / 10000 for c in plan["channels"]}
        ax.barh([c + ("  " if index else "") for c in channels], [lookup.get(c, 0) for c in channels], height=width, label=f"方案 {plan['code']}", color=PALETTE[index])
    ax.set_title("A/B 方案预算分配（万元）", fontsize=14, loc="left")
    ax.set_xlabel("万元")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(folder / "budget.png", dpi=130)
    plt.close(fig)
    # plan vs actual
    approved = plans[0]
    planned = {c["channel"]: c["budgetCents"] / 10000 for c in approved["channels"]}
    actual = {c["channel"]: (c["actualSpendCents"] or 0) / 10000 for c in data["reviews"][0]["channels"]}
    labels = list(planned.keys())
    fig, ax = plt.subplots(figsize=(10, 5.2))
    x = range(len(labels))
    ax.bar([i - 0.18 for i in x], [planned[l] for l in labels], width=0.34, label="计划", color="#9be6c0")
    ax.bar([i + 0.18 for i in x], [actual.get(l, 0) for l in labels], width=0.34, label="模拟实际", color="#243e63")
    ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("万元")
    ax.set_title("计划 vs 模拟实际花费", fontsize=14, loc="left")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(folder / "plan-actual.png", dpi=130); plt.close(fig)
    # metrics
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.2))
    rows = [
        ("CTR", metrics["baselineCtr"] * 100, (metrics["ctr"] or 0) * 100, "%", "{:.2f}"),
        ("CPC", metrics["baselineCpc"], metrics["cpcYuan"] or 0, "元", "{:.2f}"),
        ("线索成本", metrics["baselineCpl"], metrics["cplYuan"] or 0, "元", "{:.0f}"),
        ("线索量", metrics["baselineLeads"], metrics["leads"], "条", "{:.0f}"),
    ]
    for ax, (title, base, actual_value, unit, fmt) in zip(axes.flat, rows):
        ax.bar(["历史基线", "模拟实际"], [base, actual_value], color=["#8f9db0", "#243e63"], width=0.55)
        ax.set_title(title, fontsize=12, loc="left"); ax.set_ylabel(unit)
        for i, value in enumerate([base, actual_value]):
            ax.text(i, value, fmt.format(value), ha="center", va="bottom", fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("历史基线与模拟结果对比", fontsize=15, x=0.02, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.95]); fig.savefig(folder / "metrics.png", dpi=130); plt.close(fig)
    # credibility
    dims = [
        ("数据完整性", metrics["completeness"]), ("证据核实率", metrics["verifiedRatio"]),
        ("来源多样性", metrics["sourceDiversity"]), ("历史基线强度", min(meta["history"]["weeks"] / 12, 1)),
        ("偏差拟合度", max(0, 1 - metrics["mape"] / 0.5)), ("非模型依赖", 0.75),
    ]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    names = [n for n, _ in dims]; values = [v * 100 for _, v in dims]
    ax.barh(names, values, color="#5f7fa6")
    for i, value in enumerate(values):
        ax.text(value + 1, i, f"{value:.0f}", va="center", fontsize=9)
    ax.set_xlim(0, 110); ax.set_xlabel("评分（0–100）")
    ax.set_title(f"可信度分项｜综合 {metrics['credibility']:.1f}/100", fontsize=14, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(folder / "credibility.png", dpi=130); plt.close(fig)


