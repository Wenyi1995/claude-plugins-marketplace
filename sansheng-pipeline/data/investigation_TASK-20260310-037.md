# 刑部调查任务：三省流程重大缺陷彻查

**任务编号**: TASK-20260310-037
**派发时间**: 2026-03-10
**派发部门**: 尚书省
**执行部门**: 刑部
**调查期限**: 1 小时内完成并上报中书省

---

## 一、圣旨摘要

圣上发现三省流程存在以下重大问题：

1. **自动化缺失**：中书省和门下省之间应该自动流转，现在还需要朕手动批准
2. **工具混用**：handoff 还在使用 dev-flow 的工具，没有用 sansheng-pipeline 自己的
3. **流程断裂**：刚才发现门下省准奏后流程中断，没有自动推进

**圣上期望**：
- 司礼监派发任务后，中书省起草 → 门下省审议 → （如果准奏）自动批准 → 尚书省执行
- **全程自动化，圣上只在封驳超过2次时才介入裁决**
- 所有 handoff 应使用三省自己的工具，不依赖外部系统

---

## 二、调查范围

### 任务样本
- 调查任务 ID：TASK-20260310-001 到 TASK-20260310-036（共 36 个任务）
- 当前状态：所有任务状态均为 `unknown`

### 必须调查的问题

#### 1. 自动化缺失
- 哪些环节需要用户手动确认？
- 门下省准奏后为什么没有自动推进？
- 中书省提交方案后是否自动触发门下省审议？

#### 2. 工具依赖
- handoff 目前用的什么工具？（dev-flow? Agent tool?）
- sansheng-pipeline 自己有 handoff 工具吗？在哪里？
- 是否存在外部依赖？

#### 3. 流程完整性
- task_state.json 的状态流转是否完整？
- agent 之间的 handoff 是否有标准格式？
- 审计日志是否记录了所有关键操作？

#### 4. 设计缺陷
- 现有的 agent SOUL.md 是否写明了"自动 handoff"？
- sansheng_review_all 工具是否真的是"自动完成"？还是只是封装？

---

## 三、调查方法

### 步骤 1：读取系统设计文档
- `/Users/liweizhao/.claude/plugins/sansheng-pipeline/agents/sililijian/SOUL.md`
- `/Users/liweizhao/.claude/plugins/sansheng-pipeline/agents/zhongshu/SOUL.md`
- `/Users/liweizhao/.claude/plugins/sansheng-pipeline/agents/menxia/SOUL.md`
- `/Users/liweizhao/.claude/plugins/sansheng-pipeline/agents/shangshu/SOUL.md`

### 步骤 2：分析 MCP 工具实现
- `/Users/liweizhao/.claude/plugins/sansheng-pipeline/mcp-server/src/sansheng.ts`
- `/Users/liweizhao/.claude/plugins/sansheng-pipeline/mcp-server/src/index.ts`
- `/Users/liweizhao/.claude/plugins/sansheng-pipeline/mcp-server/src/task-state.ts`

### 步骤 3：检查任务数据
- `/Users/liweizhao/.claude/plugins/sansheng-pipeline/data/tasks.json`
- 分析 TASK-20260310-001 到 036 的状态流转记录

### 步骤 4：查找 handoff 依赖
- 搜索所有 SOUL.md 中的 `@` 符号（handoff 语法）
- 检查是否使用 `mcp__plugin_dev-flow_dev-flow__dev_handoff`
- 确认是否有三省自己的 handoff 机制

### 步骤 5：对比设计与实现
- 设计文档中承诺的自动化程度
- 实际代码中的自动化实现
- 差异清单

---

## 四、输出要求

### 问题清单格式

按严重程度分级（P0/P1/P2）：

**P0（核心流程中断）**：
- 问题描述
- 影响范围
- 根因分析
- 建议修复方案

**P1（自动化缺失）**：
- 问题描述
- 影响范围
- 根因分析
- 建议修复方案

**P2（工具依赖/规范缺失）**：
- 问题描述
- 影响范围
- 根因分析
- 建议修复方案

### 根因分析格式

每个问题必须包含：
1. **症状**：用户观察到的现象
2. **直接原因**：代码/配置层面的问题
3. **根本原因**：设计/架构层面的缺陷
4. **证据**：文件路径 + 行号 + 代码片段

---

## 五、上报流程

调查完成后，刑部需要：

1. **生成调查报告**：
   - 文件路径：`/Users/liweizhao/.claude/plugins/sansheng-pipeline/data/investigation_report_TASK-20260310-037.md`
   - 包含完整的问题清单和根因分析

2. **Handoff 回中书省**：
   使用格式：
   ```
   @zhongshu

   刑部已完成三省流程缺陷彻查，调查报告已生成：
   /Users/liweizhao/.claude/plugins/sansheng-pipeline/data/investigation_report_TASK-20260310-037.md

   问题摘要：
   - P0 问题：X 个
   - P1 问题：Y 个
   - P2 问题：Z 个

   请中书省根据调查结果起草解决方案。
   ```

---

## 六、调查员须知

**职责边界**：
- ✅ 彻查问题、分析根因、提供证据
- ✅ 给出修复方向建议
- ❌ 不擅自修改代码
- ❌ 不替中书省起草方案

**调查原则**：
1. **基于事实**：所有结论必须有代码/日志证据
2. **追溯根因**：不止于表面症状，挖掘设计缺陷
3. **全面覆盖**：按调查范围逐项检查
4. **优先级明确**：区分 P0/P1/P2
5. **可执行建议**：修复方案要具体可行

---

钦此。
