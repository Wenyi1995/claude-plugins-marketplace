# Claude Plugins Marketplace - Wenyi1995

三省六部决策流程插件市场

## 包含的插件

### sansheng-pipeline (v0.3.0)

三省六部审议流程插件，模拟中国古代决策机制：

- **中书省** (zhongshu) - 方案规划者：接收任务，起草执行方案
- **门下省** (menxia) - 方案审议者：评审方案质量，提出封驳意见
- **尚书省** (shangshu) - 任务派发者：拆解任务，协调六部执行

六部分工：

- **吏部** (libu-personnel) - Agent 人事管理
- **户部** (hubu-resources) - Agent 运行资源保障
- **礼部** (libu-rites) - 知识沉淀与文化传承
- **兵部** (bingbu-military) - 任务实际执行（主力）
- **刑部** (xingbu-justice) - 质量检查与合规审查
- **工部** (gongbu-works) - 系统集成与基础设施

**核心特性**：

- 多版本方案管理（v1, v2, v3...）
- 门下省封驳机制（质量把关）
- 六部协作执行（串行/并行）
- 完整审计日志
- 基于 MCP Server 实现

**适用场景**：

- 复杂任务的结构化决策
- 多 Agent 协作流程
- 需要质量审议的项目
- 学习古代官僚制度与现代软件工程的结合

## 安装

详见 [INSTALL.md](./INSTALL.md)

## 许可证

MIT License

## 作者

Wenyi1995 (tianyipc@gmail.com)
