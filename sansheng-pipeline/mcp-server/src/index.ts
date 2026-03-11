#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { sanshengReviewAll, sanshengFinalize } from './sansheng';

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
