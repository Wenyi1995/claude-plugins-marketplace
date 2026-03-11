"""
审计日志模块

记录所有关键操作到审计日志，支持追溯和审查
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


# 审计日志存储目录
AUDIT_LOG_DIR = Path(__file__).parent.parent / 'data' / 'audit'
AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_event(
    actor_id: str,
    action_type: str,
    target_id: str,
    result: str,
    details: Optional[Dict[str, Any]] = None
) -> str:
    """
    记录一个审计事件

    Args:
        actor_id: 操作者 ID（Agent ID）
        action_type: 操作类型（如 plan_submitted, task_created）
        target_id: 目标资源 ID
        result: 操作结果（success/failure）
        details: 可选的详细信息字典

    Returns:
        event_id: 生成的事件 ID
    """
    event = {
        "event_id": f"EVT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.now().isoformat(),
        "actor": {
            "type": "agent",
            "id": actor_id
        },
        "action": {
            "type": action_type,
            "resource_id": target_id
        },
        "result": result,
        "details": details or {}
    }

    # 按日期存储到 JSONL 文件
    log_file = AUDIT_LOG_DIR / f"audit-{datetime.now().strftime('%Y%m%d')}.jsonl"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    return event["event_id"]


def read_audit_log(date: Optional[str] = None) -> list:
    """
    读取指定日期的审计日志

    Args:
        date: 日期字符串（YYYYMMDD），默认为今天

    Returns:
        审计事件列表
    """
    if date is None:
        date = datetime.now().strftime('%Y%m%d')

    log_file = AUDIT_LOG_DIR / f"audit-{date}.jsonl"

    if not log_file.exists():
        return []

    events = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))

    return events


if __name__ == "__main__":
    # 自测用例
    print("=== 测试用例 1: 记录成功事件 ===")
    event_id = log_event(
        actor_id="zhongshu",
        action_type="plan_submitted",
        target_id="TASK-20260310-001-v1",
        result="success",
        details={"version": 1, "plan_length": 1234}
    )
    print(f"记录成功，event_id: {event_id}")

    print("\n=== 测试用例 2: 记录失败事件 ===")
    event_id = log_event(
        actor_id="bingbu",
        action_type="code_execution",
        target_id="TASK-20260310-001-SUB-3",
        result="failure",
        details={"error": "syntax error", "line": 42}
    )
    print(f"记录成功，event_id: {event_id}")

    print("\n=== 测试用例 3: 读取今日日志 ===")
    events = read_audit_log()
    print(f"今日共 {len(events)} 条审计日志")
    for event in events[-2:]:  # 显示最后 2 条
        print(f"  - {event['event_id']}: {event['actor']['id']} -> {event['action']['type']} -> {event['result']}")

    print("\n=== 测试用例 4: 验证日志格式 ===")
    if events:
        sample_event = events[-1]
        required_fields = ["event_id", "timestamp", "actor", "action", "result", "details"]
        missing_fields = [f for f in required_fields if f not in sample_event]

        if not missing_fields:
            print("日志格式验证通过")
            print(f"示例事件: {json.dumps(sample_event, ensure_ascii=False, indent=2)}")
        else:
            print(f"日志格式错误，缺少字段: {missing_fields}")

    print("\n=== 测试用例 5: 验证 event_id 格式 ===")
    import re
    event_id_pattern = re.compile(r'^EVT-[0-9]{8}-[0-9a-f]{8}$')
    if events:
        sample_id = events[-1]["event_id"]
        if event_id_pattern.match(sample_id):
            print(f"event_id 格式正确: {sample_id}")
        else:
            print(f"event_id 格式错误: {sample_id}")
