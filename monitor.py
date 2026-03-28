#!/usr/bin/env python3
"""
monitor.py —— 监控系统入口
用法：
 python monitor.py # 自动判断时段运行
 python monitor.py --pre # 强制盘前选股模式
 python monitor.py --intraday # 强制盘中预警模式
 python monitor.py --post # 强制盘后复盘模式
 python monitor.py --add 600519 白酒 # 加入监控池
 python monitor.py --list # 显示监控池
 python monitor.py --alerts # 查看今日预警记录
"""
import argparse
import json
import sys
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.WARNING, format="%(levelname)s │ %(message)s")

# ── 监控股票池（持久化到 JSON）────────────────────────────────
WATCHLIST_FILE = Path("results/watchlist.json")
WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_watchlist() -> dict:
    if WATCHLIST_FILE.exists():
        try:
            return json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"stocks": {}}  # {"600519": "白酒", "300750": "电池"}


def save_watchlist(wl: dict):
    WATCHLIST_FILE.write_text(
        json.dumps(wl, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_lists(wl: dict):
    stocks = wl.get("stocks", {})
    symbols = list(stocks.keys())
    industries = stocks  # symbol→industry 字典
    return symbols, industries


# ── 命令处理 ─────────────────────────────────────────────────

def cmd_add(symbol: str, industry: str, wl: dict):
    wl["stocks"][symbol] = industry
    save_watchlist(wl)
    print(f"✅ 已加入监控池：{symbol} [{industry}]")
    print(f"  当前监控池：{list(wl['stocks'].keys())}")


def cmd_remove(symbol: str, wl: dict):
    if symbol in wl["stocks"]:
        del wl["stocks"][symbol]
        save_watchlist(wl)
        print(f"✅ 已移出：{symbol}")
    else:
        print(f"⚠️ {symbol} 不在监控池中")


def cmd_list(wl: dict):
    stocks = wl.get("stocks", {})
    if not stocks:
        print("监控池为空。用 --add 600519 白酒 添加股票")
        return
    print(f"\n📋 当前监控池（{len(stocks)}只）：")
    for sym, ind in stocks.items():
        print(f"  {sym} [{ind or '未设置行业'}]")


def cmd_alerts():
    alert_log = Path("results/alerts.jsonl")
    if not alert_log.exists():
        print("暂无预警记录")
        return
    today = datetime.now().strftime("%Y-%m-%d")
    alerts = []
    with open(alert_log, encoding="utf-8") as f:
        for line in f:
            try:
                a = json.loads(line)
                if a.get("time", "").startswith(today):
                    alerts.append(a)
            except Exception:
                pass
    if not alerts:
        print(f"今日（{today}）暂无预警记录")
        return
    print(f"\n🚨 今日预警记录（{len(alerts)}条）：")
    for a in alerts:
        t = a["time"][11:19]
        sym = a["symbol"]
        sc = a["score"]
        rsn = a["reason"]
        print(f"  [{t}] {sym} {sc:.0f}分 {rsn}")
        for sig in a.get("signals", [])[:2]:
            print(f"    {sig}")


def main():
    parser = argparse.ArgumentParser(
        description="毛毛AI — 主力资金监控系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
 python monitor.py 自动选择时段模式
 python monitor.py --pre 盘前选股
 python monitor.py --intraday --interval 180 盘中预警（每3分钟）
 python monitor.py --post 盘后复盘
 python monitor.py --add 600519 白酒 添加茅台到监控池
 python monitor.py --remove 600519 从监控池移除
 python monitor.py --list 查看监控池
 python monitor.py --alerts 今日预警记录
""",
    )
    parser.add_argument("--pre", action="store_true", help="盘前选股模式")
    parser.add_argument("--intraday", action="store_true", help="盘中预警模式")
    parser.add_argument("--post", action="store_true", help="盘后复盘模式")
    parser.add_argument("--auto", action="store_true", help="自动判断时段（默认）")
    parser.add_argument("--add", nargs=2, metavar=("CODE","INDUSTRY"), help="添加到监控池")
    parser.add_argument("--remove", metavar="CODE", help="从监控池移除")
    parser.add_argument("--list", action="store_true", help="显示监控池")
    parser.add_argument("--alerts", action="store_true", help="查看今日预警")
    parser.add_argument("--threshold", type=int, default=50, help="预警阈值分数（默认50）")
    parser.add_argument("--interval", type=int, default=300, help="盘中扫描间隔秒数（默认300）")

    args = parser.parse_args()
    wl = load_watchlist()

    # ── 管理命令（不需要运行检测）──────────────────────────
    if args.add:
        cmd_add(args.add[0], args.add[1], wl)
        return
    if args.remove:
        cmd_remove(args.remove, wl)
        return
    if args.list:
        cmd_list(wl)
        return
    if args.alerts:
        cmd_alerts()
        return

    # ── 检查监控池 ────────────────────────────────────────
    symbols, industries = get_lists(wl)
    if not symbols:
        print("⚠️ 监控池为空！先添加股票：")
        print("  python monitor.py --add 600519 白酒")
        print("  python monitor.py --add 300750 电池")
        sys.exit(1)

    # ── 运行模式 ─────────────────────────────────────────
    print("📊 主力资金监控系统启动...")
    print(f"  监控股票：{symbols}")
    
    if args.pre:
        print("→ 进入【盘前选股】模式")
        # 简化版本，直接运行扫描
        from scan import cmd_batch
        cmd_batch(symbols)
    elif args.intraday:
        print("→ 进入【盘中实时预警】模式")
        print(f"  预警阈值：{args.threshold}分，扫描间隔：{args.interval}秒")
        print("  ⚠️ 简化版本，仅单次扫描")
        from scan import cmd_batch
        cmd_batch(symbols)
    elif args.post:
        print("→ 进入【盘后复盘】模式")
        from scan import cmd_batch
        cmd_batch(symbols)
    else:
        # 默认：自动判断（简化版本）
        print("→ 自动模式：运行单次扫描")
        from scan import cmd_batch
        cmd_batch(symbols)


if __name__ == "__main__":
    main()