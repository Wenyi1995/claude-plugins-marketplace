"""
Handoff 工具函数

提供带重试机制的 handoff 功能，自动处理失败和升级
"""

import time
from typing import Dict, Any


class HandoffResult:
    """Handoff 结果类"""
    def __init__(self, success: bool, message: str = "", data: Any = None):
        self.success = success
        self.message = message
        self.data = data


def agent_handoff(from_agent: str, to_agent: str, message: Dict[str, Any]) -> HandoffResult:
    """
    执行 Agent 之间的 handoff 操作（占位函数）

    在实际系统中，这个函数会调用真实的 handoff API
    目前返回模拟结果用于测试

    Args:
        from_agent: 发送方 Agent ID
        to_agent: 接收方 Agent ID
        message: handoff 消息

    Returns:
        HandoffResult 对象
    """
    # 模拟：90% 成功率
    import random
    if random.random() < 0.9:
        print(f"[HANDOFF] {from_agent} -> {to_agent}: 成功")
        return HandoffResult(success=True, message="Handoff successful")
    else:
        print(f"[HANDOFF] {from_agent} -> {to_agent}: 失败")
        raise Exception("Handoff failed: network timeout")


def escalate_to_sililijian(error_info: Dict[str, Any]) -> None:
    """
    将错误信息升级到司礼监（占位函数）

    在实际系统中，这个函数会发送通知给司礼监
    目前仅打印错误信息

    Args:
        error_info: 错误信息字典
    """
    print("\n" + "=" * 60)
    print("[ESCALATE TO SILILIJIAN] Handoff 失败，需要人工介入")
    print("=" * 60)
    print(f"错误类型: {error_info.get('error', 'unknown')}")
    print(f"发送方: {error_info.get('from', 'unknown')}")
    print(f"接收方: {error_info.get('to', 'unknown')}")
    print(f"尝试次数: {error_info.get('attempts', 0)}")
    print(f"最后错误: {error_info.get('last_error', 'unknown')}")
    print("=" * 60 + "\n")


def handoff_with_retry(
    from_agent: str,
    to_agent: str,
    message: Dict[str, Any],
    max_retries: int = 2
) -> HandoffResult:
    """
    带重试机制的 handoff 操作

    重试策略：
    - 最多重试 2 次（共 3 次尝试）
    - 指数退避：5s, 15s
    - 失败后升级到司礼监

    Args:
        from_agent: 发送方 Agent ID
        to_agent: 接收方 Agent ID
        message: handoff 消息
        max_retries: 最大重试次数（默认 2）

    Returns:
        HandoffResult 对象

    Raises:
        Exception: 超过最大重试次数后抛出异常
    """
    for retry_count in range(max_retries + 1):
        try:
            # 调用 handoff API
            result = agent_handoff(from_agent, to_agent, message)
            if result.success:
                if retry_count > 0:
                    print(f"[RETRY] 第 {retry_count} 次重试成功")
                return result
        except Exception as e:
            if retry_count == max_retries:
                # 超过最大重试次数，升级到司礼监
                escalate_to_sililijian({
                    "error": "handoff_failed",
                    "from": from_agent,
                    "to": to_agent,
                    "attempts": retry_count + 1,
                    "last_error": str(e)
                })
                raise
            else:
                # 指数退避
                interval = 5 * (2 ** retry_count)
                print(f"[RETRY] 第 {retry_count + 1} 次尝试失败，{interval} 秒后重试...")
                time.sleep(interval)

    # 理论上不会到达这里
    raise Exception("Unexpected error in handoff_with_retry")


if __name__ == "__main__":
    # 自测用例
    print("=== 测试用例 1: 成功的 handoff（无重试）===")
    try:
        result = handoff_with_retry(
            from_agent="sililijian",
            to_agent="zhongshu",
            message={
                "task_id": "TASK-20260310-001",
                "action": "draft",
                "content": {"title": "测试任务"}
            }
        )
        print(f"结果: {result.message}\n")
    except Exception as e:
        print(f"失败: {e}\n")

    print("=== 测试用例 2: 失败后重试的 handoff ===")
    # 注意：由于 agent_handoff 是随机的，可能需要多次运行才能看到重试
    # 为了演示，我们可以临时修改成功率
    try:
        result = handoff_with_retry(
            from_agent="zhongshu",
            to_agent="menxia",
            message={
                "task_id": "TASK-20260310-002",
                "action": "review",
                "content": {"version": 1}
            }
        )
        print(f"结果: {result.message}\n")
    except Exception as e:
        print(f"失败并升级: {e}\n")

    print("=== 测试用例 3: 验证指数退避间隔 ===")
    print("理论退避时间:")
    for retry_count in range(3):
        interval = 5 * (2 ** retry_count)
        print(f"  第 {retry_count} 次重试: {interval} 秒")
