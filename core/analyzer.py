#!/usr/bin/env python3
"""
core/analyzer.py
技术分析 + 基本面评分
输入：DataFetcher 返回的真实数据
输出：结构化评分字典
"""
from __future__ import annotations

import logging
from typing import Optional

import pandas as pd
import numpy as np

from config import ANALYSIS, SCORE_WEIGHTS, RATING_THRESHOLDS

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# 技术指标计算
# ══════════════════════════════════════════════════════════════

class TechIndicators:
    """给定 OHLCV DataFrame，计算各类技术指标"""

    def __init__(self, df: pd.DataFrame):
        if df is None or df.empty:
            raise ValueError("历史数据为空，无法计算技术指标")
        self.df = df.copy()
        self._compute_all()

    def _compute_all(self):
        df = self.df
        periods = ANALYSIS["ma_periods"]

        # 移动平均
        for p in periods:
            df[f"ma{p}"] = df["close"].rolling(p).mean()

        # RSI
        rsi_p = ANALYSIS["rsi_period"]
        delta = df["close"].diff()
        gain = delta.clip(lower=0).rolling(rsi_p).mean()
        loss = (-delta.clip(upper=0)).rolling(rsi_p).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - 100 / (1 + rs)

        # MACD (12/26/9)
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # 布林带 (20日)
        df["bb_mid"] = df["close"].rolling(20).mean()
        std20 = df["close"].rolling(20).std()
        df["bb_upper"] = df["bb_mid"] + 2 * std20
        df["bb_lower"] = df["bb_mid"] - 2 * std20

        # 成交量均线
        df["vol_ma5"] = df["volume"].rolling(5).mean()
        df["vol_ma20"] = df["volume"].rolling(20).mean()

        self.df = df

    def latest(self) -> dict:
        """返回最新一行所有指标"""
        row = self.df.iloc[-1]
        prev = self.df.iloc[-2] if len(self.df) > 1 else row

        close = float(row["close"])
        ma5 = float(row.get("ma5", close))
        ma20 = float(row.get("ma20", close))
        ma60 = float(row.get("ma60", close))

        return {
            "close": close,
            "ma5": round(ma5, 2),
            "ma20": round(ma20, 2),
            "ma60": round(ma60, 2),
            "rsi": round(float(row.get("rsi", 50)), 1),
            "macd": round(float(row.get("macd", 0)), 4),
            "macd_signal": round(float(row.get("macd_signal", 0)), 4),
            "macd_hist": round(float(row.get("macd_hist", 0)), 4),
            "bb_upper": round(float(row.get("bb_upper", close)), 2),
            "bb_mid": round(float(row.get("bb_mid", close)), 2),
            "bb_lower": round(float(row.get("bb_lower", close)), 2),
            "vol_ratio": round(
                float(row.get("volume", 1)) / max(float(row.get("vol_ma20", 1)), 1), 2
            ),
            "above_ma5": close > ma5,
            "above_ma20": close > ma20,
            "above_ma60": close > ma60,
            "golden_cross": ma5 > ma20,  # 5日上穿20日
            "macd_bullish": float(row.get("macd_hist", 0)) > float(prev.get("macd_hist", 0)),
        }

    def support_resistance(self) -> dict:
        """简单支撑/阻力位（近60日高低点）"""
        recent = self.df.tail(60)
        return {
            "support": [
                round(recent["low"].min(), 2),
                round(recent["low"].quantile(0.1), 2)
            ],
            "resistance": [
                round(recent["high"].max(), 2),
                round(recent["high"].quantile(0.9), 2)
            ],
        }

    def trend_strength(self) -> str:
        """判断趋势：强势上涨 / 上涨 / 震荡 / 下跌 / 强势下跌"""
        ind = self.latest()
        above_count = sum([ind["above_ma5"], ind["above_ma20"], ind["above_ma60"]])
        rsi = ind["rsi"]

        if above_count == 3 and rsi > 60:
            return "强势上涨"
        if above_count >= 2:
            return "上涨"
        if above_count == 1:
            return "震荡"
        if above_count == 0 and rsi < 40:
            return "强势下跌"
        return "下跌"


# ══════════════════════════════════════════════════════════════
# 评分引擎
# ══════════════════════════════════════════════════════════════

class ScoreEngine:
    """
    多维评分，返回 0-100 总分及各维度明细
    输入：snapshot + history_result + financial_result
    """

    def __init__(self, snapshot: dict, history: dict, financial: dict):
        self.snapshot = snapshot
        self.history = history
        self.financial = financial
        self._tech: Optional[TechIndicators] = None

        if history.get("df") is not None:
            try:
                self._tech = TechIndicators(history["df"])
            except Exception as e:
                logger.warning("技术指标计算失败：%s", e)

    # ── 估值评分（30分）────────────────────────────────────────
    def _score_valuation(self) -> tuple[float, list[str]]:
        snap = self.snapshot
        pe = snap.get("pe_ttm", 0)
        pb = snap.get("pb", 0)
        reasons = []
        score = 0.0

        # PE 评分（满15分）
        if 0 < pe <= 15:
            score += 15; reasons.append(f"PE={pe:.1f} 估值偏低")
        elif 15 < pe <= 25:
            score += 12; reasons.append(f"PE={pe:.1f} 估值合理")
        elif 25 < pe <= 40:
            score += 7; reasons.append(f"PE={pe:.1f} 估值偏高")
        elif pe > 40:
            score += 2; reasons.append(f"PE={pe:.1f} 估值过高")
        else:
            reasons.append("PE数据缺失")

        # PB 评分（满15分）
        if 0 < pb <= 1.5:
            score += 15; reasons.append(f"PB={pb:.2f} 破净或低溢价")
        elif 1.5 < pb <= 3:
            score += 10; reasons.append(f"PB={pb:.2f} 溢价合理")
        elif 3 < pb <= 6:
            score += 5; reasons.append(f"PB={pb:.2f} 溢价偏高")
        else:
            score += 1; reasons.append(f"PB={pb:.2f} 溢价过高")

        return score, reasons

    # ── 技术面评分（30分）─────────────────────────────────────
    def _score_technical(self) -> tuple[float, list[str]]:
        if self._tech is None:
            return 15.0, ["技术数据不可用，给予中性分"]

        ind = self._tech.latest()
        trend = self._tech.trend_strength()
        reasons = []
        score = 0.0

        # 趋势（满12分）
        trend_scores = {"强势上涨": 12, "上涨": 9, "震荡": 5, "下跌": 2, "强势下跌": 0}
        score += trend_scores.get(trend, 5)
        reasons.append(f"趋势：{trend}")

        # RSI（满8分）
        rsi = ind["rsi"]
        if 40 <= rsi <= 70:
            score += 8; reasons.append(f"RSI={rsi} 健康区间")
        elif 30 <= rsi < 40:
            score += 6; reasons.append(f"RSI={rsi} 接近超卖")
        elif rsi < 30:
            score += 4; reasons.append(f"RSI={rsi} 超卖（可能反弹）")
        elif 70 < rsi <= 80:
            score += 4; reasons.append(f"RSI={rsi} 偏热")
        else:
            score += 1; reasons.append(f"RSI={rsi} 严重超买")

        # MACD（满5分）
        if ind["macd_bullish"] and ind["macd"] > 0:
            score += 5; reasons.append("MACD金叉且在零轴上方")
        elif ind["macd_bullish"]:
            score += 3; reasons.append("MACD向好")
        else:
            score += 1; reasons.append("MACD偏弱")

        # 量价配合（满5分）
        if ind["vol_ratio"] > 1.5 and ind["above_ma5"]:
            score += 5; reasons.append("放量上涨，量价配合")
        elif ind["vol_ratio"] > 1.0:
            score += 3; reasons.append("成交量温和放大")
        else:
            score += 1; reasons.append("成交量偏低")

        return score, reasons

    # ── 基本面评分（40分）─────────────────────────────────────
    def _score_fundamental(self) -> tuple[float, list[str]]:
        fin = self.financial
        reasons = []
        score = 0.0

        if fin.get("status") == "error":
            return 20.0, ["财务数据不可用，给予中性分"]

        # ROE（满15分）
        roe = fin.get("roe") or 0
        if roe >= 20:
            score += 15; reasons.append(f"ROE={roe:.1f}% 盈利能力强")
        elif roe >= 12:
            score += 10; reasons.append(f"ROE={roe:.1f}% 盈利能力良")
        elif roe >= 6:
            score += 5; reasons.append(f"ROE={roe:.1f}% 盈利能力一般")
        else:
            score += 1; reasons.append(f"ROE={roe:.1f}% 盈利能力弱")

        # 净利润增速（满15分）
        growth = fin.get("net_profit_growth") or 0
        if growth >= 30:
            score += 15; reasons.append(f"净利润增速={growth:.1f}% 高速增长")
        elif growth >= 15:
            score += 11; reasons.append(f"净利润增速={growth:.1f}% 稳健增长")
        elif growth >= 0:
            score += 6; reasons.append(f"净利润增速={growth:.1f}% 微增")
        else:
            score += 1; reasons.append(f"净利润增速={growth:.1f}% 下滑")

        # 毛利率（满10分）
        gm = fin.get("gross_margin") or 0
        if gm >= 50:
            score += 10; reasons.append(f"毛利率={gm:.1f}% 护城河宽")
        elif gm >= 30:
            score += 7; reasons.append(f"毛利率={gm:.1f}% 良好")
        elif gm >= 15:
            score += 4; reasons.append(f"毛利率={gm:.1f}% 一般")
        else:
            score += 1; reasons.append(f"毛利率={gm:.1f}% 偏低")

        return score, reasons

    # ── 汇总 ─────────────────────────────────────────────────
    def compute(self) -> dict:
        val_score, val_reasons = self._score_valuation()
        tech_score, tech_reasons = self._score_technical()
        fund_score, fund_reasons = self._score_fundamental()

        # 加权总分（各维度满分已内置权重）
        total = val_score + tech_score + fund_score

        # 评级
        if total >= RATING_THRESHOLDS["strong_buy"]:
            rating, action = "A+", "强烈关注"
        elif total >= RATING_THRESHOLDS["buy"]:
            rating, action = "A", "可以关注"
        elif total >= RATING_THRESHOLDS["hold"]:
            rating, action = "B", "持续观察"
        else:
            rating, action = "C", "暂时回避"

        tech_ind = self._tech.latest() if self._tech else {}
        sr = self._tech.support_resistance() if self._tech else {}
        trend = self._tech.trend_strength() if self._tech else "未知"

        return {
            "total_score": round(total, 1),
            "rating": rating,
            "action": action,
            "breakdown": {
                "valuation": {"score": round(val_score, 1), "max": 30, "reasons": val_reasons},
                "technical": {"score": round(tech_score, 1), "max": 30, "reasons": tech_reasons},
                "fundamental": {"score": round(fund_score, 1), "max": 40, "reasons": fund_reasons},
            },
            "indicators": tech_ind,
            "trend": trend,
            "support_resistance": sr,
        }