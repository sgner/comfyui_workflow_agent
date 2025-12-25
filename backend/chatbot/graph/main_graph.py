from langgraph.graph import StateGraph
from custom_nodes.comfyui_workflow_agent.backend.chatbot.nodes.llm import router
from custom_nodes.comfyui_workflow_agent.backend.chatbot.graph.planner_graph import graph as planner_graph
from custom_nodes.comfyui_workflow_agent.backend.chatbot.state import BaseState


def main_graph():
    workflow = StateGraph(BaseState)
    workflow.add_node("Router", router)
    workflow.add_node("Planner", planner_graph)

