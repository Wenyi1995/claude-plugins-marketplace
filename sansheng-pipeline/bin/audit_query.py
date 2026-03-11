#!/usr/bin/env python3
"""
审计日志查询工具
支持按日期、actor、action、task_id 查询，支持组合查询
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='查询审计日志',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --date 20260310
  %(prog)s --actor zhongshu
  %(prog)s --action plan_submitted
  %(prog)s --task TASK-20260310-001
  %(prog)s --date 20260310 --actor zhongshu
        """
    )
    parser.add_argument('--date', help='日期 (格式: YYYYMMDD)')
    parser.add_argument('--actor', help='操作者 ID')
    parser.add_argument('--action', help='操作类型')
    parser.add_argument('--task', dest='task_id', help='任务 ID')

    args = parser.parse_args()

    # 至少需要一个查询条件
    if not any([args.date, args.actor, args.action, args.task_id]):
        parser.error('至少需要指定一个查询条件')

    return args


def get_audit_files(audit_dir: Path, target_date: Optional[str]) -> List[Path]:
    """
    获取需要查询的审计日志文件

    Args:
        audit_dir: 审计日志目录
        target_date: 目标日期 (可选)

    Returns:
        审计日志文件列表
    """
    if target_date:
        # 查询指定日期
        target_file = audit_dir / f'audit-{target_date}.jsonl'
        if not target_file.exists():
            print(f'错误: 日期 {target_date} 的审计日志不存在', file=sys.stderr)
            sys.exit(1)
        return [target_file]
    else:
        # 查询所有日期
        files = sorted(audit_dir.glob('audit-*.jsonl'))
        if not files:
            print('错误: 未找到任何审计日志文件', file=sys.stderr)
            sys.exit(1)
        return files


def match_event(event: Dict, filters: Dict) -> bool:
    """
    检查事件是否匹配过滤条件

    Args:
        event: 事件数据
        filters: 过滤条件字典

    Returns:
        是否匹配
    """
    if filters.get('actor'):
        if event.get('actor', {}).get('id') != filters['actor']:
            return False

    if filters.get('action'):
        if event.get('action', {}).get('type') != filters['action']:
            return False

    if filters.get('task_id'):
        resource_id = event.get('action', {}).get('resource_id', '')
        # 支持模糊匹配 (resource_id 可能包含版本号)
        if filters['task_id'] not in resource_id:
            return False

    return True


def query_audit_logs(audit_files: List[Path], filters: Dict) -> List[Dict]:
    """
    查询审计日志

    Args:
        audit_files: 审计日志文件列表
        filters: 过滤条件

    Returns:
        匹配的事件列表
    """
    matched_events = []

    for audit_file in audit_files:
        try:
            with open(audit_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        event = json.loads(line)
                        if match_event(event, filters):
                            matched_events.append(event)
                    except json.JSONDecodeError as e:
                        print(f'警告: {audit_file.name}:{line_num} JSON 解析失败: {e}',
                              file=sys.stderr)
                        continue

        except Exception as e:
            print(f'错误: 读取 {audit_file.name} 失败: {e}', file=sys.stderr)
            continue

    # 按时间倒序排列
    matched_events.sort(key=lambda e: e.get('timestamp', ''), reverse=True)

    return matched_events


def format_output(events: List[Dict]) -> None:
    """
    格式化输出查询结果

    Args:
        events: 事件列表
    """
    if not events:
        print('未找到匹配记录')
        return

    print(f'找到 {len(events)} 条记录:\n')

    for idx, event in enumerate(events, 1):
        event_id = event.get('event_id', 'N/A')
        timestamp = event.get('timestamp', 'N/A')
        actor_id = event.get('actor', {}).get('id', 'N/A')
        actor_type = event.get('actor', {}).get('type', 'N/A')
        action_type = event.get('action', {}).get('type', 'N/A')
        resource_id = event.get('action', {}).get('resource_id', 'N/A')
        result = event.get('result', 'N/A')

        print(f'[{idx}] {event_id}')
        print(f'时间: {timestamp}')
        print(f'操作者: {actor_id} ({actor_type})')
        print(f'动作: {action_type}')
        print(f'目标: {resource_id}')
        print(f'结果: {result}')

        # 输出详细信息 (如果有)
        details = event.get('details', {})
        if details:
            print(f'详情: {json.dumps(details, ensure_ascii=False)}')

        print()  # 空行分隔


def main():
    """主函数"""
    args = parse_args()

    # 获取审计日志目录
    script_dir = Path(__file__).parent
    audit_dir = script_dir.parent / 'data' / 'audit'

    if not audit_dir.exists():
        print(f'错误: 审计日志目录不存在: {audit_dir}', file=sys.stderr)
        sys.exit(1)

    # 构建过滤条件
    filters = {}
    if args.actor:
        filters['actor'] = args.actor
    if args.action:
        filters['action'] = args.action
    if args.task_id:
        filters['task_id'] = args.task_id

    # 获取审计文件
    audit_files = get_audit_files(audit_dir, args.date)

    # 查询日志
    matched_events = query_audit_logs(audit_files, filters)

    # 输出结果
    format_output(matched_events)


if __name__ == '__main__':
    main()
