---
# 三省审议流水线

启动司礼监协调的完整审议流程：中书省规划 → 门下省审议 → 用户确认 → 执行

## 触发条件

当用户任务满足以下任一条件时，建议使用此 skill：

1. **复杂度高**：涉及多个模块、多个步骤、跨领域协作
2. **需要审查**：方案质量要求高，不能一次定稿
3. **风险较大**：涉及数据库变更、架构调整、生产环境操作
4. **用户明确要求**："走完整流程"、"需要审议"、"让三省处理"

## 不适用场景

- 简单的单文件修改
- 已经有明确方案，只需执行
- 紧急 bug 修复（流程太长）

---

## 工作流程概览

```
用户 → 司礼监(整理背景) → 中书省(起草方案) → 门下省(审议)
         ↓                                        ↓
       [循环最多2次封驳]  ←───────────────────── 封驳
         ↓
       [第3次封驳 → 用户裁决]
         ↓
       准奏 → 用户确认 → 执行(v0.2待实现) → 回报
```

**预计耗时**：10-30 分钟（取决于方案复杂度和封驳次数）

---

## 工作流程详解

### Phase 1: 创建任务

使用 MCP tool 创建任务：

```
sansheng_create_task({
  title: "任务标题",
  context: "任务背景和需求..."
})
→ 返回 task_id: "TASK-20260311-XXX"
```

### Phase 2: 中书省起草方案

调用中书省 Agent：

```
Agent({
  subagent_type: "sansheng-pipeline:zhongshu:SOUL",
  description: "中书省起草方案",
  prompt: `
## 中书省任务
任务 ID: ${task_id}
背景：${context}

请根据上述背景起草执行方案，包含：
1. 任务背景
2. 实施方案（5个步骤）
3. 风险评估
4. 验收标准

完成后调用 MCP tool：
sansheng_submit_plan({
  task_id: "${task_id}",
  plan: "你生成的方案内容"
})
  `
})
```

### Phase 3: 门下省审议

调用门下省 Agent：

```
Agent({
  subagent_type: "sansheng-pipeline:menxia:SOUL",
  description: "门下省审议方案",
  prompt: `
## 门下省任务
任务 ID: ${task_id}

请审议中书省提交的方案：
1. 调用 sansheng_get_task({ task_id: "${task_id}" }) 获取方案
2. 根据审议标准检查方案质量
3. 调用 sansheng_submit_decision 提交决策

审议标准：
- 第1次审议：检查风险评估
- 第2次审议：检查验收标准
- 第3次审议：建议升级司礼监裁决
  `
})
```

### Phase 4: 处理封驳循环

如果门下省封驳（decision = "rejected"）：

1. 提取封驳理由
2. 将封驳理由添加到 context 中，格式：
   ```
   {原始context}

   【门下省封驳意见】
   {rejection_reason}
   ```
3. 回到 Phase 2，重新调用中书省 Agent

### Phase 5: 准奏后用户确认

如果门下省准奏（decision = "approved"）：

1. 向用户展示最终方案
2. 等待用户批准
3. 用户批准后调用：
   ```
   sansheng_finalize({
     task_id: "${task_id}",
     decision: "approve_zhongshu"
   })
   ```

### Phase 6: 升级司礼监裁决

如果第3次封驳（rejection_count >= 3）：

1. 向用户说明情况
2. 展示中书省最新方案和门下省意见
3. 请用户裁决：
   - 批准中书省方案：`decision: "approve_zhongshu"`
   - 采纳门下省意见：`decision: "approve_menxia"`
   - 自定义方案：`decision: "custom", custom_plan: "..."`

---

## 使用方式

### 方式 1: 直接调用（推荐）

在对话中直接说：
```
/pipeline 任务描述...
```

或
```
帮我走三省审议流程：[任务描述]
```

### 方式 2: 通过司礼监 Agent

如果已配置司礼监 agent：
```
@silijian 请启动审议流程：[任务描述]
```

---

## 可用 MCP Tools

本 skill 使用以下 MCP tools 进行状态管理：

### 1. sansheng_create_task

创建新任务，返回任务 ID。

**输入**：
- `title`: 任务标题
- `context`: 任务背景和需求

**输出**：
```json
{
  "task_id": "TASK-20260311-XXX"
}
```

### 2. sansheng_submit_plan

中书省提交方案版本（由中书省 Agent 调用）。

**输入**：
- `task_id`: 任务 ID
- `plan`: 方案内容

**输出**：
```json
{
  "version": 1,
  "task_id": "TASK-20260311-XXX"
}
```

### 3. sansheng_submit_decision

门下省提交审议决策（由门下省 Agent 调用）。

**输入**：
- `task_id`: 任务 ID
- `decision`: "approved" 或 "rejected"
- `reason`: 封驳理由（仅 rejected 时需要）

**输出**：
```json
{
  "decision": "rejected",
  "reason": "...",
  "rejection_count": 1,
  "escalated": false
}
```

### 4. sansheng_get_task

查询任务状态和历史（由门下省 Agent 调用）。

**输入**：
- `task_id`: 任务 ID

**输出**：完整任务对象，包含状态历史、方案版本、封驳记录。

### 5. sansheng_finalize

用户批准方案，进入执行阶段。

**输入**：
- `task_id`: 任务 ID
- `decision`: "approve_zhongshu" / "approve_menxia" / "custom"
- `custom_plan`: 自定义方案内容（仅 custom 时需要）

**输出**：
```json
{
  "success": true,
  "final_state": "done",
  "message": "圣上批准方案，任务进入执行阶段"
}
```

---

## 输出产物

- **任务记录**：完整的版本历史、封驳记录、审议结论
- **最终方案**：经过三省审议、用户批准的执行方案
- **审计日志**：所有状态变更、handoff 记录可追溯

数据存储位置：
```
~/.claude/plugins/sansheng-pipeline/data/tasks.json
```

---

## 示例场景

### 场景 1: 数据库架构调整

**用户输入**：
```
我们需要给 users 表增加一个 role 字段，支持多角色用户。
要考虑数据迁移和权限系统的适配。
```

**流程**：
1. 创建任务：`sansheng_create_task()` 生成 task_id
2. 司礼监收集信息：当前表结构、用户量、权限系统实现
3. 中书省起草：调用 Agent 生成迁移方案 + 权限适配 + 回滚步骤
4. 门下省审议：调用 Agent 检查迁移脚本、评估风险
5. 用户确认：`sansheng_finalize()` 定稿
6. 产出：可执行的迁移方案

---

### 场景 2: 性能优化方案

**用户输入**：
```
用户列表页面加载太慢（5秒+），需要优化。
现在是直接查数据库，每次查1000条记录。
```

**流程**：
1. 创建任务：`sansheng_create_task()`
2. 司礼监整理：读取代码、分析瓶颈
3. 中书省起草：调用 Agent 生成分页 + 索引 + 缓存方案
4. 门下省审议：调用 Agent，封驳要求补充性能基准测试（第1次封驳）
5. 中书省修改：再次调用 Agent，增加压测计划
6. 门下省准奏：`sansheng_submit_decision({ decision: "approved" })`
7. 用户确认：`sansheng_finalize()`
8. 产出：完整优化方案 + 测试计划

---

### 场景 3: 封驳升级裁决

**用户输入**：
```
重构用户认证模块，从 session 改为 JWT。
```

**流程**：
1. 创建任务：`sansheng_create_task()`
2. 中书省方案：调用 Agent 生成全面切换 JWT 方案
3. 门下省封驳：调用 Agent 审议，封驳未考虑旧 session 用户的迁移（第1次）
4. 中书省修改：再次调用 Agent，增加双模式兼容期
5. 门下省封驳：兼容期太长（30天），建议7天（第2次）
6. 中书省坚持：30天更安全
7. 门下省封驳：仍建议7天（第3次，`rejection_count = 3`） → **升级用户裁决**
8. 司礼监询问用户：7天 vs 30天？
9. 用户选择：折中14天，调用 `sansheng_finalize({ decision: "custom", custom_plan: "14天兼容期" })`
10. 产出：14天兼容期方案

---

## 配置说明

### Agent 配置

确保以下 agent 已在 `~/.claude/agents/` 中配置（plugin 安装时自动创建）：

- `silijian` - 司礼监
- `zhongshu` - 中书省
- `menxia` - 门下省
- `shangshu` - 尚书省（预留）

### 查看任务状态

使用 MCP tool 查询任务：

```
sansheng_get_task({
  task_id: "TASK-20260310-001"
})
```

返回包含完整状态历史、方案版本、封驳记录的任务对象。

---

## 故障排查

### 问题 1: Agent 未响应

**症状**：调用中书省/门下省后无响应

**排查**：
```bash
# 检查 agent 是否存在
ls -la ~/.claude/agents/ | grep -E 'zhongshu|menxia|silijian'

# 查看 agent 的 SOUL.md
cat ~/.claude/agents/zhongshu/SOUL.md | head -20
```

**解决**：
- 重新安装 plugin
- 或手动创建 agent workspace

---

### 问题 2: 状态文件损坏

**症状**：`FileNotFoundError` 或 JSON 解析错误

**解决**：
```bash
cd ~/.claude/plugins/sansheng-pipeline
# 备份现有数据
cp data/tasks.json data/tasks.backup.json
# 重置（会丢失历史数据）
echo '[]' > data/tasks.json
```

---

### 问题 3: 封驳次数不正确

**症状**：门下省已封驳3次但未触发升级

**排查**：
使用 `sansheng_get_task({ task_id: "TASK-20260310-001" })` 查看任务状态，检查：
- `rejection_count` 字段的值
- `escalated` 字段是否为 true
- `rejections` 数组中的封驳记录

**解决**：
- 如果 `rejection_count >= 3`，门下省应触发升级而非继续封驳
- 检查门下省 SOUL.md 中的逻辑是否正确调用 `sansheng_submit_decision`

---

## 版本历史

- **v0.1.0** (2026-03-10)
  - ✅ 司礼监协调流程
  - ✅ 中书省规划
  - ✅ 门下省审议
  - ✅ 封驳机制（最多2次）
  - ✅ 用户裁决
  - ✅ 定稿确认
  - ⏳ 尚书省执行（待实现）

---

## 贡献与反馈

如有问题或建议，请在项目仓库提 issue：
[your-repo-url]

---

## License

MIT
