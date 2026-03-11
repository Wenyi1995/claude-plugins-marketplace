"""
超时检测模块

监控 Agent 执行时长，按比例触发告警
"""

import time
from threading import Timer, Event
from typing import Callable, Any, Dict, Optional


# 超时阈值配置（单位：秒）
TIMEOUT_CONFIG = {
    "zhongshu": {
        "draft_plan": 1800,      # 起草方案：30分钟
        "revise_plan": 900,      # 修改方案：15分钟
    },
    "menxia": {
        "review_plan": 900,      # 审议方案：15分钟
    },
    "shangshu": {
        "decompose_task": 600,   # 任务拆解：10分钟
    },
    "liubu": {
        "execute_subtask": 3600, # 执行子任务：60分钟
    }
}


def get_timeout_seconds(agent: str, action: str) -> int:
    """
    获取指定 agent 和操作的超时阈值

    Args:
        agent: Agent ID（如 zhongshu, menxia）
        action: 操作类型（如 draft_plan, review_plan）

    Returns:
        超时秒数，默认 1800 秒（30分钟）
    """
    if agent in TIMEOUT_CONFIG and action in TIMEOUT_CONFIG[agent]:
        return TIMEOUT_CONFIG[agent][action]

    # 默认超时（30分钟）
    return 1800


class TimeoutMonitor:
    """超时监控器"""

    def __init__(
        self,
        agent: str,
        action: str,
        timeout_seconds: int,
        on_warn_50: Optional[Callable] = None,
        on_warn_80: Optional[Callable] = None,
        on_timeout: Optional[Callable] = None
    ):
        """
        初始化监控器

        Args:
            agent: Agent ID
            action: 操作类型
            timeout_seconds: 超时阈值（秒）
            on_warn_50: 50% 告警回调
            on_warn_80: 80% 告警回调
            on_timeout: 100% 超时回调
        """
        self.agent = agent
        self.action = action
        self.timeout_seconds = timeout_seconds
        self.start_time = time.time()
        self.completed = Event()

        self.on_warn_50 = on_warn_50
        self.on_warn_80 = on_warn_80
        self.on_timeout = on_timeout

        self.timers = []

    def start(self):
        """启动监控"""
        # 50% 告警
        timer_50 = Timer(self.timeout_seconds * 0.5, self._handle_warn_50)
        timer_50.daemon = True
        timer_50.start()
        self.timers.append(timer_50)

        # 80% 告警
        timer_80 = Timer(self.timeout_seconds * 0.8, self._handle_warn_80)
        timer_80.daemon = True
        timer_80.start()
        self.timers.append(timer_80)

        # 100% 超时
        timer_100 = Timer(self.timeout_seconds, self._handle_timeout)
        timer_100.daemon = True
        timer_100.start()
        self.timers.append(timer_100)

    def stop(self):
        """停止监控（任务完成）"""
        self.completed.set()
        for timer in self.timers:
            timer.cancel()

    def _handle_warn_50(self):
        """处理 50% 告警"""
        if not self.completed.is_set():
            elapsed = time.time() - self.start_time
            print(f"[WARNING] {self.agent} 执行 {self.action} 已耗时 {elapsed:.1f}s，达到超时阈值的 50%")

            if self.on_warn_50:
                self.on_warn_50({
                    "level": "一级告警",
                    "agent": self.agent,
                    "action": self.action,
                    "elapsed": elapsed,
                    "threshold": self.timeout_seconds,
                    "percentage": 50
                })

    def _handle_warn_80(self):
        """处理 80% 告警"""
        if not self.completed.is_set():
            elapsed = time.time() - self.start_time
            print(f"[CRITICAL] {self.agent} 执行 {self.action} 已耗时 {elapsed:.1f}s，达到超时阈值的 80%，建议人工介入")

            if self.on_warn_80:
                self.on_warn_80({
                    "level": "二级告警",
                    "agent": self.agent,
                    "action": self.action,
                    "elapsed": elapsed,
                    "threshold": self.timeout_seconds,
                    "percentage": 80
                })

    def _handle_timeout(self):
        """处理 100% 超时"""
        if not self.completed.is_set():
            elapsed = time.time() - self.start_time
            print(f"[TIMEOUT] {self.agent} 执行 {self.action} 超时（{elapsed:.1f}s），任务暂停，需要人工接管")

            if self.on_timeout:
                self.on_timeout({
                    "level": "任务暂停",
                    "agent": self.agent,
                    "action": self.action,
                    "elapsed": elapsed,
                    "threshold": self.timeout_seconds,
                    "percentage": 100
                })


def dispatch_with_timeout(
    agent: str,
    action: str,
    message: str,
    agent_handoff_func: Callable[[str, str], Any],
    timeout_seconds: Optional[int] = None,
    on_warn_50: Optional[Callable] = None,
    on_warn_80: Optional[Callable] = None,
    on_timeout: Optional[Callable] = None
) -> Any:
    """
    带超时监控的任务派发

    Args:
        agent: 目标 Agent ID
        action: 操作类型
        message: 派发消息
        agent_handoff_func: Agent handoff 函数（接收 agent, message，返回结果）
        timeout_seconds: 超时阈值（秒），None 则使用配置的默认值
        on_warn_50: 50% 告警回调
        on_warn_80: 80% 告警回调
        on_timeout: 100% 超时回调

    Returns:
        Agent 执行结果
    """
    if timeout_seconds is None:
        timeout_seconds = get_timeout_seconds(agent, action)

    monitor = TimeoutMonitor(
        agent=agent,
        action=action,
        timeout_seconds=timeout_seconds,
        on_warn_50=on_warn_50,
        on_warn_80=on_warn_80,
        on_timeout=on_timeout
    )

    monitor.start()

    try:
        result = agent_handoff_func(agent, message)
        return result
    finally:
        monitor.stop()


if __name__ == "__main__":
    # 自测用例
    print("=== 测试用例 1: 正常完成（无告警）===")

    def mock_agent_fast(agent, message):
        print(f"  [{agent}] 收到任务: {message}")
        time.sleep(1)  # 模拟快速完成
        return {"status": "success"}

    result = dispatch_with_timeout(
        agent="zhongshu",
        action="draft_plan",
        message="起草方案",
        agent_handoff_func=mock_agent_fast,
        timeout_seconds=10
    )
    print(f"结果: {result}\n")

    print("=== 测试用例 2: 触发 50% 告警 ===")

    def mock_agent_slow(agent, message):
        print(f"  [{agent}] 收到任务: {message}")
        time.sleep(6)  # 模拟慢速执行
        return {"status": "success"}

    def warn_50_handler(alert_info):
        print(f"  >>> 50% 告警触发: {alert_info}")

    result = dispatch_with_timeout(
        agent="zhongshu",
        action="draft_plan",
        message="起草方案",
        agent_handoff_func=mock_agent_slow,
        timeout_seconds=10,
        on_warn_50=warn_50_handler
    )
    print(f"结果: {result}\n")

    print("=== 测试用例 3: 触发 80% 告警 ===")

    def mock_agent_very_slow(agent, message):
        print(f"  [{agent}] 收到任务: {message}")
        time.sleep(9)  # 模拟很慢执行
        return {"status": "success"}

    def warn_80_handler(alert_info):
        print(f"  >>> 80% 告警触发: {alert_info}")

    result = dispatch_with_timeout(
        agent="menxia",
        action="review_plan",
        message="审议方案",
        agent_handoff_func=mock_agent_very_slow,
        timeout_seconds=10,
        on_warn_50=warn_50_handler,
        on_warn_80=warn_80_handler
    )
    print(f"结果: {result}\n")

    print("=== 测试用例 4: 触发 100% 超时 ===")

    def mock_agent_timeout(agent, message):
        print(f"  [{agent}] 收到任务: {message}")
        time.sleep(12)  # 模拟超时
        return {"status": "success"}

    def timeout_handler(alert_info):
        print(f"  >>> 100% 超时触发: {alert_info}")

    result = dispatch_with_timeout(
        agent="shangshu",
        action="decompose_task",
        message="任务拆解",
        agent_handoff_func=mock_agent_timeout,
        timeout_seconds=10,
        on_warn_50=warn_50_handler,
        on_warn_80=warn_80_handler,
        on_timeout=timeout_handler
    )
    print(f"结果: {result}\n")

    print("=== 测试用例 5: 验证配置读取 ===")
    test_cases = [
        ("zhongshu", "draft_plan", 1800),
        ("zhongshu", "revise_plan", 900),
        ("menxia", "review_plan", 900),
        ("shangshu", "decompose_task", 600),
        ("liubu", "execute_subtask", 3600),
        ("unknown_agent", "unknown_action", 1800),  # 默认值
    ]

    for agent, action, expected in test_cases:
        actual = get_timeout_seconds(agent, action)
        status = "✓" if actual == expected else "✗"
        print(f"  {status} {agent}.{action}: {actual}s (预期 {expected}s)")
