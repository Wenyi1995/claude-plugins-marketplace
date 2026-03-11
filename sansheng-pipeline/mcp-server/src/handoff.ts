
/**
 * Handoff 消息结构
 */
export interface HandoffMessage {
  task_id: string;
  action: string;
  content: Record<string, any>;
}

/**
 * Handoff 响应结构
 */
export interface HandoffResponse {
  success: boolean;
  agent: string;
  action: string;
  result?: any;
  error?: string;
}


/**
 * 验证 Handoff 消息格式
 *
 * 必需字段：
 * - task_id: 任务 ID（非空字符串）
 * - action: 操作类型（非空字符串）
 * - content: 上下文信息（对象）
 *
 * @param message Handoff 消息
 * @returns 验证结果
 */
export function validateHandoffMessage(message: HandoffMessage): {
  valid: boolean;
  error?: string;
} {
  if (!message.task_id || typeof message.task_id !== 'string') {
    return {
      valid: false,
      error: 'task_id 必须是非空字符串',
    };
  }

  if (!message.action || typeof message.action !== 'string') {
    return {
      valid: false,
      error: 'action 必须是非空字符串',
    };
  }

  if (!message.content || typeof message.content !== 'object') {
    return {
      valid: false,
      error: 'content 必须是对象',
    };
  }

  return { valid: true };
}





