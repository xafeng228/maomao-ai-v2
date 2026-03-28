#!/bin/bash
# 毛毛AI投研助手 - 自动Git备份脚本
# 每日自动提交代码变更到GitHub作为备份

set -e

echo "🔧 开始自动Git备份..."
echo "备份时间: $(date)"

cd /root/maomao-ai-release

# 检查是否有变更
if git diff --quiet && git diff --cached --quiet; then
    echo "✅ 无代码变更，跳过备份"
    exit 0
fi

# 添加所有变更
echo "📁 添加变更文件..."
git add .

# 创建备份提交
BACKUP_MSG="备份: $(date +%Y-%m-%d_%H%M%S) 系统状态备份"
echo "📝 创建备份提交: $BACKUP_MSG"
git commit -m "$BACKUP_MSG" --allow-empty

# 推送到远程仓库
echo "📡 推送到GitHub..."
git push origin main

# 验证备份成功
if [ $? -eq 0 ]; then
    echo "✅ 自动备份成功完成"
    echo "提交哈希: $(git rev-parse --short HEAD)"
else
    echo "❌ 备份失败，请检查网络连接"
    exit 1
fi

echo ""
echo "📊 备份统计:"
echo "• 备份时间: $(date)"
echo "• 提交信息: $BACKUP_MSG"
echo "• 远程仓库: origin/main"
echo "• 备份状态: ✅ 成功"
