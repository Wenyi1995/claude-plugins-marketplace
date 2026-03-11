# 快速开始指南

5 分钟上手三省审议流水线。

---

## 1. 验证安装

```bash
# 检查插件目录
ls -la ~/.claude/plugins/sansheng-pipeline/

# 应该看到以下结构：
# agents/     - Agent 配置
# lib/        - 状态管理库
# skills/     - 主 Skill
# data/       - 任务数据（自动创建）
```

**测试状态管理库**：

```bash
cd ~/.claude/plugins/sansheng-pipeline
python3 test_pipeline.py
```

如果看到"🎉 所有测试通过！"，说明安装成功。

---

## 2. 第一个任务

### 在 Claude Code 中启动流程

**方式 1: 使用 Skill**（推荐）

```
/pipeline 给 users 表增加一个 role 字段，支持多角色用户
```

**方式 2: 通过 Agent**

```
@silijian 请启动审议流程：优化用户列表接口的性能，现在加载太慢
```

---

## 3. 流程演示

### 场景：数据库字段增加

**用户输入**：
```
/pipeline 给 users 表增加 role 字段（VARCHAR 50），用于多角色权限管理
```

**司礼监**（自动）：
- 创建任务 TASK-20260310-004
- 收集信息：读取现有表结构（如需要）
- 调用中书省起草方案

**中书省**（自动）：
```markdown
## 一、目标拆解
给 users 表增加 role 字段，支持多角色用户

## 二、执行步骤
1. 数据库迁移
   - 创建 migration: ALTER TABLE users ADD COLUMN role VARCHAR(50)
   - 设置默认值: UPDATE users SET role = 'user' WHERE role IS NULL
   - 回滚脚本: ALTER TABLE users DROP COLUMN role

2. 代码适配
   - User model 增加 role 属性
   - 认证中间件增加角色校验

3. 测试
   - 单元测试：角色赋值、校验
   - 集成测试：完整认证流程
   - 覆盖率 > 80%

## 三、风险评估
- 数据量大时迁移慢 → 应对：先在测试环境验证
- 旧代码未处理 NULL → 应对：设置默认值

## 四、验收标准
- [ ] 新用户自动赋予 'user' 角色
- [ ] 可通过 API 修改角色
- [ ] 角色校验正常工作
```

**门下省**（自动审议）：
```
✅ 准奏

方案可行性、完整性、风险控制均达标：
- 有迁移和回滚方案
- 考虑了默认值处理
- 测试覆盖充分

建议：执行时注意大表迁移的锁表时间
```

**司礼监**（暂停，等待用户）：
```
门下省已准奏以下方案，请您最终确认：

[显示完整方案]

是否批准执行？
选项：[批准执行] [驳回重做] [我要修改]
```

**用户选择**："批准执行"

**司礼监**（完成）：
```
任务 TASK-20260310-004 已完成三省审议流程

【最终方案】
[方案内容]

注：当前版本（v0.1）暂不支持自动执行，您可以基于此方案手动实施。
下一版本将实现尚书省自动派发执行。
```

---

## 4. 常用命令

### 查看所有任务

```bash
cd ~/.claude/plugins/sansheng-pipeline
python3 -c "
import sys; sys.path.insert(0, 'lib')
from task_state import list_tasks
for t in list_tasks():
    print(f\"{t['id']}: [{t['state']}] {t['title']}\")
"
```

### 查看任务详情

```bash
python3 -c "
import sys; sys.path.insert(0, 'lib')
from task_state import get_task
import json
print(json.dumps(get_task('TASK-20260310-001'), ensure_ascii=False, indent=2))
"
```

### 查看封驳历史

```bash
python3 -c "
import sys; sys.path.insert(0, 'lib')
from task_state import get_task
task = get_task('TASK-20260310-001')
if task['rejections']:
    for i, r in enumerate(task['rejections'], 1):
        print(f\"{i}. {r['reason']}\")
else:
    print('无封驳记录')
"
```

---

## 5. 调试技巧

### 问题 1: Agent 未响应

**检查 Agent 是否存在**：
```bash
ls -la ~/.claude/agents/ | grep -E 'zhongshu|menxia|silijian'
```

如果不存在，需要在 Claude Code 中注册 Agent：
```
# 通过 openclaw.json 或 Claude Code 设置注册
```

### 问题 2: 状态文件损坏

**备份并重置**：
```bash
cd ~/.claude/plugins/sansheng-pipeline/data
cp tasks.json tasks.backup.json
echo '[]' > tasks.json
```

### 问题 3: 查看完整日志

**查看任务的所有版本**：
```bash
python3 -c "
import sys; sys.path.insert(0, 'lib')
from task_state import get_task
task = get_task('TASK-20260310-001')
print(f\"版本数: {len(task['versions'])}\")
for v in task['versions']:
    print(f\"\\nv{v['version']} ({v['created_at']}):\")
    print(v['plan'][:200] + '...')
"
```

---

## 6. 进阶使用

### 场景 1: 封驳修改流程

如果门下省封驳，中书省会自动修改方案，你只需等待最终结果。

**预期流程**：
```
中书省 v1 → 门下省封驳 → 中书省 v2 → 门下省准奏 → 用户确认
```

### 场景 2: 用户裁决

如果连续封驳 2 次仍未达成一致：
```
中书省 v1 → 封驳 → v2 → 封驳 → v3 → 升级裁决 → 用户决定
```

**司礼监会询问你**：
```
双方分歧：
【中书省观点】...
【门下省观点】...

您的决定？
选项：[采纳中书省] [采纳门下省] [我来修改] [取消任务]
```

---

## 7. 最佳实践

### ✅ 推荐的任务类型

- 数据库结构变更
- 性能优化方案
- 架构调整设计
- 复杂功能规划

### ❌ 不推荐的任务

- 简单的单文件修改（太重了）
- 紧急 bug 修复（流程太长）
- 已有明确方案，只需执行

### 💡 提高效率的技巧

1. **任务描述要清晰**：
   - ✅ "给 users 表增加 role 字段（VARCHAR 50），用于多角色权限"
   - ❌ "改一下 users 表"

2. **提供必要上下文**：
   - 当前技术栈
   - 已知约束条件
   - 预期产出格式

3. **信任审议流程**：
   - 不要在门下省封驳时立即介入
   - 让中书省有机会修改方案
   - 只有第 3 次封驳才需要你裁决

---

## 8. 下一步

- 📖 阅读 [README.md](README.md) 了解完整架构
- 🔍 查看 [agents/*/SOUL.md](agents/) 了解各 Agent 职责
- 🚀 等待 v0.2 版本的尚书省自动执行功能

---

## 问题反馈

遇到问题？欢迎反馈：
- GitHub Issues: [repo-url]
- Email: [your-email]

祝使用愉快！🎉
