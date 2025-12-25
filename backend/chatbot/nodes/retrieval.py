import json
import os

from custom_nodes.comfyui_workflow_agent.backend.chatbot.state import BaseState
import logging
from typing import List, Dict, Any
# 导入全局单例数据库和状态检查
from custom_nodes.comfyui_workflow_agent.backend.chatbot.catalog.vdb import ChromaVectorStore
# from custom_nodes.comfyui_workflow_agent import GLOBAL_VECTOR_STORE

logger = logging.getLogger("WorkflowAgent")

import json


def is_workflow_empty(workflow_data: dict | str | None) -> bool:
    """
    判断 ComfyUI 工作流是否为空（没有节点）。
    兼容 UI 格式（包含 nodes 列表）和 API 格式（字典）。
    """
    if not workflow_data:
        return True

    # 1. 处理字符串输入
    if isinstance(workflow_data, str):
        try:
            workflow_data = json.loads(workflow_data)
        except Exception:
            return True  # 解析失败视为无效/空

    # 2. UI 格式判空 (你的例子属于这种)
    # 特征：有一个 "nodes" 列表
    if "nodes" in workflow_data:
        nodes = workflow_data["nodes"]
        return len(nodes) == 0

    # 3. API 格式判空
    # 特征：顶层字典的 key 是节点 ID (数字字符串)，value 是节点内容
    # 我们需要排除掉 "id", "extra", "version" 等非节点字段
    # 通常 API 格式不像 UI 格式那样保留 metadata，它就是纯节点 ID 映射
    # 但为了保险，我们可以检查是否包含 "class_type" 或 "inputs" 这种特征 key
    if isinstance(workflow_data, dict):
        # 如果是空的 {}
        if not workflow_data:
            return True

        # 遍历 value，看是否像一个节点
        for key, val in workflow_data.items():
            if isinstance(val, dict) and ("class_type" in val or "inputs" in val):
                return False  # 只要发现一个节点，就不为空

        # 只有 metadata 字段，没有节点
        return True

    return True


def extract_node_types_from_workflow(workflow_data: dict | str) -> list[str]:
    """辅助函数：从用户提供的工作流中提取所有节点类型"""
    try:
        if isinstance(workflow_data, str):
            workflow_data = json.loads(workflow_data)

        node_types = set()
        # 兼容 API 格式 (Dict[ID, Node]) 和 UI 格式 (List[Node])
        nodes = workflow_data.get("nodes", []) if "nodes" in workflow_data else workflow_data.values()

        for node in nodes:
            ntype = node.get("type") or node.get("class_type")
            if ntype:
                node_types.add(ntype)
        return list(node_types)
    except Exception as e:
        logger.error(f"Error parsing current workflow: {e}")
        return []


def search_knowledge_node(state: BaseState) -> Dict[str, Any]:
    """
    LangGraph 节点: 知识检索
    策略：
    1. 如果有当前工作流 -> 提取其中节点 + 规划建议的节点 -> 精确检索节点详情
    2. 如果无工作流 -> 检索工作流模版 -> 提取模版节点 + 规划建议的节点 -> 精确检索节点详情
    3. 兜底 -> 模糊检索
    """
    print("\n" + "=" * 50)
    print("🗄️ [Search] Starting Knowledge Retrieval Phase")
    print("=" * 50)

    # 1. 获取意图数据
    intent_json = state.intent_result
    user_intent = intent_json.get("user_intent", {})
    planning = intent_json.get("planning_suggestions", {})

    print(f"📋 User Intent: {user_intent.get('core_function', 'N/A')}")
    print(f"📋 Details: {user_intent.get('details', [])}")

    # 如果没有意图或还在澄清阶段，跳过检索
    if not user_intent or user_intent.get("clarification_needed", False):
        print("ℹ️ [Search] Clarification needed. Skipping retrieval.")
        return {"retrieved_knowledge": []}

    ######################################################
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    db_path = os.path.join(current_dir, "vector_db")
    store = ChromaVectorStore(db_path)

    ######################################################
    # 2. 获取数据库实例
    # store = GLOBAL_VECTOR_STORE
    if store is None:
        print("❌ Vector Store is not initialized. Skipping search.")
        logger.error("❌ Vector Store is not initialized. Skipping search.")
        return {"retrieved_knowledge": [{"error": "Knowledge base not ready"}]}

    # 3. 准备检索参数
    core_function = user_intent.get("core_function", "")
    base_model = user_intent.get("base_model", "")
    details = " ".join(user_intent.get("details", []))
    expected_nodes_str = " ".join(planning.get("expected_nodes", []))

    # 构建查询词
    search_query = f"{base_model} {core_function} {details} {expected_nodes_str}".strip()
    print(f"🔎 Search Query: '{search_query}'")

    knowledge_results: List[Dict] = []
    target_node_ids = set()  # 使用集合自动去重

    # 获取规划中建议的节点
    planned_nodes = planning.get("expected_nodes", [])
    if planned_nodes:
        target_node_ids.update(planned_nodes)
        print(f"🤖 [Planner] Suggested nodes: {planned_nodes}")

    # =================================================
    # 4. 分支逻辑：已有工作流 / 从零开始
    # =================================================
    current_workflow = state.current_workflow

    # 打印一下工作流状态判断结果
    is_empty = is_workflow_empty(current_workflow)
    has_valid_workflow = current_workflow and not is_empty
    print(f"📂 Workflow Status Check: Exists={bool(current_workflow)}, IsEmpty={is_empty}, Valid={has_valid_workflow}")

    has_context = False  # 标记是否找到了上下文

    if has_valid_workflow:
        # --- 分支 A: 基于现有工作流 ---
        print("👉 Branch A: Analyzing Existing Workflow")
        extracted_nodes = extract_node_types_from_workflow(current_workflow)

        if extracted_nodes:
            target_node_ids.update(extracted_nodes)
            has_context = True
            print(f"✅ Extracted {len(extracted_nodes)} unique node types from current workflow.")
            # print(f"   Nodes: {extracted_nodes[:5]}...") # 可选：打印部分节点名
    else:
        # --- 分支 B: 检索工作流模版 ---
        print("👉 Branch B: Searching for Workflow Templates")

        if search_query:
            wf_results = store.query_workflows(search_query, n=1, threshold=0.6)

            if wf_results and wf_results['ids'] and wf_results['ids'][0]:
                # 🎯 命中模版
                doc = wf_results['documents'][0][0]
                meta = wf_results['metadatas'][0][0]
                filename = meta.get('filename', 'Unknown')

                print(f"🎉 Template HIT: {filename}")
                has_context = True

                # 添加模版文档
                knowledge_results.append({
                    "type": "workflow_template",
                    "source": filename,
                    "content": doc,
                    "metadata": meta
                })

                # 从 metadata 提取节点列表
                node_str = meta.get('nodes', '')
                if node_str:
                    template_nodes = [n.strip() for n in node_str.split(',') if n.strip()]
                    target_node_ids.update(template_nodes)
                    print(f"🔗 Extracted {len(template_nodes)} nodes from template metadata.")
            else:
                print("❌ No matching workflow template found.")

    # =================================================
    # 5. 精确节点检索 (Exact Node Lookup)
    # =================================================
    if target_node_ids:
        print(f"🕵️ [Exact Search] Looking up definitions for {len(target_node_ids)} target nodes...")

        # 过滤掉无需解释的通用节点以节省 Token
        ignored = ["Note", "Reroute", "Primitive", "PreviewImage", "SaveImage", "Pad"]
        filtered_ids = [nid for nid in target_node_ids if nid not in ignored]

        if len(target_node_ids) != len(filtered_ids):
            print(f"   (Ignored {len(target_node_ids) - len(filtered_ids)} common utility nodes)")

        if hasattr(store, 'get_nodes_by_ids'):
            node_results = store.get_nodes_by_ids(filtered_ids)
            if node_results and node_results['documents']:
                count = len(node_results['documents'])
                print(f"✅ Successfully retrieved definitions for {count} nodes.")

                # 检查有哪些没找到 (便于调试)
                found_ids = set()  # 这里需要根据实际返回结构解析ID，简单起见只打印数量
                # 如果你想看具体的: found_ids = set(m['node_id'] for m in node_results['metadatas'])
                # missing = set(filtered_ids) - found_ids
                # if missing: print(f"⚠️ Missing definitions for: {missing}")

                for i, doc in enumerate(node_results['documents']):
                    knowledge_results.append({
                        "type": "node_spec",
                        "source": "catalog_exact_match",
                        "content": doc,
                        "metadata": node_results['metadatas'][i]
                    })
            else:
                logger.warning("⚠️ Target nodes not found in Catalog (Maybe missing custom nodes?).")
                print("⚠️ No definitions found for target IDs.")

    # =================================================
    # 6. 兜底逻辑：模糊搜索 (Fuzzy Search)
    # =================================================
    if not has_context or len(knowledge_results) < 2:
        print("🔸 Context insufficient (Low confidence). Performing fuzzy node search...")

        if search_query:
            fuzzy_results = store.query_nodes(search_query, n_results=3, threshold=0.5)
            if fuzzy_results and fuzzy_results['documents']:
                count = len(fuzzy_results['documents'][0])
                print(f"🌫️ Fuzzy search found {count} related nodes.")

                for i, doc in enumerate(fuzzy_results['documents'][0]):
                    knowledge_results.append({
                        "type": "node_spec",
                        "source": "catalog_fuzzy_search",
                        "content": doc,
                        "metadata": fuzzy_results['metadatas'][0][i]
                    })
            else:
                print("❌ Fuzzy search returned no results.")

    # 去重
    unique_knowledge = []
    seen_content = set()
    for item in knowledge_results:
        content_hash = hash(item['content'])
        if content_hash not in seen_content:
            unique_knowledge.append(item)
            seen_content.add(content_hash)

    print(f"🏁 [Search] Retrieval Complete. Returning {len(unique_knowledge)} unique items.")
    print("=" * 50 + "\n")

    return {"retrieved_knowledge": unique_knowledge}
