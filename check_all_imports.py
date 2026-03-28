#!/usr/bin/env python3
"""检查所有Python文件的导入问题"""
import os
import sys
import importlib.util
from pathlib import Path

def check_file_imports(filepath):
    """检查单个文件的导入"""
    try:
        # 使用importlib检查导入
        spec = importlib.util.spec_from_file_location("module", filepath)
        if spec is None:
            return False, f"无法创建spec: {filepath}"
        
        module = importlib.util.module_from_spec(spec)
        sys.modules["module"] = module
        
        # 执行导入
        spec.loader.exec_module(module)
        return True, f"✅ {os.path.basename(filepath)} 导入成功"
    except ImportError as e:
        return False, f"❌ {os.path.basename(filepath)} 导入失败: {e}"
    except SyntaxError as e:
        return False, f"❌ {os.path.basename(filepath)} 语法错误: {e}"
    except Exception as e:
        return False, f"⚠️ {os.path.basename(filepath)} 其他错误: {e}"

# 检查所有Python文件
python_files = list(Path(".").rglob("*.py"))
print(f"检查 {len(python_files)} 个Python文件...")

results = []
for pyfile in python_files:
    if "__pycache__" in str(pyfile):
        continue
    success, message = check_file_imports(pyfile)
    results.append((success, message))

print("\n导入检查结果:")
for success, message in results:
    if not success and "✅ Tushare Token" not in message:
        print(f"  {message}")

print(f"\n✅ 成功: {sum(1 for s,_ in results if s)}/{len(results)}")
print(f"❌ 失败: {sum(1 for s,_ in results if not s)}/{len(results)}")
