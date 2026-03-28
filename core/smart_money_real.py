#!/usr/bin/env python3
"""
core/smart_money_real.py - Tushare真实数据版本
主力/量化资金布局检测器（使用真实Tushare数据）
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
# 维度一：大单资金流检测（Tushare真实数据）
# ══════════════════════════════════════════════════════════════

class BigMoneyFlow:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.df = self._fetch_tushare_data()

    def _fetch_tushare_data(self) -> Optional[pd.DataFrame]:
        """使用Tushare获取真实大单资金流数据"""
        try:
            import tushare as ts
            
            # 配置Tushare Token
            from config import TUSHARE_TOKEN
            if not TUSHARE_TOKEN:
                logger.warning("Tushare Token未配置")
                return None
                
            ts.set_token(TUSHARE_TOKEN)
            pro = ts.pro_api()
            
            print(f"   正在获取 {self.symbol} Tushare资金流数据...")
            
            # 获取资金流向数据
            ts_code = f"{self.symbol}.SH" if self.symbol.startswith("6") else f"{self.symbol}.SZ"
            today = _today()
            
            df = pro.moneyflow(ts_code=ts_code, trade_date=today)
            
            if df is None or df.empty:
                logger.warning(f"Tushare资金流数据为空: {self.symbol}")
                return None
                
            print(f"   ✅ 获取到Tushare资金流数据")
            return df
            
        except Exception as e:
            logger.error(f"Tushare资金流获取失败 {self.symbol}: {str(e)[:100]}")
            return None

    def analyze(self) -> dict:
        if self.df is None or self.df.empty:
            return {"status": "no_data", "score": 0, "signals": ["⚠️ 无Tushare资金流数据"], "summary": {}}

        df = self.df
        signals = []
        score = 0

        # Tushare数据分析逻辑
        if not df.empty:
            # 计算主力净流入（大单+特大单）
            buy_lg = _safe_float(df.iloc[0].get('buy_lg_vol', 0))
            sell_lg = _safe_float(df.iloc[0].get('sell_lg_vol', 0))
            buy_elg = _safe_float(df.iloc[0].get('buy_elg_vol', 0))
            sell_elg = _safe_float(df.iloc[0].get('sell_elg_vol', 0))
            
            main_net = (buy_lg + buy_elg) - (sell_lg + sell_elg)
            
            if main_net > 0:
                score += 30
                signals.append(f"🟢 Tushare: 今日主力净流入 {main_net/100:.0f}手")
            else:
                score += 10
                signals.append(f"🔴 Tushare: 今日主力净流出 {abs(main_net)/100:.0f}手")

        # 数据摘要
        if not df.empty:
            summary = {
                "main_net_today": main_net / 10000,  # 转换为万手
                "buy_lg_vol": buy_lg / 100,
                "sell_lg_vol": sell_lg / 100,
                "buy_elg_vol": buy_elg / 100,
                "sell_elg_vol": sell_elg / 100,
                "data_source": "Tushare Pro",
            }
        else:
            summary = {}

        return {
            "status": "ok",
            "score": min(score, 100),
            "signals": signals,
            "summary": summary,
            "raw_days": len(df),
        }


# ══════════════════════════════════════════════════════════════
# 综合检测器（Tushare真实数据版本）
# ══════════════════════════════════════════════════════════════

class SmartMoneyDetectorReal:
    WEIGHTS = {
        "big_money": 0.35,
        "quant": 0.20,
        "institution": 0.30,
        "sector": 0.15,
    }

    def __init__(self, symbol: str, industry: str = ""):
        self.symbol = symbol
        self.industry = industry

    def detect(self) -> dict:
        print(f" 🔎 [资金] 检测大单资金流（Tushare真实数据）...")
        bm = BigMoneyFlow(self.symbol).analyze()

        # 其他维度暂时使用模拟数据
        print(f" 🔎 [资金] 检测量化行为特征（模拟）...")
        quant_score = 45
        quant_signals = ["🟡 量化特征检测（待实现Tushare数据）"]

        print(f" 🔎 [资金] 检测机构席位布局（模拟）...")
        inst_score = 60
        inst_signals = ["🟡 机构席位检测（待实现Tushare数据）"]

        print(f" 🔎 [资金] 检测板块资金轮动（模拟）...")
        sector_score = 50
        sector_signals = ["🟡 板块轮动检测（待实现Tushare数据）"]

        # 加权综合评分
        w = self.WEIGHTS
        total = round(
            bm.get("score", 0) * w["big_money"] +
            quant_score * w["quant"] +
            inst_score * w["institution"] +
            sector_score * w["sector"], 1
        )

        # 信号强度
        if total >= 60:
            strength, emoji = "强烈布局信号", "🔴"
        elif total >= 40:
            strength, emoji = "温和布局信号", "🟡"
        else:
            strength, emoji = "无明显信号", "⚪"

        return {
            "symbol": self.symbol,
            "industry": self.industry,
            "total_score": total,
            "strength": strength,
            "emoji": emoji,
            "all_signals": bm.get("signals", []) + quant_signals + inst_signals + sector_signals,
            "breakdown": {
                "big_money": bm,
                "quant": {"score": quant_score, "signals": quant_signals},
                "institution": {"score": inst_score, "signals": inst_signals},
                "sector": {"score": sector_score, "signals": sector_signals},
            },
            "detected_at": datetime.now().isoformat(),
            "data_source": "Tushare Pro + 模拟数据混合",
        }
