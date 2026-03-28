#!/usr/bin/env python3
"""测试缓存清理功能"""
import time
from core.data_fetcher import DataFetcher

print("🧪 测试缓存清理功能...")
fetcher = DataFetcher()

print("1. 获取缓存统计信息...")
stats = fetcher.get_cache_stats()
print(f"   缓存配置: TTL={stats['ttl_seconds']}秒, 最大大小={stats['max_size']}")
print(f"   当前状态: 总数={stats['total_items']}, 过期={stats['expired_items']}, 最近={stats['recent_items']}")

print("\n2. 测试缓存清理机制...")
# 模拟添加大量缓存
print("   模拟添加缓存项...")
for i in range(150):  # 超过最大大小
    cache_key = f"test_cache_{i}"
    fetcher._cache[cache_key] = (time.time() - 1000, {"data": f"test_{i}"})  # 旧的缓存

print(f"   添加后缓存大小: {len(fetcher._cache)}")

print("\n3. 触发缓存清理...")
fetcher._clean_cache_if_needed()
fetcher._clean_expired_cache()

print(f"   清理后缓存大小: {len(fetcher._cache)}")

print("\n4. 测试清空缓存...")
fetcher.clear_cache()
stats = fetcher.get_cache_stats()
print(f"   清空后缓存大小: {stats['total_items']}")

print("\n✅ 缓存清理功能测试完成")
