#!/usr/bin/env ts-node
/**
 * task-state.ts 单元测试
 * 测试 TypeScript 封装调用 Python task_state.py
 */

import * as taskState from './task-state';

console.log('=== task-state.ts 单元测试 ===\n');

try {
  // 测试 1: 创建任务
  console.log('✓ 测试创建任务...');
  const taskId = taskState.createTask('测试任务', '这是一个测试任务的背景', 'test-mcp-server');
  console.log(`  任务 ID: ${taskId}\n`);

  // 测试 2: 添加规划版本
  console.log('✓ 测试添加规划版本...');
  const version = taskState.addPlanVersion(taskId, '第一版规划内容：\\n- 步骤1\\n- 步骤2', 'zhongshu');
  console.log(`  版本号: ${version}\n`);

  // 测试 3: 添加封驳
  console.log('✓ 测试添加封驳...');
  const count = taskState.addRejection(taskId, '规划不够详细，需要补充', 'menxia');
  console.log(`  封驳次数: ${count}\n`);

  // 测试 4: 获取封驳次数
  console.log('✓ 测试获取封驳次数...');
  const rejectionCount = taskState.getRejectionCount(taskId);
  console.log(`  当前封驳次数: ${rejectionCount}\n`);

  // 测试 5: 读取任务
  console.log('✓ 测试读取任务...');
  const task = taskState.getTask(taskId);
  console.log(`  任务状态: ${task.state}`);
  console.log(`  任务标题: ${task.title}`);
  console.log(`  规划版本数: ${task.versions.length}`);
  console.log(`  封驳记录数: ${task.rejections.length}\n`);

  // 测试 6: 获取最新规划
  console.log('✓ 测试获取最新规划...');
  const latestPlan = taskState.getLatestPlan(taskId);
  console.log(`  最新规划作者: ${latestPlan.author}`);
  console.log(`  最新规划版本: ${latestPlan.version}\n`);

  // 测试 7: 更新状态
  console.log('✓ 测试更新状态...');
  taskState.updateState(taskId, 'planning', '重新规划中');
  console.log(`  状态已更新为: planning\n`);

  // 测试 8: 设置升级
  console.log('✓ 测试设置升级...');
  taskState.setEscalation(taskId, '封驳次数超过阈值，升级用户裁决');
  const taskAfterEscalation = taskState.getTask(taskId);
  console.log(`  任务状态: ${taskAfterEscalation.state}`);
  console.log(`  升级记录存在: ${taskAfterEscalation.escalation !== null}\n`);

  // 测试 9: 设置批准
  console.log('✓ 测试设置批准...');
  taskState.setApproval(taskId, 'user');
  const taskAfterApproval = taskState.getTask(taskId);
  console.log(`  任务状态: ${taskAfterApproval.state}`);
  console.log(`  批准记录存在: ${taskAfterApproval.approval !== null}\n`);

  // 测试 10: 设置结果
  console.log('✓ 测试设置结果...');
  taskState.setResult(taskId, '任务已完成，产出：测试报告');
  const finalTask = taskState.getTask(taskId);
  console.log(`  任务状态: ${finalTask.state}`);
  console.log(`  任务结果: ${finalTask.result}\n`);

  // 测试 11: 创建子任务
  console.log('✓ 测试创建子任务...');
  const subtask1Id = taskState.createSubtask(
    taskId,
    '子任务1：编写代码',
    'coding',
    'bingbu',
    '实现核心逻辑'
  );
  console.log(`  子任务 1 ID: ${subtask1Id}`);

  const subtask2Id = taskState.createSubtask(
    taskId,
    '子任务2：编写测试',
    'testing',
    'bingbu',
    '覆盖核心逻辑的单元测试',
    [1]  // 依赖子任务 1
  );
  console.log(`  子任务 2 ID: ${subtask2Id}\n`);

  // 测试 12: 更新子任务状态
  console.log('✓ 测试更新子任务状态...');
  taskState.updateSubtaskStatus(subtask1Id, 'completed', '代码已提交');
  const subtask1 = taskState.getSubtask(subtask1Id);
  console.log(`  子任务 1 状态: ${subtask1.status}`);
  console.log(`  子任务 1 结果: ${subtask1.result}\n`);

  // 测试 13: 获取子任务列表
  console.log('✓ 测试获取子任务列表...');
  const subtasks = taskState.getSubtasks(taskId);
  console.log(`  子任务总数: ${subtasks.length}`);
  console.log(`  子任务列表:`);
  subtasks.forEach(st => {
    console.log(`    - ${st.id}: ${st.title} [${st.status}]`);
  });
  console.log();

  // 测试 14: 列出所有任务
  console.log('✓ 测试列出所有任务...');
  const allTasks = taskState.listTasks();
  console.log(`  总任务数: ${allTasks.length}`);
  console.log(`  最新任务: ${allTasks[0].id} - ${allTasks[0].title}\n`);

  // 测试 15: 按状态筛选任务
  console.log('✓ 测试按状态筛选任务...');
  const doneTasks = taskState.listTasks('done');
  console.log(`  已完成任务数: ${doneTasks.length}\n`);

  console.log('=== 所有测试通过 ===');
  process.exit(0);

} catch (error: any) {
  console.error('✗ 测试失败:', error.message);
  process.exit(1);
}
