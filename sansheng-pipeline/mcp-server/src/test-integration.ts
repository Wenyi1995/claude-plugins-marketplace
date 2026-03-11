#!/usr/bin/env ts-node
/**
 * 完整集成测试：验证 Task-based Agent 协作流程
 *
 * 测试场景：
 * 1. 创建任务
 * 2. 中书省提交方案（3次）
 * 3. 门下省封驳（3次，触发升级）
 * 4. 圣上裁决
 */

import * as taskState from './task-state';
import { sanshengFinalize } from './sansheng';

async function main() {
  console.log('=== 完整集成测试 ===\n');

  // ========== 场景 1: 简单任务（准奏）==========
  console.log('【场景 1】简单任务（准奏场景）');

  const task1Id = taskState.createTask(
    '创建用户注册功能',
    '需要实现手机号+验证码登录，包含邮箱验证、密码加密、用户信息存储',
    'integration-test'
  );
  console.log('✓ 任务创建:', task1Id);

  // 中书省提交完整方案
  taskState.addPlanVersion(task1Id, `
## 中书省方案 v1

### 一、任务背景
用户需要实现一个用户注册系统，支持手机号+验证码登录。

### 二、实施方案

1. 数据库设计
   - 具体动作：创建 users 表（id, phone, created_at）和 sms_codes 表（phone, code, expires_at）
   - 预期产出：PostgreSQL migration 脚本
   - 风险点：表结构变更需要与现有系统兼容

2. API 实现
   - 具体动作：开发 POST /api/register（发送验证码）和 POST /api/verify（校验验证码并创建用户）
   - 预期产出：FastAPI 路由 + Pydantic models
   - 风险点：短信接口可能限流

3. 测试
   - 具体动作：编写单元测试（验证码生成/校验逻辑）和集成测试（完整注册流程）
   - 预期产出：pytest 用例，覆盖率 > 80%
   - 风险点：测试环境短信接口需要 mock

### 三、风险评估

- **技术风险**：短信接口限流 → 应对：Redis 限流，1分钟内同手机号只能发1次
- **时间风险**：第三方短信 SDK 集成可能遇到问题 → 应对：预留 0.5 天 buffer
- **资源风险**：需要 Twilio 账号和测试额度 → 应对：提前申请开通

### 四、验收标准

- **功能完整性**：能成功注册用户，验证码5分钟过期
- **性能指标**：接口响应时间 < 200ms，支持 100 QPS
- **安全合规**：验证码错误5次锁定账号10分钟，防止暴力破解
  `, 'zhongshu');
  taskState.updateState(task1Id, 'planning', '中书省已提交方案 v1');
  console.log('✓ 中书省提交完整方案');

  // 门下省准奏
  taskState.updateState(task1Id, 'approved', '门下省准奏');
  console.log('✓ 门下省准奏');

  // 圣上批准
  const result1 = await sanshengFinalize({
    task_id: task1Id,
    decision: 'approve_zhongshu'
  });
  console.log('✓ 圣上批准:', result1.message);
  console.log('');

  // ========== 场景 2: 复杂任务（封驳场景）==========
  console.log('【场景 2】复杂任务（封驳场景）');

  const task2Id = taskState.createTask(
    '实现分布式缓存系统',
    '高并发、低延迟',
    'integration-test'
  );
  console.log('✓ 任务创建:', task2Id);

  // 中书省提交第1版（缺少风险评估）
  taskState.addPlanVersion(task2Id, `
## 中书省方案 v1

### 一、任务背景
实现分布式缓存系统，要求高并发、低延迟。

### 二、实施方案

1. 选型 Redis Cluster
2. 部署 3 主 3 从架构
3. 配置持久化
4. 性能测试

### 三、验收标准
- 响应时间 < 10ms
- 支持 10万 QPS
  `, 'zhongshu');
  taskState.updateState(task2Id, 'planning', '中书省已提交方案 v1');
  console.log('✓ 中书省提交 v1（缺少风险评估）');

  // 门下省封驳（第1次）
  taskState.addRejection(task2Id, '方案缺少风险评估章节，请补充技术风险、时间风险和资源风险的具体评估', 'menxia');
  console.log('✓ 门下省第1次封驳');

  // 中书省提交第2版（补充风险评估但不具体）
  taskState.addPlanVersion(task2Id, `
## 中书省方案 v2

（保留 v1 内容）

### 三、风险评估（新增）
- 技术风险：已评估
- 时间风险：已评估
- 资源风险：已评估
  `, 'zhongshu');
  console.log('✓ 中书省提交 v2（补充风险评估但不具体）');

  // 门下省准奏（放宽标准，80分即可）
  taskState.updateState(task2Id, 'approved', '门下省准奏');
  console.log('✓ 门下省准奏（虽然不够完美，但符合80分标准）');
  console.log('');

  // ========== 场景 3: 升级裁决场景 ==========
  console.log('【场景 3】升级裁决场景（3次封驳）');

  const task3Id = taskState.createTask(
    '重构用户认证模块',
    '从 session 改为 JWT',
    'integration-test'
  );
  console.log('✓ 任务创建:', task3Id);

  // 中书省提交 v1
  taskState.addPlanVersion(task3Id, `
## 中书省方案 v1

### 一、任务背景
从 session 改为 JWT

### 二、实施方案
1. 全面切换 JWT
2. 删除 session 代码

### 三、风险评估
- 技术风险：已评估

### 四、验收标准
- 功能：JWT 正常
  `, 'zhongshu');
  console.log('✓ 中书省提交 v1');

  // 门下省封驳（第1次）
  const count1 = taskState.addRejection(task3Id, '未考虑旧用户迁移问题', 'menxia');
  console.log(`✓ 门下省第1次封驳（rejection_count=${count1}）`);

  // 中书省提交 v2
  taskState.addPlanVersion(task3Id, `
## 中书省方案 v2

（增加双模式兼容期）
兼容期：30天
  `, 'zhongshu');
  console.log('✓ 中书省提交 v2（增加30天兼容期）');

  // 门下省封驳（第2次）
  const count2 = taskState.addRejection(task3Id, '兼容期太长，建议7天', 'menxia');
  console.log(`✓ 门下省第2次封驳（rejection_count=${count2}）`);

  // 中书省提交 v3（坚持30天）
  taskState.addPlanVersion(task3Id, `
## 中书省方案 v3

坚持30天兼容期，因为大客户需要时间适配
  `, 'zhongshu');
  console.log('✓ 中书省提交 v3（坚持30天）');

  // 门下省封驳（第3次，触发升级）
  const count3 = taskState.addRejection(task3Id, '仍建议7天兼容期，建议升级司礼监裁决', 'menxia');
  taskState.setEscalation(task3Id, '封驳次数达到3次');
  console.log(`✓ 门下省第3次封驳（rejection_count=${count3}，触发 escalation）`);

  // 验证 escalation 状态
  const task3 = taskState.getTask(task3Id);
  console.log('✓ 验证升级状态:', task3.state === 'escalated' ? '✅ escalated' : `❌ ${task3.state}`);
  console.log('✓ Escalation 记录:', task3.escalation ? '✅ 存在' : '❌ 缺失');

  // 圣上裁决（批准中书省方案）
  const result3 = await sanshengFinalize({
    task_id: task3Id,
    decision: 'approve_zhongshu'
  });
  console.log('✓ 圣上批准中书省方案（30天兼容期）:', result3.message);
  console.log('');

  // ========== 数据一致性验证 ==========
  console.log('【数据一致性验证】');

  const task1 = taskState.getTask(task1Id);
  console.log(`✓ 任务1: state=${task1.state}, versions=${task1.versions.length}, rejections=${task1.rejections.length}`);

  const task2 = taskState.getTask(task2Id);
  console.log(`✓ 任务2: state=${task2.state}, versions=${task2.versions.length}, rejections=${task2.rejections.length}`);

  console.log(`✓ 任务3: state=${task3.state}, versions=${task3.versions.length}, rejections=${task3.rejections.length}`);

  console.log('');
  console.log('🎉 所有集成测试通过');
}

main().catch(console.error);
