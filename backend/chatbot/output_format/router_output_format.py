from pydantic import BaseModel, Field
from typing import Literal


class RouteResult(BaseModel):
    destination: Literal["Planner", "Debugger", "Guidance", "Chat"] = Field(
        description="planner: 修改/创建/解释工作流; debugger: 修复报错/解决红节点; Guidance comfyui指南; chat: 纯闲聊(only comfyui)"
    )
    reasoning: str = Field(description="判断理由")
