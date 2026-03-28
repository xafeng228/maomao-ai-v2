#!/usr/bin/env python3
"""测试data_fetcher缓存功能"""
import time
from core.data_fetcher import DataFetcher

print("🧪 测试data_fetcher缓存功能...")
fetcher = DataFetcher()

# 第一次获取（应该从网络）
print("1. 第一次获取600519...")
start = time.time()
result1 = fetcher.get_snapshot("600519")
elapsed1 = time.time() - start
print(f"   耗时: {elapsed1:.2f}秒")
print(f"   状态: {result1.get('status')}")
print(f"   来源: {result1.get('source')}")

# 第二次获取（应该从缓存）
print("\n2. 第二次获取600519（应命中缓存）...")
start = time.time()
result2 = fetcher.get_snapshot("600519")
elapsed2 = time.time() - start
print(f"   耗时: {elapsed2:.4f}秒")
print(f"   状态: {result2.get('status')}")
print(f"   来源: {result2.get('source')}")

# 验证缓存效果
if elapsed2 < elapsed1 * 0.1:  # 缓存应该快10倍以上
    print("\n✅ 缓存功能正常：缓存命中速度提升明显")
else:
    print("\n⚠️ 缓存效果不明显，需要进一步优化")

# 测试不同股票
print("\n3. 测试不同股票300750...")
result3 = fetcher.get_snapshot("300750")
print(f"   状态: {result3.get('status')}")

print("\n🎯 缓存测试完成")
