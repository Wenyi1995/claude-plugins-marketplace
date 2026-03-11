#!/usr/bin/env python3
"""
三省审议流水线 - 功能测试脚本

用法:
  python3 test_pipeline.py
"""
import sys
from pathlib import Path

# 添加 lib 到路径
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from task_state import (
    create_task, get_task, update_state, add_plan_version,
    add_rejection, set_escalation, set_approval, set_result,
    list_tasks, get_rejection_count, get_latest_plan, TaskState
)

def test_basic_workflow():
    """测试基础工作流"""
    print("=" * 60)
    print("测试 1: 基础工作流（创建 → 规划 → 审议 → 批准）")
    print("=" * 60)

    # 1. 创建任务
    task_id = create_task(
        title="测试任务：用户注册系统",
        context="实现基于手机号+验证码的用户注册功能",
        created_by="silijian"
    )
    print(f"✅ 创建任务: {task_id}")

    # 2. 更新为规划中
    update_state(task_id, TaskState.PLANNING, "中书省规划中")
    print(f"✅ 状态更新: planning")

    # 3. 添加方案版本
    plan_v1 = """
## 一、目标拆解
实现用户注册 API

## 二、执行步骤
1. 数据库设计
2. API 开发
3. 测试
    """
    version = add_plan_version(task_id, plan_v1, "zhongshu")
    print(f"✅ 添加方案: v{version}")

    # 4. 更新为审议中
    update_state(task_id, TaskState.REVIEWING, "门下省审议中")
    print(f"✅ 状态更新: reviewing")

    # 5. 准奏
    set_approval(task_id, "user")
    print(f"✅ 用户批准")

    # 6. 完成
    set_result(task_id, "方案已批准，待执行")
    print(f"✅ 任务完成")

    # 验证
    task = get_task(task_id)
    assert task['state'] == TaskState.DONE
    assert len(task['versions']) == 1
    assert task['approval'] is not None
    print(f"\n✅ 测试通过！")

    return task_id

def test_rejection_workflow():
    """测试封驳流程"""
    print("\n" + "=" * 60)
    print("测试 2: 封驳流程（规划 → 封驳 → 修改 → 准奏）")
    print("=" * 60)

    # 1. 创建任务
    task_id = create_task(
        title="测试任务：性能优化",
        context="优化用户列表接口性能",
        created_by="silijian"
    )
    print(f"✅ 创建任务: {task_id}")

    # 2. 中书省方案 v1
    plan_v1 = "增加 Redis 缓存"
    add_plan_version(task_id, plan_v1, "zhongshu")
    print(f"✅ 中书省方案 v1")

    # 3. 门下省封驳
    count = add_rejection(task_id, "缺少缓存失效策略", "menxia")
    print(f"✅ 门下省第 {count} 次封驳")

    # 4. 中书省方案 v2
    plan_v2 = "增加 Redis 缓存 + TTL 60s + 主动失效"
    add_plan_version(task_id, plan_v2, "zhongshu")
    print(f"✅ 中书省方案 v2（修改后）")

    # 5. 门下省准奏
    set_approval(task_id, "user")
    print(f"✅ 门下省准奏 + 用户批准")

    # 验证
    task = get_task(task_id)
    assert len(task['rejections']) == 1
    assert len(task['versions']) == 2
    assert get_rejection_count(task_id) == 1
    print(f"\n✅ 测试通过！")

    return task_id

def test_escalation_workflow():
    """测试升级裁决流程"""
    print("\n" + "=" * 60)
    print("测试 3: 升级裁决流程（3次封驳 → 用户裁决）")
    print("=" * 60)

    # 1. 创建任务
    task_id = create_task(
        title="测试任务：认证方式改造",
        context="从 session 改为 JWT",
        created_by="silijian"
    )
    print(f"✅ 创建任务: {task_id}")

    # 2. 第1轮：方案 → 封驳
    add_plan_version(task_id, "全面切换 JWT", "zhongshu")
    add_rejection(task_id, "未考虑旧用户迁移", "menxia")
    print(f"✅ 第 1 次封驳")

    # 3. 第2轮：修改 → 封驳
    add_plan_version(task_id, "30天兼容期", "zhongshu")
    add_rejection(task_id, "兼容期太长，建议7天", "menxia")
    print(f"✅ 第 2 次封驳")

    # 4. 第3轮：坚持 → 升级
    add_plan_version(task_id, "仍坚持30天", "zhongshu")
    count = get_rejection_count(task_id)
    assert count == 2
    print(f"✅ 封驳次数达到 {count}，触发升级")

    # 5. 升级用户裁决
    set_escalation(task_id, "双方争议：30天 vs 7天")
    print(f"✅ 升级用户裁决")

    # 6. 用户裁决后批准
    set_approval(task_id, "user")
    print(f"✅ 用户裁决并批准")

    # 验证
    task = get_task(task_id)
    assert task['state'] == TaskState.APPROVED
    assert len(task['rejections']) == 2
    assert task['escalation'] is not None
    print(f"\n✅ 测试通过！")

    return task_id

def test_query_functions():
    """测试查询功能"""
    print("\n" + "=" * 60)
    print("测试 4: 查询功能")
    print("=" * 60)

    # 列出所有任务
    tasks = list_tasks()
    print(f"✅ 共有 {len(tasks)} 个任务")

    # 列出进行中的任务
    active_tasks = [t for t in tasks if t['state'] not in [TaskState.DONE, TaskState.CANCELLED]]
    print(f"✅ 其中 {len(active_tasks)} 个任务进行中")

    # 打印最近3个任务
    print("\n最近3个任务:")
    for i, task in enumerate(tasks[:3], 1):
        print(f"  {i}. {task['id']}: [{task['state']}] {task['title']}")
        if task['rejections']:
            print(f"     封驳次数: {len(task['rejections'])}")
        if task['versions']:
            latest = get_latest_plan(task['id'])
            print(f"     最新版本: v{latest['version']}")

    print(f"\n✅ 测试通过！")

def main():
    print("\n" + "🚀 三省审议流水线 - 功能测试\n")

    try:
        # 运行所有测试
        task1 = test_basic_workflow()
        task2 = test_rejection_workflow()
        task3 = test_escalation_workflow()
        test_query_functions()

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        print(f"\n测试任务已创建:")
        print(f"  1. {task1} - 基础工作流")
        print(f"  2. {task2} - 封驳流程")
        print(f"  3. {task3} - 升级裁决")
        print(f"\n查看任务详情:")
        print(f"  cd ~/.claude/plugins/sansheng-pipeline")
        print(f"  python3 -c \"import sys; sys.path.insert(0, 'lib'); from task_state import get_task; import json; print(json.dumps(get_task('{task1}'), ensure_ascii=False, indent=2))\"")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
