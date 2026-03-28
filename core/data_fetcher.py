from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from config import ANALYSIS, DATA_SOURCES, CACHE_CONFIG

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════════════

def _safe_float(val, default: float = 0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _today() -> str:
    return datetime.today().strftime("%Y%m%d")


def _n_days_ago(n: int) -> str:
    return (datetime.today() - timedelta(days=n)).strftime("%Y%m%d")


# ══════════════════════════════════════════════════════════════
# 主类
# ══════════════════════════════════════════════════════════════

class DataFetcher:
    """
    统一数据获取器
    用法：
    fetcher = DataFetcher()
    snapshot = fetcher.get_snapshot("600519") # 茅台实时快照
    history = fetcher.get_history("600519") # 历史 K 线
    info = fetcher.get_company_info("600519")
    """

    def __init__(self):
        self._check_dependencies()
        # 缓存初始化
        self._cache = {}
        self._cache_ttl = CACHE_CONFIG.get("ttl_seconds", 300)  # 默认5分钟
        self._max_cache_size = CACHE_CONFIG.get("max_size", 100)  # 最大缓存条目数
        self._cache_enabled = CACHE_CONFIG.get("enabled", True)

    # ── 依赖检查 ──────────────────────────────────────────────
    def _check_dependencies(self):
        missing = []
        try:
            import akshare  # noqa: F401
        except ImportError:
            missing.append("akshare")
        try:
            import baostock  # noqa: F401
        except ImportError:
            missing.append("baostock (可选)")

        if "akshare" in missing:
            raise ImportError(
                "缺少核心依赖 akshare，请执行：pip install akshare"
            )
        if missing:
            logger.warning("可选依赖未安装：%s", missing)

    # ── 缓存管理方法 ──────────────────────────────────────────────
    def _clean_cache_if_needed(self):
        """清理缓存，如果超过最大大小"""
        if len(self._cache) <= self._max_cache_size:
            return
        
        logger.debug("[缓存清理] 当前大小: %d，最大限制: %d", 
                    len(self._cache), self._max_cache_size)
        
        # 按时间戳排序，删除最旧的缓存
        items = list(self._cache.items())
        items.sort(key=lambda x: x[1][0])  # 按时间戳排序
        
        # 删除超过限制的部分（保留最新的max_size个）
        to_remove = len(items) - self._max_cache_size
        for i in range(to_remove):
            key, _ = items[i]
            del self._cache[key]
        
        logger.debug("[缓存清理] 已删除 %d 个旧缓存项", to_remove)
    
    def _clean_expired_cache(self):
        """清理过期的缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, (timestamp, _) in self._cache.items():
            if current_time - timestamp > self._cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug("[缓存清理] 已清理 %d 个过期缓存项", len(expired_keys))
    
    def clear_cache(self):
        """清空所有缓存"""
        cache_size = len(self._cache)
        self._cache.clear()
        logger.info("[缓存清理] 已清空所有缓存，共 %d 项", cache_size)
    
    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        current_time = time.time()
        expired_count = 0
        recent_count = 0
        
        for _, (timestamp, _) in self._cache.items():
            if current_time - timestamp > self._cache_ttl:
                expired_count += 1
            elif current_time - timestamp < 60:  # 最近1分钟
                recent_count += 1
        
        return {
            "total_items": len(self._cache),
            "expired_items": expired_count,
            "recent_items": recent_count,
            "max_size": self._max_cache_size,
            "ttl_seconds": self._cache_ttl,
            "enabled": self._cache_enabled,
        }

    # ══════════════════════════════════════════════════════════
    # 公开 API
    # ══════════════════════════════════════════════════════════

    def get_snapshot(self, symbol: str) -> dict:
        """
        获取单只股票实时快照
        返回：price / change_pct / volume / turnover / pe / pb / market_cap
        """
        if not self._cache_enabled:
            # 直接获取数据，不使用缓存
            return self._snapshot_akshare(symbol) if DATA_SOURCES[0] == "akshare" else self._snapshot_baostock(symbol)

        # 检查缓存
        cache_key = f"snapshot_{symbol}"
        if cache_key in self._cache:
            ts, data = self._cache[cache_key]
            if time.time() - ts < self._cache_ttl:
                logger.debug("[缓存命中] %s", symbol)
                return data

        # 清理过期缓存
        self._clean_expired_cache()
        
        # 检查缓存大小，必要时清理
        self._clean_cache_if_needed()

        # 多数据源尝试
        for source in DATA_SOURCES:
            try:
                if source == "akshare":
                    result = self._snapshot_akshare(symbol)
                elif source == "baostock":
                    result = self._snapshot_baostock(symbol)
                else:
                    continue
                
                # 仅缓存成功数据
                if result.get("status") == "live":
                    self._cache[cache_key] = (time.time(), result)
                    logger.debug("[缓存保存] %s → %s", symbol, source)
                
                return result
            except Exception as e:
                logger.warning("[%s] 快照失败 %s: %s", source, symbol, e)

        return {"status": "error", "symbol": symbol, "message": "所有数据源均失败"}

    def get_history(self, symbol: str, days: int = None) -> dict:
        """
        获取历史 K 线（日线）
        返回：DataFrame 含 date/open/high/low/close/volume/amount/pct_chg
        """
        days = days or ANALYSIS["history_days"]
        
        if not self._cache_enabled:
            # 直接获取数据，不使用缓存
            return self._history_akshare(symbol, days) if DATA_SOURCES[0] == "akshare" else self._history_baostock(symbol, days)

        # 检查缓存
        cache_key = f"history_{symbol}_{days}"
        if cache_key in self._cache:
            ts, data = self._cache[cache_key]
            if time.time() - ts < self._cache_ttl:
                logger.debug("[缓存命中] %s %d天历史", symbol, days)
                return data

        # 清理过期缓存
        self._clean_expired_cache()
        
        # 检查缓存大小，必要时清理
        self._clean_cache_if_needed()

        for source in DATA_SOURCES:
            try:
                if source == "akshare":
                    result = self._history_akshare(symbol, days)
                elif source == "baostock":
                    result = self._history_baostock(symbol, days)
                else:
                    continue
                
                # 仅缓存成功数据
                if result.get("status") == "live":
                    self._cache[cache_key] = (time.time(), result)
                    logger.debug("[缓存保存] %s %d天历史 → %s", symbol, days, source)
                
                return result
            except Exception as e:
                logger.warning("[%s] 历史数据失败 %s: %s", source, symbol, e)

        return {"status": "error", "symbol": symbol, "df": None}

    def get_company_info(self, symbol: str) -> dict:
        """获取公司基本信息"""
        try:
            return self._company_info_akshare(symbol)
        except Exception as e:
            logger.warning("公司信息获取失败 %s: %s", symbol, e)
            return {"status": "error", "symbol": symbol}

    def get_financial(self, symbol: str) -> dict:
        """获取最新财务指标（ROE / 净利润增速 / 毛利率等）"""
        try:
            return self._financial_akshare(symbol)
        except Exception as e:
            logger.warning("财务数据获取失败 %s: %s", symbol, e)
            return {"status": "error", "symbol": symbol}

    # ══════════════════════════════════════════════════════════
    # akshare 实现
    # ══════════════════════════════════════════════════════════

    def _snapshot_akshare(self, symbol: str) -> dict:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == symbol]
        if row.empty:
            raise ValueError(f"股票代码不存在：{symbol}")
        r = row.iloc[0]

        return {
            "status": "live",
            "source": "akshare",
            "symbol": symbol,
            "name": r.get("名称", ""),
            "price": _safe_float(r.get("最新价")),
            "change": _safe_float(r.get("涨跌额")),
            "change_pct": _safe_float(r.get("涨跌幅")),
            "open": _safe_float(r.get("今开")),
            "high": _safe_float(r.get("最高")),
            "low": _safe_float(r.get("最低")),
            "prev_close": _safe_float(r.get("昨收")),
            "volume": _safe_float(r.get("成交量")),  # 手
            "amount": _safe_float(r.get("成交额")),  # 元
            "turnover_rate": _safe_float(r.get("换手率")),
            "pe_ttm": _safe_float(r.get("市盈率-动态")),
            "pb": _safe_float(r.get("市净率")),
            "market_cap": _safe_float(r.get("总市值")),  # 元
            "float_cap": _safe_float(r.get("流通市值")),
            "timestamp": datetime.now().isoformat(),
        }

    def _history_akshare(self, symbol: str, days: int) -> dict:
        import akshare as ak

        start = _n_days_ago(days)
        end = _today()

        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start,
            end_date=end,
            adjust="qfq",  # 前复权
        )
        if df is None or df.empty:
            raise ValueError(f"无历史数据：{symbol}")

        # 统一列名
        df = df.rename(columns={
            "日期": "date", "开盘": "open", "收盘": "close",
            "最高": "high", "最低": "low", "成交量": "volume",
            "成交额": "amount", "涨跌幅": "pct_chg",
        })
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        return {
            "status": "live",
            "source": "akshare",
            "symbol": symbol,
            "df": df,
            "rows": len(df),
            "start": str(df["date"].iloc[0].date()),
            "end": str(df["date"].iloc[-1].date()),
        }

    def _company_info_akshare(self, symbol: str) -> dict:
        import akshare as ak

        df = ak.stock_individual_info_em(symbol=symbol)
        info = dict(zip(df.iloc[:, 0], df.iloc[:, 1]))

        return {
            "status": "live",
            "source": "akshare",
            "symbol": symbol,
            "name": info.get("股票简称", ""),
            "industry": info.get("行业", ""),
            "listing_date": info.get("上市时间", ""),
            "total_shares": info.get("总股本", ""),
            "float_shares": info.get("流通股", ""),
            "raw": info,
        }

    def _financial_akshare(self, symbol: str) -> dict:
        import akshare as ak

        df = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按年度")
        if df is None or df.empty:
            raise ValueError(f"无财务数据：{symbol}")

        latest = df.iloc[0]

        def _get(col_candidates):
            for c in col_candidates:
                if c in latest.index:
                    return _safe_float(latest[c])
            return None

        return {
            "status": "live",
            "source": "akshare",
            "symbol": symbol,
            "report_date": str(latest.get("报告期", "")),
            "roe": _get(["净资产收益率", "ROE"]),
            "net_profit_growth": _get(["净利润同比增长率", "净利润增长率"]),
            "gross_margin": _get(["毛利率"]),
            "net_margin": _get(["净利率"]),
            "debt_ratio": _get(["资产负债率"]),
            "raw_row": latest.to_dict(),
        }

    # ══════════════════════════════════════════════════════════
    # baostock 备用实现（历史数据）
    # ══════════════════════════════════════════════════════════

    def _snapshot_baostock(self, symbol: str) -> dict:
        """baostock 不支持实时行情，抛出让上层 fallback"""
        raise NotImplementedError("baostock 不支持实时快照")

    def _history_baostock(self, symbol: str, days: int) -> dict:
        import baostock as bs
        # 格式转换：600519 → sh.600519 / 300750 → sz.300750
        prefix = "sh" if symbol.startswith("6") else "sz"
        bs_code = f"{prefix}.{symbol}"

        lg = bs.login()
        if lg.error_code != "0":
            raise ConnectionError(f"baostock 登录失败：{lg.error_msg}")

        try:
            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,volume,amount,pctChg",
                start_date=_n_days_ago(days),
                end_date=_today(),
                frequency="d",
                adjustflag="2",
            )
            rows = []
            while rs.error_code == "0" and rs.next():
                rows.append(rs.get_row_data())

            df = pd.DataFrame(rows, columns=rs.fields)
            for col in ["open", "high", "low", "close", "volume", "amount", "pctChg"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df.rename(columns={"pctChg": "pct_chg"})
            df["date"] = pd.to_datetime(df["date"])

            return {
                "status": "live",
                "source": "baostock",
                "symbol": symbol,
                "df": df,
                "rows": len(df),
            }
        finally:
            bs.logout()
