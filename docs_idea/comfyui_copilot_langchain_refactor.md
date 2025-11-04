# ComfyUI-Copilot 后端 LangChain 和 LangGraph 重构指南

## 概述

本指南详细说明如何使用 LangChain 1.0 和 LangGraph 重构 ComfyUI-Copilot 项目的后端系统。重构将提供更好的抽象、可扩展性和维护性。

## 当前架构分析

### 现有组件

1. **Agent Factory** (`agent_factory.py`)
   - 使用 `openai-agents` 库创建代理
   - 支持多种模型和配置
   - 处理 API 密钥和基础 URL

2. **Workflow Rewrite Agent** (`workflow_rewrite_agent.py`)
   - 负责根据用户需求修改和优化 ComfyUI 工作流
   - 使用工具函数获取专家经验和操作工作流
   - 处理复杂工作流的拆解和重组

3. **Debug Agent** (`debug_agent.py`)
   - 分析和调试工作流错误
   - 使用多代理架构处理不同类型的错误
   - 运行工作流并返回结果

4. **工具和服务**
   - `workflow_rewrite_tools.py`: 工作流操作工具
   - `parameter_tools.py`: 参数处理工具
   - `link_agent_tools.py`: 连接处理工具
   - `mcp_client.py`: MCP 客户端

### 当前依赖

```
openai>=1.5.0
openai-agents>=0.3.0
fastmcp
sqlalchemy>=1.4.0,<2.0
python-dotenv>=0.19.0
requests>=2.25.0
aiohttp>=3.8.0
httpx>=0.24.0
modelscope>=1.28.0
urllib3>=1.26,<2.0
```

## 重构目标

1. **统一抽象层**: 使用 LangChain 提供统一的 LLM 抽象
2. **改进工作流管理**: 使用 LangGraph 管理复杂的多步骤工作流
3. **增强工具集成**: 利用 LangChain 的工具生态系统
4. **提高可扩展性**: 更容易添加新的 LLM 提供商和功能
5. **简化代码结构**: 减少样板代码，提高可读性

## 重构步骤

### 1. 更新依赖

首先更新 `requirements.txt` 文件，替换现有依赖：

```txt
# LangChain 生态系统
langchain>=1.0.0
langchain-community>=0.3.0
langchain-core>=0.3.0
langchain-openai>=0.2.0
langchain-anthropic>=0.3.0
langgraph>=0.2.0

# 现有依赖
sqlalchemy>=1.4.0,<2.0
python-dotenv>=0.19.0
requests>=2.25.0
aiohttp>=3.8.0
httpx>=0.24.0
modelscope>=1.28.0
urllib3>=1.26,<2.0

# 开发和测试
pytest>=6.0.0
pytest-asyncio>=0.18.0
fastmcp
```

### 2. 创建 LangChain 适配器

创建 `backend/service/langchain_adapter.py` 文件，提供 LangChain 和现有系统的桥梁：

```python
"""
LangChain 适配器，提供与现有系统的兼容接口
"""

import os
from typing import Dict, Any, List, Optional, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import AzureChatOpenAI
from langchain_core.tools import BaseTool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from ..utils.globals import LLM_DEFAULT_BASE_URL, LMSTUDIO_DEFAULT_BASE_URL, get_comfyui_copilot_api_key, is_lmstudio_url
from ..utils.request_context import get_config, get_session_id


class LangChainAdapter:
    """LangChain 适配器类，提供与现有系统的兼容接口"""
    
    def __init__(self):
        self.memory = MemorySaver()
        self.models_cache = {}
    
    def create_llm(self, config: Optional[Dict[str, Any]] = None) -> Runnable:
        """创建 LangChain LLM 实例"""
        if config is None:
            config = get_config() or {}
        
        # 获取模型配置
        model_name = config.get("model_select", "gpt-3.5-turbo")
        provider = self._detect_provider(model_name)
        
        # 获取 API 配置
        api_key = config.get("openai_api_key") or get_comfyui_copilot_api_key()
        base_url = config.get("openai_base_url") or LLM_DEFAULT_BASE_URL
        
        # 检查是否是 LMStudio
        is_lmstudio = is_lmstudio_url(base_url)
        if is_lmstudio and not api_key:
            api_key = "lmstudio-local"
        
        # 创建模型实例
        if provider == "openai":
            return ChatOpenAI(
                model=model_name,
                api_key=api_key,
                base_url=base_url,
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 8192),
            )
        elif provider == "anthropic":
            return ChatAnthropic(
                model=model_name,
                api_key=api_key,
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 8192),
            )
        elif provider == "azure":
            return AzureChatOpenAI(
                azure_deployment=config.get("deployment_name", model_name),
                api_key=api_key,
                azure_endpoint=base_url,
                api_version=config.get("api_version", "2023-12-01-preview"),
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 8192),
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _detect_provider(self, model_name: str) -> str:
        """根据模型名称检测提供商"""
        if model_name.startswith("gpt-") or model_name.startswith("o1-"):
            return "openai"
        elif model_name.startswith("claude-"):
            return "anthropic"
        elif "azure" in model_name.lower():
            return "azure"
        else:
            return "openai"  # 默认
    
    def create_agent_executor(
        self, 
        tools: List[BaseTool], 
        system_prompt: str,
        config: Optional[Dict[str, Any]] = None
    ) -> AgentExecutor:
        """创建代理执行器，兼容现有系统"""
        llm = self.create_llm(config)
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        # 创建代理
        agent = create_openai_tools_agent(llm, tools, prompt)
        
        # 创建执行器
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            memory=self.memory,
            handle_parsing_errors=True,
        )
        
        return executor
    
    def create_langgraph_agent(
        self, 
        tools: List[BaseTool], 
        system_prompt: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Runnable:
        """创建 LangGraph 代理，用于复杂工作流"""
        llm = self.create_llm(config)
        
        # 创建 LangGraph 代理
        agent = create_react_agent(
            llm,
            tools,
            state_modifier=system_prompt,
            checkpointer=self.memory
        )
        
        return agent
    
    def convert_messages(self, messages: List[Dict[str, Any]]) -> List:
        """转换消息格式以兼容 LangChain"""
        langchain_messages = []
        
        for msg in messages:
            if msg.get("role") == "user":
                langchain_messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                langchain_messages.append(AIMessage(content=msg.get("content", "")))
            elif msg.get("role") == "system":
                langchain_messages.append(SystemMessage(content=msg.get("content", "")))
        
        return langchain_messages
    
    def run_agent(
        self, 
        agent: Union[AgentExecutor, Runnable], 
        input_text: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """运行代理并返回结果"""
        try:
            # 准备输入
            if isinstance(agent, AgentExecutor):
                # 传统代理执行器
                result = agent.invoke({"input": input_text})
                return {
                    "success": True,
                    "response": result.get("output", ""),
                    "intermediate_steps": result.get("intermediate_steps", [])
                }
            else:
                # LangGraph 代理
                config = {"configurable": {"thread_id": session_id or "default"}}
                result = agent.invoke({"messages": [HumanMessage(content=input_text)]}, config)
                
                # 提取最后一条消息
                messages = result.get("messages", [])
                last_message = messages[-1] if messages else None
                
                return {
                    "success": True,
                    "response": last_message.content if last_message else "",
                    "messages": [msg.content for msg in messages]
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

### 3. 重构 Agent Factory

更新 `backend/agent_factory_langchain.py` 文件：

```python
"""
使用 LangChain 重构的 Agent Factory
"""

from typing import Dict, Any, Optional
from .service.langchain_adapter import LangChainAdapter
from .utils.globals import WORKFLOW_MODEL_NAME
from .utils.request_context import get_config


# 全局适配器实例
_adapter = LangChainAdapter()


def create_agent(**kwargs) -> Any:
    """创建代理，兼容现有接口"""
    config = kwargs.pop("config", {})
    name = kwargs.pop("name", "Agent")
    instructions = kwargs.pop("instructions", "")
    tools = kwargs.pop("tools", [])
    handoff_description = kwargs.pop("handoff_description", "")
    
    # 使用 LangChain 适配器创建代理
    if "langgraph" in kwargs and kwargs["langgraph"]:
        # 创建 LangGraph 代理
        agent = _adapter.create_langgraph_agent(
            tools=tools,
            system_prompt=instructions,
            config=config
        )
    else:
        # 创建传统代理执行器
        agent = _adapter.create_agent_executor(
            tools=tools,
            system_prompt=instructions,
            config=config
        )
    
    return agent


def get_adapter() -> LangChainAdapter:
    """获取 LangChain 适配器实例"""
    return _adapter


def create_workflow_rewrite_agent():
    """创建工作流重写代理"""
    from .service.workflow_rewrite_agent_langchain import create_workflow_rewrite_agent
    return create_workflow_rewrite_agent()


def create_debug_agent():
    """创建调试代理"""
    from .service.debug_agent_langchain import create_debug_agent
    return create_debug_agent()


def create_link_agent():
    """创建连接代理"""
    from .service.link_agent_langchain import create_link_agent
    return create_link_agent()


def create_parameter_agent():
    """创建参数代理"""
    from .service.parameter_agent_langchain import create_parameter_agent
    return create_parameter_agent()
```

### 4. 重构工作流重写代理

创建 `backend/service/workflow_rewrite_agent_langchain.py` 文件：

```python
"""
使用 LangChain 重写的工作流重写代理
"""

import json
import uuid
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough

from ..agent_factory_langchain import get_adapter
from ..utils.key_utils import workflow_config_adapt
from ..utils.globals import WORKFLOW_MODEL_NAME, get_language
from ..utils.request_context import get_config, get_session_id
from ..dao.expert_table import list_rewrite_experts_short, get_rewrite_expert_by_name_list
from .workflow_rewrite_tools import *


@tool
def get_rewrite_expert_by_name(name_list: List[str]) -> str:
    """根据经验名称来获取工作流改写专家经验"""
    result = get_rewrite_expert_by_name_list(name_list)
    temp = json.dumps(result, ensure_ascii=False)
    log.info(f"get_rewrite_expert_by_name, name_list: {name_list}, result: {temp}")
    get_rewrite_context().rewrite_expert += temp
    return temp


def get_rewrite_export_schema() -> dict:
    """获取工作流改写专家经验schema"""
    return list_rewrite_experts_short()


def create_workflow_rewrite_agent():
    """创建workflow_rewrite_agent实例"""
    adapter = get_adapter()
    
    language = get_language()
    session_id = get_session_id() or "unknown_session"
    config = get_config()
    config = workflow_config_adapt(config)
    
    # 系统提示
    system_prompt = f"""
    你是专业的ComfyUI工作流改写代理，擅长根据用户的具体需求对现有工作流进行智能修改和优化。
    如果在history_messages里有用户的历史对话，请根据历史对话中的语言来决定返回的语言。否则使用{language}作为返回的语言。

    ## 主要处理场景
    {json.dumps(get_rewrite_export_schema())}

    你可以根据用户的需求，从上面的专家经验中选择一个或多个经验，并结合经验内容进行工作流改写。
    
    ## 复杂工作流处理原则
    复杂工作流实际上是多个简单的功能性工作流的组合。例如：文生图→抠图取主体→图生图生成背景。
    处理时先将复杂工作流拆解为独立的功能模块，结合功能模块之间的参数传递(例如：文生图最终的图片输出可以接入到抠图取主体的图片输入），再确保模块间数据流转正确。
    
    ## 操作原则
    - **保持兼容性**：确保修改后的工作流与现有comfyui节点兼容
    - **优化连接**：根据节点之间对应的传参类型和专家经验参考，正确设置节点间的输入输出连接
    - **连线完整性**：修改工作流时必须确保所有节点的连线关系完整，不遗漏任何必要的输入输出连接，不能有额外的连线和节点
      * 检查每个节点的必需输入是否已连接
      * 对于未连接的必需输入，优先寻找类型匹配的现有节点输出进行连接
      * 如果找不到合适的现有输出，则创建适当的输入节点（如常量节点、加载节点等）
      * 确保连接的参数类型完全匹配，避免类型不兼容的连接
    - **连线检查**：在添加、删除或修改节点时，务必检查所有相关的输入和输出连接是否正确配置
    - **连接关系维护**：修改节点时必须保持原有的连接逻辑，确保数据流向正确
    - **类型严格匹配**：在进行任何连线操作时，必须严格验证输入输出类型匹配
      * 在修改连线前，先使用get_node_info()获取节点的完整输入输出规格信息
      * 仔细检查源节点的输出类型(output_type)与目标节点的输入类型(input_type)
      * 如果类型不匹配，寻找正确的源节点或添加类型转换节点
    - **性能考虑**：避免不必要的重复节点，优化工作流执行效率
    - **用户友好**：保持工作流结构清晰，便于用户理解和后续修改
    - **错误处理**：在修改过程中检查潜在的配置错误，提供修正建议
    
    **Tool Usage Guidelines:**
        - get_current_workflow(): Get current workflow from checkpoint or session
        - remove_node(): Use for incompatible or problematic nodes
        - update_workflow(): Use to save your changes (ALWAYS call this after you have made changes), you MUST pass argument `workflow_data` containing the FULL workflow JSON (as a JSON object or a JSON string). Never call `update_workflow` without `workflow_data`.
        - get_node_info(): Get detailed node information and verify input/output types before connecting

    ## 响应格式
    返回api格式的workflow
    
    # ComfyUI 背景知识（Background Knowledge for ComfyUI）：
    # - ComfyUI 是一个基于节点的图形化工作流系统，广泛用于 AI 图像生成、模型推理等场景。每个节点代表一个操作（如加载模型、生成图像、处理参数等），节点之间通过输入输出端口（socket）进行数据流转。
    # - 节点类型丰富，包括模型加载、图像处理、参数设置、常量输入、类型转换等。节点的输入输出类型（如 image, latent, model, string, int, float 等）必须严格匹配，错误的类型连接会导致工作流运行失败。
    # - 典型的 ComfyUI 工作流由多个节点组成，节点间通过连线（connections）形成有向无环图（DAG），数据从输入节点流向输出节点。每个节点的必需输入（required input）必须有有效连接，否则会报错。
    # - ComfyUI 支持多种模型系统（如 SDXL, Flux, wan2.1, wan2.2,Qwen_image），每种系统有其特定的模型文件和组件，模型节点的参数需与本地模型文件严格匹配。
    # - 常见问题包括：节点未连接、输入输出类型不匹配、缺少必需参数、模型文件缺失、节点结构不兼容等。改写工作流时需特别注意这些结构性和参数性问题。
    # - 工作流的每次修改都应保证整体结构的连贯性和可运行性，避免引入新的结构性错误。

    始终以用户的实际需求为导向，提供专业、准确、高效的工作流改写服务。
    """
    
    # 工具列表
    tools = [
        get_rewrite_expert_by_name,
        get_current_workflow,
        get_node_info,
        update_workflow,
        remove_node
    ]
    
    # 创建 LangGraph 代理
    agent = adapter.create_langgraph_agent(
        tools=tools,
        system_prompt=system_prompt,
        config={
            "max_tokens": 8192,
            **config
        }
    )
    
    return agent


async def rewrite_workflow(user_request: str) -> Dict[str, Any]:
    """重写工作流的主要入口点"""
    try:
        agent = create_workflow_rewrite_agent()
        session_id = get_session_id()
        
        # 运行代理
        result = adapter.run_agent(agent, user_request, session_id)
        
        if result["success"]:
            return {
                "success": True,
                "response": result["response"],
                "workflow": result.get("workflow", None)
            }
        else:
            return {
                "success": False,
                "error": result["error"]
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to rewrite workflow: {str(e)}"
        }
```

### 5. 重构调试代理

创建 `backend/service/debug_agent_langchain.py` 文件：

```python
"""
使用 LangChain 重写的调试代理
"""

import json
import uuid
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

from ..agent_factory_langchain import get_adapter
from ..utils.key_utils import workflow_config_adapt
from ..utils.globals import WORKFLOW_MODEL_NAME, get_language
from ..utils.request_context import get_config, get_session_id
from ..service.workflow_rewrite_tools import *
from ..service.parameter_tools import *
from ..service.link_agent_tools import *
from ..dao.workflow_table import get_workflow_data, save_workflow_data
from ..utils.logger import log


# 定义状态类型
class DebugState(TypedDict):
    """调试状态"""
    workflow_data: Dict[str, Any]
    error_data: str
    error_analysis: Dict[str, Any]
    fix_result: Dict[str, Any]
    messages: List[Dict[str, Any]]


@tool
async def run_workflow() -> str:
    """验证当前session的工作流并返回结果"""
    try:
        session_id = get_session_id()
        if not session_id:
            return json.dumps({"error": "No session_id found in context"})
            
        workflow_data = get_workflow_data(session_id)
        if not workflow_data:
            return json.dumps({"error": "No workflow data found for this session"})
        
        log.info(f"Run workflow for session {session_id}")
        
        # 使用 ComfyGateway 调用 server.py 的 post_prompt 逻辑
        from ..utils.comfy_gateway import ComfyGateway
        
        # 简化方法：直接使用 requests 同步调用
        gateway = ComfyGateway()

        # 准备请求数据格式（与server.py post_prompt接口一致）
        request_data = {
            "prompt": workflow_data,
            "client_id": f"debug_agent_{session_id}"
        }
        
        result = await gateway.run_prompt(request_data)
        log.info(result)
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to run workflow: {str(e)}"})


@tool
def analyze_error_type(error_data: str) -> str:
    """分析错误类型，判断应该使用哪个agent，输入可以是JSON字符串或普通文本"""
    try:
        error_analysis = {
            "error_type": "unknown",
            "recommended_agent": "workflow_bugfix_default_agent",
            "error_details": [],
            "affected_nodes": []
        }
        
        # 将输入转换为字符串进行关键词匹配
        error_text = str(error_data).lower()
        
        # 检查成功状态
        if any(keyword in error_text for keyword in [
            '"success": true', "'success': true", "validation successful", "workflow validation successful"
        ]):
            error_analysis["error_type"] = "no_error"
            error_analysis["recommended_agent"] = "none"
            error_analysis["error_details"] = [{"message": "Workflow validation successful"}]
            return json.dumps(error_analysis)
        
        # 统计不同类型的错误
        parameter_errors = 0
        connection_errors = 0
        other_errors = 0
        
        # 提取节点ID（简单的正则匹配）
        import re
        node_id_matches = re.findall(r'"(\d+)":', error_text) or re.findall(r"'(\d+)':", error_text)
        if node_id_matches:
            error_analysis["affected_nodes"] = list(set(node_id_matches))
        
        # 连接相关错误的关键词（优先判断，因为结构性错误更重要）
        connection_keywords = [
            "connection", "input connection", "required input", "missing input",
            "not connected", "no connection", "link", "output", "socket",
            "missing_input", "invalid_connection", "connection_error"
        ]
        
        # 参数相关错误的关键词
        parameter_keywords = [
            "value not in list", "invalid value", "not found in list",
            "parameter value", "invalid parameter", "model not found", 
            "invalid image file", "value_not_in_list", "invalid_input"
        ]
        
        # 计算错误类型出现次数
        for keyword in connection_keywords:
            if keyword in error_text:
                connection_errors += error_text.count(keyword)
        
        for keyword in parameter_keywords:
            if keyword in error_text:
                parameter_errors += error_text.count(keyword)
        
        # 如果没有匹配到特定错误类型，检查是否有一般性错误指示
        if connection_errors == 0 and parameter_errors == 0:
            general_error_keywords = ["error", "failed", "exception", "invalid"]
            for keyword in general_error_keywords:
                if keyword in error_text:
                    other_errors += 1
                    break
        
        # 根据错误类型决定使用哪个agent
        if connection_errors > 0 and parameter_errors == 0 and other_errors == 0:
            # 纯连接错误，使用专门的link_agent
            error_analysis["error_type"] = "connection_error"
            error_analysis["recommended_agent"] = "link_agent"
        elif connection_errors > 0:
            # 混合错误，优先处理连接问题
            error_analysis["error_type"] = "mixed_connection_error"
            error_analysis["recommended_agent"] = "link_agent"
        elif parameter_errors > 0:
            error_analysis["error_type"] = "parameter_error"
            error_analysis["recommended_agent"] = "parameter_agent"
        elif other_errors > 0:
            error_analysis["error_type"] = "structural_error"
            error_analysis["recommended_agent"] = "workflow_bugfix_default_agent"
        else:
            # 没有检测到明确的错误模式，使用默认agent
            error_analysis["error_type"] = "unknown"
            error_analysis["recommended_agent"] = "workflow_bugfix_default_agent"
        
        # 添加错误详情（基于文本内容）
        if connection_errors > 0:
            error_analysis["error_details"].append({
                "error_type": "connection_error",
                "message": f"Detected {connection_errors} connection-related issues",
                "details": "Connection or input/output related errors found"
            })
        
        if parameter_errors > 0:
            error_analysis["error_details"].append({
                "error_type": "parameter_error", 
                "message": f"Detected {parameter_errors} parameter-related issues",
                "details": "Parameter value or configuration related errors found"
            })
        
        return json.dumps(error_analysis)
        
    except Exception as e:
        return json.dumps({
            "error_type": "analysis_failed",
            "recommended_agent": "workflow_bugfix_default_agent",
            "error": f"Failed to analyze error: {str(e)}"
        })


@tool
def save_current_workflow(workflow_data: str) -> str:
    """保存当前工作流数据到数据库，workflow_data应为JSON字符串"""
    try:
        session_id = get_session_id()
        if not session_id:
            return json.dumps({"error": "No session_id found in context"})
            
        # 解析JSON字符串
        workflow_dict = json.loads(workflow_data) if isinstance(workflow_data, str) else workflow_data
        
        version_id = save_workflow_data(
            session_id, 
            workflow_dict, 
            attributes={"action": "debug_save", "description": "Workflow saved during debugging"}
        )
        return json.dumps({
            "success": True,
            "version_id": version_id,
            "message": f"Workflow saved with version ID: {version_id}"
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to save workflow: {str(e)}"})


def create_debug_workflow_graph():
    """创建调试工作流图"""
    adapter = get_adapter()
    
    # 创建节点函数
    def analyze_errors(state: DebugState) -> DebugState:
        """分析错误"""
        error_analysis = json.loads(analyze_error_type.invoke({"error_data": state["error_data"]}))
        state["error_analysis"] = error_analysis
        return state
    
    def fix_connection_errors(state: DebugState) -> DebugState:
        """修复连接错误"""
        if state["error_analysis"]["recommended_agent"] != "link_agent":
            state["fix_result"] = {"success": True, "message": "No connection errors to fix"}
            return state
        
        # 创建连接修复代理
        from .link_agent_langchain import create_link_agent
        link_agent = create_link_agent()
        
        # 运行代理
        result = adapter.run_agent(
            link_agent, 
            f"Please fix the connection errors in the workflow: {state['error_data']}",
            get_session_id()
        )
        
        state["fix_result"] = result
        return state
    
    def fix_parameter_errors(state: DebugState) -> DebugState:
        """修复参数错误"""
        if state["error_analysis"]["recommended_agent"] != "parameter_agent":
            state["fix_result"] = {"success": True, "message": "No parameter errors to fix"}
            return state
        
        # 创建参数修复代理
        from .parameter_agent_langchain import create_parameter_agent
        parameter_agent = create_parameter_agent()
        
        # 运行代理
        result = adapter.run_agent(
            parameter_agent, 
            f"Please fix the parameter errors in the workflow: {state['error_data']}",
            get_session_id()
        )
        
        state["fix_result"] = result
        return state
    
    def fix_general_errors(state: DebugState) -> DebugState:
        """修复一般错误"""
        if state["error_analysis"]["recommended_agent"] != "workflow_bugfix_default_agent":
            state["fix_result"] = {"success": True, "message": "No general errors to fix"}
            return state
        
        # 创建一般错误修复代理
        from .workflow_bugfix_agent_langchain import create_workflow_bugfix_agent
        bugfix_agent = create_workflow_bugfix_agent()
        
        # 运行代理
        result = adapter.run_agent(
            bugfix_agent, 
            f"Please fix the errors in the workflow: {state['error_data']}",
            get_session_id()
        )
        
        state["fix_result"] = result
        return state
    
    def decide_next_step(state: DebugState) -> str:
        """决定下一步操作"""
        if state["error_analysis"]["error_type"] == "no_error":
            return "no_errors"
        
        recommended_agent = state["error_analysis"]["recommended_agent"]
        if recommended_agent == "link_agent":
            return "fix_connection"
        elif recommended_agent == "parameter_agent":
            return "fix_parameter"
        else:
            return "fix_general"
    
    # 创建工作流图
    workflow = StateGraph(DebugState)
    
    # 添加节点
    workflow.add_node("analyze_errors", analyze_errors)
    workflow.add_node("fix_connection", fix_connection_errors)
    workflow.add_node("fix_parameter", fix_parameter_errors)
    workflow.add_node("fix_general", fix_general_errors)
    
    # 设置入口点
    workflow.set_entry_point("analyze_errors")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "analyze_errors",
        decide_next_step,
        {
            "no_errors": END,
            "fix_connection": "fix_connection",
            "fix_parameter": "fix_parameter",
            "fix_general": "fix_general"
        }
    )
    
    # 添加结束边
    workflow.add_edge("fix_connection", END)
    workflow.add_edge("fix_parameter", END)
    workflow.add_edge("fix_general", END)
    
    # 编译工作流
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


def create_debug_agent():
    """创建调试代理"""
    adapter = get_adapter()
    
    # 系统提示
    system_prompt = """
    你是ComfyUI工作流调试专家，专门分析和修复工作流中的错误。
    
    你的主要任务是：
    1. 分析工作流运行结果，识别错误类型
    2. 根据错误类型选择合适的修复策略
    3. 协调专门的代理修复错误
    4. 验证修复结果
    
    可用的工具：
    - run_workflow: 运行当前工作流并获取结果
    - analyze_error_type: 分析错误类型并推荐修复代理
    - save_current_workflow: 保存当前工作流状态
    
    请始终使用工具来完成任务，不要直接修改工作流。
    """
    
    # 工具列表
    tools = [
        run_workflow,
        analyze_error_type,
        save_current_workflow
    ]
    
    # 创建 LangGraph 代理
    agent = adapter.create_langgraph_agent(
        tools=tools,
        system_prompt=system_prompt,
        config=get_config()
    )
    
    return agent


async def debug_workflow_errors(workflow_data: Dict[str, Any]):
    """
    分析和调试工作流错误，使用 LangGraph 管理调试流程
    """
    try:
        # 创建调试工作流图
        debug_app = create_debug_workflow_graph()
        
        # 准备初始状态
        session_id = get_session_id()
        initial_state = {
            "workflow_data": workflow_data,
            "error_data": "",
            "error_analysis": {},
            "fix_result": {},
            "messages": []
        }
        
        # 运行工作流
        config = {"configurable": {"thread_id": session_id or "default"}}
        result = debug_app.invoke(initial_state, config)
        
        return {
            "success": True,
            "error_analysis": result.get("error_analysis", {}),
            "fix_result": result.get("fix_result", {})
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to debug workflow: {str(e)}"
        }
```

### 6. 创建专门的代理

创建 `backend/service/link_agent_langchain.py` 和 `backend/service/parameter_agent_langchain.py` 文件：

```python
# backend/service/link_agent_langchain.py
"""
使用 LangChain 重写的连接代理
"""

import json
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

from ..agent_factory_langchain import get_adapter
from ..utils.request_context import get_config, get_session_id
from .workflow_rewrite_tools import *
from .link_agent_tools import *


@tool
def fix_node_connections(node_id: str, target_connections: List[Dict[str, Any]]) -> str:
    """修复节点连接"""
    try:
        # 获取当前工作流
        workflow = get_current_workflow()
        
        # 获取节点信息
        node_info = get_node_info(node_id)
        
        # 修复连接
        # ... 实现连接修复逻辑 ...
        
        return json.dumps({
            "success": True,
            "message": f"Fixed connections for node {node_id}",
            "connections": target_connections
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


def create_link_agent():
    """创建连接代理"""
    adapter = get_adapter()
    
    # 系统提示
    system_prompt = """
    你是ComfyUI工作流连接专家，专门修复工作流中的连接错误。
    
    你的主要任务是：
    1. 分析工作流中的连接问题
    2. 识别缺失或错误的连接
    3. 修复节点间的连接关系
    4. 确保连接类型匹配
    
    连接原则：
    - 确保所有必需输入都有连接
    - 验证输入输出类型匹配
    - 保持工作流结构完整
    - 避免循环依赖
    
    可用的工具：
    - get_current_workflow: 获取当前工作流
    - get_node_info: 获取节点详细信息
    - fix_node_connections: 修复节点连接
    - update_workflow: 更新工作流
    
    请始终使用工具来完成任务，确保连接正确性。
    """
    
    # 工具列表
    tools = [
        get_current_workflow,
        get_node_info,
        fix_node_connections,
        update_workflow
    ]
    
    # 创建 LangGraph 代理
    agent = adapter.create_langgraph_agent(
        tools=tools,
        system_prompt=system_prompt,
        config=get_config()
    )
    
    return agent


# backend/service/parameter_agent_langchain.py
"""
使用 LangChain 重写的参数代理
"""

import json
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

from ..agent_factory_langchain import get_adapter
from ..utils.request_context import get_config, get_session_id
from .workflow_rewrite_tools import *
from .parameter_tools import *


@tool
def fix_node_parameters(node_id: str, parameters: Dict[str, Any]) -> str:
    """修复节点参数"""
    try:
        # 获取当前工作流
        workflow = get_current_workflow()
        
        # 获取节点信息
        node_info = get_node_info(node_id)
        
        # 修复参数
        # ... 实现参数修复逻辑 ...
        
        return json.dumps({
            "success": True,
            "message": f"Fixed parameters for node {node_id}",
            "parameters": parameters
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


def create_parameter_agent():
    """创建参数代理"""
    adapter = get_adapter()
    
    # 系统提示
    system_prompt = """
    你是ComfyUI工作流参数专家，专门修复工作流中的参数错误。
    
    你的主要任务是：
    1. 分析工作流中的参数问题
    2. 识别无效或缺失的参数值
    3. 修复节点参数配置
    4. 确保参数值在有效范围内
    
    参数原则：
    - 验证参数值的有效性
    - 确保参数类型正确
    - 使用默认值替代无效值
    - 保持参数一致性
    
    可用的工具：
    - get_current_workflow: 获取当前工作流
    - get_node_info: 获取节点详细信息
    - fix_node_parameters: 修复节点参数
    - update_workflow: 更新工作流
    
    请始终使用工具来完成任务，确保参数正确性。
    """
    
    # 工具列表
    tools = [
        get_current_workflow,
        get_node_info,
        fix_node_parameters,
        update_workflow
    ]
    
    # 创建 LangGraph 代理
    agent = adapter.create_langgraph_agent(
        tools=tools,
        system_prompt=system_prompt,
        config=get_config()
    )
    
    return agent
```

### 7. 更新控制器

更新 `backend/controller` 中的 API 控制器，使其使用新的 LangChain 代理：

```python
# backend/controller/workflow_api_langchain.py
"""
使用 LangChain 重写的工作流 API 控制器
"""

import json
from typing import Dict, Any
from fastapi import HTTPException
from ..service.workflow_rewrite_agent_langchain import rewrite_workflow
from ..service.debug_agent_langchain import debug_workflow_errors
from ..utils.request_context import set_session_context


async def rewrite_workflow_api(request: Dict[str, Any]) -> Dict[str, Any]:
    """工作流重写 API"""
    try:
        # 设置会话上下文
        set_session_context(request.get("session_id"), request.get("config"))
        
        # 获取用户请求
        user_request = request.get("user_request", "")
        if not user_request:
            raise HTTPException(status_code=400, detail="user_request is required")
        
        # 重写工作流
        result = await rewrite_workflow(user_request)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def debug_workflow_api(request: Dict[str, Any]) -> Dict[str, Any]:
    """工作流调试 API"""
    try:
        # 设置会话上下文
        set_session_context(request.get("session_id"), request.get("config"))
        
        # 获取工作流数据
        workflow_data = request.get("workflow_data")
        if not workflow_data:
            raise HTTPException(status_code=400, detail="workflow_data is required")
        
        # 调试工作流
        result = await debug_workflow_errors(workflow_data)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 8. 创建迁移脚本

创建 `scripts/migrate_to_langchain.py` 脚本，帮助迁移现有代码：

```python
"""
迁移脚本：将现有代码迁移到 LangChain
"""

import os
import re
import shutil
from pathlib import Path


def backup_original_files():
    """备份原始文件"""
    backend_dir = Path("backend")
    backup_dir = Path("backend_backup")
    
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    
    shutil.copytree(backend_dir, backup_dir)
    print(f"原始文件已备份到 {backup_dir}")


def update_imports():
    """更新导入语句"""
    files_to_update = [
        "backend/controller/workflow_api.py",
        "backend/controller/conversation_api.py",
        "backend/controller/llm_api.py"
    ]
    
    for file_path in files_to_update:
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r') as f:
            content = f.read()
        
        # 替换导入语句
        content = re.sub(
            r'from \.\.agent_factory import',
            'from ..agent_factory_langchain import',
            content
        )
        
        content = re.sub(
            r'from \.service\.workflow_rewrite_agent import',
            'from ..service.workflow_rewrite_agent_langchain import',
            content
        )
        
        content = re.sub(
            r'from \.service\.debug_agent import',
            'from ..service.debug_agent_langchain import',
            content
        )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"已更新 {file_path}")


def main():
    """主函数"""
    print("开始迁移到 LangChain...")
    
    # 备份原始文件
    backup_original_files()
    
    # 更新导入语句
    update_imports()
    
    print("迁移完成！")
    print("请检查更新后的文件，并根据需要进行调整。")


if __name__ == "__main__":
    main()
```

### 9. 创建测试脚本

创建 `tests/test_langchain_agents.py` 测试脚本：

```python
"""
测试 LangChain 代理
"""

import pytest
import asyncio
from backend.service.langchain_adapter import LangChainAdapter
from backend.service.workflow_rewrite_agent_langchain import create_workflow_rewrite_agent
from backend.service.debug_agent_langchain import create_debug_agent


class TestLangChainAdapter:
    """测试 LangChain 适配器"""
    
    def test_create_llm(self):
        """测试创建 LLM"""
        adapter = LangChainAdapter()
        
        config = {
            "model_select": "gpt-3.5-turbo",
            "openai_api_key": "test-key",
            "temperature": 0.7
        }
        
        llm = adapter.create_llm(config)
        assert llm is not None
    
    def test_convert_messages(self):
        """测试消息格式转换"""
        adapter = LangChainAdapter()
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        
        langchain_messages = adapter.convert_messages(messages)
        assert len(langchain_messages) == 2


class TestWorkflowRewriteAgent:
    """测试工作流重写代理"""
    
    def test_create_agent(self):
        """测试创建代理"""
        agent = create_workflow_rewrite_agent()
        assert agent is not None
    
    @pytest.mark.asyncio
    async def test_rewrite_workflow(self):
        """测试重写工作流"""
        from backend.service.workflow_rewrite_agent_langchain import rewrite_workflow
        
        result = await rewrite_workflow("Add a text to image node")
        assert "success" in result


class TestDebugAgent:
    """测试调试代理"""
    
    def test_create_agent(self):
        """测试创建代理"""
        agent = create_debug_agent()
        assert agent is not None
    
    @pytest.mark.asyncio
    async def test_debug_workflow(self):
        """测试调试工作流"""
        from backend.service.debug_agent_langchain import debug_workflow_errors
        
        workflow_data = {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {}
            }
        }
        
        result = await debug_workflow_errors(workflow_data)
        assert "success" in result


if __name__ == "__main__":
    pytest.main([__file__])
```

### 10. 创建文档

创建 `docs/LANGCHAIN_MIGRATION.md` 文档：

```markdown
# LangChain 迁移指南

## 概述

本文档描述了如何将 ComfyUI-Copilot 项目从 `openai-agents` 迁移到 `LangChain` 和 `LangGraph`。

## 迁移原因

1. **更好的抽象**: LangChain 提供了更丰富的 LLM 抽象和工具集成
2. **更强的工作流管理**: LangGraph 提供了强大的状态管理和工作流编排能力
3. **更广泛的社区支持**: LangChain 有更活跃的社区和更丰富的生态系统
4. **更好的可扩展性**: 更容易添加新的 LLM 提供商和功能

## 主要变化

### 1. 依赖更新

```diff
- openai-agents>=0.3.0
+ langchain>=1.0.0
+ langchain-community>=0.3.0
+ langchain-core>=0.3.0
+ langchain-openai>=0.2.0
+ langchain-anthropic>=0.3.0
+ langgraph>=0.2.0
```

### 2. 代理创建

```diff
- from agents.agent import Agent
- from agents.tool import function_tool
- from ..agent_factory import create_agent

+ from langchain_core.tools import tool
+ from ..agent_factory_langchain import get_adapter
```

### 3. 工具定义

```diff
- @function_tool
- def my_tool(param: str) -> str:
-     """工具描述"""
-     return result

+ @tool
+ def my_tool(param: str) -> str:
+     """工具描述"""
+     return result
```

### 4. 代理执行

```diff
- agent = create_agent(name="My Agent", tools=[my_tool])
- result = await agent.run("用户输入")

+ adapter = get_adapter()
+ agent = adapter.create_langgraph_agent(
+     tools=[my_tool],
+     system_prompt="系统提示"
+ )
+ result = adapter.run_agent(agent, "用户输入", session_id)
```

## 迁移步骤

1. **更新依赖**: 更新 `requirements.txt`
2. **创建适配器**: 实现 `LangChainAdapter` 类
3. **重构代理**: 重写现有代理以使用 LangChain
4. **更新控制器**: 更新 API 控制器
5. **运行测试**: 确保功能正常
6. **部署**: 部署更新后的代码

## 注意事项

1. **兼容性**: 确保新实现与现有 API 兼容
2. **性能**: 监控性能变化，必要时进行优化
3. **错误处理**: 确保错误处理逻辑完整
4. **日志**: 保持日志记录的一致性

## 故障排除

### 常见问题

1. **导入错误**: 检查依赖是否正确安装
2. **API 调用失败**: 验证 API 密钥和端点
3. **工具执行失败**: 检查工具函数的输入输出格式
4. **性能问题**: 考虑使用缓存和批处理

### 调试技巧

1. 启用详细日志
2. 使用 LangChain 的调试工具
3. 检查中间结果
4. 验证状态转换
```

## 实施计划

### 阶段 1: 准备工作 (1-2 天)

1. 创建开发分支
2. 更新依赖
3. 创建 LangChain 适配器
4. 设置测试环境

### 阶段 2: 核心组件重构 (3-5 天)

1. 重构 Agent Factory
2. 重构工作流重写代理
3. 重构调试代理
4. 创建专门的代理

### 阶段 3: 集成和测试 (2-3 天)

1. 更新控制器
2. 集成测试
3. 性能测试
4. 修复问题

### 阶段 4: 部署和文档 (1-2 天)

1. 代码审查
2. 部署到测试环境
3. 用户验收测试
4. 更新文档

## 总结

使用 LangChain 和 LangGraph 重构 ComfyUI-Copilot 后端将带来以下好处：

1. **更好的代码组织**: 更清晰的模块结构和职责分离
2. **更强的扩展性**: 更容易添加新功能和 LLM 提供商
3. **更好的工作流管理**: 使用 LangGraph 管理复杂的多步骤流程
4. **更丰富的工具集成**: 利用 LangChain 的工具生态系统
5. **更好的调试能力**: 更强大的错误分析和修复能力

重构完成后，系统将更加健壮、可维护和可扩展，为未来的功能开发奠定坚实基础。