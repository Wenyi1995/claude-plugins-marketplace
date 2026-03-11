# 三省六部 MCP Server

## 功能

提供三省审议流程的后台服务，实现：
- 中书省自动起草方案
- 门下省自动审议
- 封驳循环（最多3次）
- 信息过滤（正常不展示中间过程）

## 工具

### sansheng_review_all

自动完成三省审议流程，返回最终方案或争议裁决。

**输入**：
- `title` (string): 任务标题
- `context` (string): 任务背景和需求

**输出**：

**场景1：正常准奏（0-2次封驳后通过）**
```json
{
  "status": "approved",
  "task_id": "TASK-20260310-001",
  "summary": "方案已通过三省审议，请确认是否批准执行",
  "final_plan": "完整的方案内容...",
  "meta": {
    "versions": 1,
    "rejections": 0
  }
}
```

**场景2：升级裁决（第3次封驳）**
```json
{
  "status": "escalated",
  "task_id": "TASK-20260310-002",
  "summary": "三省意见分歧，已封驳3次，请裁决",
  "conflict": {
    "zhongshu_latest_plan": "中书省最新方案...",
    "menxia_concerns": "门下省封驳理由...",
    "rejection_history": [
      {
        "count": 1,
        "reason": "第1次封驳理由",
        "reviewer": "menxia",
        "timestamp": "2026-03-10T14:00:00"
      },
      ...
    ]
  }
}
```

## 开发

```bash
# 安装依赖
npm install

# 构建
npm run build

# 测试
npm run test

# 开发模式（启动 MCP Server）
npm run dev
```

## 部署

MCP Server 通过 Claude Code 的 `.mcp.json` 自动加载。

配置文件位置：`/Users/liweizhao/.claude/plugins/sansheng-pipeline/.mcp.json`

## 架构

```
mcp-server/
├── src/
│   ├── index.ts          # MCP Server 入口
│   ├── sansheng.ts       # 三省审议逻辑
│   ├── task-state.ts     # 任务状态管理（调用 Python）
│   ├── test-sansheng.ts  # 三省审议测试
│   └── test-task-state.ts # 状态管理测试
├── dist/
│   └── mcp-server.cjs    # 构建产物
├── package.json
├── tsconfig.json
└── README.md
```

## 状态流转

```
created → planning → reviewing → approved
                              ↓
                          rejected → planning (v2)
                              ↓
                          rejected → planning (v3)
                              ↓
                          rejected → escalated
```

## 依赖

- Node.js >= 18
- Python 3 (用于任务状态持久化)
- @modelcontextprotocol/sdk ^1.0.4
