#!/usr/bin/env python3
"""
毛毛AI - 全局配置
所有路径、参数集中管理，不允许在其他文件硬编码
"""
from pathlib import Path

# ── 目录结构 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "results"
MEMORY_DIR = BASE_DIR / "memory" / "store"
LOGS_DIR = BASE_DIR / "logs"

for _d in [RESULTS_DIR, MEMORY_DIR, LOGS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── 数据源优先级 ──────────────────────────────────────────
# akshare 免费；tushare / baostock 需 token，留空则跳过
DATA_SOURCES = ["akshare", "baostock"]  # 按优先级排列
TUSHARE_TOKEN = ""  # 填入 token 后自动启用

# ── 分析参数 ──────────────────────────────────────────────
ANALYSIS = {
    "history_days": 120,  # 历史数据天数
    "ma_periods": [5, 20, 60],  # 均线周期
    "rsi_period": 14,
    "request_timeout": 15,  # 网络请求超时(秒)
}

# ── 投资评分权重 ──────────────────────────────────────────
SCORE_WEIGHTS = {
    "valuation": 0.30,  # 估值
    "technical": 0.30,  # 技术面
    "fundamental": 0.40,  # 基本面
}

# ── 评级阈值 ──────────────────────────────────────────────
RATING_THRESHOLDS = {
    "strong_buy": 80,
    "buy": 65,
    "hold": 45,
    "avoid": 0,
}

# ── 合规免责声明（所有报告必须附加）────────────────────────
DISCLAIMER = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 重要免责声明
本系统输出仅供学习研究参考，不构成任何投资建议。
股市有风险，投资须谨慎。请在专业人士指导下决策。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ── 日志配置 ──────────────────────────────────────────────
LOGGING_CONFIG = {
    "level": "WARNING",
    "format": "%(levelname)s │ %(name)s │ %(message)s",
}

# ── 批量分析配置 ──────────────────────────────────────────
BATCH_CONFIG = {
    "max_concurrent": 3,  # 最大并发数
    "delay_between": 1.0,  # 请求间隔(秒)
}

# ── 调试模式 ──────────────────────────────────────────────
DEBUG = False

# ── 配置验证 ──────────────────────────────────────────────
def validate_config():
    """验证配置有效性"""
    errors = []
    
    # 检查目录可写
    for dir_name, dir_path in [
        ("RESULTS_DIR", RESULTS_DIR),
        ("MEMORY_DIR", MEMORY_DIR),
        ("LOGS_DIR", LOGS_DIR),
    ]:
        if not dir_path.exists():
            errors.append(f"{dir_name}不存在: {dir_path}")
        elif not os.access(dir_path, os.W_OK):
            errors.append(f"{dir_name}不可写: {dir_path}")
    
    # 检查权重总和为1
    weight_sum = sum(SCORE_WEIGHTS.values())
    if abs(weight_sum - 1.0) > 0.001:
        errors.append(f"评分权重总和应为1.0，实际为{weight_sum:.3f}")
    
    # 检查评级阈值顺序
    thresholds = list(RATING_THRESHOLDS.values())
    if thresholds != sorted(thresholds, reverse=True):
        errors.append("评级阈值应按降序排列")
    
    return errors

# 导入os用于验证
import os

if __name__ == "__main__":
    print("🔧 毛毛AI配置中心")
    print(f"   基础目录: {BASE_DIR}")
    print(f"   结果目录: {RESULTS_DIR}")
    print(f"   记忆目录: {MEMORY_DIR}")
    print(f"   日志目录: {LOGS_DIR}")
    print(f"   数据源: {DATA_SOURCES}")
    print(f"   分析参数: {ANALYSIS}")
    print(f"   评分权重: {SCORE_WEIGHTS}")
    
    errors = validate_config()
    if errors:
        print("\n❌ 配置错误:")
        for err in errors:
            print(f"   - {err}")
    else:
        print("\n✅ 配置验证通过")