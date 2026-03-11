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
@sililijian 请启动审议流程：[任务描述]
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
1. 司礼监收集信息：当前表结构、用户量、权限系统实现
2. 中书省起草：迁移方案 + 权限适配 + 回滚步骤
3. 门下省审议：检查迁移脚本、评估风险
4. 用户确认定稿
5. 产出：可执行的迁移方案

---

### 场景 2: 性能优化方案

**用户输入**：
```
用户列表页面加载太慢（5秒+），需要优化。
现在是直接查数据库，每次查1000条记录。
```

**流程**：
1. 司礼监整理：读取代码、分析瓶颈
2. 中书省起草：分页 + 索引 + 缓存方案
3. 门下省审议：要求补充性能基准测试（第1次封驳）
4. 中书省修改：增加压测计划
5. 门下省准奏
6. 用户确认定稿
7. 产出：完整优化方案 + 测试计划

---

### 场景 3: 封驳升级裁决

**用户输入**：
```
重构用户认证模块，从 session 改为 JWT。
```

**流程**：
1. 中书省方案：全面切换 JWT
2. 门下省封驳：未考虑旧 session 用户的迁移（第1次）
3. 中书省修改：增加双模式兼容期
4. 门下省封驳：兼容期太长（30天），建议7天（第2次）
5. 中书省坚持：30天更安全
6. 门下省封驳：仍建议7天（第3次） → **升级用户裁决**
7. 司礼监询问用户：7天 vs 30天？
8. 用户选择：折中14天
9. 产出：14天兼容期方案

---

## 配置说明

### Agent 配置

确保以下 agent 已在 `~/.claude/agents/` 中配置（plugin 安装时自动创建）：

- `sililijian` - 司礼监
- `zhongshu` - 中书省
- `menxia` - 门下省
- `shangshu` - 尚书省（预留）

### 查看任务历史

```bash
cd ~/.claude/plugins/sansheng-pipeline
python3 -c "
import sys; sys.path.insert(0, 'lib')
from task_state import list_tasks
for t in list_tasks()[:10]:
    print(f\"{t['id']}: {t['state']} - {t['title']}\")
"
```

### 查看任务详情

```bash
python3 -c "
import sys; sys.path.insert(0, 'lib')
from task_state import get_task
import json
task = get_task('TASK-20260310-001')
print(json.dumps(task, ensure_ascii=False, indent=2))
"
```

---

## 故障排查

### 问题 1: Agent 未响应

**症状**：调用中书省/门下省后无响应

**排查**：
```bash
# 检查 agent 是否存在
ls -la ~/.claude/agents/ | grep -E 'zhongshu|menxia|sililijian'

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
```bash
python3 -c "
import sys; sys.path.insert(0, 'lib')
from task_state import get_task, get_rejection_count
task_id = 'TASK-20260310-001'
count = get_rejection_count(task_id)
print(f'封驳次数: {count}')
task = get_task(task_id)
for i, r in enumerate(task['rejections'], 1):
    print(f\"{i}. {r['timestamp']}: {r['reason'][:50]}...\")
"
```

**解决**：
- 如果 `count >= 2`，门下省应触发升级而非继续封驳
- 检查门下省 SOUL.md 中的逻辑

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
