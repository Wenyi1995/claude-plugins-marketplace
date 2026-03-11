#!/usr/bin/env python3
"""
三省六部实时监控面板

功能：
1. 从 tasks.json 采集任务状态
2. 从 stats-cache.json 采集 token 统计
3. 实时刷新 TUI 界面（5 秒刷新）
4. 显示 Agent 当前状态、操作次数、封驳次数

作者：工部
任务：SUB-036-001
日期：2026-03-10
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
except ImportError:
    print("错误：Rich 库未安装")
    print("请运行：pip3 install rich")
    exit(1)

# 配置路径
DATA_DIR = Path.home() / '.claude/plugins/sansheng-pipeline/data'
STATS_FILE = Path.home() / '.claude/stats-cache.json'
REFRESH_INTERVAL = 5  # 刷新间隔（秒）


def format_timedelta(delta: timedelta) -> str:
    """
    格式化时间差为易读格式

    示例：
    - 3661 秒 → "1h 1m"
    - 125 秒 → "2m"
    - 45 秒 → "45s"
    """
    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return f"{seconds}s"


def collect_task_status() -> List[Dict]:
    """
    从 tasks.json 采集任务状态

    返回格式：
    [
        {
            'task_id': 'TASK-20260310-036',
            'title': '...',
            'status': 'reviewing',
            'current_agent': 'menxia',
            'operation_count': 2,
            'rejection_count': 1,
            'elapsed_time': '1h 15m',
            'last_update': '11:45'
        }
    ]
    """
    tasks_file = DATA_DIR / 'tasks.json'
    if not tasks_file.exists():
        return []

    try:
        with open(tasks_file, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
    except json.JSONDecodeError as e:
        print(f"警告：tasks.json 解析失败 - {e}")
        return []
    except Exception as e:
        print(f"警告：读取 tasks.json 失败 - {e}")
        return []

    # 只显示未完成的任务
    active_tasks = [t for t in tasks if t['state'] not in ['done', 'cancelled']]

    result = []
    for task in active_tasks:
        # 推断当前负责的 agent
        state = task['state']
        if state == 'planning' or state == 'rejected':
            current_agent = 'zhongshu'
        elif state == 'reviewing':
            current_agent = 'menxia'
        elif state in ['approved', 'executing']:
            current_agent = 'shangshu'
        else:
            current_agent = '待分配'

        # 计算运行时长
        try:
            created = datetime.fromisoformat(task['created_at'])
            elapsed = datetime.now() - created
        except (KeyError, ValueError):
            elapsed = timedelta(0)

        # 格式化最后更新时间
        try:
            updated = datetime.fromisoformat(task['updated_at'])
            last_update = updated.strftime('%H:%M')
        except (KeyError, ValueError):
            last_update = 'N/A'

        result.append({
            'task_id': task.get('id', 'UNKNOWN'),
            'title': task.get('title', 'Untitled')[:40],  # 截断标题
            'status': state,
            'current_agent': current_agent,
            'operation_count': len(task.get('versions', [])),
            'rejection_count': len(task.get('rejections', [])),
            'elapsed_time': format_timedelta(elapsed),
            'last_update': last_update
        })

    return result


def collect_token_stats() -> Optional[Dict]:
    """
    从 stats-cache.json 采集 token 统计

    返回格式：
    {
        'today': 125000,
        'total_input': 488495,
        'total_output': 1619490,
        'cache_read': 534564177,
        'cache_write': 73422670
    }
    """
    if not STATS_FILE.exists():
        return None

    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            stats = json.load(f)
    except json.JSONDecodeError as e:
        print(f"警告：stats-cache.json 解析失败 - {e}")
        return None
    except Exception as e:
        print(f"警告：读取 stats-cache.json 失败 - {e}")
        return None

    # 提取模型使用统计
    model_usage = stats.get('modelUsage', {})
    # 取第一个模型的统计（通常只有一个模型）
    usage = next(iter(model_usage.values()), {})

    # 今日 token（如果有）
    today = datetime.now().strftime('%Y-%m-%d')
    daily = stats.get('dailyModelTokens', [])
    today_tokens = 0
    for day in daily:
        if day.get('date') == today:
            today_tokens = sum(day.get('tokensByModel', {}).values())
            break

    return {
        'today': today_tokens,
        'total_input': usage.get('inputTokens', 0),
        'total_output': usage.get('outputTokens', 0),
        'cache_read': usage.get('cacheReadInputTokens', 0),
        'cache_write': usage.get('cacheCreationInputTokens', 0)
    }


def render_dashboard(tasks: List[Dict], token_stats: Optional[Dict]) -> Layout:
    """
    渲染监控面板

    布局：
    ┌─────────────────────────────────────────────────┐
    │ Token 统计                                       │
    └─────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────┐
    │ Agent 任务监控                                   │
    └─────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────┐
    │ 提示信息                                         │
    └─────────────────────────────────────────────────┘
    """
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )

    # ========== 头部：全局 token 统计 ==========
    if token_stats:
        header_text = (
            f"[cyan]今日 Tokens:[/cyan] {token_stats['today']:,} | "
            f"[green]总输入:[/green] {token_stats['total_input']:,} | "
            f"[yellow]总输出:[/yellow] {token_stats['total_output']:,} | "
            f"[magenta]缓存读:[/magenta] {token_stats['cache_read']:,}"
        )
    else:
        header_text = "[red]Token 统计数据不可用[/red]"

    layout["header"].update(Panel(header_text, title="Token 统计", border_style="blue"))

    # ========== 主体：任务列表 ==========
    table = Table(title="Agent 任务监控", show_header=True, header_style="bold magenta")
    table.add_column("任务 ID", style="cyan", width=20)
    table.add_column("标题", style="white", width=42)
    table.add_column("状态", style="yellow", width=12)
    table.add_column("负责 Agent", style="green", width=12)
    table.add_column("操作", justify="right", width=6)
    table.add_column("封驳", justify="right", style="red", width=6)
    table.add_column("运行时长", justify="right", width=10)
    table.add_column("最后更新", justify="right", width=10)

    if not tasks:
        # 无任务时显示提示
        table.add_row("暂无未完成任务", "", "", "", "", "", "", "")
    else:
        for task in tasks:
            # 根据状态添加颜色
            status_style = {
                'planning': 'yellow',
                'reviewing': 'cyan',
                'rejected': 'red',
                'approved': 'green',
                'executing': 'blue'
            }.get(task['status'], 'white')

            table.add_row(
                task['task_id'],
                task['title'],
                f"[{status_style}]{task['status']}[/{status_style}]",
                task['current_agent'],
                str(task['operation_count']),
                str(task['rejection_count']),
                task['elapsed_time'],
                task['last_update']
            )

    layout["body"].update(table)

    # ========== 底部：提示信息 ==========
    footer_text = f"[dim]按 Ctrl+C 退出 | 刷新间隔: {REFRESH_INTERVAL} 秒 | 最后刷新: {datetime.now().strftime('%H:%M:%S')}[/dim]"
    layout["footer"].update(Panel(footer_text, border_style="dim"))

    return layout


def main():
    """主循环：每 5 秒刷新一次监控面板"""
    console = Console()

    # 检查数据目录是否存在
    if not DATA_DIR.exists():
        console.print(f"[red]错误：数据目录不存在 - {DATA_DIR}[/red]")
        console.print("[yellow]请确保三省六部系统已初始化[/yellow]")
        return

    console.print("[green]三省六部实时监控面板启动中...[/green]")
    console.print(f"[dim]数据源：{DATA_DIR / 'tasks.json'}[/dim]\n")

    try:
        with Live(console=console, refresh_per_second=0.2) as live:
            while True:
                # 采集数据
                tasks = collect_task_status()
                token_stats = collect_token_stats()

                # 渲染界面
                dashboard = render_dashboard(tasks, token_stats)
                live.update(dashboard)

                # 等待下次刷新
                time.sleep(REFRESH_INTERVAL)

    except KeyboardInterrupt:
        console.print("\n[yellow]监控已停止[/yellow]")
    except Exception as e:
        console.print(f"\n[red]发生错误：{e}[/red]")
        raise


if __name__ == "__main__":
    main()
