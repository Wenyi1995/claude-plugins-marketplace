#!/usr/bin/env python3
"""
方案审议检查清单工具
自动检查方案文档的技术可行性、风险评估、实施可行性
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='检查方案文档质量',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 bin/plan_checker.py data/plan_draft.md
  python3 bin/plan_checker.py -v data/plan_draft.md
        """
    )
    parser.add_argument('plan_file', help='方案文档路径')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细检查信息')
    return parser.parse_args()


class PlanChecker:
    """方案检查器"""

    # 检查项定义: (名称, 关键词列表, 说明)
    CHECKS = {
        '技术可行性': [
            ('技术路线是否存在', ['技术栈', '技术方案', '技术选型', '实现方案', '实现思路', 'python', 'javascript', 'sql', 'api'],
             '检查是否包含技术栈关键词'),
            ('依赖的工具/库是否提及', ['requirements', '依赖', 'import', 'package', 'npm', 'pip', '第三方库', 'framework'],
             '检查是否有 requirements.txt 或依赖说明'),
            ('是否考虑了兼容性', ['兼容', '版本', 'python 3', 'node', '系统要求', '环境', 'platform'],
             '检查是否提及系统/版本'),
            ('是否有已知的技术限制', ['限制', '约束', '注意事项', '已知问题', '风险', '局限'],
             '检查是否有"限制"、"约束"章节'),
            ('时间估算是否基于经验值', ['时间', '工时', '预计', '估算', '周期', '天', '小时', 'week', 'day'],
             '检查是否有时间估算'),
        ],
        '风险评估': [
            ('是否识别了外部依赖风险', ['api', 'database', '数据库', '网络', '第三方', '外部服务', '依赖服务'],
             '检查是否提及 API/数据库/网络'),
            ('是否考虑了性能风险', ['性能', '大数据', '高并发', '负载', '压力', '优化', '瓶颈', 'scalability'],
             '检查是否提及大数据量/高并发'),
            ('是否考虑了安全风险', ['安全', '权限', '鉴权', '加密', '数据泄露', '隐私', '敏感信息', 'security'],
             '检查是否提及权限/数据泄露'),
            ('是否有回滚方案', ['回滚', '回退', 'rollback', '撤销', '恢复', '备份'],
             '检查是否包含"回滚"关键词'),
            ('是否评估了影响范围', ['影响', '用户', '系统', '业务', '功能', '模块', '影响面'],
             '检查是否提及用户/系统影响'),
        ],
        '实施可行性': [
            ('执行步骤是否可操作', ['步骤', 'step', '实现', '流程', '操作', '执行', '具体'],
             '检查是否有具体步骤、代码示例'),
            ('是否有数据迁移/初始化步骤', ['迁移', 'migration', '初始化', 'init', '数据准备', 'setup'],
             '检查是否提及 migration'),
            ('是否包含测试环节', ['测试', 'test', '验证', 'verify', '单元测试', '集成测试'],
             '检查是否提及测试/验证'),
            ('是否有验收标准', ['验收', '标准', 'acceptance', '交付标准', 'definition of done'],
             '检查是否有"验收"章节'),
            ('是否明确了交付物', ['交付物', '产出', 'deliverable', '文件路径', '代码文件', '.py', '.js', '.md'],
             '检查是否列出文件路径'),
        ]
    }

    def __init__(self, file_path: str, verbose: bool = False):
        self.file_path = Path(file_path)
        self.verbose = verbose
        self.content = ""
        self.content_lower = ""

    def load_file(self) -> bool:
        """加载文件内容"""
        try:
            self.content = self.file_path.read_text(encoding='utf-8')
            self.content_lower = self.content.lower()
            return True
        except FileNotFoundError:
            print(f"错误: 文件不存在 {self.file_path}")
            return False
        except Exception as e:
            print(f"错误: 读取文件失败 {e}")
            return False

    def check_item(self, keywords: List[str]) -> bool:
        """检查是否包含任一关键词"""
        return any(keyword.lower() in self.content_lower for keyword in keywords)

    def check_category(self, category: str, items: List[Tuple]) -> Tuple[int, int, List[str]]:
        """检查某个类别的所有项目

        Returns:
            (通过数, 总数, 失败项列表)
        """
        passed = 0
        total = len(items)
        failed_items = []

        for name, keywords, desc in items:
            if self.check_item(keywords):
                passed += 1
                if self.verbose:
                    print(f"  ✅ {name}")
                    print(f"     匹配关键词: {[k for k in keywords if k.lower() in self.content_lower][:3]}")
            else:
                failed_items.append((name, desc))
                if self.verbose:
                    print(f"  ⚠️  {name}")
                    print(f"     {desc}")

        return passed, total, failed_items

    def generate_report(self) -> dict:
        """生成检查报告"""
        report = {
            'file': str(self.file_path),
            'categories': {},
            'total_passed': 0,
            'total_items': 0
        }

        for category, items in self.CHECKS.items():
            passed, total, failed = self.check_category(category, items)
            report['categories'][category] = {
                'passed': passed,
                'total': total,
                'failed': failed
            }
            report['total_passed'] += passed
            report['total_items'] += total

        return report

    def print_report(self, report: dict):
        """打印检查报告"""
        print(f"\n方案检查报告：{report['file']}")
        print()

        for category, result in report['categories'].items():
            print("=" * 40)
            print(f"{category} ({result['passed']}/{result['total']})")
            print("=" * 40)

            if not self.verbose:
                # 非详细模式：只显示通过/失败汇总
                for name, desc in result['failed']:
                    print(f"⚠️  {name}（{desc}）")

                # 显示通过的数量
                passed_count = result['passed']
                if passed_count > 0:
                    print(f"✅ {passed_count} 项检查通过")

            print()

        # 总结
        total_passed = report['total_passed']
        total_items = report['total_items']
        percentage = int(total_passed / total_items * 100) if total_items > 0 else 0

        print("=" * 40)
        print(f"总体评分: {total_passed}/{total_items} ({percentage}%)")

        # 给出建议
        if percentage >= 90:
            suggestion = "方案质量优秀，可以开始实施"
        elif percentage >= 80:
            suggestion = "方案质量良好，建议补充缺失项后实施"
        elif percentage >= 70:
            suggestion = "方案质量一般，需要补充多个关键项"
        else:
            suggestion = "方案质量不足，建议重新评估和完善"

        print(f"建议: {suggestion}")
        print("=" * 40)
        print()


def main():
    """主函数"""
    args = parse_args()

    checker = PlanChecker(args.plan_file, args.verbose)

    if not checker.load_file():
        sys.exit(1)

    report = checker.generate_report()
    checker.print_report(report)

    # 返回码：90%以上返回0，否则返回1
    percentage = int(report['total_passed'] / report['total_items'] * 100)
    sys.exit(0 if percentage >= 90 else 1)


if __name__ == '__main__':
    main()
