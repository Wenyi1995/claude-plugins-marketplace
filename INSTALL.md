# 安装指南

## 前置条件

- Claude Code CLI
- Python 3.8+
- Node.js 16+ (用于 MCP Server)

## 安装步骤

### 方式 1: 从 Marketplace 安装（推荐）

```bash
# 克隆 marketplace
git clone https://github.com/Wenyi1995/claude-plugins-marketplace.git

# 安装 sansheng-pipeline 插件
cd claude-plugins-marketplace
claude plugin install ./sansheng-pipeline
```

### 方式 2: 直接安装插件

```bash
# 克隆仓库
git clone https://github.com/Wenyi1995/claude-plugins-marketplace.git

# 复制到 Claude 插件目录
cp -r claude-plugins-marketplace/sansheng-pipeline ~/.claude/plugins/

# 安装 MCP Server 依赖
cd ~/.claude/plugins/sansheng-pipeline/mcp-server
npm install
```

## 配置

插件会自动在 `~/.claude/plugins/sansheng-pipeline/data/` 创建数据目录。

首次运行时，会初始化：
- `tasks.json` - 任务状态存储
- `audit/*.jsonl` - 审计日志

## 验证安装

```bash
# 启动 Claude Code
claude code

# 在对话中测试
/skill pipeline "测试任务：创建一个 hello.txt 文件"
```

## 卸载

```bash
rm -rf ~/.claude/plugins/sansheng-pipeline
```

## 故障排查

### MCP Server 无法启动

检查 Node.js 版本：
```bash
node --version  # 应该 >= 16.0.0
```

重新安装依赖：
```bash
cd ~/.claude/plugins/sansheng-pipeline/mcp-server
rm -rf node_modules
npm install
```

### 任务状态丢失

检查数据目录权限：
```bash
ls -la ~/.claude/plugins/sansheng-pipeline/data/
chmod -R 755 ~/.claude/plugins/sansheng-pipeline/data/
```

### Agent 无法加载

检查 plugin.json 配置：
```bash
cat ~/.claude/plugins/sansheng-pipeline/plugin.json
```

确保 `agents` 字段指向正确的目录。

## 更多帮助

- 查看 [README.md](./README.md)
- 查看插件内置文档：`~/.claude/plugins/sansheng-pipeline/README.md`
- 提交 Issue: https://github.com/Wenyi1995/claude-plugins-marketplace/issues
