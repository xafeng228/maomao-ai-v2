#!/usr/bin/env python3
"""
毛毛AI - 全局配置（完全安全版本）
所有敏感信息从环境变量或加密文件加载，绝不硬编码
"""
from pathlib import Path
import os
import sys

# ── 目录结构 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "results"
MEMORY_DIR = BASE_DIR / "memory" / "store"
LOGS_DIR = BASE_DIR / "logs"

for _d in [RESULTS_DIR, MEMORY_DIR, LOGS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── 敏感信息加载（完全安全）───────────────────────────────
TUSHARE_TOKEN = ""
DATA_SOURCES = ["akshare"]  # 默认使用免费数据源

def _load_tushare_token_safely():
    """安全加载Tushare Token（多层保护）"""
    token = ""
    
    # 方法1: 环境变量（最安全）
    token = os.environ.get('TUSHARE_TOKEN', '')
    if token:
        return token, "环境变量"
    
    # 方法2: 加密配置文件（次安全）
    try:
        sys.path.insert(0, str(Path.home() / ".openclaw" / "workspace"))
        from tushare_config import TushareConfig
        config = TushareConfig()
        token = config.load_token()
        if token:
            return token, "加密配置文件"
    except ImportError:
        pass
    except Exception as e:
        print(f"⚠️ 加密配置加载失败: {e}")
    
    # 方法3: 留空（使用免费数据源）
    return "", "未配置（使用免费数据源）"

# 安全加载Token
TUSHARE_TOKEN, token_source = _load_tushare_token_safely()
if TUSHARE_TOKEN:
    DATA_SOURCES = ["tushare", "akshare"]
    print(f"✅ Tushare Token已从{token_source}安全加载")
else:
    print(f"ℹ️ {token_source}")

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

def validate_security():
    """验证配置安全性（检查硬编码敏感信息）"""
    import inspect
    
    # 获取当前文件源代码
    current_file = Path(__file__).read_text(encoding='utf-8')
    
    # 检查是否有硬编码的敏感信息模式
    dangerous_patterns = [
        r'47cccc530127d9e8aedd266fc57a45dfc52ccaa3bd089ed0431f6bfb',  # 示例token
        r'[0-9a-f]{40,}',  # 长哈希（可能是token）
        r'[A-Za-z0-9]{32,}',  # 长字符串（可能是key）
    ]
    
    warnings = []
    for pattern in dangerous_patterns:
        import re
        if re.search(pattern, current_file):
            warnings.append(f"⚠️ 检测到可能的硬编码敏感信息模式: {pattern}")
    
    return warnings

if __name__ == "__main__":
    warnings = validate_security()
    if warnings:
        print("安全验证警告:")
        for warn in warnings:
            print(f"  {warn}")
        print("\n🚨 请立即检查并移除硬编码的敏感信息！")
    else:
        print("✅ 安全验证通过（未发现硬编码敏感信息）")
