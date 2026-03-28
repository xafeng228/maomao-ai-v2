#!/usr/bin/env python3
"""
core/reporter.py
报告生成器
输入：analysis_result 字典
输出：格式化字符串（终端）/ Markdown 文件
所有报告强制附加免责声明
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from config import DISCLAIMER, RESULTS_DIR


def _bar(score: float, max_score: float, width: int = 20) -> str:
    filled = int(score / max_score * width)
    return "█" * filled + "░" * (width - filled)


class Reporter:

    # ── 终端报告 ──────────────────────────────────────────────
    @staticmethod
    def print_report(result: dict):
        snap = result.get("snapshot", {})
        score = result.get("score", {})
        fin = result.get("financial", {})
        info = result.get("info", {})

        symbol = snap.get("symbol", "?")
        name = snap.get("name", "")
        price = snap.get("price", 0)
        chg = snap.get("change_pct", 0)
        chg_s = f"+{chg:.2f}%" if chg >= 0 else f"{chg:.2f}%"

        print()
        print("━" * 60)
        print(f" 📊 {name}（{symbol}） {price:.2f} {chg_s}")
        print(f" 行业：{info.get('industry', '—')} 上市：{info.get('listing_date', '—')}")
        print("━" * 60)

        # 综合评分
        total = score.get("total_score", 0)
        rating = score.get("rating", "—")
        action = score.get("action", "—")
        print(f"\n 综合评分 {total:.1f} / 100 [{rating}] → {action}")
        print(f" {_bar(total, 100)} {total:.0f}%")

        # 三维拆分
        bd = score.get("breakdown", {})
        print()
        for dim, label in [("valuation", "估值"), ("technical", "技术"), ("fundamental", "基本面")]:
            d = bd.get(dim, {})
            s = d.get("score", 0)
            m = d.get("max", 0)
            print(f" {label:6} {_bar(s, m, 15)} {s:.0f}/{m}")
            for r in d.get("reasons", []):
                print(f" · {r}")

        # 技术指标
        ind = score.get("indicators", {})
        trend = score.get("trend", "—")
        sr = score.get("support_resistance", {})
        if ind:
            print(f"\n 趋势：{trend}")
            print(f" RSI={ind.get('rsi', '—')} MACD柱={ind.get('macd_hist', '—')}")
            print(f" MA5={ind.get('ma5', '—')} MA20={ind.get('ma20', '—')} MA60={ind.get('ma60', '—')}")
            if sr:
                print(f" 支撑：{sr.get('support', [])} 阻力：{sr.get('resistance', [])}")

        # 财务摘要
        if fin.get("status") == "live":
            print(f"\n ROE={fin.get('roe', '—')}% 净利增速={fin.get('net_profit_growth', '—')}%")
            print(f" 毛利率={fin.get('gross_margin', '—')}% 资负率={fin.get('debt_ratio', '—')}%")

        # 快照详情
        print(f"\n PE(TTM)={snap.get('pe_ttm', '—')} PB={snap.get('pb', '—')}")
        print(f" 市值={snap.get('market_cap', 0) / 1e8:.1f}亿 换手率={snap.get('turnover_rate', '—')}%")
        print(f" 成交额={snap.get('amount', 0) / 1e8:.2f}亿")

        print()
        print(DISCLAIMER)

    # ── Markdown 文件 ─────────────────────────────────────────
    @staticmethod
    def save_markdown(result: dict) -> Path:
        snap = result.get("snapshot", {})
        score = result.get("score", {})
        fin = result.get("financial", {})
        info = result.get("info", {})
        symbol = snap.get("symbol", "unknown")
        name = snap.get("name", "")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        bd = score.get("breakdown", {})

        lines = [
            f"# {name}（{symbol}）分析报告",
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 综合评分",
            f"| 维度 | 得分 | 满分 |",
            f"|------|------|------|",
        ]
        for dim, label in [("valuation", "估值"), ("technical", "技术"), ("fundamental", "基本面")]:
            d = bd.get(dim, {})
            lines.append(f"| {label} | {d.get('score', 0):.1f} | {d.get('max', 0)} |")

        lines += [
            f"| 合计 | {score.get('total_score', 0):.1f} | 100 |",
            "",
            f"评级：{score.get('rating', '—')} 建议：{score.get('action', '—')}",
            "",
            "## 各维度分析依据",
        ]
        for dim, label in [("valuation", "估值"), ("technical", "技术"), ("fundamental", "基本面")]:
            lines.append(f"\n### {label}")
            for r in bd.get(dim, {}).get("reasons", []):
                lines.append(f"- {r}")

        # 技术指标
        ind = score.get("indicators", {})
        if ind:
            lines += [
                "",
                "## 技术指标",
                f"- 趋势：{score.get('trend', '—')}",
                f"- RSI：{ind.get('rsi', '—')}",
                f"- MACD柱：{ind.get('macd_hist', '—')}",
                f"- MA5/20/60：{ind.get('ma5', '—')} / {ind.get('ma20', '—')} / {ind.get('ma60', '—')}",
            ]
            sr = score.get("support_resistance", {})
            if sr:
                lines.append(f"- 支撑位：{sr.get('support', [])} 阻力位：{sr.get('resistance', [])}")

        # 财务
        if fin.get("status") == "live":
            lines += [
                "",
                "## 财务摘要",
                f"| 指标 | 数值 |",
                f"|------|------|",
                f"| ROE | {fin.get('roe', '—')}% |",
                f"| 净利润增速 | {fin.get('net_profit_growth', '—')}% |",
                f"| 毛利率 | {fin.get('gross_margin', '—')}% |",
                f"| 资产负债率 | {fin.get('debt_ratio', '—')}% |",
            ]

        lines += ["", "---", DISCLAIMER]

        path = RESULTS_DIR / f"{symbol}_{ts}.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    # ── JSON 原始数据 ─────────────────────────────────────────
    @staticmethod
    def save_json(result: dict) -> Path:
        snap = result.get("snapshot", {})
        symbol = snap.get("symbol", "unknown")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = RESULTS_DIR / f"{symbol}_{ts}.json"

        # DataFrame 无法直接序列化，移除
        clean = {k: v for k, v in result.items() if k != "_df"}
        path.write_text(json.dumps(clean, ensure_ascii=False, indent=2, default=str),
                       encoding="utf-8")
        return path