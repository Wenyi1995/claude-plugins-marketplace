"""
告警通知模块

负责将告警信息通知司礼监并记录审计日志
"""

import sys
from pathlib import Path
from typing import Dict, Any

# 兼容不同导入场景
try:
    from .audit_log import log_event
except ImportError:
    # 支持直接运行或从外部脚本导入
    sys.path.insert(0, str(Path(__file__).parent))
    from audit_log import log_event


def notify_silijian(alert_info: Dict[str, Any]) -> str:
    """
    通知司礼监（告警信息）

    Args:
        alert_info: 告警信息字典，包含：
            - level: 告警级别（一级告警/二级告警/任务暂停）
            - agent: Agent ID
            - action: 操作类型
            - elapsed: 已耗时（秒）
            - threshold: 超时阈值（秒）
            - percentage: 超时百分比
            - message: 告警消息（可选）

    Returns:
        event_id: 审计日志事件 ID
    """
    level = alert_info.get("level", "未知级别")
    agent = alert_info.get("agent", "unknown")
    action = alert_info.get("action", "unknown")
    elapsed = alert_info.get("elapsed", 0)
    threshold = alert_info.get("threshold", 0)
    percentage = alert_info.get("percentage", 0)

    # 构造告警消息
    if "message" in alert_info:
        message = alert_info["message"]
    else:
        message = f"{agent} 执行 {action} 已耗时 {elapsed:.1f}s，达到超时阈值的 {percentage}%（阈值 {threshold}s）"

    # 打印告警到控制台
    print(f"\n{'='*60}")
    print(f"[通知司礼监] {level}")
    print(f"{'='*60}")
    print(f"Agent: {agent}")
    print(f"操作: {action}")
    print(f"已耗时: {elapsed:.1f}s / {threshold}s ({percentage}%)")
    print(f"消息: {message}")
    print(f"{'='*60}\n")

    # 记录到审计日志
    event_id = log_event(
        actor_id="timeout_monitor",
        action_type="alert_sent",
        target_id=f"{agent}:{action}",
        result="success",
        details={
            "alert_level": level,
            "agent": agent,
            "action": action,
            "elapsed_seconds": elapsed,
            "threshold_seconds": threshold,
            "percentage": percentage,
            "message": message
        }
    )

    # TODO: 未来可接入钉钉/企业微信通知
    # send_to_dingtalk(alert_info)
    # send_to_wecom(alert_info)

    return event_id


def escalate_to_silijian(alert_info: Dict[str, Any]) -> str:
    """
    升级到司礼监（任务暂停，需要人工接管）

    这是 notify_silijian 的增强版本，用于 100% 超时的紧急情况

    Args:
        alert_info: 告警信息字典，必须包含 action 字段

    Returns:
        event_id: 审计日志事件 ID
    """
    # 添加紧急标记
    alert_info["level"] = "任务暂停"
    alert_info["urgent"] = True

    # 如果没有自定义消息，生成默认消息
    if "message" not in alert_info:
        agent = alert_info.get("agent", "unknown")
        action = alert_info.get("action", "unknown")
        alert_info["message"] = f"{agent} 执行 {action} 超时，任务已暂停，需要人工接管"

    # 记录升级动作到审计日志
    event_id = log_event(
        actor_id="timeout_monitor",
        action_type="task_escalated",
        target_id=f"{alert_info.get('agent', 'unknown')}:{alert_info.get('action', 'unknown')}",
        result="escalated",
        details={
            "reason": "timeout",
            "alert_info": alert_info
        }
    )

    # 调用标准通知
    notify_silijian(alert_info)

    return event_id


def pause_task() -> None:
    """
    暂停任务（占位实现）

    当前只打印消息，未来可以：
    - 设置任务状态为 PAUSED
    - 释放资源（内存、GPU）
    - 保存中间状态到磁盘
    """
    print("[SYSTEM] 任务已暂停，等待人工接管")


if __name__ == "__main__":
    # 自测用例
    print("=== 测试用例 1: 一级告警（50%）===")
    event_id = notify_silijian({
        "level": "一级告警",
        "agent": "zhongshu",
        "action": "draft_plan",
        "elapsed": 900.5,
        "threshold": 1800,
        "percentage": 50
    })
    print(f"审计日志 event_id: {event_id}\n")

    print("=== 测试用例 2: 二级告警（80%）===")
    event_id = notify_silijian({
        "level": "二级告警",
        "agent": "menxia",
        "action": "review_plan",
        "elapsed": 720.3,
        "threshold": 900,
        "percentage": 80,
        "message": "审议方案接近超时，建议人工介入"
    })
    print(f"审计日志 event_id: {event_id}\n")

    print("=== 测试用例 3: 任务暂停（100%）===")
    event_id = escalate_to_silijian({
        "agent": "shangshu",
        "action": "decompose_task",
        "elapsed": 610.0,
        "threshold": 600,
        "percentage": 100
    })
    print(f"审计日志 event_id: {event_id}\n")

    print("=== 测试用例 4: 验证审计日志集成 ===")
    from audit_log import read_audit_log

    events = read_audit_log()
    recent_alerts = [e for e in events if e["action"]["type"] in ["alert_sent", "task_escalated"]]

    print(f"今日共记录 {len(recent_alerts)} 条告警相关的审计日志")
    for event in recent_alerts[-3:]:  # 显示最后 3 条
        details = event.get("details", {})
        print(f"  - {event['event_id']}: {details.get('alert_level', 'N/A')} | {details.get('agent', 'N/A')} | {details.get('action', 'N/A')}")

    print("\n=== 测试用例 5: 验证告警信息完整性 ===")
    if recent_alerts:
        sample = recent_alerts[-1]
        required_fields = ["alert_level", "agent", "action", "elapsed_seconds", "threshold_seconds", "percentage"]
        details = sample.get("details", {})
        missing = [f for f in required_fields if f not in details]

        if not missing:
            print("告警信息完整性验证通过")
            print(f"示例: {details.get('agent')} 执行 {details.get('action')} 耗时 {details.get('elapsed_seconds')}s，达到 {details.get('percentage')}%")
        else:
            print(f"告警信息缺少字段: {missing}")
