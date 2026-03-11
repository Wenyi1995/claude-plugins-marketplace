import { execSync } from 'child_process';
import * as path from 'path';

const PLUGIN_ROOT = path.resolve(__dirname, '../..');
const LIB_PATH = path.join(PLUGIN_ROOT, 'lib');

/**
 * 执行 Python 代码并返回结果
 */
function execPython(code: string): string {
  const cmd = `cd ${PLUGIN_ROOT} && python3 -c "import sys; sys.path.insert(0, '${LIB_PATH}'); ${code}"`;
  try {
    return execSync(cmd, { encoding: 'utf-8' }).trim();
  } catch (error: any) {
    throw new Error(`Python execution failed: ${error.message}`);
  }
}

/**
 * 将字符串转为 Base64（用于传递复杂字符串到 Python）
 */
function toBase64(str: string): string {
  return Buffer.from(str, 'utf-8').toString('base64');
}

/**
 * 创建新任务
 *
 * @param title 任务标题
 * @param context 任务背景和需求
 * @param createdBy 创建者（默认 'mcp-server'）
 * @returns 任务 ID（格式：TASK-20260310-001）
 */
export function createTask(title: string, context: string, createdBy: string = 'mcp-server'): string {
  const titleB64 = toBase64(title);
  const contextB64 = toBase64(context);
  const createdByB64 = toBase64(createdBy);

  const code = `
import base64
from task_state import create_task
title = base64.b64decode('${titleB64}').decode('utf-8')
context = base64.b64decode('${contextB64}').decode('utf-8')
created_by = base64.b64decode('${createdByB64}').decode('utf-8')
task_id = create_task(title, context, created_by)
print(task_id)
`;
  return execPython(code);
}

/**
 * 添加规划版本
 *
 * @param taskId 任务 ID
 * @param plan 规划内容
 * @param author 规划者（默认 'zhongshu'）
 * @returns 版本号
 */
export function addPlanVersion(taskId: string, plan: string, author: string = 'zhongshu'): number {
  const planB64 = toBase64(plan);
  const authorB64 = toBase64(author);

  const code = `
import base64
from task_state import add_plan_version
plan = base64.b64decode('${planB64}').decode('utf-8')
author = base64.b64decode('${authorB64}').decode('utf-8')
version = add_plan_version('${taskId}', plan, author)
print(version)
`;
  return parseInt(execPython(code));
}

/**
 * 添加封驳记录
 *
 * @param taskId 任务 ID
 * @param reason 封驳理由
 * @param reviewer 审议者（默认 'menxia'）
 * @returns 当前封驳次数
 */
export function addRejection(taskId: string, reason: string, reviewer: string = 'menxia'): number {
  const reasonB64 = toBase64(reason);
  const reviewerB64 = toBase64(reviewer);

  const code = `
import base64
from task_state import add_rejection
reason = base64.b64decode('${reasonB64}').decode('utf-8')
reviewer = base64.b64decode('${reviewerB64}').decode('utf-8')
count = add_rejection('${taskId}', reason, reviewer)
print(count)
`;
  return parseInt(execPython(code));
}

/**
 * 获取封驳次数
 *
 * @param taskId 任务 ID
 * @returns 封驳次数
 */
export function getRejectionCount(taskId: string): number {
  const code = `
from task_state import get_rejection_count
count = get_rejection_count('${taskId}')
print(count)
`;
  return parseInt(execPython(code));
}

/**
 * 更新任务状态
 *
 * @param taskId 任务 ID
 * @param newState 新状态
 * @param note 备注（可选）
 */
export function updateState(taskId: string, newState: string, note?: string): void {
  if (note) {
    const noteB64 = toBase64(note);
    const code = `
import base64
from task_state import update_state
note = base64.b64decode('${noteB64}').decode('utf-8')
update_state('${taskId}', '${newState}', note)
`;
    execPython(code);
  } else {
    const code = `
from task_state import update_state
update_state('${taskId}', '${newState}')
`;
    execPython(code);
  }
}

/**
 * 获取任务详情
 *
 * @param taskId 任务 ID
 * @returns 任务对象
 */
export function getTask(taskId: string): any {
  const code = `
import json
from task_state import get_task
task = get_task('${taskId}')
print(json.dumps(task, ensure_ascii=False))
`;
  const result = execPython(code);
  return JSON.parse(result);
}

/**
 * 设置用户批准
 *
 * @param taskId 任务 ID
 * @param approvedBy 批准者（默认 'user'）
 */
export function setApproval(taskId: string, approvedBy: string = 'user'): void {
  const approvedByB64 = toBase64(approvedBy);

  const code = `
import base64
from task_state import set_approval
approved_by = base64.b64decode('${approvedByB64}').decode('utf-8')
set_approval('${taskId}', approved_by)
`;
  execPython(code);
}

/**
 * 设置任务升级（用户裁决）
 *
 * @param taskId 任务 ID
 * @param reason 升级原因
 */
export function setEscalation(taskId: string, reason: string): void {
  const reasonB64 = toBase64(reason);

  const code = `
import base64
from task_state import set_escalation
reason = base64.b64decode('${reasonB64}').decode('utf-8')
set_escalation('${taskId}', reason)
`;
  execPython(code);
}

/**
 * 设置最终成果
 *
 * @param taskId 任务 ID
 * @param result 执行结果
 */
export function setResult(taskId: string, result: string): void {
  const resultB64 = toBase64(result);

  const code = `
import base64
from task_state import set_result
result = base64.b64decode('${resultB64}').decode('utf-8')
set_result('${taskId}', result)
`;
  execPython(code);
}

/**
 * 获取最新版本的规划
 *
 * @param taskId 任务 ID
 * @returns 最新规划版本，不存在则返回 null
 */
export function getLatestPlan(taskId: string): any {
  const code = `
import json
from task_state import get_latest_plan
plan = get_latest_plan('${taskId}')
print(json.dumps(plan, ensure_ascii=False))
`;
  const result = execPython(code);
  return JSON.parse(result);
}

/**
 * 列出任务
 *
 * @param state 可选，按状态过滤
 * @returns 任务列表
 */
export function listTasks(state?: string): any[] {
  const stateArg = state ? `'${state}'` : 'None';

  const code = `
import json
from task_state import list_tasks
tasks = list_tasks(${stateArg})
print(json.dumps(tasks, ensure_ascii=False))
`;
  const result = execPython(code);
  return JSON.parse(result);
}

/**
 * 创建子任务
 *
 * @param parentId 父任务 ID
 * @param title 子任务标题
 * @param taskType 任务类型（部门 ID）
 * @param assignedTo 负责部门
 * @param description 子任务描述
 * @param dependencies 依赖的子任务序号列表
 * @returns 子任务 ID（格式：{parent_id}-SUB-{sequence}）
 */
export function createSubtask(
  parentId: string,
  title: string,
  taskType: string,
  assignedTo: string,
  description: string = '',
  dependencies: number[] = []
): string {
  const titleB64 = toBase64(title);
  const taskTypeB64 = toBase64(taskType);
  const assignedToB64 = toBase64(assignedTo);
  const descriptionB64 = toBase64(description);
  const depsJson = JSON.stringify(dependencies);

  const code = `
import json
import base64
from task_state import create_subtask
title = base64.b64decode('${titleB64}').decode('utf-8')
task_type = base64.b64decode('${taskTypeB64}').decode('utf-8')
assigned_to = base64.b64decode('${assignedToB64}').decode('utf-8')
description = base64.b64decode('${descriptionB64}').decode('utf-8')
subtask_id = create_subtask('${parentId}', title, task_type, assigned_to, description, ${depsJson})
print(subtask_id)
`;
  return execPython(code);
}

/**
 * 更新子任务状态
 *
 * @param subtaskId 子任务 ID
 * @param status 新状态（pending/in_progress/completed/failed）
 * @param result 执行结果（可选）
 */
export function updateSubtaskStatus(subtaskId: string, status: string, result?: string): void {
  if (result) {
    const resultB64 = toBase64(result);
    const code = `
import base64
from task_state import update_subtask_status
result = base64.b64decode('${resultB64}').decode('utf-8')
update_subtask_status('${subtaskId}', '${status}', result)
`;
    execPython(code);
  } else {
    const code = `
from task_state import update_subtask_status
update_subtask_status('${subtaskId}', '${status}')
`;
    execPython(code);
  }
}

/**
 * 获取子任务列表
 *
 * @param parentId 父任务 ID
 * @param filterByDepartment 可选，按部门筛选
 * @returns 子任务列表
 */
export function getSubtasks(parentId: string, filterByDepartment?: string): any[] {
  const filterArg = filterByDepartment ? `'${filterByDepartment}'` : 'None';

  const code = `
import json
from task_state import get_subtasks
subtasks = get_subtasks('${parentId}', ${filterArg})
print(json.dumps(subtasks, ensure_ascii=False))
`;
  const result = execPython(code);
  return JSON.parse(result);
}

/**
 * 获取单个子任务
 *
 * @param subtaskId 子任务 ID
 * @returns 子任务对象，不存在则返回 null
 */
export function getSubtask(subtaskId: string): any {
  const code = `
import json
from task_state import get_subtask
subtask = get_subtask('${subtaskId}')
print(json.dumps(subtask, ensure_ascii=False))
`;
  const result = execPython(code);
  return JSON.parse(result);
}
