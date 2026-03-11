# MCP Server 集成工具使用指南

## 概述

工部已完成两个核心集成模块：

1. **utils.ts** - Python 执行工具（增强版）
2. **handoff.ts** - Agent Handoff 机制

这两个模块提供了 TypeScript 与 Python 的桥接能力，实现了跨语言的 Agent 协作。

---

## 一、utils.ts - Python 执行工具

### 核心功能

#### 1. execPython() - 通用 Python 执行

```typescript
import { execPython, PythonResult } from './utils';

const result = execPython('print("Hello from Python")');
console.log(result.data); // 输出：Hello from Python
```

**特点**：
- 使用 Base64 编码避免转义问题
- 支持超时控制（默认 30 秒）
- 返回结构化结果（success/error/data）
- 自动捕获 stderr

#### 2. callPythonFunction() - 调用 Python 函数

```typescript
import { callPythonFunction } from './utils';

// 调用 task_state.list_tasks()
const result = callPythonFunction('task_state', 'list_tasks', [], true);

if (result.success) {
  console.log(result.data); // 返回任务列表
}
```

**参数说明**：
- `moduleName`: Python 模块名（如 'task_state'）
- `functionName`: 函数名（如 'list_tasks'）
- `args`: 参数列表（支持 string/number/array/object）
- `returnJson`: 是否解析 JSON（默认 true）

**字符串参数自动 Base64 编码**：
```typescript
// 包含特殊字符的字符串自动转为 Base64
callPythonFunction('task_state', 'create_task', [
  '任务标题：包含中文和特殊字符 "quotes"',
  '任务内容',
  'creator'
]);
```

#### 3. execPythonBatch() - 批量执行

```typescript
import { execPythonBatch } from './utils';

const operations = [
  "from task_state import create_task",
  "task_id = create_task('批量任务1', '内容', 'creator')",
  "print(task_id)"
];

const result = execPythonBatch(operations, false);
```

#### 4. execPythonScript() - 执行 Python 脚本

```typescript
import { execPythonScript } from './utils';

// 执行 lib/task_decompose.py
const result = execPythonScript('task_decompose.py', ['arg1', 'arg2']);
```

---

## 二、handoff.ts - Agent Handoff 机制

### 核心功能

#### 1. handoffToAgent() - 发起 Handoff

```typescript
import { handoffToAgent, HandoffMessage } from './handoff';

const message: HandoffMessage = {
  task_id: 'TASK-20260310-001',
  action: 'draft',
  content: { version: 1 }
};

const response = await handoffToAgent('zhongshu', message);

if (response.success) {
  console.log('方案版本:', response.result.version);
  console.log('生成的方案:', response.result.plan);
}
```

**支持的 Agent**：
- `zhongshu` - 中书省（起草方案）
- `menxia` - 门下省（审议方案）
- 未来可扩展：六部 agent

#### 2. validateHandoffMessage() - 验证消息格式

```typescript
import { validateHandoffMessage } from './handoff';

const validation = validateHandoffMessage(message);

if (!validation.valid) {
  console.error('消息格式错误:', validation.error);
}
```

**必需字段**：
- `task_id`: 任务 ID（非空字符串）
- `action`: 操作类型（如 'draft', 'review'）
- `content`: 上下文信息（对象）

#### 3. handoffChain() - 顺序调用多个 Agent

```typescript
import { handoffChain } from './handoff';

const handoffs = [
  {
    agent: 'zhongshu',
    message: { task_id: 'TASK-001', action: 'draft', content: {} }
  },
  {
    agent: 'menxia',
    message: { task_id: 'TASK-001', action: 'review', content: { version: 1 } }
  }
];

const responses = await handoffChain(handoffs);

// 如果任何环节失败，后续调用会自动停止
responses.forEach((resp, index) => {
  console.log(`第 ${index + 1} 步:`, resp.success ? '成功' : '失败');
});
```

#### 4. handoffParallel() - 并行调用多个 Agent

```typescript
import { handoffParallel } from './handoff';

// 同时调用六部 agent
const handoffs = [
  { agent: 'libu', message: { task_id: 'TASK-001', action: 'execute', content: {} } },
  { agent: 'hubu', message: { task_id: 'TASK-001', action: 'execute', content: {} } },
  { agent: 'bingbu', message: { task_id: 'TASK-001', action: 'execute', content: {} } }
];

const responses = await handoffParallel(handoffs);
```

#### 5. handoffWithRetry() - 带重试的 Handoff

```typescript
import { handoffWithRetry } from './handoff';

const response = await handoffWithRetry(
  'zhongshu',
  message,
  3,      // 最大重试 3 次
  1000    // 每次重试间隔 1 秒
);
```

#### 6. listAvailableAgents() - 获取可用 Agent 列表

```typescript
import { listAvailableAgents } from './handoff';

const agents = await listAvailableAgents();
console.log('当前可用 Agent:', agents); // ['zhongshu', 'menxia']
```

#### 7. checkAgentAvailable() - 检查 Agent 可用性

```typescript
import { checkAgentAvailable } from './handoff';

const check = await checkAgentAvailable('zhongshu');
if (check.available) {
  console.log('中书省可用');
} else {
  console.error('不可用:', check.error);
}
```

---

## 三、集成测试

运行完整测试套件：

```bash
cd mcp-server
npm run build
npx ts-node src/test-utils-handoff.ts
```

**测试覆盖**：
1. ✓ execPython 基础功能
2. ✓ callPythonFunction 调用 Python 模块
3. ✓ validateHandoffMessage 消息验证
4. ✓ listAvailableAgents 列出可用 Agent
5. ✓ checkAgentAvailable 检查 Agent 可用性
6. ✓ handoffToAgent 真实 Handoff（创建任务并调用中书省）

---

## 四、架构说明

### 调用链路

```
TypeScript (index.ts)
    ↓ import
utils.ts (execPython / callPythonFunction)
    ↓ Base64 编码
Python 执行环境
    ↓ import
lib/call_mcp_agent.py (invoke_agent)
    ↓ 调用
lib/agent_internal_tools.py (zhongshu_internal / menxia_internal)
    ↓ 读写
data/tasks.json (任务状态)
```

### 关键设计

1. **Base64 编码**：所有 Python 代码通过 Base64 编码传递，避免转义问题
2. **结构化返回**：统一的 `PythonResult` 接口，包含 success/error/data
3. **超时控制**：默认 30 秒超时，防止 Agent 卡死
4. **错误隔离**：Python 执行错误不会导致 TypeScript 进程崩溃

---

## 五、使用场景

### 场景 1：MCP Server 调用三省流程

```typescript
import { handoffToAgent } from './handoff';

// 1. 中书省起草方案
const draftResponse = await handoffToAgent('zhongshu', {
  task_id: taskId,
  action: 'draft',
  content: {}
});

// 2. 门下省审议方案
const reviewResponse = await handoffToAgent('menxia', {
  task_id: taskId,
  action: 'review',
  content: { version: draftResponse.result.version }
});
```

### 场景 2：查询任务状态

```typescript
import { callPythonFunction } from './utils';

const result = callPythonFunction('task_state', 'get_task', [taskId], true);

if (result.success) {
  const task = result.data;
  console.log('任务状态:', task.state);
  console.log('方案版本数:', task.versions.length);
  console.log('封驳次数:', task.rejections.length);
}
```

### 场景 3：任务拆解

```typescript
import { execPythonScript } from './utils';

const result = execPythonScript('task_decompose.py', [
  taskId,
  '--mode', 'auto'
]);

console.log('拆解结果:', result.data);
```

---

## 六、错误处理

### 标准错误处理模式

```typescript
import { handoffToAgent } from './handoff';

const response = await handoffToAgent('zhongshu', message);

if (!response.success) {
  console.error(`Handoff 失败: ${response.error}`);

  // 根据错误类型决定处理方式
  if (response.error?.includes('timeout')) {
    // 超时 → 重试
    return handoffWithRetry('zhongshu', message);
  } else if (response.error?.includes('not_found')) {
    // Agent 不存在 → 记录错误
    logError('Agent 不存在', { agent: 'zhongshu' });
  } else {
    // 其他错误 → 升级处理
    escalateToUser(response.error);
  }
}
```

---

## 七、性能优化建议

1. **批量操作使用 execPythonBatch()**：减少 Python 进程启动次数
2. **并行 Handoff 使用 handoffParallel()**：六部任务可并行执行
3. **合理设置超时时间**：复杂任务可增加 timeout 参数
4. **缓存 Agent 可用性检查结果**：避免重复调用 `listAvailableAgents()`

---

## 八、扩展指南

### 添加新的 Agent

1. 在 `lib/agent_internal_tools.py` 中添加函数：

```python
def xinagent_internal(task_id: str, action: str, content: dict) -> dict:
    """新 Agent 的内部工具"""
    # 实现逻辑
    pass

def xinagent_submit_result(task_id: str, result: dict) -> dict:
    """新 Agent 提交结果"""
    # 实现逻辑
    pass
```

2. 在 `lib/call_mcp_agent.py` 中添加调用逻辑：

```python
def invoke_xinagent_agent(task_id: str, action: str, content: dict) -> dict:
    # 调用 xinagent_internal
    # 处理结果
    # 调用 xinagent_submit_result
    pass
```

3. 在 TypeScript 中直接使用：

```typescript
const response = await handoffToAgent('xinagent', message);
```

---

## 总结

工部已完成集成基础设施搭建：

- ✅ TypeScript ↔ Python 桥接（utils.ts）
- ✅ Agent Handoff 机制（handoff.ts）
- ✅ 集成测试通过（test-utils-handoff.ts）
- ✅ 支持中书省、门下省两个 Agent
- ✅ 可扩展到六部 Agent

**下一步**：
1. 礼部：审查技术文档准确性
2. 刑部：验收测试并审查合规性
3. 兵部：基于 handoff.ts 实现六部 Agent 调用逻辑
