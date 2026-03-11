#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { sanshengReviewAll, sanshengFinalize } from './sansheng';
import * as taskState from './task-state';

const server = new Server(
  {
    name: 'sansheng-mcp-server',
    version: '0.1.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// 列出可用工具
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'sansheng_review_all',
        description: '三省审议流程：自动完成中书省起草和门下省审议',
        inputSchema: {
          type: 'object',
          properties: {
            title: {
              type: 'string',
              description: '任务标题',
            },
            context: {
              type: 'string',
              description: '任务背景和需求',
            },
          },
          required: ['title', 'context'],
        },
      },
      {
        name: 'sansheng_finalize',
        description: '圣上裁决：批准方案或自定义方案',
        inputSchema: {
          type: 'object',
          properties: {
            task_id: {
              type: 'string',
              description: '任务ID（来自 sansheng_review_all 的返回值）',
            },
            decision: {
              type: 'string',
              enum: ['approve_zhongshu', 'approve_menxia', 'custom'],
              description: '决策类型：approve_zhongshu=批准中书省方案，approve_menxia=采纳门下省意见，custom=自定义方案',
            },
            custom_plan: {
              type: 'string',
              description: '自定义方案内容（仅当 decision=custom 时需要）',
            },
          },
          required: ['task_id', 'decision'],
        },
      },
      {
        name: 'sansheng_create_task',
        description: '创建新任务，返回任务ID',
        inputSchema: {
          type: 'object',
          properties: {
            title: {
              type: 'string',
              description: '任务标题',
            },
            context: {
              type: 'string',
              description: '任务背景和需求',
            },
          },
          required: ['title', 'context'],
        },
      },
      {
        name: 'sansheng_submit_plan',
        description: '中书省提交方案版本',
        inputSchema: {
          type: 'object',
          properties: {
            task_id: {
              type: 'string',
              description: '任务ID',
            },
            plan: {
              type: 'string',
              description: '方案内容',
            },
          },
          required: ['task_id', 'plan'],
        },
      },
      {
        name: 'sansheng_submit_decision',
        description: '门下省提交审议决策',
        inputSchema: {
          type: 'object',
          properties: {
            task_id: {
              type: 'string',
              description: '任务ID',
            },
            decision: {
              type: 'string',
              enum: ['approved', 'rejected'],
              description: '审议结果',
            },
            reason: {
              type: 'string',
              description: '封驳理由（仅 decision=rejected 时需要）',
            },
          },
          required: ['task_id', 'decision'],
        },
      },
      {
        name: 'sansheng_get_task',
        description: '查询任务状态和历史',
        inputSchema: {
          type: 'object',
          properties: {
            task_id: {
              type: 'string',
              description: '任务ID',
            },
          },
          required: ['task_id'],
        },
      },
    ],
  };
});

// 调用工具
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === 'sansheng_review_all') {
    try {
      const args = request.params.arguments as any;
      const result = await sanshengReviewAll({
        title: args.title,
        context: args.context,
      });

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: 'text',
            text: `执行失败: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }

  if (request.params.name === 'sansheng_finalize') {
    try {
      const args = request.params.arguments as any;
      const result = await sanshengFinalize({
        task_id: args.task_id,
        decision: args.decision,
        custom_plan: args.custom_plan,
      });

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: 'text',
            text: `执行失败: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }

  if (request.params.name === 'sansheng_create_task') {
    try {
      const args = request.params.arguments as any;
      const taskId = taskState.createTask(args.title, args.context, 'mcp-server');

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({ task_id: taskId }, null, 2),
          },
        ],
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: 'text',
            text: `执行失败: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }

  if (request.params.name === 'sansheng_submit_plan') {
    try {
      const args = request.params.arguments as any;
      const version = taskState.addPlanVersion(args.task_id, args.plan, 'zhongshu');
      taskState.updateState(args.task_id, 'planning', `中书省已提交方案 v${version}`);

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({ version, task_id: args.task_id }, null, 2),
          },
        ],
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: 'text',
            text: `执行失败: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }

  if (request.params.name === 'sansheng_submit_decision') {
    try {
      const args = request.params.arguments as any;

      if (args.decision === 'approved') {
        taskState.updateState(args.task_id, 'approved', '门下省准奏');
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({ decision: 'approved', task_id: args.task_id }, null, 2),
            },
          ],
        };
      } else if (args.decision === 'rejected') {
        const rejectionCount = taskState.addRejection(args.task_id, args.reason || '无具体理由', 'menxia');

        if (rejectionCount >= 3) {
          taskState.setEscalation(args.task_id, args.reason || '封驳次数达到上限');
        }

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                decision: 'rejected',
                reason: args.reason,
                rejection_count: rejectionCount,
                escalated: rejectionCount >= 3,
              }, null, 2),
            },
          ],
        };
      } else {
        throw new Error(`Invalid decision: ${args.decision}`);
      }
    } catch (error: any) {
      return {
        content: [
          {
            type: 'text',
            text: `执行失败: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }

  if (request.params.name === 'sansheng_get_task') {
    try {
      const args = request.params.arguments as any;
      const task = taskState.getTask(args.task_id);

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(task, null, 2),
          },
        ],
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: 'text',
            text: `执行失败: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }

  throw new Error(`Unknown tool: ${request.params.name}`);
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Sansheng MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});
