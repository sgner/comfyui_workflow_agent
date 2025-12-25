from planner_graph import graph
from custom_nodes.comfyui_workflow_agent.backend.chatbot.state import BaseState

if __name__ == '__main__':
    from langchain_core.messages import HumanMessage

    state = {
        "user_input": "我要一个使用z-image-turbo模型的工作流",
        "messages": [],
        "current_workflow": """
        {
  "id": "60251574-e82b-48b7-8e7a-3ecd46022c8d",
  "revision": 0,
  "last_node_id": 0,
  "last_link_id": 0,
  "nodes": [],
  "links": [],
  "groups": [],
  "config": {},
  "extra": {
    "workflowRendererVersion": "LG",
    "ue_links": [],
    "ds": {
      "scale": 0.45,
      "offset": [
        1416.4784948844667,
        1089.8145638994752
      ]
    }
  },
  "version": 0.4
}
        """
    }
    config = {"configurable": {"thread_id": '60251574-e82b-48b7-8e7a-3ecd46022c8w'}}
    app= graph()
    app.invoke(state,config=config)
    states=app.get_state(config)
    print(states.values)
