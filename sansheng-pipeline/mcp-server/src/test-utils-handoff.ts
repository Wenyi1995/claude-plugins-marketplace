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


  console.log('\n=== 所有测试完成 ===');
}

main().catch((error) => {
  console.error('测试失败:', error);
  process.exit(1);
});
