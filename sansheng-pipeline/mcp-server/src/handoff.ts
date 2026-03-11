import { callPythonFunction, execPython, PythonResult } from './utils';

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
 * 发起 Handoff：将任务派发给指定 Agent
 *
 * 工作流程：
 * 1. 验证 handoff 消息格式
 * 2. 调用 Python 的 call_mcp_agent.invoke_agent()
 * 3. 返回 agent 执行结果
 *
 * @param agentName Agent 名称（zhongshu / menxia / libu / hubu / etc.）
 * @param message Handoff 消息
 * @returns Handoff 响应
 */
export async function handoffToAgent(
  agentName: string,
  message: HandoffMessage
): Promise<HandoffResponse> {
  // 验证消息格式
  const validation = validateHandoffMessage(message);
  if (!validation.valid) {
    return {
      success: false,
      agent: agentName,
      action: message.action,
      error: `Handoff 消息验证失败: ${validation.error}`,
    };
  }

  // 调用 Python agent 调用桥接
  const result = callPythonFunction(
    'call_mcp_agent',
    'invoke_agent',
    [agentName, message],
    true // 返回 JSON
  );

  if (!result.success) {
    return {
      success: false,
      agent: agentName,
      action: message.action,
      error: result.error,
    };
  }

  return {
    success: true,
    agent: agentName,
    action: message.action,
    result: result.data,
  };
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

/**
 * 批量 Handoff：顺序执行多个 Agent 调用
 *
 * 适用场景：
 * - 需要按顺序调用多个 Agent（如：中书省起草 → 门下省审议）
 * - 后一个 Agent 的输入依赖前一个 Agent 的输出
 *
 * @param handoffs Handoff 列表，格式：[{agent, message}, ...]
 * @returns 所有响应结果
 */
export async function handoffChain(
  handoffs: Array<{ agent: string; message: HandoffMessage }>
): Promise<HandoffResponse[]> {
  const responses: HandoffResponse[] = [];

  for (const { agent, message } of handoffs) {
    const response = await handoffToAgent(agent, message);
    responses.push(response);

    // 如果任何一个环节失败，停止后续调用
    if (!response.success) {
      break;
    }
  }

  return responses;
}

/**
 * 并行 Handoff：同时执行多个 Agent 调用（无依赖关系）
 *
 * 适用场景：
 * - 多个 Agent 可以并行执行（如：同时调用六部 agent）
 * - Agent 之间无依赖关系
 *
 * @param handoffs Handoff 列表
 * @returns 所有响应结果
 */
export async function handoffParallel(
  handoffs: Array<{ agent: string; message: HandoffMessage }>
): Promise<HandoffResponse[]> {
  const promises = handoffs.map(({ agent, message }) =>
    handoffToAgent(agent, message)
  );

  return Promise.all(promises);
}

/**
 * 带重试的 Handoff
 *
 * 适用场景：
 * - Agent 调用可能因网络或资源问题暂时失败
 * - 需要自动重试
 *
 * @param agentName Agent 名称
 * @param message Handoff 消息
 * @param maxRetries 最大重试次数（默认 3）
 * @param retryDelay 重试延迟（毫秒，默认 1000）
 * @returns Handoff 响应
 */
export async function handoffWithRetry(
  agentName: string,
  message: HandoffMessage,
  maxRetries: number = 3,
  retryDelay: number = 1000
): Promise<HandoffResponse> {
  let lastError = '';

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    const response = await handoffToAgent(agentName, message);

    if (response.success) {
      return response;
    }

    lastError = response.error || 'Unknown error';

    // 如果不是最后一次尝试，等待后重试
    if (attempt < maxRetries) {
      await new Promise((resolve) => setTimeout(resolve, retryDelay));
    }
  }

  // 所有重试都失败
  return {
    success: false,
    agent: agentName,
    action: message.action,
    error: `重试 ${maxRetries} 次后仍失败: ${lastError}`,
  };
}

/**
 * 检查 Agent 是否可用
 *
 * @param agentName Agent 名称
 * @returns 可用性检查结果
 */
export async function checkAgentAvailable(agentName: string): Promise<{
  available: boolean;
  error?: string;
}> {
  const result = execPython(
    `
from pathlib import Path
import importlib.util

# 检查 agent_internal_tools.py 中是否有对应的函数
spec = importlib.util.find_spec('agent_internal_tools')
if spec and spec.origin:
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # 检查是否有对应的 internal 函数
    func_name = f'${agentName}_internal'
    if hasattr(module, func_name):
        print('available')
    else:
        print(f'not_found:{func_name}')
else:
    print('module_not_found:agent_internal_tools')
`,
    false
  );

  if (!result.success) {
    return {
      available: false,
      error: result.error,
    };
  }

  if (result.data === 'available') {
    return { available: true };
  } else {
    return {
      available: false,
      error: result.data,
    };
  }
}

/**
 * 获取所有可用的 Agent 列表
 *
 * @returns Agent 名称列表
 */
export async function listAvailableAgents(): Promise<string[]> {
  const result = execPython(
    `
import importlib.util
import re

spec = importlib.util.find_spec('agent_internal_tools')
if spec and spec.origin:
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # 提取所有 *_internal 函数的 agent 名称
    agents = []
    for name in dir(module):
        if name.endswith('_internal') and not name.startswith('_'):
            agent_name = name.replace('_internal', '')
            agents.append(agent_name)

    print(','.join(agents))
else:
    print('')
`,
    false
  );

  if (!result.success || !result.data) {
    return [];
  }

  return result.data.split(',').filter((name: string) => name.length > 0);
}
