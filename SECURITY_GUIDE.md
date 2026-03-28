# 🔐 毛毛AI安全使用指南

## 重要安全原则

### 1. 绝不硬编码敏感信息
```python
# ❌ 错误做法（绝对禁止！）
TUSHARE_TOKEN = "your_actual_token_here_never_commit_this"

# ✅ 正确做法
TUSHARE_TOKEN = os.environ.get('TUSHARE_TOKEN', '')
# 或从加密配置文件加载
```

### 2. 使用.gitignore保护敏感文件
```
# 必须包含在.gitignore中
*.key
*.pem
*.env
secrets.*
config.json
credentials.json
.openclaw/tushare/
.openclaw/workspace/config/
```

### 3. 加密存储敏感信息
```python
# 使用加密存储（如tushare_config.py中的Fernet加密）
from tushare_config import TushareConfig
config = TushareConfig()
token = config.load_token()  # 自动解密
```

## 安全配置步骤

### 1. 环境变量方式（推荐）
```bash
# 设置环境变量
export TUSHARE_TOKEN="你的token"

# 在Python中读取
import os
token = os.environ.get('TUSHARE_TOKEN')
```

### 2. 加密配置文件方式
```python
# 使用提供的tushare_config.py
from tushare_config import TushareConfig
config = TushareConfig()
config.save_token("你的token", "备注信息")
```

### 3. 安全检查清单
- [ ] 确保.gitignore包含所有敏感文件模式
- [ ] 检查代码中是否有硬编码的token/key
- [ ] 验证Git提交历史是否泄露敏感信息
- [ ] 设置文件权限（敏感文件600权限）

## 紧急处理

如果发现敏感信息已泄露：
1. **立即撤销泄露的token/key**
2. **生成新的token/key替换**
3. **从Git历史中清除敏感信息**
4. **通知相关方更新配置**

## 最佳实践

1. **最小权限原则**: 只给必要的权限
2. **定期轮换**: 定期更新token/key
3. **访问日志**: 监控API调用情况
4. **错误处理**: 不泄露详细错误信息

## 当前安全状态

### ✅ 已实施的安全措施
1. **配置安全**: config.py使用环境变量+加密配置双加载
2. **文件保护**: .gitignore已配置保护敏感文件
3. **加密存储**: Tushare Token使用Fernet对称加密
4. **权限控制**: 敏感文件设置600权限

### 🔍 安全验证方法
```bash
# 1. 检查是否有硬编码敏感信息
grep -r "your_actual_token" .  # 替换为你的实际token关键词

# 2. 验证.gitignore配置
cat .gitignore | grep -E "(token|key|secret|\.env)"

# 3. 检查文件权限
ls -la .openclaw/tushare/
```

### 🚨 安全警告
- **绝对不要**将包含真实token的代码提交到GitHub
- **绝对不要**在公开场合分享加密密钥
- **定期检查**Git提交历史是否意外泄露敏感信息
- **立即处理**发现的任何安全漏洞

## 开发者责任

作为开发者，您有责任：
1. **保护用户数据**: 绝不泄露任何敏感信息
2. **遵循最佳实践**: 使用行业标准的安全措施
3. **及时响应**: 快速处理发现的安全问题
4. **透明沟通**: 向用户说明安全措施和风险

## 联系方式

如发现安全问题，请立即联系项目维护者。

---
*安全第一，代码第二* 🔐