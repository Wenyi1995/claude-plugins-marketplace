#!/usr/bin/env python3
"""
MCP Agent 调用桥接

通过内部工具调用中书省和门下省 agent
当前实现：使用固定规则模拟 agent 行为
未来升级：可接入真实 LLM agent
"""
import json
import sys
import traceback
from pathlib import Path
from typing import Dict, Any

# 添加 lib 路径以导入其他模块
sys.path.insert(0, str(Path(__file__).parent))

from agent_internal_tools import (
    zhongshu_internal,
    zhongshu_submit_plan,
    menxia_internal,
    menxia_submit_decision
)
from audit_log import log_event
from handoff_validator import validate_handoff_message

def invoke_agent(agent_name: str, message: Dict[str, Any]) -> Dict[str, Any]:
    """
    调用 MCP Agent

    Args:
        agent_name: agent 名称（zhongshu / menxia）
        message: handoff 消息，包含 task_id, action, content

    Returns:
        agent 的响应结果

    Raises:
        ValueError: 未知的 agent 名称或消息格式错误
    """
    task_id = message.get('task_id', '')
    action = message.get('action', '')
    content = message.get('content', {})

    # 构造完整的 handoff 消息（用于验证）
    from datetime import datetime
    full_message = {
        'task_id': task_id,
        'from_agent': 'shangshu',  # 尚书省调度器
        'to_agent': agent_name,
        'action': action,
        'content': content,
        'timestamp': datetime.now().isoformat()
    }

    # 验证消息格式
    is_valid, errors = validate_handoff_message(full_message)
    if not is_valid:
        error_msg = f"Handoff 消息验证失败: {', '.join(errors)}"
        # 记录验证失败
        log_event(
            actor_id='mcp_server',
            action_type='handoff',
            target_id=agent_name,
            result='validation_error',
            details={
                'task_id': task_id,
                'action': action,
                'errors': errors,
                'message': str(message)[:200]
            }
        )
        raise ValueError(error_msg)

    # 记录 handoff 开始
    log_event(
        actor_id='mcp_server',
        action_type='handoff',
        target_id=agent_name,
        result='initiated',
        details={
            'task_id': task_id,
            'action': action,
            'from': 'mcp_server',
            'to': agent_name,
            'message': str(message)[:200]  # 截断以避免过长
        }
    )

    try:
        if agent_name == 'zhongshu':
            result = invoke_zhongshu_agent(task_id, action, content)
        elif agent_name == 'menxia':
            result = invoke_menxia_agent(task_id, action, content)
        else:
            raise ValueError(f"Unknown agent: {agent_name}")

        # 记录 handoff 成功
        log_event(
            actor_id=agent_name,
            action_type='handoff_response',
            target_id=task_id,
            result='success',
            details={
                'task_id': task_id,
                'action': action,
                'summary': str(result)[:200]  # 截断以避免过长
            }
        )

        return result
    except Exception as e:
        # 记录 handoff 失败
        log_event(
            actor_id=agent_name,
            action_type='handoff_response',
            target_id=task_id,
            result='error',
            details={
                'task_id': task_id,
                'action': action,
                'error': str(e),
                'traceback': traceback.format_exc()[:500]  # 截断以避免过长
            }
        )
        raise

def invoke_zhongshu_agent(task_id: str, action: str, content: Dict) -> Dict:
    """
    调用中书省 agent

    工作流程：
    1. 获取任务信息（通过 zhongshu_internal）
    2. 生成方案（当前使用模板，未来可接入 LLM）
    3. 提交方案（通过 zhongshu_submit_plan）

    Args:
        task_id: 任务ID
        action: 'draft' 或 'revise'
        content: 上下文信息

    Returns:
        {
            'agent': 'zhongshu',
            'action': str,
            'version': int,
            'plan': str,
            'status': 'submitted'
        }
    """
    # 1. 获取任务信息
    task_info = zhongshu_internal(task_id, action, content)

    # 2. 生成方案
    if action == 'draft':
        plan = _generate_initial_plan(task_info)
    elif action == 'revise':
        plan = _generate_revised_plan(task_info)
    else:
        raise ValueError(f"Unknown action: {action}")

    # 3. 提交方案
    result = zhongshu_submit_plan(task_id, plan)

    return {
        'agent': 'zhongshu',
        'action': action,
        'version': result['version'],
        'plan': plan,
        'status': 'submitted'
    }

def _generate_initial_plan(task_info: Dict) -> str:
    """
    生成初始方案

    根据 context 长度生成不同质量的方案：
    - context >= 50 字：生成完整方案（包含风险评估和验收标准）
    - context < 50 字：生成简化方案（缺少关键章节，会被封驳）
    """
    context_length = len(task_info['context'])

    # 基础部分（所有方案都有）
    plan = f"""## 执行方案

### 一、目标
{task_info['title']}

### 二、背景
{task_info['context']}

### 三、实施步骤
1. 需求分析与技术调研
2. 方案设计与架构评审
3. 核心功能开发与单元测试
4. 集成测试与问题修复
5. 部署上线与监控验证
"""

    # 如果 context 足够详细（>= 50 字），生成完整方案
    if context_length >= 50:
        plan += """
### 四、风险与应对
- 技术风险：新技术栈需要学习，预留缓冲时间
- 集成风险：与现有系统对接需提前测试
- 时间风险：关键路径预留应急方案

### 五、验收标准
- 功能完整性：所有需求点通过测试
- 性能指标：满足 SLA 要求
- 代码质量：通过 code review 和静态检查
"""

    plan += f"\n（由中书省 agent 自动生成，版本 v{task_info['current_version'] + 1}）\n"
    return plan

def _generate_revised_plan(task_info: Dict) -> str:
    """
    生成修订版方案（响应门下省封驳）

    策略：
    - 第 1 次修改：补充风险评估
    - 第 2 次修改：补充验收标准
    - 第 3 次修改：补充技术细节说明
    - 第 4 次修改：补充性能指标
    - 第 5 次修改：补充安全审计（如仍不完善，会升级司礼监裁决）
    """
    rejection_count = task_info['rejection_count']

    plan = f"""## 执行方案（修订版 v{task_info['current_version'] + 1}）

### 【修改说明】
针对门下省第 {rejection_count} 次封驳意见：
{task_info['rejection_reason']}

已修正上述问题。

### 一、目标
{task_info['title']}

### 二、背景
{task_info['context']}

### 三、实施步骤
1. 需求分析与技术调研
2. 方案设计与架构评审
3. 核心功能开发与单元测试
4. 集成测试与问题修复
5. 部署上线与监控验证
"""

    # 第 1 次修改：补充风险评估
    if rejection_count >= 1:
        plan += """
### 四、风险与应对
- 技术风险：新技术栈需要学习，预留缓冲时间
- 集成风险：与现有系统对接需提前测试
- 时间风险：关键路径预留应急方案
"""

    # 第 2 次修改：补充验收标准
    if rejection_count >= 2:
        plan += """
### 五、验收标准
- 功能完整性：所有需求点通过测试
- 性能指标：满足 SLA 要求
- 代码质量：通过 code review 和静态检查
"""

    # 第 3 次修改：补充技术细节说明
    if rejection_count >= 3:
        plan += """
### 六、技术细节说明
- 技术栈选型：Python 3.9+ / TypeScript / Node.js 18+
- 架构设计：MCP Server 架构，Agent 通过 handoff 机制通信
- 实施细节：使用 Base64 编码传递 JSON 参数，避免 shell 转义问题
"""

    # 第 4 次修改：补充性能指标
    if rejection_count >= 4:
        plan += """
### 七、性能指标
- 响应时间：P95 < 200ms
- 吞吐量：QPS > 1000
- 资源消耗：CPU < 70%, Memory < 80%
- 并发处理：支持 >= 100 并发请求
"""

    # 第 5 次修改：补充安全审计
    if rejection_count >= 5:
        plan += """
### 八、安全审计
- 权限控制：基于角色的访问控制（RBAC）
- 数据加密：敏感字段使用 AES-256 加密存储
- 审计日志：所有写操作记录到 audit log（JSONL 格式）
- SQL 注入防护：使用参数化查询，禁止拼接 SQL
- XSS 防护：用户输入自动转义

（注：如仍不符合要求，建议升级司礼监裁决）
"""

    plan += f"\n（中书省已修改，响应第 {rejection_count} 次封驳）\n"
    return plan

def invoke_menxia_agent(task_id: str, action: str, content: Dict) -> Dict:
    """
    调用门下省 agent

    工作流程：
    1. 获取待审议方案（通过 menxia_internal）
    2. 审议方案（当前使用规则检查，未来可接入 LLM）
    3. 提交决策（通过 menxia_submit_decision）

    Args:
        task_id: 任务ID
        action: 'review'
        content: 包含 version 等信息

    Returns:
        准奏时：
        {
            'agent': 'menxia',
            'action': 'review',
            'decision': 'approved',
            'version': int,
            'plan': str
        }

        封驳时：
        {
            'agent': 'menxia',
            'action': 'review',
            'decision': 'rejected',
            'version': int,
            'reason': str,
            'rejection_count': int
        }
    """
    # 1. 获取待审议方案
    version = content.get('version', 1)
    plan_info = menxia_internal(task_id, version)

    # 2. 审议方案
    plan = plan_info['plan']
    rejection_count = plan_info['rejection_count']

    # 执行质量检查（根据封驳次数循序渐进）
    check_result = _check_plan_quality(plan, rejection_count)

    if check_result['passed']:
        # 准奏
        result = menxia_submit_decision(task_id, 'approved')
        return {
            'agent': 'menxia',
            'action': 'review',
            'decision': 'approved',
            'version': version,
            'plan': plan
        }
    else:
        # 封驳
        reason = _format_rejection_reason(check_result['issues'])
        result = menxia_submit_decision(task_id, 'rejected', reason)
        return {
            'agent': 'menxia',
            'action': 'review',
            'decision': 'rejected',
            'version': version,
            'reason': reason,
            'rejection_count': result['rejection_count']
        }

def _check_plan_quality(plan: str, rejection_count: int = 0) -> Dict[str, Any]:
    """
    门下省质量检查（循序渐进）

    根据封驳次数提出不同要求：
    - 第 0 次审议：检查基础形式 + 风险评估
    - 第 1 次审议：检查基础形式 + 风险评估 + 验收标准
    - 第 2 次审议：检查基础形式 + 风险评估 + 验收标准 + 技术细节

    基础检查（形式）：
    1. 长度检查：方案不得少于 100 字
    2. 结构检查：必须包含"步骤"或"方案"等关键词
    3. 目标检查：必须包含"目标"或"背景"
    4. 可执行性：步骤描述不能过于抽象
    5. 完整性：不能只有标题没有内容

    Args:
        plan: 方案内容
        rejection_count: 当前封驳次数

    Returns:
        {
            'passed': bool,
            'issues': List[str]  # 发现的问题列表
        }
    """
    issues = []

    # 基础检查（所有审议都执行）
    # 检查 1: 长度检查
    if len(plan) < 100:
        issues.append(f"方案过于简略（长度 {len(plan)} 字），应不少于 100 字")

    # 检查 2: 结构检查
    if '步骤' not in plan and '方案' not in plan:
        issues.append("方案缺少关键结构，应包含'步骤'或'方案'章节")

    # 检查 3: 目标检查
    if '目标' not in plan and '背景' not in plan:
        issues.append("方案缺少目标说明，应包含'目标'或'背景'章节")

    # 检查 4: 可执行性检查（避免纯标题式方案）
    lines = [line.strip() for line in plan.split('\n') if line.strip()]
    content_lines = [line for line in lines if not line.startswith('#')]
    if len(content_lines) < 5:
        issues.append("方案内容过于简单，缺少具体描述（有效内容行少于 5 行）")

    # 检查 5: 完整性检查（避免只有一级标题）
    if plan.count('###') < 2 and plan.count('##') < 3:
        issues.append("方案结构不完整，应包含多个章节")

    # 循序渐进的内容检查
    # 第 0 次审议：只检查风险评估
    if rejection_count == 0:
        if '风险' not in plan and '应对' not in plan:
            issues.append("方案缺少风险评估章节，应包含'风险与应对'")

    # 第 1 次审议：检查风险评估 + 验收标准
    elif rejection_count == 1:
        if '验收' not in plan and '标准' not in plan:
            issues.append("方案缺少验收标准章节，应包含'验收标准'")

    # 第 2 次审议：检查技术细节（且不能是"待补充"）
    elif rejection_count == 2:
        has_tech_details = '技术细节' in plan or '技术栈' in plan or '架构设计' in plan
        if not has_tech_details:
            issues.append("方案缺少技术细节说明，应包含'技术细节说明'章节，详细描述技术栈选型、架构设计和实施细节")
        elif '待补充' in plan:
            issues.append("技术细节说明内容不完整，存在'待补充'标记，请提供具体的技术方案")

    # 第 3 次审议：检查性能指标
    elif rejection_count == 3:
        has_performance = '性能' in plan or '响应时间' in plan or 'QPS' in plan or '吞吐量' in plan
        if not has_performance:
            issues.append("方案缺少性能指标章节，应包含响应时间、吞吐量、资源消耗等性能指标")

    # 第 4 次审议：检查安全审计
    elif rejection_count == 4:
        has_security = '安全' in plan or '权限' in plan or '加密' in plan or '审计日志' in plan
        if not has_security:
            issues.append("方案缺少安全审计章节，应包含权限控制、数据加密、审计日志等安全措施")

    return {
        'passed': len(issues) == 0,
        'issues': issues
    }

def _format_rejection_reason(issues: list) -> str:
    """
    格式化封驳理由

    Args:
        issues: 发现的问题列表

    Returns:
        格式化的封驳理由（不少于 20 字）
    """
    if not issues:
        return "方案存在质量问题，建议修改后重新提交。"

    reason = "门下省发现以下问题：\n\n"
    for i, issue in enumerate(issues, 1):
        reason += f"{i}. {issue}\n"

    reason += "\n请中书省针对上述问题修改方案后重新提交。"

    return reason

if __name__ == "__main__":
    # 测试用例
    print("=== call_mcp_agent.py 测试 ===\n")
    print("这个模块需要真实的任务ID进行测试")
    print("实际使用场景：由尚书省调度器调用\n")

    # 示例：如果有任务 ID，可以这样测试
    # test_task_id = "TASK-20260310-001"
    #
    # print("1. 测试调用中书省起草方案")
    # result = invoke_agent('zhongshu', {
    #     'task_id': test_task_id,
    #     'action': 'draft',
    #     'content': {}
    # })
    # print(json.dumps(result, ensure_ascii=False, indent=2))
    #
    # print("\n2. 测试调用门下省审议方案")
    # result = invoke_agent('menxia', {
    #     'task_id': test_task_id,
    #     'action': 'review',
    #     'content': {'version': 1}
    # })
    # print(json.dumps(result, ensure_ascii=False, indent=2))
    #
    # print("\n3. 测试质量检查")
    # test_plan = "## 测试方案\n这是一个测试"
    # check_result = _check_plan_quality(test_plan)
    # print(f"通过: {check_result['passed']}")
    # print(f"问题: {check_result['issues']}")

    print("提示：将上述注释代码取消注释，并提供真实任务ID即可测试")
    print("\n模块功能：")
    print("- invoke_agent(): 统一入口，路由到对应的 agent")
    print("- invoke_zhongshu_agent(): 调用中书省起草/修改方案")
    print("- invoke_menxia_agent(): 调用门下省审议方案")
    print("- _check_plan_quality(): 5 项基础质量检查")
