#!/usr/bin/env python3
"""
中书省和门下省的内部工具

这些工具只给对应的 agent 使用，不暴露给用户
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from task_state import get_task, add_plan_version, update_state, add_rejection

def zhongshu_internal(task_id: str, action: str, context: dict) -> dict:
    """
    中书省内部工具：起草或修改方案

    Args:
        task_id: 任务ID
        action: 'draft' 或 'revise'
        context: 上下文（初次起草或封驳理由）

    Returns:
        {'action': str, 'title': str, 'context': str, 'current_version': int, ...}
    """
    task = get_task(task_id)
    if not task:
        raise ValueError(f"任务 {task_id} 不存在")

    if action == 'draft':
        # 初次起草
        # 注意：实际的方案内容由中书省 agent 的 SOUL.md 逻辑生成
        # 这里只是返回任务信息，让 agent 知道要做什么
        return {
            'action': 'draft',
            'title': task['title'],
            'context': task['context'],
            'current_version': len(task['versions'])
        }
    elif action == 'revise':
        # 修改方案（响应封驳）
        rejection_count = len(task['rejections'])
        last_rejection = task['rejections'][-1] if task['rejections'] else None

        return {
            'action': 'revise',
            'title': task['title'],
            'context': task['context'],
            'rejection_count': rejection_count,
            'rejection_reason': last_rejection['reason'] if last_rejection else '',
            'previous_plan': task['versions'][-1]['plan'] if task['versions'] else '',
            'current_version': len(task['versions'])
        }
    else:
        raise ValueError(f"Unknown action: {action}")

def zhongshu_submit_plan(task_id: str, plan: str) -> dict:
    """
    中书省提交方案

    Args:
        task_id: 任务ID
        plan: 方案内容

    Returns:
        {'version': int, 'task_id': str, 'status': str}
    """
    task = get_task(task_id)
    if not task:
        raise ValueError(f"任务 {task_id} 不存在")

    version = add_plan_version(task_id, plan, 'zhongshu')
    update_state(task_id, 'reviewing', f'中书省已提交方案 v{version}')

    return {
        'version': version,
        'task_id': task_id,
        'status': 'submitted'
    }

def menxia_internal(task_id: str, version: int) -> dict:
    """
    门下省内部工具：获取待审议方案

    Args:
        task_id: 任务ID
        version: 方案版本号

    Returns:
        {'plan': str, 'version': int, 'rejection_count': int, 'task_id': str}
    """
    task = get_task(task_id)
    if not task:
        raise ValueError(f"任务 {task_id} 不存在")

    if not task['versions']:
        raise ValueError(f"任务 {task_id} 没有方案可审议")

    # 获取指定版本的方案
    plan_version = next((v for v in task['versions'] if v['version'] == version), None)
    if not plan_version:
        raise ValueError(f"方案版本 v{version} 不存在")

    return {
        'plan': plan_version['plan'],
        'version': version,
        'rejection_count': len(task['rejections']),
        'task_id': task_id
    }

def menxia_submit_decision(task_id: str, decision: str, reason: str = '') -> dict:
    """
    门下省提交审议决策

    Args:
        task_id: 任务ID
        decision: 'approved' 或 'rejected'
        reason: 封驳理由（仅 rejected 时需要）

    Returns:
        {'decision': str, 'task_id': str, 'version': int, ...}
    """
    task = get_task(task_id)
    if not task:
        raise ValueError(f"任务 {task_id} 不存在")

    current_version = len(task['versions'])

    if decision == 'approved':
        update_state(task_id, 'approved', f'门下省准奏方案 v{current_version}')
        return {
            'decision': 'approved',
            'task_id': task_id,
            'version': current_version
        }
    elif decision == 'rejected':
        if not reason or len(reason) < 20:
            raise ValueError("封驳理由不得少于 20 字")

        add_rejection(task_id, reason, 'menxia')
        update_state(task_id, 'planning', f'门下省封驳方案 v{current_version}，退回中书省修改')

        return {
            'decision': 'rejected',
            'task_id': task_id,
            'version': current_version,
            'reason': reason,
            'rejection_count': len(task['rejections'])
        }
    else:
        raise ValueError(f"Unknown decision: {decision}")

if __name__ == "__main__":
    # 测试用例（需要一个真实任务ID）
    import json

    print("=== agent_internal_tools.py 测试 ===")
    print("\n这个脚本需要真实的任务ID进行测试")
    print("实际使用场景：由中书省和门下省 agent 调用\n")

    # 示例：如果有任务 ID，可以这样测试
    # test_task_id = "TASK-20260310-001"
    #
    # print("1. 测试中书省起草")
    # draft_info = zhongshu_internal(test_task_id, 'draft', {})
    # print(json.dumps(draft_info, ensure_ascii=False, indent=2))
    #
    # print("\n2. 测试中书省提交方案")
    # result = zhongshu_submit_plan(test_task_id, "这是一个测试方案")
    # print(json.dumps(result, ensure_ascii=False, indent=2))
    #
    # print("\n3. 测试门下省获取方案")
    # plan_info = menxia_internal(test_task_id, version=1)
    # print(json.dumps(plan_info, ensure_ascii=False, indent=2))
    #
    # print("\n4. 测试门下省封驳")
    # decision = menxia_submit_decision(test_task_id, 'rejected', '理由太简略，需要更详细的实施步骤说明')
    # print(json.dumps(decision, ensure_ascii=False, indent=2))

    print("提示：将上述注释代码取消注释，并提供真实任务ID即可测试")
