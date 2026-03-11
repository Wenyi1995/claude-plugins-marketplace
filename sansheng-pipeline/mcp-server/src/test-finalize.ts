#!/usr/bin/env ts-node
/**
 * sansheng_finalize 快速测试
 */

import { sanshengReviewAll, sanshengFinalize } from './sansheng';

async function testFinalize() {
  console.log('=== 测试 sansheng_finalize ===\n');

  // 1. 创建一个升级任务
  console.log('步骤1：创建升级任务...');
  const reviewResult = await sanshengReviewAll({
    title: 'Finalize 测试任务',
    context: '测试', // 极简context，触发3次封驳
  });
  console.log('  任务ID:', reviewResult.task_id);
  console.log('  状态:', reviewResult.status);
  console.log();

  if (reviewResult.status !== 'escalated') {
    console.error('✗ 错误：预期状态为 escalated，实际为', reviewResult.status);
    process.exit(1);
  }

  // 2. 测试批准中书省方案
  console.log('步骤2：测试批准中书省方案...');
  const result1 = await sanshengFinalize({
    task_id: reviewResult.task_id,
    decision: 'approve_zhongshu',
  });
  console.log('  成功:', result1.success);
  console.log('  最终状态:', result1.final_state);
  console.log('  消息:', result1.message);
  console.log('  方案长度:', result1.final_plan.length, '字符');
  console.log();

  if (!result1.success || result1.final_state !== 'done') {
    console.error('✗ 错误：finalize 失败');
    process.exit(1);
  }

  // 3. 创建第二个任务测试 custom 决策
  console.log('步骤3：测试自定义方案...');
  const reviewResult2 = await sanshengReviewAll({
    title: 'Custom 测试任务',
    context: '需要自定义',
  });
  console.log('  任务ID:', reviewResult2.task_id);

  const result2 = await sanshengFinalize({
    task_id: reviewResult2.task_id,
    decision: 'custom',
    custom_plan: '圣上钦定：采用方案C，结合中书省和门下省的意见',
  });
  console.log('  成功:', result2.success);
  console.log('  消息:', result2.message);
  console.log('  方案预览:', result2.final_plan.substring(0, 100) + '...');
  console.log();

  // 4. 测试 approve_menxia 决策
  console.log('步骤4：测试采纳门下省意见...');
  const reviewResult3 = await sanshengReviewAll({
    title: 'Menxia 测试任务',
    context: '门下省测试',
  });
  console.log('  任务ID:', reviewResult3.task_id);

  if (reviewResult3.status === 'escalated') {
    const result3 = await sanshengFinalize({
      task_id: reviewResult3.task_id,
      decision: 'approve_menxia',
    });
    console.log('  成功:', result3.success);
    console.log('  消息:', result3.message);
    console.log('  方案包含门下省关切:', result3.final_plan.includes('门下省关切'));
    console.log();

    if (!result3.success) {
      console.error('✗ 错误：finalize 失败');
      process.exit(1);
    }
  } else {
    console.log('  (任务直接通过，跳过 approve_menxia 测试)');
    console.log();
  }

  console.log('✓ 所有测试通过');
  process.exit(0);
}

testFinalize().catch((err) => {
  console.error('✗ 测试失败:', err.message);
  console.error(err.stack);
  process.exit(1);
});
