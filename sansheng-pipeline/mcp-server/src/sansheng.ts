import * as taskState from './task-state';

interface ReviewAllArgs {
  title: string;
  context: string;
}

interface ReviewAllResult {
  status: 'approved' | 'escalated';
  task_id: string;
  summary: string;
  final_plan?: string;
  meta?: {
    versions: number;
    rejections: number;
  };
  conflict?: {
    zhongshu_latest_plan: string;
    menxia_concerns: string;
    rejection_history: Array<{
      count: number;
      reason: string;
      reviewer: string;
      timestamp: string;
    }>;
  };
}

interface FinalizeArgs {
  task_id: string;
  decision: 'approve_zhongshu' | 'approve_menxia' | 'custom';
  custom_plan?: string;
}

interface FinalizeResult {
  success: boolean;
  task_id: string;
  final_state: string;
  message: string;
  final_plan: string;
}


/**
 * 三省审议流程（已废弃 - 占位实现）
 *
 * 新流程请使用：
 * 1. sansheng_create_task 创建任务
 * 2. 调用中书省 Agent 起草方案
 * 3. 调用门下省 Agent 审议方案
 */
export async function sanshengReviewAll(
  args: ReviewAllArgs
): Promise<ReviewAllResult> {
  return {
    status: 'approved',
    task_id: 'DEPRECATED',
    summary: '此工具已废弃，请使用新的 Agent-based 流程：\n' +
             '1. sansheng_create_task 创建任务\n' +
             '2. 调用中书省 Agent 起草方案\n' +
             '3. 调用门下省 Agent 审议方案',
    final_plan: '请使用新流程',
    meta: { versions: 0, rejections: 0 }
  };
}

/**
 * 圣上裁决：finalize 任务
 * 处理三种决策：
 * 1. approve_zhongshu：批准中书省方案
 * 2. approve_menxia：采纳门下省意见，驳回方案
 * 3. custom：圣上自定义方案
 */
export async function sanshengFinalize(
  args: FinalizeArgs
): Promise<FinalizeResult> {
  const { task_id, decision, custom_plan } = args;

  // 获取任务
  const task = taskState.getTask(task_id);
  if (!task) {
    throw new Error(`任务 ${task_id} 不存在`);
  }

  // 检查任务状态
  if (task.state !== 'escalated' && task.state !== 'approved') {
    throw new Error(
      `任务 ${task_id} 状态为 ${task.state}，不能执行 finalize（仅支持 escalated 或 approved）`
    );
  }

  let finalPlan = '';
  let message = '';

  switch (decision) {
    case 'approve_zhongshu':
      // 批准中书省方案
      const latestPlan = taskState.getLatestPlan(task_id);
      if (!latestPlan) {
        throw new Error(`任务 ${task_id} 没有可用的中书省方案`);
      }
      finalPlan = latestPlan.plan;
      taskState.setApproval(task_id, 'emperor');
      taskState.setResult(task_id, '圣上批准中书省方案');
      message = '圣上批准中书省方案，任务进入执行阶段';
      break;

    case 'approve_menxia':
      // 采纳门下省意见
      if (!task.rejections || task.rejections.length === 0) {
        throw new Error(`任务 ${task_id} 没有门下省封驳记录`);
      }
      const latestRejection = task.rejections[task.rejections.length - 1];
      finalPlan = `## 圣上裁决\n\n采纳门下省意见，驳回中书省方案。\n\n### 门下省关切\n${latestRejection.reason}\n\n### 裁决理由\n门下省意见合理，中书省方案不符合要求。`;
      taskState.setApproval(task_id, 'emperor');
      taskState.setResult(task_id, '圣上采纳门下省意见，驳回中书省方案');
      message = '圣上采纳门下省意见，任务需重新规划';
      break;

    case 'custom':
      // 圣上自定义方案
      if (!custom_plan) {
        throw new Error('decision 为 custom 时，必须提供 custom_plan');
      }
      finalPlan = `## 圣上钦定方案\n\n${custom_plan}`;
      taskState.setApproval(task_id, 'emperor');
      taskState.setResult(task_id, '圣上钦定方案');
      message = '圣上钦定方案，任务进入执行阶段';
      break;

    default:
      throw new Error(
        `不支持的 decision: ${decision}（仅支持 approve_zhongshu, approve_menxia, custom）`
      );
  }

  // 更新任务状态为 done
  taskState.updateState(task_id, 'done', `圣上裁决：${decision}`);

  return {
    success: true,
    task_id: task_id,
    final_state: 'done',
    message: message,
    final_plan: finalPlan,
  };
}
