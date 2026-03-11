#!/usr/bin/env python3
"""
六部集成测试 - 端到端验证

测试场景：
1. 任务拆解和分类
2. 子任务创建和状态管理
3. 结果汇总
"""
import sys
sys.path.insert(0, 'lib')

from task_state import create_task, get_task, create_subtask, update_subtask_status, get_subtasks
from task_decompose import classify_task_type, decompose_task, aggregate_results


def test_task_classification():
    """测试任务分类"""
    print("=== 测试 1: 任务分类 ===\n")

    test_cases = [
        ("创建新的 code-reviewer Agent", "libu-personnel"),
        ("为 Agent 准备历史数据", "hubu-resources"),
        ("从会话中提炼用户偏好规范", "libu-rites"),
        ("编写 task_decompose.py 文件", "bingbu-military"),
        ("执行集成测试验证流程", "gongbu-works"),
        ("审查代码质量和测试覆盖率", "xingbu-justice"),
    ]

    passed = 0
    for desc, expected in test_cases:
        result = classify_task_type(desc)
        status = "✅" if result == expected else "❌"
        print(f"{status} {desc}")
        print(f"   期望: {expected}, 实际: {result}\n")
        if result == expected:
            passed += 1

    print(f"通过: {passed}/{len(test_cases)}\n")
    return passed == len(test_cases)


def test_task_decomposition():
    """测试任务拆解"""
    print("=== 测试 2: 任务拆解 ===\n")

    # 模拟方案
    plan = """
## 执行步骤

步骤 1: 创建六部 Agent 基础设施
- 创建 6 个目录
- 编写 SOUL.md 文件
预计工时：5-6 小时

步骤 2: 实现尚书省调度逻辑
- 编写 task_decompose.py
- 更新 shangshu SOUL.md
预计工时：5-6 小时

步骤 3: 扩展状态管理
- 添加子任务管理函数
预计工时：1-2 小时
"""

    subtasks = decompose_task(plan, "TEST-001")

    print(f"拆解结果：{len(subtasks)} 个子任务\n")
    for i, st in enumerate(subtasks, 1):
        print(f"{i}. [{st['assigned_to']}] {st['title']}")
        print(f"   依赖: {st['dependencies']}\n")

    # 验证
    assert len(subtasks) == 3, f"预期 3 个子任务，实际 {len(subtasks)}"
    # 注意："创建六部 Agent" 包含 "Agent" 关键词，会被分类为吏部
    # 这是符合逻辑的，因为创建 Agent 属于吏部职责
    assert subtasks[1]['dependencies'] == [1], "步骤2 应依赖步骤1"

    print("✅ 任务拆解测试通过\n")
    return True


def test_subtask_management():
    """测试子任务管理"""
    print("=== 测试 3: 子任务管理 ===\n")

    # 创建测试任务
    task_id = create_task(
        title="测试任务-六部协作",
        context="测试子任务创建和状态管理",
        created_by="test"
    )
    print(f"创建测试任务: {task_id}\n")

    # 创建子任务
    sub1_id = create_subtask(
        parent_id=task_id,
        title="子任务1-准备资源",
        task_type="hubu-resources",
        assigned_to="hubu-resources",
        description="为任务准备必要资源"
    )
    print(f"创建子任务1: {sub1_id}")

    sub2_id = create_subtask(
        parent_id=task_id,
        title="子任务2-执行任务",
        task_type="bingbu-military",
        assigned_to="bingbu-military",
        description="实际执行任务",
        dependencies=[1]
    )
    print(f"创建子任务2: {sub2_id}\n")

    # 更新状态
    update_subtask_status(sub1_id, 'completed', '资源已准备完成')
    print(f"更新子任务1状态: completed")

    update_subtask_status(sub2_id, 'in_progress')
    print(f"更新子任务2状态: in_progress\n")

    # 查询子任务
    subtasks = get_subtasks(task_id)
    print(f"查询子任务列表: {len(subtasks)} 个")
    for st in subtasks:
        print(f"  - {st['id']}: {st['status']}")

    # 验证
    assert len(subtasks) == 2, f"预期 2 个子任务，实际 {len(subtasks)}"
    assert subtasks[0]['status'] == 'completed', "子任务1 应为 completed"
    assert subtasks[1]['status'] == 'in_progress', "子任务2 应为 in_progress"

    print("\n✅ 子任务管理测试通过\n")
    return True


def test_result_aggregation():
    """测试结果汇总"""
    print("=== 测试 4: 结果汇总 ===\n")

    results = [
        {
            'subtask_id': 'TEST-001-SUB-1',
            'title': '准备资源',
            'department': 'hubu-resources',
            'status': 'completed',
            'result': '已准备历史数据 50 条'
        },
        {
            'subtask_id': 'TEST-001-SUB-2',
            'title': '执行任务',
            'department': 'bingbu-military',
            'status': 'completed',
            'result': '已创建 6 个 SOUL.md 文件'
        },
        {
            'subtask_id': 'TEST-001-SUB-3',
            'title': '验收质量',
            'department': 'xingbu-justice',
            'status': 'completed',
            'result': '格式统一，内容完整'
        }
    ]

    report = aggregate_results(results)
    print(report)

    # 验证
    assert '总任务数**: 3' in report, "应包含任务总数"
    assert '已完成**: 3' in report, "应包含完成数"
    assert '100.0%' in report, "完成率应为 100%"

    print("✅ 结果汇总测试通过\n")
    return True


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("六部集成测试")
    print("="*60 + "\n")

    tests = [
        ("任务分类", test_task_classification),
        ("任务拆解", test_task_decomposition),
        ("子任务管理", test_subtask_management),
        ("结果汇总", test_result_aggregation),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {name} 测试失败\n")
        except Exception as e:
            failed += 1
            print(f"❌ {name} 测试异常: {e}\n")

    print("="*60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("="*60 + "\n")

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
