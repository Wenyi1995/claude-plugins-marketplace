#!/bin/bash
# 三省审议流水线 - 管理脚本

PLUGIN_DIR="$HOME/.claude/plugins/sansheng-pipeline"
cd "$PLUGIN_DIR" || exit 1

case "$1" in
    test)
        echo "🧪 运行测试..."
        python3 test_pipeline.py
        ;;

    list)
        echo "📋 任务列表："
        python3 -c "
import sys; sys.path.insert(0, 'lib')
from task_state import list_tasks
tasks = list_tasks()
if not tasks:
    print('  (无任务)')
else:
    for t in tasks:
        print(f\"  {t['id']}: [{t['state']}] {t['title']}\")
"
        ;;

    show)
        if [ -z "$2" ]; then
            echo "用法: ./manage.sh show TASK-ID"
            exit 1
        fi
        echo "📄 任务详情: $2"
        python3 -c "
import sys; sys.path.insert(0, 'lib')
from task_state import get_task
import json
task = get_task('$2')
if task:
    print(json.dumps(task, ensure_ascii=False, indent=2))
else:
    print('任务不存在')
"
        ;;

    history)
        if [ -z "$2" ]; then
            echo "用法: ./manage.sh history TASK-ID"
            exit 1
        fi
        echo "📜 版本历史: $2"
        python3 -c "
import sys; sys.path.insert(0, 'lib')
from task_state import get_task
task = get_task('$2')
if task:
    for v in task['versions']:
        print(f\"\\nv{v['version']} ({v['created_at']}):\")
        print(v['plan'])
        print('-' * 60)
    if task['rejections']:
        print('\\n封驳记录:')
        for i, r in enumerate(task['rejections'], 1):
            print(f\"{i}. {r['timestamp']}: {r['reason']}\")
else:
    print('任务不存在')
"
        ;;

    clean)
        echo "🧹 清理完成任务..."
        python3 -c "
import sys; sys.path.insert(0, 'lib')
from task_state import list_tasks, TaskState
import json
tasks = list_tasks()
active = [t for t in tasks if t['state'] not in [TaskState.DONE, TaskState.CANCELLED]]
with open('data/tasks.json', 'w') as f:
    json.dump(active, f, ensure_ascii=False, indent=2)
print(f\"保留 {len(active)} 个进行中的任务\")
"
        ;;

    reset)
        echo "⚠️  重置所有数据（将丢失所有任务历史）"
        read -p "确认？(y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp data/tasks.json data/tasks.backup.$(date +%Y%m%d_%H%M%S).json
            echo '[]' > data/tasks.json
            echo "✅ 已重置（备份已保存）"
        fi
        ;;

    stats)
        echo "📊 统计信息："
        python3 -c "
import sys; sys.path.insert(0, 'lib')
from task_state import list_tasks, TaskState
tasks = list_tasks()
print(f\"  总任务数: {len(tasks)}\")

states = {}
for t in tasks:
    states[t['state']] = states.get(t['state'], 0) + 1
print('\\n  按状态分布:')
for state, count in sorted(states.items()):
    print(f\"    {state}: {count}\")

total_rejections = sum(len(t['rejections']) for t in tasks)
print(f\"\\n  总封驳次数: {total_rejections}\")
escalated = sum(1 for t in tasks if t.get('escalation'))
print(f\"  用户裁决次数: {escalated}\")
"
        ;;

    *)
        cat <<EOF
三省审议流水线 - 管理脚本

用法: ./manage.sh <command> [args]

命令:
  test              运行测试
  list              列出所有任务
  show TASK-ID      查看任务详情
  history TASK-ID   查看版本历史和封驳记录
  clean             清理已完成的任务
  reset             重置所有数据（慎用）
  stats             显示统计信息

示例:
  ./manage.sh test
  ./manage.sh list
  ./manage.sh show TASK-20260310-001
  ./manage.sh history TASK-20260310-001
  ./manage.sh stats
EOF
        exit 1
        ;;
esac
