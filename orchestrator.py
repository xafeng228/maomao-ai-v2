#!/usr/bin/env python3
"""
orchestrator.py
主协调器 —— 串联数据获取 / 分析 / 记忆 / 报告

单只股票：orchestrator.analyze("600519")
批量：    orchestrator.batch(["600519","300750"])
"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import config
from core.data_fetcher import DataFetcher
from core.analyzer import ScoreEngine
from core.reporter import Reporter
from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class Orchestrator:

    def __init__(self, verbose: bool = True):
        self.fetcher = DataFetcher()
        self.memory = MemoryManager()
        self.reporter = Reporter()
        self.verbose = verbose

    def _log(self, msg: str):
        """控制台日志输出"""
        if self.verbose:
            print(msg)

    # ── 核心：单只股票分析 ─────────────────────────────────────
    def analyze(
        self,
        symbol: str,
        save_report: bool = True,
        print_report: bool = True,
    ) -> dict:
        t0 = time.time()
        self._log(f"\n🔍 开始分析：{symbol}")

        # 1. 获取数据
        self._log(" [1/4] 获取实时快照...")
        snapshot = self.fetcher.get_snapshot(symbol)
        if snapshot.get("status") == "error":
            self._log(f"   ❌ 快照获取失败：{snapshot.get('message')}")
            return None

        self._log(" [2/4] 获取历史K线...")
        history = self.fetcher.get_history(symbol)

        self._log(" [3/4] 获取公司信息...")
        info = self.fetcher.get_company_info(symbol)

        self._log(" [4/4] 计算多维评分...")
        financial = self.fetcher.get_financial(symbol)
        engine = ScoreEngine(snapshot, history, financial)
        score = engine.compute()

        # 2. 组装结果
        result = {
            "symbol": symbol,
            "snapshot": snapshot,
            "financial": financial,
            "info": info,
            "score": score,
        }

        # 3. 保存记忆
        if save_report:
            record_id = self.memory.save(symbol, result)
            self._log(f"   💾 已保存记忆：{record_id}")

        # 4. 生成报告
        if print_report:
            self.reporter.print_report(result)

        if save_report:
            md_path = self.reporter.save_markdown(result)
            json_path = self.reporter.save_json(result)
            self._log(f"   📄 报告已保存：{md_path.name}, {json_path.name}")

        elapsed = time.time() - t0
        self._log(f"   📊 分析完成，耗时：{elapsed:.2f}秒")

        return result

    # ── 批量分析（并发优化版）──────────────────────────────────
    def batch(
        self,
        symbols: list[str],
        save_report: bool = True,
        print_report: bool = True,
        sort_by: str = "score",  # score / rating / symbol
    ) -> list[dict]:
        """并发批量分析多只股票"""
        t0 = time.time()
        total = len(symbols)
        self._log(f"\n🚀 批量分析 {total} 只股票（并发模式）")

        if total == 0:
            self._log("   ⚠️ 股票列表为空")
            return []

        # 获取并发配置
        max_workers = config.BATCH_CONFIG.get("max_concurrent", 3)
        self._log(f"   并发数：{max_workers}（配置：BATCH_CONFIG['max_concurrent']）")

        results = []
        completed = 0
        failed = 0

        # 使用线程池并发执行
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_symbol = {
                executor.submit(
                    self._analyze_single,
                    symbol,
                    save_report=False,  # 批量时不单独保存报告
                    print_report=False,  # 批量时不单独打印报告
                ): symbol
                for symbol in symbols
            }

            # 处理完成的任务
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                completed += 1
                
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        self._log(f"   [{completed}/{total}] ✅ {symbol} 分析完成")
                    else:
                        failed += 1
                        self._log(f"   [{completed}/{total}] ❌ {symbol} 分析失败")
                except Exception as e:
                    failed += 1
                    self._log(f"   [{completed}/{total}] ❌ {symbol} 异常：{str(e)[:50]}")

        # 排序结果
        if sort_by == "score":
            results.sort(key=lambda x: x.get("score", {}).get("total_score", 0), reverse=True)
        elif sort_by == "rating":
            rating_order = {"A+": 4, "A": 3, "B": 2, "C": 1}
            results.sort(key=lambda x: rating_order.get(x.get("score", {}).get("rating", "C"), 0), reverse=True)

        # 显示排行榜
        if results and print_report:
            self._log(f"\n🏆 综合排名（按{sort_by}排序）：")
            for i, r in enumerate(results[:10], 1):  # 只显示前10名
                score = r.get("score", {})
                snap = r.get("snapshot", {})
                self._log(f"   {i:2d}. {snap.get('symbol', '?'):6} "
                         f"{snap.get('name', '')[:10]:10} "
                         f"{score.get('total_score', 0):5.1f}分 "
                         f"[{score.get('rating', '—')}] "
                         f"{score.get('action', '')}")

        # 批量保存报告
        if save_report and results:
            for result in results:
                self.memory.save(result["symbol"], result)
                self.reporter.save_markdown(result)
                self.reporter.save_json(result)
            self._log(f"   💾 批量保存完成：{len(results)}份报告")

        elapsed = time.time() - t0
        self._log(f"\n📊 批量分析完成")
        self._log(f"   成功：{len(results)} 只，失败：{failed} 只")
        self._log(f"   总耗时：{elapsed:.2f}秒，平均：{elapsed/max(1, len(results)):.2f}秒/只")
        self._log(f"   并发效率：{(total * 5) / elapsed:.1f}x 加速")  # 假设串行每只5秒

        return results

    def _analyze_single(self, symbol: str, save_report: bool, print_report: bool) -> Optional[dict]:
        """单股票分析包装方法，用于并发执行"""
        try:
            return self.analyze(symbol, save_report=save_report, print_report=print_report)
        except Exception as e:
            logger.error("分析失败 %s: %s", symbol, e)
            return None

    # ── 历史评分趋势 ───────────────────────────────────────────
    def trend(self, symbol: str) -> dict:
        """查看某只股票的历史评分趋势"""
        self._log(f"\n📈 查看历史评分趋势：{symbol}")
        trend = self.memory.score_trend(symbol)

        if trend["scores"]:
            self._log(f"   趋势：{trend['trend']}")
            self._log("   最近评分记录：")
            for s in trend["scores"][-5:]:  # 显示最近5条
                self._log(f"     {s['date']}  评分：{s.get('score', '—'):5}  价格：{s.get('price', '—'):7.2f}")
        else:
            self._log("   ⚠️ 无历史数据")

        return trend

    # ── 记忆系统概览 ───────────────────────────────────────────
    def summary(self):
        """显示记忆系统概览"""
        self._log("\n🧠 记忆系统概览")
        s = self.memory.summary()

        self._log(f"   总记录数：{s['total_records']}")
        self._log(f"   覆盖股票：{s['stocks_covered']} 只 → {s['stock_list']}")

        # 历史最高评分展示
        if s["stocks_covered"] > 0:
            self._log("\n   🏆 历史最高评分：")
            top_scores = []
            for stock in s["stock_list"][:5]:  # 只显示前5只
                records = self.memory.load(stock, last_n=1)
                if records:
                    rec = records[0]
                    top_scores.append((
                        rec["symbol"],
                        rec.get("score", 0),
                        rec.get("rating", "—"),
                        rec.get("price", 0)
                    ))
            
            # 按评分排序
            top_scores.sort(key=lambda x: x[1], reverse=True)
            for sym, score, rating, price in top_scores[:3]:  # 只显示前3名
                self._log(f"     {sym:6} {score:5.1f}分 [{rating}] ¥{price:.2f}")

        # 最近分析记录
        if s.get("recent_analyses"):
            self._log("\n   ⏰ 最近分析记录：")
            for ra in s["recent_analyses"][:3]:
                self._log(f"     {ra['id']}")

        self._log(f"\n   记忆目录：{s['memory_dir']}")
