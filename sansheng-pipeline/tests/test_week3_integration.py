"""
Week 3 异常处理模块集成测试

测试超时监控和告警通知的协同工作
"""

import sys
import time
from pathlib import Path

# 添加 lib 目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from timeout_monitor import dispatch_with_timeout
from notification import notify_silijian, escalate_to_silijian


def test_integrated_workflow():
    """测试完整的超时告警流程"""
    print("=== 集成测试: 完整超时告警流程 ===\n")

    # 模拟一个慢速 agent
    def mock_slow_agent(agent, message):
        print(f"[{agent}] 开始执行: {message}")
        time.sleep(9)  # 模拟耗时操作
        print(f"[{agent}] 执行完成")
        return {"status": "completed", "data": "some result"}

    # 定义告警处理器
    def handle_50_warning(alert_info):
        print(f"\n>>> 一级告警处理器触发 <<<")
        print(f"    Agent: {alert_info['agent']}")
        print(f"    进度: {alert_info['percentage']}%\n")

    def handle_80_warning(alert_info):
        print(f"\n>>> 二级告警处理器触发 <<<")
        notify_silijian(alert_info)
        print()

    def handle_timeout(alert_info):
        print(f"\n>>> 超时处理器触发 <<<")
        escalate_to_silijian(alert_info)
        print()

    # 执行带监控的任务派发
    start = time.time()
    result = dispatch_with_timeout(
        agent="zhongshu",
        action="draft_plan",
        message="起草新功能方案",
        agent_handoff_func=mock_slow_agent,
        timeout_seconds=10,
        on_warn_50=handle_50_warning,
        on_warn_80=handle_80_warning,
        on_timeout=handle_timeout
    )
    elapsed = time.time() - start

    print(f"\n=== 执行结果 ===")
    print(f"耗时: {elapsed:.1f}s")
    print(f"结果: {result}")
    print(f"状态: {'✓ 成功' if result else '✗ 失败'}")


def test_timeout_escalation():
    """测试超时后的升级流程"""
    print("\n\n=== 集成测试: 超时升级流程 ===\n")

    def mock_timeout_agent(agent, message):
        print(f"[{agent}] 开始执行: {message}")
        time.sleep(11)  # 故意超时
        print(f"[{agent}] 执行完成（已超时）")
        return {"status": "completed"}

    def handle_timeout(alert_info):
        print(f"\n>>> 触发升级流程 <<<")
        event_id = escalate_to_silijian(alert_info)
        print(f"升级事件已记录: {event_id}\n")

    result = dispatch_with_timeout(
        agent="shangshu",
        action="decompose_task",
        message="拆解复杂任务",
        agent_handoff_func=mock_timeout_agent,
        timeout_seconds=10,
        on_timeout=handle_timeout
    )

    print(f"\n=== 执行结果 ===")
    print(f"结果: {result}")


def test_alert_logging():
    """测试告警日志记录"""
    print("\n\n=== 集成测试: 告警日志记录 ===\n")

    from audit_log import read_audit_log

    # 触发一系列告警
    alerts = [
        {
            "level": "一级告警",
            "agent": "test_agent_1",
            "action": "test_action_1",
            "elapsed": 500,
            "threshold": 1000,
            "percentage": 50
        },
        {
            "level": "二级告警",
            "agent": "test_agent_2",
            "action": "test_action_2",
            "elapsed": 800,
            "threshold": 1000,
            "percentage": 80
        }
    ]

    event_ids = []
    for alert in alerts:
        event_id = notify_silijian(alert)
        event_ids.append(event_id)
        print(f"记录告警: {event_id}")

    # 验证日志记录
    print("\n验证审计日志...")
    events = read_audit_log()
    alert_events = [e for e in events if e["event_id"] in event_ids]

    print(f"共记录 {len(alert_events)} 条告警审计日志")
    for event in alert_events:
        details = event.get("details", {})
        print(f"  - {event['event_id']}: {details.get('alert_level')} | {details.get('agent')}")

    # 验证完整性
    if len(alert_events) == len(alerts):
        print("\n✓ 日志记录完整")
    else:
        print(f"\n✗ 日志记录不完整（预期 {len(alerts)}，实际 {len(alert_events)}）")


if __name__ == "__main__":
    print("="*70)
    print("Week 3 异常处理模块集成测试")
    print("="*70)

    try:
        test_integrated_workflow()
        test_timeout_escalation()
        test_alert_logging()

        print("\n" + "="*70)
        print("所有集成测试完成")
        print("="*70)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
