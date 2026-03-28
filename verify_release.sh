#!/bin/bash
# 毛毛AI v2.0 发布验证脚本

echo "🔍 毛毛AI v2.0 发布验证"
echo "="*70

echo "1. 📁 项目结构验证..."
find . -name "*.py" -type f | wc -l | xargs echo "   Python文件数量:"
find . -type f | wc -l | xargs echo "   总文件数量:"

echo ""
echo "2. 🧪 单元测试验证..."
python3 -m pytest tests/ -v 2>&1 | tail -5

echo ""
echo "3. 📦 依赖检查..."
pip list | grep -E "akshare|baostock|pandas|numpy|pytest" || echo "   依赖未安装，请运行: pip install -r requirements.txt"

echo ""
echo "4. 🚀 功能验证..."
python3 main.py --help 2>&1 | head -20

echo ""
echo "5. 📄 文档检查..."
ls -la README.md GITHUB_SETUP.md RELEASE_GUIDE.md 2>/dev/null | awk '{print "   "$9" - "$5" bytes"}'

echo ""
echo "✅ 验证完成"
echo "="*70
