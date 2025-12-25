import os
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, END, START
from custom_nodes.comfyui_workflow_agent.backend.chatbot.state import BaseState
from custom_nodes.comfyui_workflow_agent.backend.chatbot.nodes.llm import intent_node
from custom_nodes.comfyui_workflow_agent.backend.chatbot.nodes.ask_human import ask_human
from custom_nodes.comfyui_workflow_agent.backend.chatbot.nodes.retrieval import search_knowledge_node

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data",
                       "history.sqlite")
conn = sqlite3.connect(db_path, check_same_thread=False)
checkpointer = SqliteSaver(conn)


def ask_human_need(state: BaseState):
    if state.intent_result['user_intent']['clarification_needed']:
        return "ask_human"
    return "retrieval"


def graph():
    workflow = StateGraph(BaseState)
    workflow.add_node("intent", intent_node)
    workflow.add_node("ask_human", ask_human)
    workflow.add_node("retrieval", search_knowledge_node)
    workflow.add_edge(START, "intent")
    workflow.add_conditional_edges(
        "intent",
        ask_human_need,
        {
            "ask_human": "ask_human",
            "retrieval": "retrieval"
        }
    )
    workflow.add_edge("ask_human", "intent")
    workflow.add_edge("retrieval", END)
    return workflow.compile(checkpointer=checkpointer, interrupt_before=["ask_human"])
