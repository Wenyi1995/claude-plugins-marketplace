#!/usr/bin/env python3
"""
快速通道分类器测试矩阵
验收测试用例（8个）
"""
import sys
sys.path.insert(0, 'lib')

from fast_track import classify_task, format_classification_result


def test_case(case_num: int, title: str, context: str, expected_track: str, expected_confidence_min: float):
    """运行单个测试用例"""
    print(f"\n{'=' * 60}")
    print(f"测试用例 {case_num}: {title}")
    print(f"{'=' * 60}")

    result = classify_task(title, context)

    print(f"\n输入: {title}")
    print(f"预期轨道: {expected_track}")
    print(f"实际结果:\n{format_classification_result(result)}")

    # 验证
    passed = True
    if result['track'] != expected_track:
        print(f"\n❌ FAIL: 期望 track='{expected_track}'，实际 track='{result['track']}'")
        passed = False

    if result['confidence'] < expected_confidence_min:
        print(f"\n❌ FAIL: 期望置信度 >= {expected_confidence_min:.0%}，实际 {result['confidence']:.0%}")
        passed = False

    if passed:
        print(f"\n✅ PASS")

    return passed


def run_all_tests():
    """运行所有测试用例"""
    print("=" * 60)
    print("快速通道分类器 - 测试矩阵")
    print("=" * 60)

    results = []

    # 测试用例 1: 白名单模板 - 纯信息收集
    results.append(test_case(
        1,
        "查询系统日志",
        "导出最近7天的错误日志，格式为 JSON",
        expected_track='fast',
        expected_confidence_min=0.90
    ))

    # 测试用例 2: 白名单模板 - 纯文档整理
    results.append(test_case(
        2,
        "格式化 README",
        "补充目录索引，修正 Markdown 格式错误",
        expected_track='fast',
        expected_confidence_min=0.90
    ))

    # 测试用例 3: 双重否决 - 架构关键词
    results.append(test_case(
        3,
        "设计用户登录系统",
        "需要考虑架构设计、安全鉴权和性能优化",
        expected_track='normal',
        expected_confidence_min=0.85
    ))

    # 测试用例 4: 双重否决 - 安全关键词
    results.append(test_case(
        4,
        "配置 API 密钥",
        "更新加密密钥和权限变更",
        expected_track='normal',
        expected_confidence_min=0.85
    ))

    # 测试用例 5: 长度阈值
    results.append(test_case(
        5,
        "批量修改配置文件",
        "修改 20 个服务的配置文件，包括数据库连接、缓存配置、日志级别。需要考虑环境差异（dev/staging/production），如果某个服务配置错误则回滚，同时更新监控告警阈值，并通知相关负责人。",
        expected_track='normal',
        expected_confidence_min=0.80
    ))

    # 测试用例 6: 复杂度指标
    results.append(test_case(
        6,
        "根据用户角色批量调整权限",
        "如果用户是管理员则授予所有权限，普通用户根据部门分配，需要同时更新 5 个系统",
        expected_track='normal',
        expected_confidence_min=0.80
    ))

    # 测试用例 7: 边界情况 - 白名单 + 否决（否决优先）
    results.append(test_case(
        7,
        "查询并优化性能瓶颈",
        "查询慢查询日志，分析性能瓶颈并提出优化方案",
        expected_track='normal',
        expected_confidence_min=0.85
    ))

    # 测试用例 8: 旧任务兼容性 - 纯查询操作
    results.append(test_case(
        8,
        "列出所有 MCP 服务",
        "查看当前运行的 MCP 服务状态",
        expected_track='fast',
        expected_confidence_min=0.90
    ))

    # 汇总结果
    print(f"\n{'=' * 60}")
    print("测试汇总")
    print(f"{'=' * 60}")

    passed = sum(results)
    total = len(results)

    print(f"通过: {passed}/{total}")
    print(f"失败: {total - passed}/{total}")
    print(f"通过率: {passed/total*100:.1f}%")

    if passed == total:
        print("\n✅ 所有测试通过")
        return 0
    else:
        print(f"\n❌ {total - passed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
