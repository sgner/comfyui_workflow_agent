from typing import TypedDict, Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class BaseState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_input: str
    current_workflow: dict | str | None


class ValidatorState(BaseState):  # 专为 validator
    missing_nodes: list[dict]
    download_suggestions: list[dict]
    validated_workflow: dict


class PlannerState(BaseState):  # 专为 planner
    planning_result: dict
    retrieved_knowledge: list[dict]
