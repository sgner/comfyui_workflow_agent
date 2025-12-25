import json
import os

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from custom_nodes.comfyui_workflow_agent.backend.chatbot.output_format.planner_intent_output_format import output_format
from custom_nodes.comfyui_workflow_agent.backend.chatbot.output_format.router_output_format import RouteResult
from custom_nodes.comfyui_workflow_agent.backend.chatbot.state import BaseState
from custom_nodes.comfyui_workflow_agent.backend.chatbot.config.llm_config import llm_config

INTENT_PROMPT = ""
prompt_path = os.path.join(os.path.dirname(__file__), "..", "config", "prompts", "intent_prompt.md")
if os.path.exists(prompt_path):
    with open(prompt_path, 'r', encoding='utf-8') as f:
        INTENT_PROMPT = f.read()
else:
    raise FileNotFoundError(f"Intent prompt not found: {prompt_path}")


def intent_node(state: BaseState):
    llm = llm_config()
    prompt_messages = [SystemMessage(content=INTENT_PROMPT)]

    prompt_messages.extend(state.messages)
    wf_context = json.dumps(state.current_workflow, ensure_ascii=False) if state.current_workflow else "None"

    final_human_content = f"""
    [用户输入]
    {state.user_input}

    [当前工作流状态]
    {wf_context}
    """
    prompt_messages.append(HumanMessage(content=final_human_content))
    llm_with_format = llm.with_structured_output(output_format)
    response_obj = llm_with_format.invoke(prompt_messages)
    intent_data = response_obj
    need_human = response_obj['user_intent']['clarification_needed']
    print(response_obj)
    print(need_human)
    ai_msg_content = intent_data.get('notes', 'Intent Analysis Completed.')
    return {
        "intent_result": intent_data,
        "iteration": 1,
        "need_human": need_human,
        "messages": [
            HumanMessage(content=state.user_input),
            AIMessage(content=ai_msg_content)
        ]
    }


ROUTE_PROMPT = ""
prompt_path = os.path.join(os.path.dirname(__file__), "..", "config", "prompts", "router_prompt.md")
with open(prompt_path, "r") as f:
    ROUTER_PROMPT = f.read()


def router(state: BaseState):
    print("🚦 [Master] Routing request...")

    # 1. 显式规则优先 (Heuristics)
    # 如果前端直接传来了 error_logs，大概率是修 bug
    if state.error_logs and len(state.error_logs) > 10:
        print("   -> Detected Error Logs, routing to Debugger.")
        return {"route_decision": "debugger"}

    llm = llm_config()
    structured_llm = llm.with_structured_output(RouteResult)

    messages = [
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=f"User Input: {state.user_input}\nHas Error Logs: {bool(state.error_logs)}")
    ]

    result = structured_llm.invoke(messages)

    decision = result.destination
    print(f"   -> LLM Decision: {decision} ({result.reasoning})")

    return {"route_decision": decision}
