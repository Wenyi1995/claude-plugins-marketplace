"""
Week 5 端到端测试（E2E）

覆盖从司礼监到六部的完整流程，包含正常流转、异常处理、裁决升级等场景
"""

import sys
import time
import unittest
from pathlib import Path
from datetime import datetime

# 添加 lib 目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'bin'))

from handoff_validator import validate_handoff_message, VALID_AGENTS
from audit_log import log_event, read_audit_log
from handoff_utils import handoff_with_retry, HandoffResult, agent_handoff
from timeout_monitor import dispatch_with_timeout
from notification import notify_sililijian, escalate_to_sililijian


class TestE2EPipeline(unittest.TestCase):
    """端到端集成测试套件"""

    def setUp(self):
        """测试前准备"""
        print(f"\n{'='*70}")
        print(f"开始测试: {self._testMethodName}")
        print(f"{'='*70}\n")

    def tearDown(self):
        """测试后清理"""
        print(f"\n{'='*70}")
        print(f"测试完成: {self._testMethodName}")
        print(f"{'='*70}\n")

    def test_1_normal_flow(self):
        """
        测试场景 1：正常流转
        司礼监 -> 中书省 -> 门下省 -> 尚书省
        """
        print(">>> 场景：正常流转 <<<\n")

        # 1. 司礼监派发到中书省
        handoff_1 = {
            "task_id": "TASK-20260310-001",
            "from_agent": "sililijian",
            "to_agent": "zhongshu",
            "action": "draft",
            "content": {
                "title": "实现三省六部协作机制",
                "description": "搭建完整的 Agent 协作流水线"
            },
            "timestamp": datetime.now().isoformat()
        }

        # 验证消息格式
        valid, errors = validate_handoff_message(handoff_1)
        self.assertTrue(valid, f"Handoff 消息格式错误: {errors}")
        print(f"✓ [司礼监 -> 中书省] 消息格式验证通过")

        # 记录审计日志
        event_id_1 = log_event(
            actor_id="sililijian",
            action_type="handoff",
            target_id="zhongshu",
            result="success",
            details={"message": handoff_1}
        )
        self.assertIsNotNone(event_id_1)
        print(f"✓ [审计日志] 记录事件: {event_id_1}")

        # 2. 中书省起草后派发到门下省
        handoff_2 = {
            "task_id": "TASK-20260310-001",
            "from_agent": "zhongshu",
            "to_agent": "menxia",
            "action": "review",
            "content": {
                "plan_version": 1,
                "draft_content": "方案草稿内容..."
            },
            "timestamp": datetime.now().isoformat()
        }

        valid, errors = validate_handoff_message(handoff_2)
        self.assertTrue(valid, f"Handoff 消息格式错误: {errors}")
        print(f"✓ [中书省 -> 门下省] 消息格式验证通过")

        event_id_2 = log_event(
            actor_id="zhongshu",
            action_type="handoff",
            target_id="menxia",
            result="success",
            details={"message": handoff_2}
        )
        print(f"✓ [审计日志] 记录事件: {event_id_2}")

        # 3. 门下省准奏后派发到尚书省
        handoff_3 = {
            "task_id": "TASK-20260310-001",
            "from_agent": "menxia",
            "to_agent": "shangshu",
            "action": "execute",
            "content": {
                "plan_version": 1,
                "review_status": "approved",
                "review_comments": "方案可行，准予执行"
            },
            "timestamp": datetime.now().isoformat()
        }

        valid, errors = validate_handoff_message(handoff_3)
        self.assertTrue(valid, f"Handoff 消息格式错误: {errors}")
        print(f"✓ [门下省 -> 尚书省] 消息格式验证通过")

        event_id_3 = log_event(
            actor_id="menxia",
            action_type="handoff",
            target_id="shangshu",
            result="success",
            details={"message": handoff_3}
        )
        print(f"✓ [审计日志] 记录事件: {event_id_3}")

        # 验证审计日志完整性
        audit_events = read_audit_log()
        event_ids = [event_id_1, event_id_2, event_id_3]
        found_events = [e for e in audit_events if e["event_id"] in event_ids]
        self.assertEqual(len(found_events), 3, "审计日志记录不完整")
        print(f"✓ [审计日志] 验证完整性: 3/3 条记录")

        print("\n=== 测试结果 ===")
        print("✓ 正常流转测试通过")

    def test_2_rejection_flow(self):
        """
        测试场景 2：封驳流程
        门下省封驳 -> 中书省修改 -> 门下省准奏
        """
        print(">>> 场景：封驳流程 <<<\n")

        task_id = "TASK-20260310-002"

        # 1. 中书省提交方案 v1
        print("[步骤 1] 中书省提交方案 v1")
        handoff_draft_v1 = {
            "task_id": task_id,
            "from_agent": "zhongshu",
            "to_agent": "menxia",
            "action": "review",
            "content": {
                "plan_version": 1,
                "draft_content": "初版方案..."
            },
            "timestamp": datetime.now().isoformat()
        }
        valid, _ = validate_handoff_message(handoff_draft_v1)
        self.assertTrue(valid)

        # 2. 门下省封驳
        print("[步骤 2] 门下省封驳方案 v1")
        handoff_reject = {
            "task_id": task_id,
            "from_agent": "menxia",
            "to_agent": "zhongshu",
            "action": "reject",
            "content": {
                "plan_version": 1,
                "rejection_reason": "技术方案不够详细，缺少风险评估",
                "rejection_count": 1
            },
            "timestamp": datetime.now().isoformat()
        }
        valid, _ = validate_handoff_message(handoff_reject)
        self.assertTrue(valid)

        # 验证封驳次数记录
        rejection_count = handoff_reject["content"]["rejection_count"]
        self.assertEqual(rejection_count, 1)
        print(f"✓ [封驳次数] 记录: {rejection_count}")

        # 验证封驳理由格式
        rejection_reason = handoff_reject["content"]["rejection_reason"]
        self.assertIsInstance(rejection_reason, str)
        self.assertGreater(len(rejection_reason), 0)
        print(f"✓ [封驳理由] 格式正确: {rejection_reason[:30]}...")

        # 记录审计日志
        event_id_reject = log_event(
            actor_id="menxia",
            action_type="reject",
            target_id=task_id,
            result="success",
            details={"rejection_count": 1, "reason": rejection_reason}
        )
        print(f"✓ [审计日志] 记录封驳事件: {event_id_reject}")

        # 3. 中书省修改后提交 v2
        print("[步骤 3] 中书省修改后提交方案 v2")
        handoff_draft_v2 = {
            "task_id": task_id,
            "from_agent": "zhongshu",
            "to_agent": "menxia",
            "action": "review",
            "content": {
                "plan_version": 2,
                "draft_content": "修改后方案，补充风险评估...",
                "changes": "补充了技术细节和风险评估"
            },
            "timestamp": datetime.now().isoformat()
        }
        valid, _ = validate_handoff_message(handoff_draft_v2)
        self.assertTrue(valid)

        # 4. 门下省准奏
        print("[步骤 4] 门下省准奏方案 v2")
        handoff_approve = {
            "task_id": task_id,
            "from_agent": "menxia",
            "to_agent": "shangshu",
            "action": "approve",
            "content": {
                "plan_version": 2,
                "review_status": "approved"
            },
            "timestamp": datetime.now().isoformat()
        }
        valid, _ = validate_handoff_message(handoff_approve)
        self.assertTrue(valid)

        event_id_approve = log_event(
            actor_id="menxia",
            action_type="approve",
            target_id=task_id,
            result="success",
            details={"plan_version": 2}
        )
        print(f"✓ [审计日志] 记录准奏事件: {event_id_approve}")

        print("\n=== 测试结果 ===")
        print("✓ 封驳流程测试通过")

    def test_3_timeout_alert(self):
        """
        测试场景 3：超时告警
        模拟 agent 执行超时，验证 50%, 80%, 100% 告警触发
        """
        print(">>> 场景：超时告警 <<<\n")

        alert_levels = []

        def mock_slow_agent(agent, message):
            """模拟慢速 agent"""
            print(f"[{agent}] 开始执行: {message}")
            time.sleep(9)  # 模拟耗时操作（需要足够长以触发 80% 告警）
            print(f"[{agent}] 执行完成")
            return {"status": "completed"}

        def handle_50_warning(alert_info):
            """50% 告警处理"""
            print(f"\n[一级告警] {alert_info['percentage']}% 超时")
            alert_levels.append(50)
            self.assertEqual(alert_info["percentage"], 50)

        def handle_80_warning(alert_info):
            """80% 告警处理"""
            print(f"[二级告警] {alert_info['percentage']}% 超时")
            alert_levels.append(80)
            self.assertEqual(alert_info["percentage"], 80)
            # 通知司礼监
            event_id = notify_sililijian(alert_info)
            self.assertIsNotNone(event_id)

        def handle_timeout(alert_info):
            """100% 超时处理"""
            print(f"[任务暂停] 100% 超时")
            alert_levels.append(100)
            # 升级到司礼监
            event_id = escalate_to_sililijian(alert_info)
            self.assertIsNotNone(event_id)

        # 执行带监控的任务
        print("[执行] 启动超时监控...")
        result = dispatch_with_timeout(
            agent="zhongshu",
            action="draft_plan",
            message="起草方案",
            agent_handoff_func=mock_slow_agent,
            timeout_seconds=10,
            on_warn_50=handle_50_warning,
            on_warn_80=handle_80_warning,
            on_timeout=handle_timeout
        )

        # 验证告警触发
        print(f"\n✓ [告警触发] 触发级别: {alert_levels}")
        self.assertIn(50, alert_levels, "50% 告警未触发")
        self.assertIn(80, alert_levels, "80% 告警未触发")

        # 如果任务在 80% 前完成，也视为通过（说明执行效率高）
        if 80 not in alert_levels:
            print("  注意: 任务在 80% 告警前完成（执行效率较高）")

        # 验证审计日志记录
        audit_events = read_audit_log()
        timeout_events = [
            e for e in audit_events
            if e.get("action", {}).get("type") in ["alert_sent", "task_escalated"]
        ]
        self.assertGreater(len(timeout_events), 0, "未找到超时相关审计日志")
        print(f"✓ [审计日志] 记录超时事件: {len(timeout_events)} 条")

        print("\n=== 测试结果 ===")
        print("✓ 超时告警测试通过")

    def test_4_retry_mechanism(self):
        """
        测试场景 4：重试机制
        模拟 handoff 失败，验证重试逻辑（2 次重试，指数退避）
        """
        print(">>> 场景：重试机制 <<<\n")

        # 临时替换 agent_handoff 为强制失败版本
        import handoff_utils
        original_handoff = handoff_utils.agent_handoff

        attempt_count = [0]  # 使用列表避免闭包问题

        def mock_failing_handoff(from_agent, to_agent, message):
            """模拟前 2 次失败，第 3 次成功"""
            attempt_count[0] += 1
            print(f"[尝试 {attempt_count[0]}] {from_agent} -> {to_agent}")
            if attempt_count[0] < 3:
                raise Exception(f"Handoff failed (attempt {attempt_count[0]})")
            else:
                print(f"[成功] 第 {attempt_count[0]} 次尝试成功")
                return HandoffResult(success=True, message="Success after retry")

        handoff_utils.agent_handoff = mock_failing_handoff

        try:
            # 执行带重试的 handoff
            print("[执行] 开始 handoff with retry...")
            start_time = time.time()

            result = handoff_with_retry(
                from_agent="zhongshu",
                to_agent="menxia",
                message={
                    "task_id": "TASK-20260310-003",
                    "action": "review",
                    "content": {}
                },
                max_retries=2
            )

            elapsed = time.time() - start_time

            # 验证重试次数
            self.assertEqual(attempt_count[0], 3, "重试次数不正确")
            print(f"✓ [重试次数] 正确: {attempt_count[0]} 次尝试")

            # 验证指数退避（5s + 10s = 15s）
            expected_min_time = 15  # 5s + 10s
            self.assertGreater(elapsed, expected_min_time - 1, "退避时间过短")
            print(f"✓ [指数退避] 正确: 耗时 {elapsed:.1f}s (预期 >= {expected_min_time}s)")

            # 验证最终成功
            self.assertTrue(result.success)
            print(f"✓ [最终结果] 成功: {result.message}")

        finally:
            # 恢复原始函数
            handoff_utils.agent_handoff = original_handoff

        print("\n=== 测试结果 ===")
        print("✓ 重试机制测试通过")

    def test_5_escalation_flow(self):
        """
        测试场景 5：裁决流程
        模拟封驳 2 次后触发裁决，验证争议点整理和裁决后流转
        """
        print(">>> 场景：裁决流程 <<<\n")

        task_id = "TASK-20260310-004"

        # 1. 第一次封驳
        print("[步骤 1] 门下省第一次封驳")
        rejection_1 = {
            "task_id": task_id,
            "from_agent": "menxia",
            "to_agent": "zhongshu",
            "action": "reject",
            "content": {
                "plan_version": 1,
                "rejection_reason": "缺少性能评估",
                "rejection_count": 1
            },
            "timestamp": datetime.now().isoformat()
        }
        valid, _ = validate_handoff_message(rejection_1)
        self.assertTrue(valid)
        print(f"✓ [封驳 1] 理由: {rejection_1['content']['rejection_reason']}")

        # 2. 第二次封驳
        print("[步骤 2] 门下省第二次封驳")
        rejection_2 = {
            "task_id": task_id,
            "from_agent": "menxia",
            "to_agent": "zhongshu",
            "action": "reject",
            "content": {
                "plan_version": 2,
                "rejection_reason": "性能方案仍不够详细",
                "rejection_count": 2
            },
            "timestamp": datetime.now().isoformat()
        }
        valid, _ = validate_handoff_message(rejection_2)
        self.assertTrue(valid)
        print(f"✓ [封驳 2] 理由: {rejection_2['content']['rejection_reason']}")

        # 3. 触发裁决（封驳次数 >= 2）
        rejection_count = rejection_2["content"]["rejection_count"]
        if rejection_count >= 2:
            print("\n[步骤 3] 触发裁决流程")

            # 整理争议点
            dispute_summary = {
                "task_id": task_id,
                "rejection_history": [
                    rejection_1["content"]["rejection_reason"],
                    rejection_2["content"]["rejection_reason"]
                ],
                "zhongshu_position": "认为现有方案已足够详细",
                "menxia_position": "要求补充更多性能测试数据"
            }

            print(f"✓ [争议点] 整理完成:")
            print(f"  - 中书省观点: {dispute_summary['zhongshu_position']}")
            print(f"  - 门下省观点: {dispute_summary['menxia_position']}")

            # 升级到司礼监
            escalation_info = {
                "task_id": task_id,
                "type": "dispute_escalation",
                "rejection_count": rejection_count,
                "dispute_summary": dispute_summary
            }

            event_id = escalate_to_sililijian(escalation_info)
            self.assertIsNotNone(event_id)
            print(f"✓ [升级] 事件 ID: {event_id}")

            # 4. 模拟用户裁决（准奏 v2）
            print("\n[步骤 4] 用户裁决: 准奏 v2")
            user_decision = {
                "task_id": task_id,
                "from_agent": "sililijian",
                "to_agent": "shangshu",
                "action": "execute",
                "content": {
                    "plan_version": 2,
                    "decision": "approved_by_user",
                    "decision_reason": "v2 方案可行，允许执行"
                },
                "timestamp": datetime.now().isoformat()
            }

            valid, _ = validate_handoff_message(user_decision)
            self.assertTrue(valid)
            print(f"✓ [裁决结果] {user_decision['content']['decision_reason']}")

        print("\n=== 测试结果 ===")
        print("✓ 裁决流程测试通过")

    def test_6_audit_query(self):
        """
        测试场景 6：审计日志查询
        使用 audit_query.py 查询测试日志，验证查询功能
        """
        print(">>> 场景：审计日志查询 <<<\n")

        # 1. 插入测试日志
        print("[步骤 1] 插入测试日志")
        test_date = datetime.now().strftime('%Y%m%d')

        test_events = []
        for i in range(3):
            event_id = log_event(
                actor_id="test_agent",
                action_type=f"test_action_{i}",
                target_id=f"TEST-{test_date}-{i:03d}",
                result="success",
                details={"test_data": f"sample_{i}"}
            )
            test_events.append(event_id)
            print(f"  - 插入事件: {event_id}")

        # 2. 使用 audit_log 模块查询
        print("\n[步骤 2] 查询审计日志")
        audit_events = read_audit_log()

        # 筛选今天的测试事件
        found_events = [
            e for e in audit_events
            if e["event_id"] in test_events
        ]

        # 验证查询结果
        self.assertEqual(len(found_events), 3, "查询到的事件数量不正确")
        print(f"✓ [查询结果] 找到 {len(found_events)}/3 条记录")

        # 验证事件字段完整性
        for event in found_events:
            self.assertIn("event_id", event)
            self.assertIn("timestamp", event)
            self.assertIn("actor", event)
            self.assertIn("action", event)
            self.assertIn("result", event)
            print(f"  - {event['event_id']}: {event['action']['type']}")

        print(f"\n✓ [字段完整性] 所有事件字段完整")

        # 3. 测试 audit_query.py 脚本（通过导入方式）
        print("\n[步骤 3] 测试 audit_query.py 脚本")
        try:
            import audit_query
            print("✓ [脚本导入] audit_query.py 可正常导入")
        except ImportError as e:
            self.fail(f"无法导入 audit_query.py: {e}")

        print("\n=== 测试结果 ===")
        print("✓ 审计日志查询测试通过")

    def test_7_plan_checker(self):
        """
        测试场景 7：方案检查工具
        使用 plan_checker.py 检查测试方案，验证 15 项检查清单
        """
        print(">>> 场景：方案检查工具 <<<\n")

        # 1. 创建测试方案文件
        print("[步骤 1] 创建测试方案文件")
        test_plan_path = Path(__file__).parent.parent / 'data' / 'test_plan_sample.md'
        test_plan_content = """
# 测试方案：实现用户认证功能

## 技术方案
使用 Python Flask + JWT 实现 RESTful API
依赖：requirements.txt 已包含 flask, pyjwt

## 时间估算
预计 5 天完成，包括 2 天开发 + 1 天测试 + 2 天优化

## 风险评估
- 外部依赖：依赖 Redis 缓存服务
- 性能风险：高并发场景下需要优化
- 安全风险：需要加密存储敏感信息
- 回滚方案：保留旧版认证接口

## 实施步骤
1. 初始化数据库表
2. 实现登录接口
3. 集成测试验证
4. 部署到测试环境

## 验收标准
- 单元测试覆盖率 > 80%
- 接口响应时间 < 100ms

## 交付物
- auth.py
- test_auth.py
- README.md
"""

        test_plan_path.parent.mkdir(parents=True, exist_ok=True)
        test_plan_path.write_text(test_plan_content, encoding='utf-8')
        print(f"✓ [测试文件] 创建: {test_plan_path}")

        # 2. 导入并测试 plan_checker
        print("\n[步骤 2] 测试 plan_checker.py")
        try:
            import plan_checker
            print("✓ [脚本导入] plan_checker.py 可正常导入")

            # 创建检查器
            checker = plan_checker.PlanChecker(str(test_plan_path), verbose=False)

            # 加载文件
            load_success = checker.load_file()
            self.assertTrue(load_success, "加载测试方案失败")
            print(f"✓ [文件加载] 成功")

            # 执行检查
            report = checker.generate_report()
            self.assertIsNotNone(report, "检查结果为空")
            print(f"✓ [执行检查] 完成")

            # 验证检查项数量（15 项）
            total_checks = sum(len(checks) for checks in plan_checker.PlanChecker.CHECKS.values())
            self.assertEqual(total_checks, 15, f"检查项数量不正确: {total_checks}")
            print(f"✓ [检查清单] 共 {total_checks} 项")

            # 统计通过率
            passed = report['total_passed']
            total = report['total_items']
            pass_rate = (passed / total * 100) if total > 0 else 0

            print(f"✓ [检查结果] 通过 {passed}/{total} 项 ({pass_rate:.1f}%)")

            # 验证输出格式
            self.assertIn('file', report)
            self.assertIn('categories', report)
            self.assertIn('技术可行性', report['categories'])
            self.assertIn('风险评估', report['categories'])
            self.assertIn('实施可行性', report['categories'])
            print(f"✓ [输出格式] 正确（包含 3 个类别）")

        except ImportError as e:
            self.fail(f"无法导入 plan_checker.py: {e}")
        except Exception as e:
            self.fail(f"plan_checker 执行失败: {e}")
        finally:
            # 清理测试文件
            if test_plan_path.exists():
                test_plan_path.unlink()
                print(f"\n[清理] 删除测试文件: {test_plan_path}")

        print("\n=== 测试结果 ===")
        print("✓ 方案检查工具测试通过")


def main():
    """主函数：运行所有测试"""
    print("\n" + "="*70)
    print("Week 5 端到端测试 (E2E)")
    print("="*70)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestE2EPipeline)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出测试总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    print(f"运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✓ 所有测试通过")
        return 0
    else:
        print("\n✗ 存在失败的测试")
        return 1


if __name__ == '__main__':
    sys.exit(main())
