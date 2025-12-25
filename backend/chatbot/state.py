import operator
from typing import Annotated, Literal, Sequence, List, Dict, Any, Union
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, AnyMessage
from langgraph.graph.message import add_messages


# 导入之前定义的 Pydantic 模型 (假设在 schema.py)
# from .schema import IntentResponse

class BaseState(BaseModel):
    # === 基础通信 ===
    messages: Annotated[Sequence[AnyMessage], add_messages] = Field(default_factory=list)

    user_input: str = ""

    # === 工作流上下文 ===
    current_workflow: Union[Dict[str, Any], str, None] = None

    workflow_source: Literal["uploaded", "text", "retrieved", "none"] = "none"

    # === 校验器状态 (Validator) ===
    missing_nodes: List[Dict[str, Any]] = Field(default_factory=list)
    download_suggestions: List[Dict[str, Any]] = Field(default_factory=list)
    validated_workflow: Union[Dict[str, Any], None] = None

    # === 意图与知识 (Intent & Search) ===

    intent_result: Union[Dict[str, Any], None] = None
    retrieved_knowledge: List[Dict[str, Any]] = Field(default_factory=list)

    # === 流程控制 ===
    next: str = "entry"
    need_human: bool = False

    # === 循环计数器 ===
    # 防止 Agent 陷入死循环 (如：搜索->分析->搜索->分析...)
    # 每次返回 {"iteration": 1} 会自动累加
    iteration: Annotated[int, operator.add] = 0

    error_logs: str = ""  # 前端传来的报错信息 (Traceback / UI Error)
    error_node_id: str = ""  # 报错红框节点的 ID

    route_decision: Literal["planner", "debugger", "Guidance", "chat"] = "planner"
