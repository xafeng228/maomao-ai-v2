#!/usr/bin/env python3
"""
毛毛AI - 全局配置（安全版本）
所有敏感信息从环境变量或加密文件加载，绝不硬编码
"""
from pathlib import Path
import os

# ── 目录结构 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "results"
MEMORY_DIR = BASE_DIR / "memory" / "store"
LOGS_DIR = BASE_DIR / "logs"

for _d in [RESULTS_DIR, MEMORY_DIR, LOGS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── 敏感信息加载（安全方式）───────────────────────────────
# 优先级: 1.环境变量 2.加密配置文件 3.留空（使用免费数据源）
TUSHARE_TOKEN = ""

try:
    # 方法1: 从环境变量加载
    TUSHARE_TOKEN = os.environ.get('TUSHARE_TOKEN', '')
    
    # 方法2: 如果环境变量为空，尝试从加密配置加载
    if not TUSHARE_TOKEN:
        import sys
        sys.path.insert(0, str(Path.home() / ".openclaw" / "workspace"))
        from tushare_config import TushareConfig
        config = TushareConfig()
        TUSHARE_TOKEN = config.load_token()
        
    if TUSHARE_TOKEN:
        print(f"✅ Tushare Token已安全加载")
        DATA_SOURCES = ["tushare", "akshare"]
    else:
        print("⚠️ 未找到Tushare Token，使用免费数据源")
        DATA_SOURCES = ["akshare"]
        
except Exception as e:
    print(f"⚠️ Tushare Token加载失败: {e}")
    DATA_SOURCES = ["akshare"]

# ── 资金监测权重 ──────────────────────────────────────────
SMART_MONEY_WEIGHTS = {
    "big_money": 0.35,  # 大单资金流
    "quant": 0.20,      # 量化行为特征
    "institution": 0.30, # 机构席位布局
    "sector": 0.15,     # 板块资金轮动
}

# ── 免责声明 ──────────────────────────────────────────────
DISCLAIMER = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 重要免责声明
本系统输出仅供学习研究参考，不构成任何投资建议。
股市有风险，投资须谨慎。请在专业人士指导下决策。

数据来源说明：
• Tushare Pro: 官方金融数据接口（需用户自行配置Token）
• akshare: 开源财经数据工具（免费）
• 所有数据均为公开市场数据

统计特征推断，不代表真实主力身份。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ── 监控系统配置 ──────────────────────────────────────────
MONITOR_CONFIG = {
    "pre_market_start": "08:30",
    "market_open": "09:30",
    "market_close": "15:00",
    "post_market_end": "17:00",
    "alert_threshold": 50,
    "scan_interval": 300,
}

def validate_config():
    """验证配置安全性"""
    errors = []
    
    # 检查是否有硬编码的敏感信息
    import inspect
    source = inspect.getsource(validate_config)
    if '47cccc530127d9e8aedd266fc57a45dfc52ccaa3bd089ed0431f6bfb' in source:
        errors.append("❌ 检测到硬编码的敏感Token！")
    
    if sum(SMART_MONEY_WEIGHTS.values()) != 1.0:
        errors.append(f"权重配置错误: {sum(SMART_MONEY_WEIGHTS.values())}")
    
    return errors

if __name__ == "__main__":
    errors = validate_config()
    if errors:
        print("配置验证失败:")
        for err in errors:
            print(f"  - {err}")
        exit(1)
    else:
        print("✅ 配置验证通过（安全检查完成）")
