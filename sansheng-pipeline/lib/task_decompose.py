#!/usr/bin/env python3
"""
任务拆解与派发 - 尚书省核心逻辑

负责：
1. 将批准的方案拆解为子任务
2. 根据任务类型派发给对应的部门
3. 汇总各部执行结果
"""
import re
from typing import List, Dict, Optional
from datetime import datetime


def classify_task_type(task_description: str) -> str:
    """
    根据任务描述判断任务类型，分配给对应的部门

    决策树：
    1. Agent 注册/考核/调配/Prompt 调整 → 吏部
    2. 资源/权限/数据准备 → 户部
    3. 知识提炼/规范形成/制度更新 → 礼部
    4. 实际编写代码/修改文件/执行操作 → 兵部
    5. 系统集成/工具开发/Pipeline 搭建 → 工部
    6. 质量检查/合规审查/成果验收 → 刑部

    Args:
        task_description: 任务描述文本

    Returns:
        部门 ID (libu-personnel/hubu-resources/libu-rites/bingbu-military/xingbu-justice/gongbu-works)
    """
    desc = task_description.lower()

    # 优先级顺序很重要！按专业性从高到低排列

    # 1. 礼部关键词（知识类，优先级最高）
    libu2_keywords = [
        '知识', '规范', '制度', '会话', '提炼', '沉淀',
        '最佳实践', '文化', '培训', 'claude.md', '用户偏好'
    ]
    if any(kw in desc for kw in libu2_keywords):
        return 'libu-rites'

    # 2. 刑部关键词（检查类）
    xingbu_keywords = [
        '检查', '审查', '验收', '质量', '合规', '审核',
        '测试覆盖率', '标准', '审议'
    ]
    if any(kw in desc for kw in xingbu_keywords):
        return 'xingbu-justice'

    # 3. 工部关键词（集成类）
    gongbu_keywords = [
        '集成测试', '端到端测试', '构建', 'pipeline', '工具开发', '系统集成',
        '监控', '部署', '验证流程'
    ]
    if any(kw in desc for kw in gongbu_keywords):
        return 'gongbu-works'

    # 4. 吏部关键词（Agent 管理类，注意避免与"准备"冲突）
    if 'agent' in desc and any(kw in desc for kw in ['创建', '注册', '考核', '调配', '优化', '停用']):
        return 'libu-personnel'
    if any(kw in desc for kw in ['prompt', 'soul.md 优化', '能力评估']):
        return 'libu-personnel'

    # 5. 户部关键词（资源准备类）
    hubu_keywords = [
        '准备数据', '准备资源', '历史数据', '权限配置', '上下文准备',
        'token 预算', '环境配置', 'mcp 服务'
    ]
    if any(kw in desc for kw in hubu_keywords):
        return 'hubu-resources'

    # 6. 兵部关键词（实际执行类，优先级最低作为兜底）
    bingbu_keywords = [
        '创建文件', '编写代码', '修改文件', '执行脚本', '生成文件', '实现功能',
        '写测试', '运行测试'
    ]
    if any(kw in desc for kw in bingbu_keywords):
        return 'bingbu-military'

    # 默认：如果是"实际动手"的任务，归兵部
    return 'bingbu-military'


def decompose_task(plan: str, task_id: str) -> List[Dict]:
    """
    将批准的方案拆解为子任务

    策略：
    - 识别方案中的"步骤"章节
    - 每个步骤拆解为一个子任务
    - 为每个子任务分配负责部门

    Args:
        plan: 批准的方案文本
        task_id: 父任务 ID

    Returns:
        子任务列表，每个子任务包含：
        - title: 子任务标题
        - description: 子任务描述
        - task_type: 任务类型
        - assigned_to: 负责部门
        - dependencies: 依赖的子任务序号列表
    """
    subtasks = []

    # 正则匹配步骤（支持多种格式）
    # 格式1: "步骤 1: xxx"
    # 格式2: "**步骤 1**: xxx"
    # 格式3: "### 步骤 1: xxx"
    step_pattern = r'(?:###\s*)?(?:\*\*)?步骤\s*(\d+)(?:\*\*)?[:：]\s*(.+?)(?:\n|$)'
    matches = re.finditer(step_pattern, plan, re.MULTILINE | re.IGNORECASE)

    for match in matches:
        step_num = int(match.group(1))
        step_title = match.group(2).strip()

        # 提取步骤的详细描述（从当前匹配到下一个步骤之间的文本）
        start_pos = match.end()
        next_match = re.search(step_pattern, plan[start_pos:], re.MULTILINE | re.IGNORECASE)
        end_pos = start_pos + next_match.start() if next_match else len(plan)
        step_desc = plan[start_pos:end_pos].strip()

        # 限制描述长度
        if len(step_desc) > 500:
            step_desc = step_desc[:500] + '...'

        # 分类任务类型
        task_type = classify_task_type(step_title + ' ' + step_desc)

        # 推断依赖关系（简单策略：当前步骤依赖前一步骤）
        dependencies = [step_num - 1] if step_num > 1 else []

        subtask = {
            'title': step_title,
            'description': step_desc if step_desc else step_title,
            'task_type': task_type,
            'assigned_to': task_type,  # 部门 ID 即任务类型
            'dependencies': dependencies,
            'sequence': step_num
        }

        subtasks.append(subtask)

    # 如果未能提取到步骤，则将整个任务分配给兵部
    if not subtasks:
        subtasks.append({
            'title': '执行任务',
            'description': plan[:500],
            'task_type': 'bingbu-military',
            'assigned_to': 'bingbu-military',
            'dependencies': [],
            'sequence': 1
        })

    return subtasks


def dispatch_to_department(subtask: Dict, parent_task_id: str) -> str:
    """
    派发子任务给对应部门

    Args:
        subtask: 子任务字典
        parent_task_id: 父任务 ID

    Returns:
        handoff 消息（Markdown 格式）
    """
    dept_map = {
        'libu-personnel': '吏部',
        'hubu-resources': '户部',
        'libu-rites': '礼部',
        'bingbu-military': '兵部',
        'xingbu-justice': '刑部',
        'gongbu-works': '工部'
    }

    dept_name = dept_map.get(subtask['assigned_to'], '未知部门')

    message = f"""## 尚书省派发任务

**父任务**: {parent_task_id}
**子任务序号**: {subtask['sequence']}
**派发给**: {dept_name}

### 任务标题
{subtask['title']}

### 任务描述
{subtask['description']}

### 依赖关系
"""

    if subtask['dependencies']:
        message += f"- 依赖子任务: {', '.join(map(str, subtask['dependencies']))}\n"
    else:
        message += "- 无依赖，可立即执行\n"

    message += f"""
### 要求
1. 完成后 handoff 回尚书省
2. 遇到问题及时汇报
3. 格式：@shangshu [执行结果]
"""

    return message


def aggregate_results(subtask_results: List[Dict]) -> str:
    """
    汇总各部执行结果

    Args:
        subtask_results: 子任务结果列表，每个包含：
            - subtask_id: 子任务 ID
            - department: 负责部门
            - status: 执行状态 (completed/failed)
            - result: 执行结果描述

    Returns:
        汇总报告（Markdown 格式）
    """
    total = len(subtask_results)
    completed = sum(1 for r in subtask_results if r.get('status') == 'completed')
    failed = sum(1 for r in subtask_results if r.get('status') == 'failed')

    report = f"""## 尚书省执行汇总

**总任务数**: {total}
**已完成**: {completed}
**失败**: {failed}
**完成率**: {completed/total*100:.1f}%

### 详细结果

"""

    for idx, result in enumerate(subtask_results, 1):
        status_icon = '✅' if result.get('status') == 'completed' else '❌'
        dept_map = {
            'libu-personnel': '吏部',
            'hubu-resources': '户部',
            'libu-rites': '礼部',
            'bingbu-military': '兵部',
            'xingbu-justice': '刑部',
            'gongbu-works': '工部'
        }
        dept = dept_map.get(result.get('department'), result.get('department'))

        report += f"""#### {idx}. {status_icon} {result.get('title', '未知任务')}
- **负责部门**: {dept}
- **执行状态**: {result.get('status')}
- **结果**: {result.get('result', '无结果')}

"""

    # 总结
    if failed == 0:
        report += "\n### 总结\n\n✅ 所有子任务已成功完成。\n"
    else:
        report += f"\n### 总结\n\n⚠️ 有 {failed} 个子任务失败，需要处理。\n"

    return report


# 部门映射（用于 handoff）
DEPARTMENT_MAP = {
    'libu-personnel': 'libu-personnel',
    'hubu-resources': 'hubu-resources',
    'libu-rites': 'libu-rites',
    'bingbu-military': 'bingbu-military',
    'xingbu-justice': 'xingbu-justice',
    'gongbu-works': 'gongbu-works'
}


def get_department_agent_id(department: str) -> str:
    """获取部门对应的 Agent ID"""
    return DEPARTMENT_MAP.get(department, 'bingbu-military')
