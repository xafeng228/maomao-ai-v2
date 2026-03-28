#!/usr/bin/env python3
"""测试smart_money.py导入"""
import sys
sys.path.insert(0, '.')

print("🧪 测试smart_money.py导入...")
try:
    from core.smart_money import SmartMoneyDetector, SectorRotation
    print("✅ 导入成功！")
    print(f"  SmartMoneyDetector: {SmartMoneyDetector}")
    print(f"  SectorRotation: {SectorRotation}")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("\n🔍 检查core/smart_money.py中的类定义...")
    import core.smart_money
    print("可用的类:", [cls for cls in dir(core.smart_money) if not cls.startswith('_')])
