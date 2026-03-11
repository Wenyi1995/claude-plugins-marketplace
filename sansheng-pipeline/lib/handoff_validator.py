"""
Handoff 消息验证器

根据三省信息流转标准格式验证 handoff 消息的合法性
"""

import re
from datetime import datetime
from typing import Tuple, List, Dict, Any


# 合法的 Agent ID 枚举
VALID_AGENTS = {
    "silijian", "zhongshu", "menxia", "shangshu",
    "libu1", "hubu", "libu2", "bingbu", "xingbu", "gongbu"
}

# 合法的 Action 类型枚举
VALID_ACTIONS = {
    "draft", "revise", "review", "approve", "reject", "escalate", "execute", "report"
}

# Task ID 格式正则：TASK-YYYYMMDD-NNN
TASK_ID_PATTERN = re.compile(r'^TASK-[0-9]{8}-[0-9]{3}$')


def validate_handoff_message(message: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    验证 handoff 消息是否符合标准格式

    Args:
        message: handoff 消息字典

    Returns:
        (是否通过, 错误列表)
    """
    errors = []

    # 检查必填字段
    required_fields = ["task_id", "from_agent", "to_agent", "action", "content", "timestamp"]
    for field in required_fields:
        if field not in message:
            errors.append(f"缺少必填字段: {field}")

    # 如果缺少必填字段，直接返回
    if errors:
        return False, errors

    # 验证 task_id 格式
    task_id = message.get("task_id")
    if not TASK_ID_PATTERN.match(task_id):
        errors.append(f"task_id 格式错误: {task_id}，应为 TASK-YYYYMMDD-NNN")

    # 验证 from_agent
    from_agent = message.get("from_agent")
    if from_agent not in VALID_AGENTS:
        errors.append(f"from_agent 非法: {from_agent}，合法值: {VALID_AGENTS}")

    # 验证 to_agent
    to_agent = message.get("to_agent")
    if to_agent not in VALID_AGENTS:
        errors.append(f"to_agent 非法: {to_agent}，合法值: {VALID_AGENTS}")

    # 验证 action
    action = message.get("action")
    if action not in VALID_ACTIONS:
        errors.append(f"action 非法: {action}，合法值: {VALID_ACTIONS}")

    # 验证 timestamp 格式（ISO 8601）
    timestamp = message.get("timestamp")
    try:
        # 尝试解析 ISO 8601 格式，严格检查必须包含 'T' 分隔符
        if not timestamp:
            raise ValueError("timestamp is empty")
        if 'T' not in timestamp:
            raise ValueError("timestamp must contain 'T' separator")
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    except (ValueError, AttributeError, TypeError) as e:
        errors.append(f"timestamp 格式错误: {timestamp}，应为 ISO 8601 格式（如 2026-03-10T10:00:00Z）")

    # 验证 content 是否为对象
    content = message.get("content")
    if not isinstance(content, dict):
        errors.append(f"content 必须是对象，当前类型: {type(content).__name__}")

    # 验证可选字段格式（如果存在）
    if "priority" in message:
        priority = message["priority"]
        if priority not in {"P0", "P1", "P2"}:
            errors.append(f"priority 非法: {priority}，合法值: P0, P1, P2")

    if "deadline" in message:
        deadline = message["deadline"]
        try:
            datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            errors.append(f"deadline 格式错误: {deadline}，应为 ISO 8601 格式")

    if "attachments" in message:
        attachments = message["attachments"]
        if not isinstance(attachments, list):
            errors.append(f"attachments 必须是数组，当前类型: {type(attachments).__name__}")
        else:
            for idx, att in enumerate(attachments):
                if not isinstance(att, dict):
                    errors.append(f"attachments[{idx}] 必须是对象")
                elif "type" in att and att["type"] not in {"plan", "code", "doc", "log"}:
                    errors.append(f"attachments[{idx}].type 非法: {att['type']}")

    return len(errors) == 0, errors


if __name__ == "__main__":
    # 自测用例
    print("=== 测试用例 1: 正常消息 ===")
    valid_message = {
        "task_id": "TASK-20260310-001",
        "from_agent": "silijian",
        "to_agent": "zhongshu",
        "action": "draft",
        "content": {
            "title": "实现用户注册系统",
            "context": "需要支持手机号+验证码登录"
        },
        "timestamp": "2026-03-10T10:00:00Z",
        "priority": "P1"
    }
    is_valid, errors = validate_handoff_message(valid_message)
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    if errors:
        print(f"错误: {errors}")

    print("\n=== 测试用例 2: 缺少必填字段 ===")
    missing_field_message = {
        "task_id": "TASK-20260310-001",
        "from_agent": "silijian",
        "action": "draft"
    }
    is_valid, errors = validate_handoff_message(missing_field_message)
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    print(f"错误: {errors}")

    print("\n=== 测试用例 3: task_id 格式错误 ===")
    invalid_task_id_message = {
        "task_id": "TASK-123-45",
        "from_agent": "silijian",
        "to_agent": "zhongshu",
        "action": "draft",
        "content": {},
        "timestamp": "2026-03-10T10:00:00Z"
    }
    is_valid, errors = validate_handoff_message(invalid_task_id_message)
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    print(f"错误: {errors}")

    print("\n=== 测试用例 4: 非法 agent ID ===")
    invalid_agent_message = {
        "task_id": "TASK-20260310-001",
        "from_agent": "invalid_agent",
        "to_agent": "zhongshu",
        "action": "draft",
        "content": {},
        "timestamp": "2026-03-10T10:00:00Z"
    }
    is_valid, errors = validate_handoff_message(invalid_agent_message)
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    print(f"错误: {errors}")

    print("\n=== 测试用例 5: 非法 action 类型 ===")
    invalid_action_message = {
        "task_id": "TASK-20260310-001",
        "from_agent": "silijian",
        "to_agent": "zhongshu",
        "action": "invalid_action",
        "content": {},
        "timestamp": "2026-03-10T10:00:00Z"
    }
    is_valid, errors = validate_handoff_message(invalid_action_message)
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    print(f"错误: {errors}")

    print("\n=== 测试用例 6: timestamp 格式错误 ===")
    invalid_timestamp_message = {
        "task_id": "TASK-20260310-001",
        "from_agent": "silijian",
        "to_agent": "zhongshu",
        "action": "draft",
        "content": {},
        "timestamp": "2026-03-10 10:00:00"
    }
    is_valid, errors = validate_handoff_message(invalid_timestamp_message)
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    print(f"错误: {errors}")
