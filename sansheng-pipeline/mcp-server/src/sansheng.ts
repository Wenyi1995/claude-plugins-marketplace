import * as taskState from './task-state';
import { handoffToAgent, handoffWithRetry } from './handoff';

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
 * 中书省：起草方案
 */
function zhongshuPlan(taskId: string, context: string, version: number): string {
  // 提取原始 context（去除封驳意见）
  const originalContext = context.split('\n\n【门下省封驳意见】')[0];
  const isVerySimpleContext = originalContext.length < 20;

  // 基础方案框架
  let plan = `
## 中书省方案 v${version}

### 一、任务背景
${context}

### 二、实施方案
1. 需求分析
2. 技术选型
3. 架构设计
4. 开发实施
5. 测试验证
`;

  // 判断是否应该补充完整章节
  // 极简context（<20字符）：中书省态度消极，即使修订也不补充
  // 详细context（>=50字符）：直接生成完整方案
  // 中等context（20-50字符）：修订后才补充
  const isDetailedContext = originalContext.length >= 50;
  const isRevision = version > 1 && context.includes('【门下省封驳意见】');

  if (!isVerySimpleContext && (isDetailedContext || isRevision)) {
    plan += `
### 三、风险评估
- 技术风险：已评估
- 时间风险：已评估
- 资源风险：已评估

### 四、验收标准
- 功能完整性
- 性能指标
- 安全合规
`;
  }

  // 如果是修订版，添加修订说明
  if (isRevision) {
    const concernMatch = context.match(/【门下省封驳意见】\n(.+)/s);
    if (concernMatch) {
      if (isVerySimpleContext) {
        plan += `\n### 五、针对门下省封驳意见的说明\n中书省认为当前方案已符合要求，门下省过于苛刻。\n`;
      } else {
        plan += `\n### 五、针对门下省封驳意见的修订\n已根据封驳意见补充完善上述章节内容。\n`;
      }
    }
  }

  // 添加方案版本到任务状态
  taskState.addPlanVersion(taskId, plan, 'zhongshu');
  taskState.updateState(taskId, 'planning', `中书省已起草方案 v${version}`);

  return plan;
}

/**
 * 门下省：审议方案
 */
function menxiaReview(
  taskId: string,
  plan: string,
  version: number,
  currentRejectionCount: number
): {
  decision: 'approved' | 'rejected';
  reason?: string;
} {
  taskState.updateState(taskId, 'reviewing', `门下省正在审议方案 v${version}`);

  // 基础审查规则
  const hasRiskAssessment = plan.includes('风险评估');
  const hasAcceptanceCriteria = plan.includes('验收标准');
  const hasTechnicalDetailsSection = plan.includes('### 六、技术细节说明');

  // 审议逻辑：根据封驳次数提出不同的要求
  if (currentRejectionCount === 0) {
    // 第一次审议：检查风险评估
    if (!hasRiskAssessment) {
      const reason = `方案 v${version} 缺少风险评估章节，请补充可能的技术风险、时间风险和资源风险`;
      taskState.addRejection(taskId, reason, 'menxia');
      return { decision: 'rejected', reason };
    }
  } else if (currentRejectionCount === 1) {
    // 第二次审议：检查验收标准
    if (!hasAcceptanceCriteria) {
      const reason = `方案 v${version} 缺少验收标准，请明确功能完整性、性能指标、安全合规的验收标准`;
      taskState.addRejection(taskId, reason, 'menxia');
      return { decision: 'rejected', reason };
    }
  } else if (currentRejectionCount === 2) {
    // 第三次审议：检查技术细节说明章节（更严格的要求）
    if (!hasTechnicalDetailsSection) {
      const reason = `方案 v${version} 缺少技术细节说明章节，请补充【六、技术细节说明】，包括技术选型依据、架构设计说明和实施细节`;
      taskState.addRejection(taskId, reason, 'menxia');
      return { decision: 'rejected', reason };
    }
  }

  // 通过审议
  return { decision: 'approved' };
}

/**
 * 自动循环协调器：中书省 ↔ 门下省自动审议
 *
 * 流程：
 * 1. Handoff 给中书省起草 v1
 * 2. While 封驳次数 < 3:
 *    2.1 Handoff 给门下省审议
 *    2.2 如果准奏 → 返回结果
 *    2.3 如果封驳 → Handoff 给中书省修改
 * 3. 封驳 5 次 → 升级司礼监
 */
async function autoCoordinateLoop(taskId: string): Promise<ReviewAllResult> {
  const MAX_REJECTIONS = 5;
  let rejectionCount = 0;
  let version = 0;

  // 步骤 1: Handoff 给中书省起草（带重试）
  console.log(`[AUTO-LOOP] 任务 ${taskId} 开始，Handoff 给中书省起草...`);

  const zhongshuDraftResult = await handoffWithRetry(
    'zhongshu',
    {
      task_id: taskId,
      action: 'draft',
      content: {
        instruction: '请起草执行方案'
      }
    },
    3,    // 最大重试 3 次
    1000  // 每次重试间隔 1 秒
  );

  if (!zhongshuDraftResult.success) {
    throw new Error(`中书省起草失败: ${zhongshuDraftResult.error}`);
  }

  version = zhongshuDraftResult.result?.version || 1;
  console.log(`[AUTO-LOOP] 中书省已提交方案 v${version}`);

  // 步骤 2: 循环审议
  while (rejectionCount < MAX_REJECTIONS) {
    console.log(`[AUTO-LOOP] Handoff 给门下省审议方案 v${version}...`);

    // 2.1 Handoff 给门下省审议（带重试）
    const menxiaResult = await handoffWithRetry(
      'menxia',
      {
        task_id: taskId,
        action: 'review',
        content: {
          version: version
        }
      },
      3,
      1000
    );

    if (!menxiaResult.success) {
      throw new Error(`门下省审议失败: ${menxiaResult.error}`);
    }

    // 2.2 门下省决策
    if (menxiaResult.result?.decision === 'approved') {
      // 准奏，结束循环
      console.log(`[AUTO-LOOP] 门下省准奏方案 v${version}，流程结束`);

      return {
        status: 'approved',
        task_id: taskId,
        summary: `方案 v${version} 已通过三省审议，等待圣上批准`,
        final_plan: menxiaResult.result?.plan || '',
        meta: {
          versions: version,
          rejections: rejectionCount,
        },
      };
    } else if (menxiaResult.result?.decision === 'rejected') {
      // 封驳，handoff 回中书省修改
      rejectionCount++;
      console.log(`[AUTO-LOOP] 门下省封驳方案 v${version}（第 ${rejectionCount} 次）`);

      if (rejectionCount >= MAX_REJECTIONS) {
        // 封驳 5 次，升级裁决
        console.log(`[AUTO-LOOP] 封驳 ${MAX_REJECTIONS} 次，升级圣上裁决`);

        taskState.updateState(taskId, 'escalated', `封驳 ${MAX_REJECTIONS} 次，升级圣上裁决`);

        const task = taskState.getTask(taskId);

        return {
          status: 'escalated',
          task_id: taskId,
          summary: `方案 v${version} 已被封驳 3 次，需要圣上裁决`,
          conflict: {
            zhongshu_latest_plan: menxiaResult.result?.zhongshu_plan || '',
            menxia_concerns: menxiaResult.result?.reason || '',
            rejection_history: task.rejections || [],
          },
        };
      }

      // 继续修改
      console.log(`[AUTO-LOOP] Handoff 给中书省修改方案...`);

      const zhongshuReviseResult = await handoffWithRetry(
        'zhongshu',
        {
          task_id: taskId,
          action: 'revise',
          content: {
            rejection_reason: menxiaResult.result?.reason || '',
            rejection_count: rejectionCount
          }
        },
        3,
        1000
      );

      if (!zhongshuReviseResult.success) {
        throw new Error(`中书省修改失败: ${zhongshuReviseResult.error}`);
      }

      version = zhongshuReviseResult.result?.version || version + 1;
      console.log(`[AUTO-LOOP] 中书省已提交修改版 v${version}`);
    }
  }

  // 理论上不会到达这里
  throw new Error('Unexpected state in autoCoordinateLoop');
}

/**
 * 三省审议流程（核心函数）
 *
 * 修改后：不再模拟中书省和门下省，而是启动自动循环协调器
 */
export async function sanshengReviewAll(
  args: ReviewAllArgs
): Promise<ReviewAllResult> {
  const { title, context } = args;

  // 1. 司礼监：创建任务
  const taskId = taskState.createTask(title, context, 'sililijian');
  taskState.updateState(taskId, 'created', '司礼监已创建任务');

  // 2. 启动自动循环协调器
  try {
    const result = await autoCoordinateLoop(taskId);
    return result;
  } catch (error: any) {
    // 失败升级司礼监
    taskState.updateState(taskId, 'escalated', `自动循环失败: ${error.message}`);
    throw error;
  }
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
