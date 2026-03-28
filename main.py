#!/usr/bin/env python3
"""
main.py —— 唯一入口

用法：
 python main.py 600519              # 分析单只股票
 python main.py 600519 300750 000858 # 批量分析
 python main.py 600519 --trend       # 查看历史趋势
 python main.py --summary            # 记忆系统概览
"""
import argparse
import logging
import sys

import config

# ── 日志配置 ─────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, config.LOGGING_CONFIG["level"]),
    format=config.LOGGING_CONFIG["format"],
)

from orchestrator import Orchestrator


def main():
    parser = argparse.ArgumentParser(
        description="毛毛AI投研助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
 python main.py 600519              茅台单只分析
 python main.py 600519 300750 000858 批量排名
 python main.py 600519 --trend      历史评分趋势
 python main.py --summary           记忆系统概览
""",
    )
    parser.add_argument("symbols", nargs="*", help="股票代码（可多个）")
    parser.add_argument("--trend", action="store_true", help="查看第一个股票的历史评分趋势")
    parser.add_argument("--summary", action="store_true", help="显示记忆系统概览")
    parser.add_argument("--no-save", action="store_true", help="不保存报告文件")
    parser.add_argument("--quiet", action="store_true", help="减少日志输出")

    args = parser.parse_args()

    orchestrator = Orchestrator(verbose=not args.quiet)

    # ── 路由 ────────────────────────────────────────────────
    if args.summary:
        orchestrator.summary()
        return

    if not args.symbols:
        parser.print_help()
        sys.exit(0)

    if args.trend:
        orchestrator.trend(args.symbols[0])
        return

    save = not args.no_save

    if len(args.symbols) == 1:
        orchestrator.analyze(args.symbols[0], save_report=save)
    else:
        orchestrator.batch(args.symbols)


if __name__ == "__main__":
    main()