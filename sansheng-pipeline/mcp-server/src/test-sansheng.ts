#!/usr/bin/env ts-node
/**
 * sansheng.ts 单元测试
 * 测试三省审议流程
 */

import { sanshengReviewAll } from './sansheng';

async function testScenario1() {
  console.log('\n=== 场景1：正常准奏（无封驳）===');
  console.log('说明：提供完整的任务背景，预期一次通过审议\n');

  const result = await sanshengReviewAll({
    title: '实现用户注册API',
    context:
      '需要实现用户注册API，包括邮箱验证、密码加密、用户信息存储。要求使用JWT认证，密码使用bcrypt加密，邮箱验证采用SMTP发送验证码。',
  });

  console.log('任务ID:', result.task_id);
  console.log('状态:', result.status);
  console.log('摘要:', result.summary);
  console.log('方案长度:', result.final_plan?.length, '字符');
  console.log('元信息:', result.meta);
  console.log('方案预览:');
  console.log(result.final_plan?.substring(0, 200) + '...\n');

  if (result.status !== 'approved') {
    throw new Error('场景1失败：预期状态为 approved');
  }
  if (!result.final_plan) {
    throw new Error('场景1失败：缺少 final_plan');
  }
  if (!result.meta || result.meta.rejections !== 0) {
    throw new Error('场景1失败：预期无封驳');
  }

  console.log('✓ 场景1通过\n');
}

async function testScenario2() {
  console.log('\n=== 场景2：封驳后准奏 ===');
  console.log('说明：提供简单的任务背景，预期会被封驳1-2次后通过\n');

  const result = await sanshengReviewAll({
    title: '实现支付系统',
    context: '需要实现支付功能', // 简单context，预期会触发封驳
  });

  console.log('任务ID:', result.task_id);
  console.log('状态:', result.status);
  console.log('摘要:', result.summary);
  console.log('元信息:', result.meta);

  if (result.status === 'approved') {
    console.log('方案版本数:', result.meta?.versions);
    console.log('封驳次数:', result.meta?.rejections);

    if (!result.meta || result.meta.rejections === 0) {
      console.log(
        '⚠ 警告：预期会有封驳，但实际无封驳（可能是审议规则太宽松）'
      );
    } else {
      console.log('✓ 场景2通过（经过封驳后准奏）\n');
    }
  } else if (result.status === 'escalated') {
    console.log('触发升级裁决（封驳3次）');
    console.log('冲突信息:', {
      concerns: result.conflict?.menxia_concerns,
      rejection_count: result.conflict?.rejection_history.length,
    });
    console.log('✓ 场景2通过（触发升级）\n');
  }
}

async function testScenario3() {
  console.log('\n=== 场景3：升级裁决（封驳3次）===');
  console.log('说明：提供极简任务背景，预期会触发3次封驳并升级裁决\n');

  const result = await sanshengReviewAll({
    title: '系统改造',
    context: '需要改造', // 极简context，预期触发多次封驳
  });

  console.log('任务ID:', result.task_id);
  console.log('状态:', result.status);
  console.log('摘要:', result.summary);

  if (result.status === 'escalated') {
    console.log('冲突详情:');
    console.log('  - 中书省方案长度:', result.conflict?.zhongshu_latest_plan.length);
    console.log('  - 门下省关切:', result.conflict?.menxia_concerns);
    console.log('  - 封驳次数:', result.conflict?.rejection_history.length);
    console.log('  - 封驳历史:');
    result.conflict?.rejection_history.forEach((r) => {
      console.log(`    ${r.count}. ${r.reason.substring(0, 50)}...`);
    });

    if (!result.conflict || result.conflict.rejection_history.length !== 3) {
      throw new Error('场景3失败：预期封驳3次');
    }

    console.log('\n✓ 场景3通过\n');
  } else {
    console.log(
      '⚠ 警告：预期触发升级裁决，但实际状态为:',
      result.status
    );
  }
}

async function main() {
  console.log('=== 三省审议流程测试 ===\n');

  try {
    await testScenario1();
    await testScenario2();
    await testScenario3();

    console.log('\n=== 所有测试通过 ===');
    process.exit(0);
  } catch (error: any) {
    console.error('\n✗ 测试失败:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();
