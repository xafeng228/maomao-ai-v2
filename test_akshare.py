#!/usr/bin/env python3
"""测试akshare基础数据获取"""
import sys
try:
    import akshare as ak
    print("✅ akshare导入成功")
    
    # 测试简单数据获取
    print("测试股票列表获取...")
    try:
        df = ak.stock_info_a_code_name()
        if df is not None and not df.empty:
            print(f"✅ 获取到 {len(df)} 只A股列表")
            print(f"示例: {df.iloc[0]['code']} - {df.iloc[0]['name']}")
        else:
            print("⚠️ 股票列表为空")
    except Exception as e:
        print(f"❌ 股票列表获取失败: {e}")
        
except ImportError as e:
    print(f"❌ akshare导入失败: {e}")
    print("请运行: pip install akshare --upgrade")
