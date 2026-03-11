# 快速通道使用指南

## 概述

快速通道机制允许司礼监直接将简单任务派发给尚书省执行，跳过三省审议流程，提升效率。

**版本**: v0.4
**实施日期**: 2026-03-11

---

## 使用场景

### 适合快速通道的任务

- **纯信息收集**: 查询日志、导出数据、列出服务状态
- **纯文档整理**: 格式化 README、补充注释、生成目录
- **标准化配置**: 安装依赖、启动服务、设置环境变量
- **重复性任务**: 有既定规范的标准操作

### 不适合快速通道的任务

- 涉及架构决策
- 修改核心业务逻辑
- 涉及安全/性能风险
- 包含复杂条件逻辑

---

## 使用步骤

### 1. 司礼监使用（自动分类）

在司礼监 SOUL.md 的阶段 0，会自动调用分类器：

```python
cd ~/.claude/plugins/sansheng-pipeline
python3 -c "
import sys
sys.path.insert(0, 'lib')
from fast_track import classify_task, format_classification_result

result = classify_task(
    title='查询系统日志',
    context='导出最近7天的错误日志，格式为 JSON'
)

print(format_classification_result(result))
"
```

输出示例：
```
轨道: fast
置信度: 95%

判断依据:
  1. 匹配白名单模板: (查询|导出).*(日志|数据)
```

### 2. 根据置信度决策

**置信度 >= 80%**: 自动派发，无需人工确认
**置信度 < 80%**: 询问用户选择

### 3. 创建快速通道任务

```python
cd ~/.claude/plugins/sansheng-pipeline
python3 -c "
import sys
sys.path.insert(0, 'lib')
from task_state import create_task

task_id = create_task(
    title='查询系统日志',
    context='导出最近7天的错误日志',
    track='fast'  # 标记为快速通道
)
print(f'任务ID: {task_id}')
"
```

### 4. 派发给尚书省

```
@shangshu

【快速通道任务】
任务ID: TASK-20260311-XXX
任务: 查询系统日志

请拆解并执行。
```

---

## 测试示例

运行测试矩阵验证分类器：

```bash
cd ~/.claude/plugins/sansheng-pipeline
python3 test_fast_track.py
```

预期输出：
```
通过: 8/8
失败: 0/8
通过率: 100.0%

✅ 所有测试通过
```

---

## 置信度说明

| 置信度 | 含义 | 处理方式 |
|--------|------|---------|
| 95% | 白名单模板匹配 | 自动派发 |
| 90% | 否决关键词触发 | 自动走三省审议 |
| 85% | 复杂度阈值触发 | 自动走三省审议 |
| < 80% | 不确定 | 询问用户 |

---

## 旧任务兼容性

使用 `get_task_safe()` 代替 `get_task()` 可确保旧任务自动补充 `track='normal'`：

```python
from task_state import get_task_safe

task = get_task_safe('TASK-20260310-001')  # 旧任务
print(task['track'])  # 输出: 'normal'
```

---

## 四层判断逻辑

```
第一层（95%）：白名单模板匹配
    ↓ 匹配 → track='fast'
    ↓ 不匹配
第二层（90%）：双重否决检查
    ↓ 触发 → track='normal'
    ↓ 未触发
第三层（85%）：长度/复杂度阈值
    ↓ 超出 → track='normal'
    ↓ 未超出
第四层（75%）：默认值
    → track='normal'（建议三省审议）
```

---

## API 参考

### `classify_task(title: str, context: str) -> Dict`

分类任务为快速通道或正常流程。

**返回值**:
```python
{
    'track': 'fast' | 'normal',
    'confidence': 0.95,  # 0.0 - 1.0
    'reasons': ['匹配白名单模板: ...'],
    'warnings': []  # 置信度 < 0.8 时包含警告
}
```

### `get_task_safe(task_id: str) -> Dict`

安全查询任务（自动补充 track 字段）。

### `create_task(title, context, track='normal')`

创建任务，支持指定 track 参数。

---

## 注意事项

1. **优先级**: 否决关键词优先于白名单模板
2. **边界情况**: 如"查询并优化"包含否决词"优化"，会走正常流程
3. **用户覆盖**: 司礼监可以手动覆盖分类结果
4. **审计日志**: 所有快速通道决策都应记录（未来版本实现）

---

## 版本历史

- v0.4 (2026-03-11): 初始实现快速通道机制
