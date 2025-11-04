import json
from custom_nodes.agent_nodepack.backend.utils.request_context import get_session_id, get_rewrite_context
from custom_nodes.agent_nodepack.backend.dao.workflow_table import get_workflow_data
from langchain.tools import tool


@tool(description="获取comfyui当前会话下的工作流数据")
def get_current_workflow() -> str:
    """获取当前session的工作流数据"""
    session_id = get_session_id()
    if not session_id:
        return json.dumps({"error": "No session_id found in context"})

    workflow_data = get_workflow_data(session_id)
    if not workflow_data:
        return json.dumps({"error": "No workflow data found for this session"})

    workflow_data_str = json.dumps(workflow_data, ensure_ascii=False)
    get_rewrite_context().current_workflow = workflow_data_str
    return workflow_data_str
