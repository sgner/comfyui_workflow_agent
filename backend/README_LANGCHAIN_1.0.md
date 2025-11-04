# LangChain 1.0 重构说明

本文档说明如何使用重构后的基于LangChain 1.0的agents。

## 概述

我们已将后端agent系统从直接调用API的方式重构为使用LangChain 1.0框架，提供了更好的抽象和扩展性。

## 主要变化

### 1. 依赖更新

更新了以下依赖包：

- `langchain>=1.0.0`
- `langchain-community>=0.3.0`
- `langchain-core>=0.3.0`
- `langchain-openai>=0.2.0`
- `langchain-anthropic>=0.3.0`
- `langgraph>=0.2.0`

### 2. 重构的组件

#### LLM工具类 (`llm_tools_langchain.py`)

- 使用LangChain的LLM抽象，支持多种提供商
- 提供统一的API调用接口
- 支持消息格式转换和链式调用

#### ConversationAgent (`conversation_agent_langchain.py`)

- 使用LangChain的ChatPromptTemplate和StrOutputParser
- 支持对话历史管理
- 提供更灵活的消息处理

#### WorkflowGenerationAgent (`workflow_generation_agent_langchain.py`)

- 使用LangChain的链式处理
- 支持工作流模板和自定义生成
- 提供工作流验证和修复功能

## 使用方法

### 1. 配置LLM

```python
llm_config = {
    "provider": "openai",  # 支持 "openai", "azure", "anthropic"
    "model": "gpt-3.5-turbo",
    "api_key": "your-api-key-here",
    "temperature": 0.7,
    "max_tokens": 1000
}

# Azure配置示例
azure_config = {
    "provider": "azure",
    "model": "gpt-35-turbo",
    "api_key": "your-azure-api-key",
    "api_base": "https://your-resource.openai.azure.com/",
    "api_version": "2023-12-01-preview",
    "deployment_name": "your-deployment-name",
    "temperature": 0.7,
    "max_tokens": 1000
}

# Anthropic配置示例
anthropic_config = {
    "provider": "anthropic",
    "model": "claude-3-sonnet-20240229",
    "api_key": "your-anthropic-api-key",
    "temperature": 0.7,
    "max_tokens": 1000
}
```

### 2. 使用ConversationAgent

```python
from agents.conversation_agent_langchain import ConversationAgent

# 创建agent
agent = ConversationAgent(llm_config)

# 创建新对话
conversation_id = agent.create_conversation()

# 添加消息
response = agent.add_message(conversation_id, "你好，请介绍一下你自己。")

# 获取对话历史
history = agent.get_conversation(conversation_id)

# 删除对话
agent.delete_conversation(conversation_id)
```

### 3. 使用WorkflowGenerationAgent

```python
from agents.workflow_generation_agent_langchain import WorkflowGenerationAgent

# 创建agent
agent = WorkflowGenerationAgent(llm_config)

# 获取模板工作流
templates = agent.get_template_workflows()

# 基于模板生成工作流
template_name = "text_to_image"
parameters = {
    "text": "a beautiful sunset over mountains",
    "width": 512,
    "height": 512
}
result = agent.generate_from_template(template_name, parameters)

# 生成自定义工作流
user_request = "请生成一个文本到图像的工作流，使用Stable Diffusion模型"
result = agent.generate_workflow(user_request)
```

### 4. 使用LLM工具类

```python
from service.llm_tools_langchain import LLMTools

# 创建LLM工具实例
llm_tools = LLMTools()

# 获取可用模型
models = llm_tools.get_available_models()

# 验证LLM配置
is_valid = llm_tools.validate_llm_config(llm_config)

# 测试LLM连接
connection_result = llm_tools.test_llm_connection(llm_config)

# 生成响应
response = llm_tools.generate_response("你好，请用一句话介绍你自己。", llm_config)
```

## 测试

运行测试脚本验证功能：

```bash
cd backend
python test_langchain_agents.py
```

## 注意事项

1. **API密钥**: 请确保设置了正确的API密钥
2. **模型名称**: 使用正确的模型名称，不同提供商的模型名称可能不同
3. **错误处理**: 所有方法都包含错误处理，但建议添加额外的错误处理逻辑
4. **资源管理**: 对于长时间运行的应用，注意管理LLM连接和资源

## 迁移指南

如果您正在从旧版本迁移：

1. 更新依赖包
2. 替换导入语句：
   - `from agents.conversation_agent import ConversationAgent` → `from agents.conversation_agent_langchain import ConversationAgent`
   - `from agents.workflow_generation_agent import WorkflowGenerationAgent` → `from agents.workflow_generation_agent_langchain import WorkflowGenerationAgent`
   - `from service.llm_tools import LLMTools` → `from service.llm_tools_langchain import LLMTools`
3. 更新配置格式（如需要）
4. 测试功能是否正常

## 故障排除

### 常见问题

1. **导入错误**: 确保已安装所有依赖包
2. **API调用失败**: 检查API密钥和网络连接
3. **模型不可用**: 确认模型名称正确且有访问权限
4. **内存不足**: 减少max_tokens或使用更小的模型

### 调试

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 未来计划

1. 添加更多LLM提供商支持
2. 实现更复杂的工作流模板
3. 添加对话上下文管理
4. 优化性能和资源使用