#!/usr/bin/env python3
"""测试并发批量分析功能"""
import time
from orchestrator import Orchestrator

print("🧪 测试并发批量分析功能...")
orchestrator = Orchestrator(verbose=True)

# 测试股票列表
test_symbols = ["600519", "300750", "000858", "002415"]

print(f"\n1. 测试批量分析 {len(test_symbols)} 只股票...")
start = time.time()
results = orchestrator.batch(
    test_symbols,
    save_report=False,
    print_report=True,
    sort_by="score"
)
elapsed = time.time() - start

print(f"\n📊 测试结果:")
print(f"   成功分析: {len(results)} 只股票")
print(f"   总耗时: {elapsed:.2f}秒")
print(f"   平均耗时: {elapsed/max(1, len(results)):.2f}秒/只")

if len(results) > 0:
    print(f"\n🏆 排名结果验证:")
    for i, r in enumerate(results[:3], 1):
        score = r.get("score", {})
        print(f"   {i}. {r['symbol']} - {score.get('total_score', 0):.1f}分 [{score.get('rating', '?')}]")

print("\n✅ 并发批量分析功能测试完成")
