#!/usr/bin/env python3
"""
任务状态管理 - 三省审议流水线

负责：
1. 任务创建、查询、更新
2. 版本历史记录（每次规划/封驳都是一个版本）
3. 状态流转追踪
"""
import json
import fcntl
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 任务状态定义
class TaskState:
    CREATED = "created"           # 司礼监已创建
    PLANNING = "planning"         # 中书省规划中
    REVIEWING = "reviewing"       # 门下省审议中
    REJECTED = "rejected"         # 门下省封驳
    ESCALATED = "escalated"       # 升级用户裁决
    APPROVED = "approved"         # 门下省准奏 + 用户确认
    EXECUTING = "executing"       # 尚书省执行中（预留）
    DONE = "done"                 # 已完成
    CANCELLED = "cancelled"       # 已取消

# 数据目录
DATA_DIR = Path(__file__).parent.parent / 'data'
TASKS_FILE = DATA_DIR / 'tasks.json'

def _ensure_data_dir():
    """确保数据目录存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text('[]', encoding='utf-8')

def _atomic_read() -> List[Dict]:
    """原子读取任务列表"""
    _ensure_data_dir()
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        try:
            data = json.load(f)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    return data

def _atomic_write(tasks: List[Dict]):
    """原子写入任务列表"""
    _ensure_data_dir()
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

def create_task(title: str, context: str, created_by: str = "silijian", track: str = "normal") -> str:
    """
    创建新任务

    Args:
        title: 任务标题
        context: 任务详细描述
        created_by: 创建者
        track: 任务轨道，'normal'（三省审议）或 'fast'（快速通道）

    Returns:
        task_id: 格式为 TASK-20260310-001
    """
    tasks = _atomic_read()

    # 生成任务 ID
    today = datetime.now().strftime("%Y%m%d")
    existing_today = [t for t in tasks if t['id'].startswith(f'TASK-{today}')]
    seq = len(existing_today) + 1
    task_id = f'TASK-{today}-{seq:03d}'

    task = {
        'id': task_id,
        'title': title,
        'context': context,
        'track': track,  # 'normal' 或 'fast'
        'state': TaskState.CREATED,
        'created_by': created_by,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'versions': [],  # 规划版本历史
        'rejections': [],  # 封驳历史
        'escalation': None,  # 升级记录
        'approval': None,  # 批准记录
        'result': None  # 最终成果
    }

    tasks.append(task)
    _atomic_write(tasks)
    return task_id

def get_task(task_id: str) -> Optional[Dict]:
    """查询任务"""
    tasks = _atomic_read()
    return next((t for t in tasks if t['id'] == task_id), None)

def get_task_safe(task_id: str) -> Optional[Dict]:
    """
    安全查询任务（自动补充缺失的 track 字段）

    用于兼容旧任务，自动将缺失 track 字段的任务设为 'normal'
    """
    task = get_task(task_id)
    if task and 'track' not in task:
        task['track'] = 'normal'
    return task

def update_state(task_id: str, new_state: str, note: str = ""):
    """更新任务状态"""
    tasks = _atomic_read()
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        raise ValueError(f"任务 {task_id} 不存在")

    task['state'] = new_state
    task['updated_at'] = datetime.now().isoformat()

    if note:
        if 'history' not in task:
            task['history'] = []
        task['history'].append({
            'timestamp': datetime.now().isoformat(),
            'state': new_state,
            'note': note
        })

    _atomic_write(tasks)

def add_plan_version(task_id: str, plan: str, author: str = "zhongshu"):
    """
    添加规划版本

    Args:
        task_id: 任务ID
        plan: 规划内容
        author: 规划者
    """
    tasks = _atomic_read()
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        raise ValueError(f"任务 {task_id} 不存在")

    version = {
        'version': len(task['versions']) + 1,
        'plan': plan,
        'author': author,
        'created_at': datetime.now().isoformat()
    }

    task['versions'].append(version)
    task['updated_at'] = datetime.now().isoformat()
    _atomic_write(tasks)

    return version['version']

def add_rejection(task_id: str, reason: str, reviewer: str = "menxia") -> int:
    """
    添加封驳记录

    Returns:
        rejection_count: 当前封驳次数
    """
    tasks = _atomic_read()
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        raise ValueError(f"任务 {task_id} 不存在")

    rejection = {
        'count': len(task['rejections']) + 1,
        'reason': reason,
        'reviewer': reviewer,
        'timestamp': datetime.now().isoformat()
    }

    task['rejections'].append(rejection)
    task['state'] = TaskState.REJECTED
    task['updated_at'] = datetime.now().isoformat()
    _atomic_write(tasks)

    return rejection['count']

def set_escalation(task_id: str, reason: str):
    """设置升级用户裁决"""
    tasks = _atomic_read()
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        raise ValueError(f"任务 {task_id} 不存在")

    task['escalation'] = {
        'reason': reason,
        'rejection_count': len(task['rejections']),
        'timestamp': datetime.now().isoformat()
    }
    task['state'] = TaskState.ESCALATED
    task['updated_at'] = datetime.now().isoformat()
    _atomic_write(tasks)

def set_approval(task_id: str, approved_by: str = "user"):
    """设置用户批准"""
    tasks = _atomic_read()
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        raise ValueError(f"任务 {task_id} 不存在")

    task['approval'] = {
        'approved_by': approved_by,
        'timestamp': datetime.now().isoformat()
    }
    task['state'] = TaskState.APPROVED
    task['updated_at'] = datetime.now().isoformat()
    _atomic_write(tasks)

def set_result(task_id: str, result: str):
    """设置最终成果"""
    tasks = _atomic_read()
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        raise ValueError(f"任务 {task_id} 不存在")

    task['result'] = result
    task['state'] = TaskState.DONE
    task['updated_at'] = datetime.now().isoformat()
    _atomic_write(tasks)

def list_tasks(state: Optional[str] = None) -> List[Dict]:
    """
    列出任务

    Args:
        state: 可选，按状态过滤
    """
    tasks = _atomic_read()
    if state:
        tasks = [t for t in tasks if t['state'] == state]
    return sorted(tasks, key=lambda t: t['created_at'], reverse=True)

def get_rejection_count(task_id: str) -> int:
    """获取封驳次数"""
    task = get_task(task_id)
    return len(task['rejections']) if task else 0

def get_latest_plan(task_id: str) -> Optional[Dict]:
    """获取最新版本的规划"""
    task = get_task(task_id)
    if task and task['versions']:
        return task['versions'][-1]
    return None


# ===== 子任务管理功能（v0.2 新增）=====

def create_subtask(parent_id: str, title: str, task_type: str, assigned_to: str,
                   description: str = "", dependencies: List[int] = None) -> str:
    """
    创建子任务

    Args:
        parent_id: 父任务 ID
        title: 子任务标题
        task_type: 任务类型（部门 ID）
        assigned_to: 负责部门
        description: 子任务描述
        dependencies: 依赖的子任务序号列表

    Returns:
        subtask_id: 格式为 {parent_id}-SUB-{sequence}
    """
    tasks = _atomic_read()
    parent = next((t for t in tasks if t['id'] == parent_id), None)
    if not parent:
        raise ValueError(f"父任务 {parent_id} 不存在")

    # 初始化 subtasks 字段
    if 'subtasks' not in parent:
        parent['subtasks'] = []

    # 生成子任务 ID
    sequence = len(parent['subtasks']) + 1
    subtask_id = f"{parent_id}-SUB-{sequence}"

    subtask = {
        'id': subtask_id,
        'parent_id': parent_id,
        'sequence': sequence,
        'title': title,
        'description': description,
        'task_type': task_type,
        'assigned_to': assigned_to,
        'dependencies': dependencies or [],
        'status': 'pending',  # pending/in_progress/completed/failed
        'result': None,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }

    parent['subtasks'].append(subtask)
    parent['updated_at'] = datetime.now().isoformat()
    _atomic_write(tasks)

    return subtask_id


def update_subtask_status(subtask_id: str, status: str, result: str = None):
    """
    更新子任务状态

    Args:
        subtask_id: 子任务 ID（格式：TASK-xxx-SUB-N）
        status: 新状态（pending/in_progress/completed/failed）
        result: 执行结果（可选）
    """
    tasks = _atomic_read()

    # 解析父任务 ID
    parent_id = '-'.join(subtask_id.split('-')[:-2])
    parent = next((t for t in tasks if t['id'] == parent_id), None)
    if not parent:
        raise ValueError(f"父任务 {parent_id} 不存在")

    if 'subtasks' not in parent:
        raise ValueError(f"父任务 {parent_id} 没有子任务")

    # 查找子任务
    subtask = next((st for st in parent['subtasks'] if st['id'] == subtask_id), None)
    if not subtask:
        raise ValueError(f"子任务 {subtask_id} 不存在")

    # 更新状态
    subtask['status'] = status
    subtask['updated_at'] = datetime.now().isoformat()
    if result is not None:
        subtask['result'] = result

    parent['updated_at'] = datetime.now().isoformat()
    _atomic_write(tasks)


def get_subtasks(parent_id: str, filter_by_department: str = None) -> List[Dict]:
    """
    获取子任务列表

    Args:
        parent_id: 父任务 ID
        filter_by_department: 可选，按部门筛选

    Returns:
        子任务列表
    """
    task = get_task(parent_id)
    if not task or 'subtasks' not in task:
        return []

    subtasks = task['subtasks']
    if filter_by_department:
        subtasks = [st for st in subtasks if st['assigned_to'] == filter_by_department]

    return subtasks


def get_subtask(subtask_id: str) -> Optional[Dict]:
    """
    获取单个子任务

    Args:
        subtask_id: 子任务 ID

    Returns:
        子任务字典，不存在则返回 None
    """
    # 解析父任务 ID
    parent_id = '-'.join(subtask_id.split('-')[:-2])
    subtasks = get_subtasks(parent_id)
    return next((st for st in subtasks if st['id'] == subtask_id), None)
