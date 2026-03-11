# 端到端集成测试验收清单

**任务**: SUB-037-005
**验收人**: 尚书省 / 刑部
**测试执行**: 工部

---

## 验收标准（8项）

### ✅ 验收 1：用户调用 sansheng_review_all，中书省自动起草方案

**测试方法**:
```bash
cd /Users/liweizhao/.claude/plugins/sansheng-pipeline/mcp-server
npm test
```

**验收条件**:
- [ ] 控制台输出：`[AUTO-LOOP] 任务 TASK-* 开始，Handoff 给中书省起草...`
- [ ] 控制台输出：`[AUTO-LOOP] 中书省已提交方案 v1`
- [ ] 无需用户手动触发中书省

**当前状态**: ✅ 通过（见 E2E_TEST_REPORT.md 第 78 行）

---

### ✅ 验收 2：中书省完成后，自动 handoff 给门下省

**验收条件**:
- [ ] 控制台输出：`[AUTO-LOOP] Handoff 给门下省审议方案 v1...`
- [ ] 无需用户手动触发门下省
- [ ] handoffToAgent('menxia', ...) 返回成功

**当前状态**: ✅ 通过（见 E2E_TEST_REPORT.md 第 90 行）

---

### ✅ 验收 3：门下省封驳后，自动 handoff 回中书省

**验收条件**:
- [ ] 场景 2 或场景 3 中触发封驳
- [ ] 控制台输出：`[AUTO-LOOP] 门下省封驳方案 v*（第 N 次）`
- [ ] 控制台输出：`[AUTO-LOOP] Handoff 给中书省修改方案...`
- [ ] 中书省提交修改版：`[AUTO-LOOP] 中书省已提交修改版 v*`

**当前状态**: ⚠ 代码正确，但测试未触发（需修复审议规则）

**修复后验证**:
```bash
npm test
# 查看场景 2 的输出，应包含上述日志
```

---

### ✅ 验收 4：循环最多 3 次封驳，超过自动升级司礼监

**验收条件**:
- [ ] 场景 3 触发 3 次封驳
- [ ] 控制台输出：`[AUTO-LOOP] 封驳 3 次，升级圣上裁决`
- [ ] 返回结果：`status: 'escalated'`
- [ ] 返回结果包含 `conflict` 字段（中书省方案、门下省关切、封驳历史）

**当前状态**: ⚠ 代码正确，但测试未触发（需修复审议规则）

**修复后验证**:
```bash
npm test
# 查看场景 3 的输出，应返回 escalated 状态
```

---

### ✅ 验收 5：门下省准奏后，返回结果给用户

**验收条件**:
- [ ] 场景 1 返回 `status: 'approved'`
- [ ] 包含 `final_plan` 字段（完整的方案内容）
- [ ] 包含 `meta` 字段（版本数、封驳次数）
- [ ] `summary` 包含"等待圣上批准"字样

**当前状态**: ✅ 通过（见 E2E_TEST_REPORT.md 第 140 行）

**验证命令**:
```bash
npm test | grep -A 5 "场景1"
```

---

### ⚠ 验收 6：每次 handoff 都记录审计日志

**验收条件**:
- [ ] 执行测试后，`data/audit/audit-20260310.jsonl` 有新记录
- [ ] 包含 `handoff` 事件（发起）
- [ ] 包含 `handoff_response` 事件（响应）
- [ ] `from_agent` 和 `to_agent` 字段正确
- [ ] `timestamp` 对应测试执行时间

**当前状态**: ⚠ 未记录（需修复）

**修复后验证**:
```bash
npm test
cat /Users/liweizhao/.claude/plugins/sansheng-pipeline/data/audit/audit-20260310.jsonl | grep handoff | tail -10
```

**期望输出示例**:
```json
{
  "event_id": "EVT-20260310-xxx",
  "timestamp": "2026-03-10T20:xx:xx",
  "actor": {"type": "system", "id": "mcp_server"},
  "action": {"type": "handoff", "resource_id": "zhongshu"},
  "result": "initiated",
  "details": {"task_id": "TASK-*", "action": "draft", ...}
}
{
  "event_id": "EVT-20260310-yyy",
  "timestamp": "2026-03-10T20:xx:xx",
  "actor": {"type": "agent", "id": "zhongshu"},
  "action": {"type": "handoff_response", "resource_id": "TASK-*"},
  "result": "success",
  "details": {"version": 1, "plan": "...", ...}
}
```

---

### ❓ 验收 7：每次 handoff 都验证消息格式

**验收条件**:
- [ ] TypeScript 层有消息验证（validateHandoffMessage）
- [ ] Python 层有消息验证（handoff_validator.py）
- [ ] 无效消息被拦截（返回 validation_error）

**当前状态**: ❓ TypeScript 层有验证，Python 层未调用

**测试方法**（手动测试）:
```typescript
// 在 test-sansheng.ts 中添加负面测试
const invalidMessage = {
  task_id: '',  // 无效：空字符串
  action: 'draft',
  content: {}
};

const result = await handoffToAgent('zhongshu', invalidMessage);
// 期望：result.success === false
// 期望：result.error 包含 "task_id 必须是非空字符串"
```

**修复后验证**:
```bash
# 运行手动测试
npx ts-node mcp-server/src/test-invalid-message.ts
```

---

### ❓ 验收 8：Handoff 失败自动重试 2 次

**验收条件**:
- [ ] 使用 `handoffWithRetry()` 替代 `handoffToAgent()`
- [ ] Agent 调用失败时自动重试
- [ ] 最多重试 3 次（共 4 次尝试）
- [ ] 重试间隔：1 秒

**当前状态**: ❓ 重试机制已实现，但未使用

**测试方法**（需要模拟失败）:
1. 临时修改 `call_mcp_agent.py`，让第 1 次调用抛出异常
2. 运行测试，观察重试行为
3. 恢复代码

**修复后验证**:
```bash
# 检查代码是否使用 handoffWithRetry
grep -n "handoffWithRetry" mcp-server/src/sansheng.ts
# 期望：第 173、193、248 行（3 处 handoff 调用）
```

---

## 完整验收流程

### 步骤 1：执行修复（工部）
```bash
# 按照 FIX_PLAN.md 执行修复
# - 修改 lib/call_mcp_agent.py（审议规则 + 审计日志）
# - 修改 mcp-server/src/sansheng.ts（使用 handoffWithRetry）
```

### 步骤 2：运行测试
```bash
cd /Users/liweizhao/.claude/plugins/sansheng-pipeline/mcp-server
npm test > test_output.log 2>&1
```

### 步骤 3：验证测试结果
```bash
# 检查测试输出
cat test_output.log | grep "场景"

# 期望输出：
# ✓ 场景1通过
# ✓ 场景2通过（经过封驳后准奏）
# ✓ 场景3通过（触发升级）
```

### 步骤 4：验证审计日志
```bash
# 查看最新的审计日志
cat /Users/liweizhao/.claude/plugins/sansheng-pipeline/data/audit/audit-20260310.jsonl | \
  jq -r 'select(.action.type == "handoff" or .action.type == "handoff_response") | .timestamp + " " + .actor.id + " -> " + .action.resource_id' | \
  tail -20

# 期望输出：包含多条 handoff 记录，时间戳为测试执行时间
```

### 步骤 5：验证任务状态
```bash
# 查看测试任务的状态
cat /Users/liweizhao/.claude/plugins/sansheng-pipeline/data/tasks.json | \
  jq '.[] | select(.id | startswith("TASK-20260310-04")) | {id, state, versions: .versions | length, rejections: .rejections | length}'

# 期望输出：
# TASK-*-040: state=approved, versions=1, rejections=0
# TASK-*-041: state=approved, versions=2-3, rejections=1-2
# TASK-*-042: state=escalated, versions=3-4, rejections=3
```

---

## 验收通过标准

### 必须满足（P0）
- [x] 验收 1：中书省自动起草方案 ✅
- [x] 验收 2：中书省→门下省自动 handoff ✅
- [ ] 验收 3：门下省封驳→中书省自动 handoff ⏳
- [ ] 验收 4：封驳 3 次自动升级 ⏳
- [x] 验收 5：准奏后返回结果 ✅

### 应该满足（P1）
- [ ] 验收 6：审计日志记录完整 ⏳

### 可选满足（P2）
- [ ] 验收 7：消息格式验证生效 ⏳
- [ ] 验收 8：重试机制生效 ⏳

### 通过条件
- **最低标准**（可以验收，但需标注问题）：P0 全部通过
- **完美标准**（无条件通过）：P0 + P1 全部通过

---

## 当前状态总结

| 验收项 | 状态 | 说明 |
|--------|------|------|
| 验收 1 | ✅ | 已通过 |
| 验收 2 | ✅ | 已通过 |
| 验收 3 | ⏳ | 代码正确，需调整测试 |
| 验收 4 | ⏳ | 代码正确，需调整测试 |
| 验收 5 | ✅ | 已通过 |
| 验收 6 | ⏳ | 需添加审计日志记录 |
| 验收 7 | ⏳ | 需在 Python 层调用验证 |
| 验收 8 | ⏳ | 需使用 handoffWithRetry |

**P0 通过率**: 3/5 (60%)
**P1 通过率**: 0/1 (0%)
**P2 通过率**: 0/2 (0%)

**下一步**: 执行 FIX_PLAN.md，完成修复后重新验收

---

**清单完成时间**: 2026-03-10 20:55
**创建人**: 工部
**使用方法**: 修复完成后，按照本清单逐项验收
