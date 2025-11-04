# Agent Node Pack

一个为ComfyUI设计的智能代理节点包，提供工作流生成、调试、优化和参数测试等功能。

## 主要问题和解决方案
| 问题         | 解决方案                                      |
| ---------- | ----------------------------------------- |
| JSON 太大太复杂 | 拆分为中间 IR + 增量生成                           |
| 节点依赖复杂     | 图结构管理（Node Graph）                         |
| 节点参数繁琐     | Node Registry + 自动补全                      |
| 模型难直接输出    | 只生成结构性指令（DSL）                             |
| 可维护性差      | 多 Agent 分层协作（Builder / Validator / Fixer） |
让大模型不要生成 JSON，而是生成“构建 JSON 的操作”。

用程序保证结构正确性，用多 Agent 协作保证任务完成度。

最终 JSON 只是结果，而不是生成目标。

## 功能特点

- **工作流生成**：基于自然语言描述生成ComfyUI工作流
- **工作流调试**：自动检测工作流中的问题并提供修复建议
- **工作流优化**：优化工作流性能和内存使用
- **参数测试**：测试不同参数组合的效果
- **节点搜索**：全文搜索和语义搜索节点
- **智能对话**：基于LLM的对话系统，提供工作流相关建议

## 安装

1. 将此文件夹复制到ComfyUI的`custom_nodes`目录
2. 重启ComfyUI
3. 在节点菜单中找到"Agent Node Pack"类别

## 使用方法

### 简单节点（推荐初学者使用）

1. **SimpleAgentNode**：基础的代理节点，输入任务描述，获取处理结果
2. **WorkflowGenerationNode**：输入描述，生成工作流
3. **WorkflowDebugNode**：输入工作流JSON，获取调试建议
4. **WorkflowOptimizationNode**：输入工作流JSON，获取优化建议
5. **ParameterTestNode**：输入工作流JSON和节点ID，测试不同参数
6. **NodeSearchNode**：输入查询关键词，搜索相关节点

### 高级节点

1. **AgentNode**：通用代理节点，支持多种代理类型
2. **WorkflowGenerationNode**（高级版）：支持模板和需求列表
3. **WorkflowDebugNode**（高级版）：支持多种调试模式
4. **WorkflowOptimizationNode**（高级版）：支持多种优化类型
5. **ParameterTestNode**（高级版）：支持更多测试选项
6. **NodeSearchNode**（高级版）：支持相似节点搜索

## 配置

插件会在首次运行时自动创建配置文件`config/config.json`，可以修改以下设置：

```json
{
  "api_key": "your-openai-api-key",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "temperature": 0.2,
  "auto_scan_on_start": true
}
```

## API接口

插件提供以下REST API接口：

- `GET /api/workflow_agent/config` - 获取配置
- `POST /api/workflow_agent/config` - 更新配置
- `POST /api/workflow_agent/scan` - 扫描节点
- `POST /api/workflow_agent/current_workflow` - 保存当前工作流

## 故障排除

如果遇到导入错误，请检查：

1. Python路径是否正确
2. 依赖是否已安装
3. ComfyUI版本是否兼容

## 开发

插件采用模块化设计，主要组件：

- `agents/` - 代理实现
- `core/` - 核心功能
- `dao/` - 数据访问对象
- `utils/` - 工具函数
- `app.py` - Web应用
- `__init__.py` - 插件入口

## 许可证

MIT License
