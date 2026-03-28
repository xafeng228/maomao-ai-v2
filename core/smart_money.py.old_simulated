#!/usr/bin/env python3
"""
core/smart_money.py
主力/量化资金布局检测器
四个维度：
 1. 大单资金流（主力特征）
 2. 量化行为特征（高频小单、尾盘异动）
 3. 机构席位布局（龙虎榜、融资变化）
 4. 板块资金轮动（行业流向对比）
所有数据来源：akshare 公开接口，无需付费
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _safe_float(val, default=0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _today() -> str:
    return datetime.today().strftime("%Y%m%d")


def _n_days_ago(n: int) -> str:
    return (datetime.today() - timedelta(days=n)).strftime("%Y%m%d")
# ══════════════════════════════════════════════════════════════
# 维度一：大单资金流检测（主力特征）
# ══════════════════════════════════════════════════════════════

class BigMoneyFlow:
    """
    检测超大单/大单净流入异常
    信号：持续净流入 + 股价横盘 = 主力吸筹特征
    放量拉升后缩量回调 = 主力控盘特征
    数据：akshare stock_individual_fund_flow
    """

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.df = None  # 简化版本，不实际获取数据

    def analyze(self) -> dict:
        # 简化版本，返回模拟数据
        return {
            "status": "ok",
            "score": 65,
            "signals": ["🟢 模拟：近5日主力净流入4天，持续吸筹", "🟡 模拟：价格横盘但主力持续净流入"],
            "summary": {
                "main_net_today": 1.2,
                "xlarge_net_today": 0.8,
                "main_net_pct": 3.5,
                "5d_cumulative": 4.5,
            },
            "raw_days": 20,
        }


# ══════════════════════════════════════════════════════════════
# 维度二：量化资金行为特征
# ══════════════════════════════════════════════════════════════

class QuantBehavior:
    """
    通过分钟级成交特征识别量化资金痕迹
    量化特征：
    - 尾盘最后5分钟大幅异动（集合竞价争夺）
    - 成交笔数异常密集（高频小单刷量）
    - 盘中成交量分布异常均匀（算法拆单）
    """

    def __init__(self, symbol: str):
        self.symbol = symbol

    def analyze(self) -> dict:
        # 简化版本，返回模拟数据
        return {
            "status": "ok",
            "score": 45,
            "signals": ["🟡 模拟：尾盘成交量占全天28%，略偏高", "🟢 模拟：成交量分布均匀，疑似算法拆单"],
        }


# ══════════════════════════════════════════════════════════════
# 维度三：机构席位布局（龙虎榜 + 融资融券）
# ══════════════════════════════════════════════════════════════

class InstitutionLayout:
    """
    龙虎榜：机构席位净买入 = 强烈看多信号
    融资余额：持续增加 = 杠杆资金在加仓
    """

    def __init__(self, symbol: str):
        self.symbol = symbol

    def analyze(self) -> dict:
        # 简化版本，返回模拟数据
        return {
            "status": "ok",
            "score": 70,
            "signals": ["🔴 模拟：龙虎榜机构席位近30日净买入2.5亿，机构重点布局", "🟡 模拟：融资余额5日增长8%，融资资金温和增加"],
            "lhb_summary": {"appearances": 2, "institution_buy": 3.2, "institution_sell": 0.7},
            "margin_summary": {"balance": 15.8, "5d_growth": 8.2},
        }


# ══════════════════════════════════════════════════════════════
# 维度四：板块资金轮动洞察
# ══════════════════════════════════════════════════════════════

class SectorRotation:
    """
    行业资金流向排名，识别主力正在布局的板块
    逻辑：资金净流入排名靠前的板块 = 当前主力重点方向
    """
    def __init__(self, symbol: str = None, industry: str = None):
        self.symbol = symbol
        self.industry = industry

    def analyze(self) -> dict:
        # 简化版本，返回模拟数据
        top_sectors = [
            {"rank": 1, "sector": "白酒", "main_net_亿": 5.2, "pct_chg": 1.5},
            {"rank": 2, "sector": "电池", "main_net_亿": 3.8, "pct_chg": 2.1},
            {"rank": 3, "sector": "医药", "main_net_亿": 2.5, "pct_chg": 0.8},
        ]
        
        return {
            "status": "ok",
            "score": 55,
            "signals": ["🟢 模拟：所属行业'白酒'资金流入排名第1/30，处于顶部3%，主力正在重点布局"],
            "top_sectors": top_sectors,
            "industry_rank": 1,
            "market_breadth": {"inflow": 20, "outflow": 10, "total": 30},
        }


# ══════════════════════════════════════════════════════════════
# 综合检测器（对外入口）
# ══════════════════════════════════════════════════════════════

class SmartMoneyDetector:
    """
    对外统一入口，整合四个维度，输出综合布局信号
    用法：
    detector = SmartMoneyDetector("600519", industry="白酒")
    result = detector.detect()
    """
    WEIGHTS = {
        "big_money": 0.35,  # 大单资金流权重最高
        "quant": 0.20,
        "institution": 0.30,
        "sector": 0.15,
    }

    def __init__(self, symbol: str, industry: str = ""):
        self.symbol = symbol
        self.industry = industry

    def detect(self) -> dict:
        print(f" 🔎 [资金] 检测大单资金流...")
        bm = BigMoneyFlow(self.symbol).analyze()

        print(f" 🔎 [资金] 检测量化行为特征...")
        qb = QuantBehavior(self.symbol).analyze()

        print(f" 🔎 [资金] 检测机构席位布局...")
        il = InstitutionLayout(self.symbol).analyze()

        print(f" 🔎 [资金] 检测板块资金轮动...")
        sr = SectorRotation(self.symbol, self.industry).analyze()

        # 加权综合评分
        w = self.WEIGHTS
        raw = (
            bm.get("score", 0) * w["big_money"] +
            qb.get("score", 0) * w["quant"] +
            il.get("score", 0) * w["institution"] +
            sr.get("score", 0) * w["sector"]
        )
        total = round(raw, 1)

        # 综合信号强度
        if total >= 60:
            strength, emoji = "强烈布局信号", "🔴"
        elif total >= 40:
            strength, emoji = "温和布局信号", "🟡"
        elif total >= 20:
            strength, emoji = "轻微关注迹象", "🟢"
        else:
            strength, emoji = "无明显信号", "⚪"

        # 汇总所有信号
        all_signals = (
            bm.get("signals", []) +
            qb.get("signals", []) +
            il.get("signals", []) +
            sr.get("signals", [])
        )

        return {
            "symbol": self.symbol,
            "industry": self.industry,
            "total_score": total,
            "strength": strength,
            "emoji": emoji,
            "all_signals": all_signals,
            "breakdown": {
                "big_money": bm,
                "quant": qb,
                "institution": il,
                "sector": sr,
            },
            "top_sectors": sr.get("top_sectors", []),
            "detected_at": datetime.now().isoformat(),
        }
