#!/usr/bin/env python3
"""直接测试akshare真实数据获取"""
import sys
import time

print("🧪 测试akshare真实数据获取...")

try:
    import akshare as ak
    print("✅ akshare导入成功")
    
    # 测试1: 股票列表
    print("\n1. 测试股票列表...")
    try:
        start = time.time()
        df = ak.stock_info_a_code_name()
        elapsed = time.time() - start
        
        if df is not None and not df.empty:
            print(f"   ✅ 成功获取 {len(df)} 只A股列表")
            print(f"   耗时: {elapsed:.2f}秒")
            print(f"   示例: {df.iloc[0]['code']} - {df.iloc[0]['name']}")
        else:
            print("   ⚠️ 股票列表为空")
    except Exception as e:
        print(f"   ❌ 股票列表失败: {str(e)[:100]}")
    
    # 测试2: 单股票资金流
    print("\n2. 测试单股票资金流...")
    try:
        start = time.time()
        df = ak.stock_individual_fund_flow(stock="600519", market="sh")
        elapsed = time.time() - start
        
        if df is not None and not df.empty:
            print(f"   ✅ 成功获取茅台资金流数据")
            print(f"   数据行数: {len(df)}")
            print(f"   耗时: {elapsed:.2f}秒")
            print(f"   最新日期: {df.iloc[-1]['日期'] if '日期' in df.columns else '未知'}")
        else:
            print("   ⚠️ 资金流数据为空")
    except Exception as e:
        print(f"   ❌ 资金流失败: {str(e)[:100]}")
        
except ImportError as e:
    print(f"❌ akshare导入失败: {e}")
