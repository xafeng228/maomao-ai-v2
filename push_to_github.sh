#!/bin/bash
# 毛毛AI投研助手 v2.0 GitHub推送脚本
# 使用方法: bash push_to_github.sh YOUR_GITHUB_USERNAME

set -e  # 遇到错误立即退出

echo "🚀 毛毛AI投研助手 v2.0 GitHub推送脚本"
echo "="*70

# 检查参数
if [ -z "$1" ]; then
    echo "❌ 错误: 请提供GitHub用户名"
    echo "使用方法: bash push_to_github.sh YOUR_GITHUB_USERNAME"
    exit 1
fi

GITHUB_USERNAME="$1"
REPO_NAME="maomao-ai-v2"
REPO_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

echo "📊 推送配置:"
echo "  GitHub用户名: ${GITHUB_USERNAME}"
echo "  仓库名称: ${REPO_NAME}"
echo "  仓库URL: ${REPO_URL}"
echo ""

# 检查是否在项目目录
if [ ! -f "main.py" ] || [ ! -f "README.md" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

echo "1. 🔍 检查项目状态..."
echo "   文件数量: $(find . -name "*.py" -type f | wc -l) 个Python文件"
echo "   代码行数: $(find . -name "*.py" -type f -exec wc -l {} + | tail -1 | awk '{print $1}') 行"
echo "   测试状态: $(python3 -m pytest tests/ -v 2>&1 | grep -E "passed|failed" | tail -1)"
echo ""

echo "2. 📦 配置Git远程仓库..."
# 移除现有的远程仓库（如果有）
git remote remove origin 2>/dev/null || true

# 添加新的远程仓库
git remote add origin "${REPO_URL}"

echo "   远程仓库已配置: ${REPO_URL}"
echo ""

echo "3. 🚀 推送代码到GitHub..."
echo "   推送主分支..."
git push -u origin main

echo "   推送版本标签..."
git push origin v2.0.0

echo ""
echo "4. ✅ 推送完成！"
echo ""
echo "📋 下一步操作:"
echo ""
echo "🔗 访问您的GitHub仓库:"
echo "   https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
echo ""
echo "🎯 创建Release:"
echo "   1. 点击 'Releases'"
echo "   2. 点击 'Create a new release'"
echo "   3. 版本: v2.0.0"
echo "   4. 标题: '毛毛AI投研助手 v2.0.0'"
echo "   5. 描述: 使用 GITHUB_SETUP.md 中的发布说明"
echo "   6. 点击 'Publish release'"
echo ""
echo "📊 项目信息:"
echo "   • 版本: v2.0.0"
echo "   • 提交: $(git log --oneline -1 | cut -d' ' -f1)"
echo "   • 文件: $(find . -type f | wc -l) 个文件"
echo "   • 大小: $(du -sh . | cut -f1)"
echo ""
echo "🎉 毛毛AI投研助手 v2.0 已成功发布到GitHub！"
echo "="*70