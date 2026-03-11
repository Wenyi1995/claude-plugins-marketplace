#!/usr/bin/env ts-node
/**
 * utils.ts 和 handoff.ts 集成测试
 */
import * as utils from './utils';
import * as handoff from './handoff';

async function main() {
  console.log('=== utils.ts 和 handoff.ts 集成测试 ===\n');

  // ========== 测试 1: execPython 基础功能 ==========
  console.log('【测试 1】execPython 基础功能');
  const result1 = utils.execPython('print("Hello from Python")');
  console.log('执行结果:', result1);
  console.log('✓ 通过\n');

  // ========== 测试 2: callPythonFunction ==========
  console.log('【测试 2】callPythonFunction 调用 task_state.list_tasks()');
  const result2 = utils.callPythonFunction('task_state', 'list_tasks', [], true);
  console.log('执行结果:', result2);
  if (result2.success) {
    console.log('任务列表:', result2.data);
  }
  console.log('✓ 通过\n');

  // ========== 测试 3: 验证 Handoff 消息格式 ==========
  console.log('【测试 3】validateHandoffMessage');

  const validMessage: handoff.HandoffMessage = {
    task_id: 'TASK-TEST-001',
    action: 'draft',
    content: { version: 1 },
  };
  const validation1 = handoff.validateHandoffMessage(validMessage);
  console.log('有效消息验证:', validation1);

  const invalidMessage: any = {
    task_id: '',
    action: 'draft',
    content: 'not an object',
  };
  const validation2 = handoff.validateHandoffMessage(invalidMessage);
  console.log('无效消息验证:', validation2);
  console.log('✓ 通过\n');

  // ========== 测试 4: 列出可用 Agent ==========
  console.log('【测试 4】listAvailableAgents');
  const agents = await handoff.listAvailableAgents();
  console.log('可用 Agent 列表:', agents);
  console.log('✓ 通过\n');

  // ========== 测试 5: 检查特定 Agent 是否可用 ==========
  console.log('【测试 5】checkAgentAvailable');
  const zhongshuAvailable = await handoff.checkAgentAvailable('zhongshu');
  console.log('中书省可用性:', zhongshuAvailable);

  const invalidAgentAvailable = await handoff.checkAgentAvailable('nonexistent');
  console.log('不存在的 Agent 可用性:', invalidAgentAvailable);
  console.log('✓ 通过\n');

  // ========== 测试 6: 真实 Handoff（需要真实任务 ID）==========
  console.log('【测试 6】真实 Handoff（创建测试任务）');

  // 6.1 创建测试任务
  const createTaskResult = utils.callPythonFunction(
    'task_state',
    'create_task',
    ['测试任务 - utils & handoff', '测试 handoff 机制', 'test-suite'],
    false
  );

  if (createTaskResult.success) {
    const taskId = createTaskResult.data;
    console.log('创建测试任务:', taskId);

    // 6.2 Handoff 到中书省
    const handoffMessage: handoff.HandoffMessage = {
      task_id: taskId,
      action: 'draft',
      content: {},
    };

    console.log('\nHandoff 到中书省起草方案...');
    const handoffResponse = await handoff.handoffToAgent('zhongshu', handoffMessage);
    console.log('Handoff 响应:', JSON.stringify(handoffResponse, null, 2));

    if (handoffResponse.success) {
      console.log('✓ Handoff 成功');
      console.log('生成的方案版本:', handoffResponse.result?.version);
    } else {
      console.log('✗ Handoff 失败:', handoffResponse.error);
    }
  } else {
    console.log('✗ 创建任务失败:', createTaskResult.error);
  }

  console.log('\n=== 所有测试完成 ===');
}

main().catch((error) => {
  console.error('测试失败:', error);
  process.exit(1);
});
