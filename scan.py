#!/usr/bin/env python3
"""
scan.py —— 独立资金扫描入口
用法：
 python scan.py 600519 # 单股资金检测
 python scan.py 600519 --industry 白酒 # 含板块分析
 python scan.py --sector # 今日全市场板块资金流向
 python scan.py 600519 300750 000858 # 批量资金对比
"""
import argparse
import sys
import logging

logging.basicConfig(level=logging.WARNING, format="%(levelname)s │ %(message)s")

from core.smart_money import SmartMoneyDetector, SectorRotation


def _bar(score: float, width: int = 20) -> str:
    filled = int(score / 100 * width)
    return "█" * filled + "░" * (width - filled)


def print_result(result: dict):
    total = result.get("total_score", 0)
    strength = result.get("strength", "")
    emoji = result.get("emoji", "")
    symbol = result.get("symbol", "")
    industry = result.get("industry", "")

    print()
    print("━" * 62)
    print(f" {emoji} {symbol} {'[' + industry + ']' if industry else ''} 主力/量化资金布局检测")
    print(f" 综合信号强度：{total:.0f}/100 {strength}")
    print(f" {_bar(total)}")
    print()

    bd = result.get("breakdown", {})
    dim_map = [
        ("big_money", "大单资金流", 35),
        ("quant", "量化特征 ", 20),
        ("institution", "机构席位 ", 30),
        ("sector", "板块轮动 ", 15),
    ]
    for key, label, weight in dim_map:
        d = bd.get(key, {})
        s = d.get("score", 0)
        bar = "█" * int(s / 10) + "░" * (10 - int(s / 10))
        print(f" {label} {bar} {s:.0f}分 (权重{weight}%)")
        for sig in d.get("signals", []):
            print(f" {sig}")

    # 板块 TOP
    top = result.get("top_sectors", [])
    if top:
        print()
        print(" 💰 今日主力资金流入 TOP 板块：")
        for t in top[:5]:
            direction = "+" if t["main_net_亿"] >= 0 else ""
            bar = "█" * min(int(abs(t["main_net_亿"]) / 1), 20)
            print(f" {t['rank']:2}. {t['sector']:12} {direction}{t['main_net_亿']:.1f}亿 {bar}")

    # 大单资金摘要
    bm = bd.get("big_money", {}).get("summary", {})
    if bm:
        print()
        print(" 📊 大单资金摘要（今日）：")
        print(f" 主力净流入：{bm.get('main_net_today', 0):.2f}万手")
        print(f" 数据来源：{bm.get('data_source', '未知')}")
        print(f" 交易日：{bm.get('trade_date', '未知')}")

    print()
    print(" ⚠️ 统计特征推断，不代表真实主力身份，不构成投资建议")
    print("━" * 62)


def cmd_sector_overview():
    """全市场板块资金流向概览"""
    print("\n🗺 今日全市场行业资金流向")
    sr = SectorRotation()
    result = sr.analyze()

    top = result.get("top_sectors", [])
    print(f"\n{'排名':4} {'行业':12} {'主力净流入(亿)':15} {'涨跌幅':8}")
    print("─" * 45)

    if top:
        for t in top[:15]:
            net = t["main_net_亿"]
            chg = t["pct_chg"]
            bar = ("+" if net >= 0 else "") + f"{net:.1f}"
            print(f" {t['rank']:3} {t['sector'][:10]:12} {bar:>10}亿 {chg:+.2f}%")
    print()


def cmd_batch(symbols: list, industry: str = ""):
    """批量资金对比"""
    results = []
    for sym in symbols:
        print(f"\n⏳ 检测 {sym}...")
        detector = SmartMoneyDetector(sym, industry)
        r = detector.detect()
        results.append(r)

    results.sort(key=lambda x: x["total_score"], reverse=True)

    print("\n" + "═" * 62)
    print(" 📊 资金布局信号排行榜")
    print("═" * 62)
    for i, r in enumerate(results, 1):
        emoji = r.get("emoji", "")
        total = r.get("total_score", 0)
        sym = r.get("symbol", "")
        str_ = r.get("strength", "")
        bar = _bar(total, 15)
        print(f" {i:2}. {sym} {bar} {total:.0f}分 {emoji} {str_}")
    print("═" * 62)

    # 详细输出得分最高的
    if results:
        print(f"\n📋 信号最强：{results[0]['symbol']} 详细报告")
        print_result(results[0])


def main():
    parser = argparse.ArgumentParser(
        description="毛毛AI — 主力/量化资金布局检测",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
 python scan.py 600519 茅台资金检测
 python scan.py 600519 --industry 白酒 含板块对比
 python scan.py --sector 全市场板块概览
 python scan.py 600519 300750 000858 批量对比排名
""",
    )
    parser.add_argument("symbols", nargs="*", help="股票代码")
    parser.add_argument("--industry", default="", help="所属行业（用于板块对比）")
    parser.add_argument("--sector", action="store_true", help="显示全市场板块资金流向")

    args = parser.parse_args()

    if args.sector:
        cmd_sector_overview()
        return

    if not args.symbols:
        parser.print_help()
        sys.exit(0)

    if len(args.symbols) == 1:
        sym = args.symbols[0]
        print(f"\n⏳ 正在检测 {sym} 的主力/量化资金布局...")
        detector = SmartMoneyDetector(sym, args.industry)
        result = detector.detect()
        print_result(result)
    else:
        cmd_batch(args.symbols, args.industry)


if __name__ == "__main__":
    main()
