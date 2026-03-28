#!/usr/bin/env python3
"""
memory/memory_manager.py
持久化记忆系统
- 记录每次分析结果
- 追踪股票历史评分趋势
- 有界管理（超过上限自动压缩）
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import MEMORY_DIR

logger = logging.getLogger(__name__)

MAX_RECORDS_PER_STOCK = 30  # 每只股票最多保留30条历史记录
MAX_TOTAL_RECORDS = 500  # 总记录上限


class MemoryManager:
    """
    用法：
    mm = MemoryManager()
    mm.save(symbol, analysis_result)
    history = mm.load(symbol)
    mm.summary()
    """

    def __init__(self):
        self._index_path = MEMORY_DIR / "_index.json"
        self._index = self._load_index()

    # ── 索引管理 ──────────────────────────────────────────────
    def _load_index(self) -> dict:
        if self._index_path.exists():
            try:
                return json.loads(self._index_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"stocks": {}, "total_records": 0, "created_at": datetime.now().isoformat()}

    def _save_index(self):
        self._index_path.write_text(
            json.dumps(self._index, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    # ── 核心 API ─────────────────────────────────────────────
    def save(self, symbol: str, result: dict) -> str:
        """保存一条分析记录，返回记录ID"""
        ts = datetime.now()
        record_id = f"{symbol}_{ts.strftime('%Y%m%d_%H%M%S')}"
        record = {
            "id": record_id,
            "symbol": symbol,
            "saved_at": ts.isoformat(),
            "score": result.get("score", {}).get("total_score"),
            "rating": result.get("score", {}).get("rating"),
            "action": result.get("score", {}).get("action"),
            "price": result.get("snapshot", {}).get("price"),
            "trend": result.get("score", {}).get("trend"),
            "full": result,
        }

        # 写入单条文件
        path = MEMORY_DIR / f"{record_id}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

        # 更新索引
        if symbol not in self._index["stocks"]:
            self._index["stocks"][symbol] = []
        self._index["stocks"][symbol].append(record_id)
        self._index["total_records"] = self._index.get("total_records", 0) + 1

        # 有界管理
        self._prune(symbol)
        self._save_index()

        logger.info("记忆已保存：%s → %s", symbol, record_id)
        return record_id

    def load(self, symbol: str, last_n: int = 5) -> list[dict]:
        """读取某只股票最近 n 条记录"""
        ids = self._index["stocks"].get(symbol, [])[-last_n:]
        records = []
        for rid in ids:
            path = MEMORY_DIR / f"{rid}.json"
            if path.exists():
                try:
                    records.append(json.loads(path.read_text(encoding="utf-8")))
                except Exception as e:
                    logger.warning("读取记录失败 %s: %s", rid, e)
        return records

    def load_latest(self, symbol: str) -> Optional[dict]:
        """读取最新一条记录"""
        records = self.load(symbol, last_n=1)
        return records[0] if records else None

    def score_trend(self, symbol: str) -> dict:
        """返回评分趋势（用于判断是否持续改善）"""
        records = self.load(symbol, last_n=10)
        if not records:
            return {"symbol": symbol, "trend": "无历史数据", "scores": []}

        scores = [
            {"date": r["saved_at"][:10], "score": r.get("score"), "price": r.get("price")}
            for r in records if r.get("score") is not None
        ]
        if len(scores) >= 2:
            delta = scores[-1]["score"] - scores[0]["score"]
            trend = "改善" if delta > 3 else "恶化" if delta < -3 else "稳定"
        else:
            trend = "数据不足"

        return {"symbol": symbol, "trend": trend, "scores": scores}

    def summary(self) -> dict:
        """系统概览"""
        stocks = self._index["stocks"]
        total = self._index.get("total_records", 0)
        coverage = len(stocks)
        # 最近10条记录（跨股票）
        recent = []
        for sym, ids in stocks.items():
            if ids:
                recent.append((ids[-1], sym))
        recent.sort(reverse=True)
        recent = recent[:10]

        return {
            "total_records": total,
            "stocks_covered": coverage,
            "stock_list": list(stocks.keys()),
            "recent_analyses": [{"id": r[0], "symbol": r[1]} for r in recent],
            "memory_dir": str(MEMORY_DIR),
        }

    # ── 有界管理 ──────────────────────────────────────────────
    def _prune(self, symbol: str):
        """超过上限时删除最旧记录"""
        ids = self._index["stocks"].get(symbol, [])
        while len(ids) > MAX_RECORDS_PER_STOCK:
            old_id = ids.pop(0)
            old_path = MEMORY_DIR / f"{old_id}.json"
            if old_path.exists():
                old_path.unlink()
            logger.debug("清理旧记录：%s", old_id)

        # 全局上限
        total = sum(len(v) for v in self._index["stocks"].values())
        if total > MAX_TOTAL_RECORDS:
            # 找最旧的股票的最旧记录
            for sym, sym_ids in self._index["stocks"].items():
                if sym_ids:
                    old_id = sym_ids.pop(0)
                    old_path = MEMORY_DIR / f"{old_id}.json"
                    if old_path.exists():
                        old_path.unlink()
                    break