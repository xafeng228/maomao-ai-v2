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
            logger.error("快照获取失败：%s", snapshot.get("message"))
            return snapshot

        self._log(f" ✓ {snapshot['name']} 当前价 {snapshot['price']}")

        self._log(" [2/4] 获取历史K线...")
        history = self.fetcher.get_history(symbol)

        self._log(" [3/4] 获取财务数据...")
        financial = self.fetcher.get_financial(symbol)

        self._log(" [3b] 获取公司信息...")
        info = self.fetcher.get_company_info(symbol)

        # 2. 评分
        self._log(" [4/4] 计算多维评分...")
        engine = ScoreEngine(snapshot, history, financial)
        score = engine.compute()
        self._log(f" ✓ 综合评分 {score['total_score']} / 100 [{score['rating']}]")

        # 3. 组装结果
        result = {
            "symbol": symbol,
            "snapshot": snapshot,
            "financial": financial,
            "info": info,
            "score": score,
            "elapsed": round(time.time() - t0, 2),
        }

        # 4. 记忆 & 报告
        record_id = self.memory.save(symbol, result)
        self._log(f" 💾 已保存记忆：{record_id}")

        if print_report:
            self.reporter.print_report(result)

        if save_report:
            md = self.reporter.save_markdown(result)
            js = self.reporter.save_json(result)
            result["report_md"] = str(md)
            result["report_json"] = str(js)
            self._log(f" 📄 报告已保存：{md.name}")

        self._log(f" ⏱ 耗时 {result['elapsed']}s")
        return result

    # ── 批量分析 ──────────────────────────────────────────────
    def batch(
        self,
        symbols: list[str],
        sort_by: str = "score",  # "score" | "symbol"
    ) -> dict:
        self._log(f"\n🚀 批量分析 {len(symbols)} 只股票")
        results = []

        for i, sym in enumerate(symbols, 1):
            self._log(f"\n[{i}/{len(symbols)}]")
            try:
                r = self.analyze(sym, print_report=False)
                results.append(r)
            except Exception as e:
                logger.error("分析失败 %s: %s", sym, e)
                results.append({"symbol": sym, "status": "error", "message": str(e)})

        # 排序
        ok = [r for r in results if r.get("score")]
        err = [r for r in results if not r.get("score")]
        if sort_by == "score":
            ok.sort(key=lambda r: r["score"]["total_score"], reverse=True)

        # 打印排行
        self._print_ranking(ok)

        return {"results": ok + err, "success": len(ok), "failed": len(err)}

    @staticmethod
    def _print_ranking(results: list[dict]):
        """打印综合评分排行榜"""
        if not results:
            return
        
        print("\n" + "═" * 60)
        print(" 📊 综合评分排行榜")
        print("═" * 60)
        
        for i, r in enumerate(results, 1):
            snap = r.get("snapshot", {})
            score = r.get("score", {})
            name = snap.get("name", "—")
            sym = r.get("symbol", "—")
            total = score.get("total_score", 0)
            rating = score.get("rating", "—")
            action = score.get("action", "—")
            price = snap.get("price", 0)
            chg = snap.get("change_pct", 0)
            chg_s = f"+{chg:.2f}%" if chg >= 0 else f"{chg:.2f}%"
            print(f" {i:2}. {name:8}({sym}) {total:5.1f}分 [{rating}] {action} ¥{price} {chg_s}")
        
        print("═" * 60)

    # ── 历史趋势 ──────────────────────────────────────────────
    def trend(self, symbol: str):
        trend = self.memory.score_trend(symbol)
        print(f"\n📈 {symbol} 历史评分趋势：{trend['trend']}")
        for s in trend["scores"]:
            bar = "█" * int((s["score"] or 0) / 5)
            print(f" {s['date']} {bar:20} {s['score']:.1f} ¥{s['price']}")

    # ── 记忆系统概览 ──────────────────────────────────────────
    def summary(self):
        """显示记忆系统概览"""
        s = self.memory.summary()
        print(f"\n🧠 记忆系统概览")
        print(f"   总记录数：{s['total_records']}")
        print(f"   覆盖股票：{s['stocks_covered']} 只 → {s['stock_list']}")
        
        if s.get('top_scored'):
            print(f"\n🏆 历史最高评分：")
            for sym, score in s['top_scored'][:5]:
                print(f"   {sym}: {score:.1f}分")