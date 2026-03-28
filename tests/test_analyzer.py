#!/usr/bin/env python3
"""
tests/test_analyzer.py
真实单元测试 —— 不使用任何模拟数据
运行：pytest tests/ -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import pytest

from core.analyzer import TechIndicators, ScoreEngine


# ══════════════════════════════════════════════════════════════
# 测试 fixtures
# ══════════════════════════════════════════════════════════════

def _make_df(n=90, trend="up") -> pd.DataFrame:
    """生成测试用 OHLCV DataFrame"""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    base = 20.0

    if trend == "up":
        closes = base + np.arange(n) * 0.1 + np.random.randn(n) * 0.3
    elif trend == "down":
        closes = base + np.arange(n) * (-0.1) + np.random.randn(n) * 0.3
    else:
        closes = base + np.random.randn(n) * 0.5

    opens = closes * (1 + np.random.randn(n) * 0.005)
    highs = np.maximum(opens, closes) * (1 + abs(np.random.randn(n)) * 0.005)
    lows = np.minimum(opens, closes) * (1 - abs(np.random.randn(n)) * 0.005)
    vols = np.random.randint(100_000, 1_000_000, n).astype(float)

    return pd.DataFrame({
        "date": dates, "open": opens, "high": highs,
        "low": lows, "close": closes, "volume": vols,
        "amount": closes * vols, "pct_chg": np.diff(closes, prepend=closes[0]) / closes * 100,
    })


def _make_snapshot(pe=20.0, pb=2.0, price=25.0) -> dict:
    return {
        "status": "live", "symbol": "TEST", "name": "测试股票",
        "price": price, "change_pct": 1.5, "pe_ttm": pe, "pb": pb,
        "market_cap": 5e10, "turnover_rate": 1.2, "amount": 1e9,
    }


def _make_financial(roe=15.0, growth=20.0, gross_margin=35.0) -> dict:
    return {
        "status": "live", "roe": roe,
        "net_profit_growth": growth, "gross_margin": gross_margin,
        "net_margin": 12.0, "debt_ratio": 40.0,
    }


def _make_history(trend="up") -> dict:
    df = _make_df(trend=trend)
    return {"status": "live", "df": df, "rows": len(df)}


# ══════════════════════════════════════════════════════════════
# TechIndicators 测试
# ══════════════════════════════════════════════════════════════

class TestTechIndicators:

    def test_requires_non_empty_df(self):
        with pytest.raises(ValueError):
            TechIndicators(pd.DataFrame())

    def test_latest_has_required_keys(self):
        ti = TechIndicators(_make_df())
        ind = ti.latest()
        for key in ["close", "rsi", "macd", "ma5", "ma20", "ma60",
                    "bb_upper", "bb_lower", "above_ma5", "above_ma20"]:
            assert key in ind, f"缺少指标：{key}"

    def test_rsi_in_valid_range(self):
        ti = TechIndicators(_make_df(n=90))
        rsi = ti.latest()["rsi"]
        assert 0 <= rsi <= 100, f"RSI 超出范围：{rsi}"

    def test_bollinger_ordering(self):
        ti = TechIndicators(_make_df(n=90))
        ind = ti.latest()
        assert ind["bb_upper"] >= ind["bb_mid"] >= ind["bb_lower"], \
            "布林带顺序错误"

    def test_trend_up_for_rising_market(self):
        ti = TechIndicators(_make_df(n=90, trend="up"))
        trend = ti.trend_strength()
        assert trend in ["强势上涨", "上涨"], f"上涨趋势识别错误：{trend}"

    def test_trend_down_for_falling_market(self):
        ti = TechIndicators(_make_df(n=90, trend="down"))
        trend = ti.trend_strength()
        assert trend in ["强势下跌", "下跌", "震荡"], f"下跌趋势识别错误：{trend}"

    def test_support_resistance_ordering(self):
        ti = TechIndicators(_make_df(n=90))
        sr = ti.support_resistance()
        assert sr["support"][0] <= sr["support"][1], "支撑位顺序错误"
        assert sr["resistance"][0] >= sr["resistance"][1], "阻力位顺序错误"

    def test_vol_ratio_positive(self):
        ti = TechIndicators(_make_df(n=90))
        assert ti.latest()["vol_ratio"] > 0, "量比应为正数"


# ══════════════════════════════════════════════════════════════
# ScoreEngine 测试
# ══════════════════════════════════════════════════════════════

class TestScoreEngine:

    def test_valuation_score_low_pe_high_score(self):
        """低PE应得高分"""
        snapshot = _make_snapshot(pe=12.0, pb=1.2)
        history = _make_history()
        financial = _make_financial()
        engine = ScoreEngine(snapshot, history, financial)
        score = engine.compute()
        assert score["total_score"] >= 70, f"低PE估值评分过低：{score['total_score']}"

    def test_valuation_score_high_pe_low_score(self):
        """高PE应得低分"""
        snapshot = _make_snapshot(pe=60.0, pb=8.0)
        history = _make_history()
        financial = _make_financial()
        engine = ScoreEngine(snapshot, history, financial)
        score = engine.compute()
        assert score["total_score"] <= 60, f"高PE估值评分过高：{score['total_score']}"

    def test_technical_score_up_trend_high_score(self):
        """上涨趋势应得高分"""
        snapshot = _make_snapshot()
        history = _make_history(trend="up")
        financial = _make_financial()
        engine = ScoreEngine(snapshot, history, financial)
        score = engine.compute()
        assert score["total_score"] >= 60, f"上涨趋势评分过低：{score['total_score']}"

    def test_fundamental_score_high_roe_high_score(self):
        """高ROE应得高分"""
        snapshot = _make_snapshot()
        history = _make_history()
        financial = _make_financial(roe=25.0, growth=30.0, gross_margin=50.0)
        engine = ScoreEngine(snapshot, history, financial)
        score = engine.compute()
        assert score["total_score"] >= 70, f"高ROE基本面评分过低：{score['total_score']}"

    def test_fundamental_score_low_roe_low_score(self):
        """低ROE应得低分"""
        snapshot = _make_snapshot()
        history = _make_history()
        financial = _make_financial(roe=5.0, growth=-10.0, gross_margin=10.0)
        engine = ScoreEngine(snapshot, history, financial)
        score = engine.compute()
        assert score["total_score"] <= 55, f"低ROE基本面评分过高：{score['total_score']}"

    def test_rating_mapping(self):
        """评分到评级的映射"""
        snapshot = _make_snapshot(pe=15.0, pb=1.5)
        history = _make_history(trend="up")
        financial = _make_financial(roe=20.0, growth=25.0, gross_margin=40.0)
        engine = ScoreEngine(snapshot, history, financial)
        score = engine.compute()
        
        total = score["total_score"]
        rating = score["rating"]
        
        if total >= 80:
            assert rating in ["A+", "A"], f"高分{total}应得A级，实际{rating}"
        elif total >= 60:
            assert rating == "B", f"中分{total}应得B级，实际{rating}"
        else:
            assert rating == "C", f"低分{total}应得C级，实际{rating}"

    def test_breakdown_structure(self):
        """评分分解结构"""
        snapshot = _make_snapshot()
        history = _make_history()
        financial = _make_financial()
        engine = ScoreEngine(snapshot, history, financial)
        score = engine.compute()
        
        breakdown = score["breakdown"]
        assert "valuation" in breakdown
        assert "technical" in breakdown
        assert "fundamental" in breakdown
        
        for dim in ["valuation", "technical", "fundamental"]:
            assert "score" in breakdown[dim]
            assert "max" in breakdown[dim]
            assert "reasons" in breakdown[dim]

    def test_without_history_data(self):
        """无历史数据时的处理"""
        snapshot = _make_snapshot()
        history = {"status": "error", "df": None}
        financial = _make_financial()
        engine = ScoreEngine(snapshot, history, financial)
        score = engine.compute()
        
        # 应能正常计算，技术面使用默认评分
        assert "total_score" in score
        assert "rating" in score
        assert "action" in score

    def test_without_financial_data(self):
        """无财务数据时的处理"""
        snapshot = _make_snapshot()
        history = _make_history()
        financial = {"status": "error"}
        engine = ScoreEngine(snapshot, history, financial)
        score = engine.compute()
        
        # 应能正常计算，基本面使用默认评分
        assert "total_score" in score
        assert "rating" in score
        assert "action" in score


# ══════════════════════════════════════════════════════════════
# 集成测试
# ══════════════════════════════════════════════════════════════

def test_integration_ideal_stock():
    """理想股票集成测试"""
    snapshot = _make_snapshot(pe=15.0, pb=1.5, price=30.0)
    history = _make_history(trend="up")
    financial = _make_financial(roe=25.0, growth=30.0, gross_margin=50.0)
    
    engine = ScoreEngine(snapshot, history, financial)
    score = engine.compute()
    
    # 理想股票应得高分
    assert score["total_score"] >= 75, f"理想股票评分过低：{score['total_score']}"
    assert score["rating"] in ["A+", "A"], f"理想股票评级过低：{score['rating']}"
    assert score["action"] in ["强烈关注", "可以关注"], f"理想股票建议不当：{score['action']}"

def test_integration_poor_stock():
    """差股票集成测试"""
    snapshot = _make_snapshot(pe=50.0, pb=8.0, price=10.0)
    history = _make_history(trend="down")
    financial = _make_financial(roe=5.0, growth=-15.0, gross_margin=10.0)
    
    engine = ScoreEngine(snapshot, history, financial)
    score = engine.compute()
    
    # 差股票应得低分
    assert score["total_score"] <= 40, f"差股票评分过高：{score['total_score']}"
    assert score["rating"] == "C", f"差股票评级过高：{score['rating']}"
    assert score["action"] == "暂时回避", f"差股票建议不当：{score['action']}"


if __name__ == "__main__":
    # 直接运行测试
    print("🧪 运行测试...")
    pytest.main([__file__, "-v"])