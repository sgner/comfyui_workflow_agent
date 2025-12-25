import threading
import time
import logging
import os
import sys
import json
import hashlib

# 1. 环境配置
# 强制使用国内镜像
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
# 禁用 Chroma 遥测
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_SERVER_NOINTERACTIVE"] = "True"

logging.basicConfig(format="%(asctime)s [WorkflowAgent] %(message)s", level=logging.INFO)
logger = logging.getLogger("WorkflowAgent")

# 2. 导入模块
try:
    from custom_nodes.comfyui_workflow_agent.backend.chatbot.catalog.scanner import NodeScanner
    from custom_nodes.comfyui_workflow_agent.backend.chatbot.catalog.workflow_parser import WorkflowParser
    from custom_nodes.comfyui_workflow_agent.backend.chatbot.catalog.node_formatter import KnowledgeBaseFormatter
    from custom_nodes.comfyui_workflow_agent.backend.chatbot.catalog.vdb import ChromaVectorStore
except ImportError as e:
    logger.error(f"❌ Failed to import: {e}")
    NodeScanner = None
    WorkflowParser = None
    KnowledgeBaseFormatter = None
    ChromaVectorStore = None

# 3. 状态管理
GLOBAL_VECTOR_STORE = None


class SystemStatus:
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"


CURRENT_STATUS = SystemStatus.INITIALIZING
STATUS_MESSAGE = "System is initializing..."


def get_system_status():
    if CURRENT_STATUS != SystemStatus.READY:
        raise RuntimeError(f"Service Unavailable: {STATUS_MESSAGE}")
    return True


# =========================================================
# 哈希辅助函数
# =========================================================

def get_workflow_fingerprint(wf_data):
    """计算工作流指纹: 文件名 + 原始内容"""
    content = wf_data['filename'] + wf_data.get('raw_json', '')
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def get_node_fingerprint(node_data):
    """计算节点指纹: ID + IO定义 + 描述 + Readme"""
    content_str = (
        str(node_data['id']) +
        str(node_data['input_types']) +
        str(node_data['return_types']) +
        str(node_data['description']) +
        str(node_data['readme_snippet'])
    )
    return hashlib.md5(content_str.encode('utf-8')).hexdigest()


def load_local_hashes(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_local_hashes(path, hash_map):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(hash_map, f, indent=2)


def ensure_vector_store():
    """单例模式获取数据库实例"""
    global GLOBAL_VECTOR_STORE
    if GLOBAL_VECTOR_STORE is None:
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, "vector_db")
            GLOBAL_VECTOR_STORE = ChromaVectorStore(db_path)
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB: {e}")
            return None
    return GLOBAL_VECTOR_STORE


# =========================================================
# 后台任务主逻辑
# =========================================================

def background_indexing_task():
    global CURRENT_STATUS, STATUS_MESSAGE

    delay_seconds = 5
    logger.info(f"⏳ Scanner scheduled in {delay_seconds}s...")
    time.sleep(delay_seconds)

    # 检查核心依赖
    if NodeScanner is None or ChromaVectorStore is None:
        CURRENT_STATUS = SystemStatus.ERROR
        STATUS_MESSAGE = "Missing dependencies"
        return

    # 初始化数据库连接 (只做一次)
    if not ensure_vector_store():
        CURRENT_STATUS = SystemStatus.ERROR
        return

    # ------------------------------------------------------------------
    # 任务 1: 增量扫描工作流 (Workflow Templates)
    # ------------------------------------------------------------------
    try:
        logger.info("🔍 [Catalog] Scanning example workflows...")

        base_path = os.path.dirname(os.path.abspath(__file__))
        examples_dir = os.path.join(base_path, "example_workflows")
        hash_file = os.path.join(base_path, "workflow_fingerprints.json")

        if not os.path.exists(examples_dir):
            os.makedirs(examples_dir)

        # 扫描
        wf_scanner = WorkflowParser(examples_dir)
        current_workflows = wf_scanner.scan()

        # 加载旧哈希
        old_hashes = load_local_hashes(hash_file)
        new_hashes = {}
        to_upsert = []
        to_delete = []

        # Diff 计算
        for wf in current_workflows:
            fid = wf['filename']
            fingerprint = get_workflow_fingerprint(wf)
            new_hashes[fid] = fingerprint

            if (fid not in old_hashes) or (old_hashes[fid] != fingerprint):
                to_upsert.append(wf)

        for old_id in old_hashes:
            if old_id not in new_hashes:
                to_delete.append(old_id)

        # 执行更新
        if not old_hashes and current_workflows:
            logger.info(f"🆕 [Workflow] First run. Indexing {len(current_workflows)} templates...")
            GLOBAL_VECTOR_STORE.process_workflow_update(current_workflows, [])
        elif to_upsert or to_delete:
            logger.info(f"🔄 [Workflow] Syncing: {len(to_upsert)} changed, {len(to_delete)} deleted.")
            GLOBAL_VECTOR_STORE.process_workflow_update(to_upsert, to_delete)
        else:
            logger.info("⚡ [Workflow] No changes detected.")

        # 保存状态
        save_local_hashes(hash_file, new_hashes)

    except Exception as e:
        logger.error(f"❌ [Catalog] Workflow scan failed: {e}")
        # 注意：工作流扫描失败不应阻止节点扫描

    # ------------------------------------------------------------------
    # 任务 2: 增量扫描节点 (Nodes)
    # ------------------------------------------------------------------
    try:
        logger.info("🔍 [Catalog] Scanning nodes...")
        scanner = NodeScanner()

        # 智能重试防止字典变化
        current_nodes_list = []
        for _ in range(3):
            try:
                current_nodes_list = scanner.scan()
                break
            except RuntimeError:
                time.sleep(1)

        if not current_nodes_list:
            logger.warning("⚠️ No nodes scanned.")
            # 即使没扫到节点，系统也算 Ready (可能是用户真的没装插件)
            CURRENT_STATUS = SystemStatus.READY
            return

        base_path = os.path.dirname(os.path.abspath(__file__))
        hash_file_path = os.path.join(base_path, "node_fingerprints.json")

        # 加载旧哈希
        old_hashes = load_local_hashes(hash_file_path)
        new_hashes = {}
        nodes_to_upsert = []
        ids_to_delete = []

        # Diff 计算
        for node in current_nodes_list:
            nid = str(node['id'])
            fingerprint = get_node_fingerprint(node)
            new_hashes[nid] = fingerprint

            if (nid not in old_hashes) or (old_hashes[nid] != fingerprint):
                nodes_to_upsert.append(node)

        for old_id in old_hashes:
            if old_id not in new_hashes:
                ids_to_delete.append(old_id)

        # 检查是否需要全量重建 (首次运行或数据库文件丢失)
        # 注意：这里复用 ensure_vector_store() 得到的实例，不再重复初始化

        is_fresh_start = not old_hashes

        if is_fresh_start:
            logger.info("🆕 [Node] First run. Indexing all nodes...")
            docs = KnowledgeBaseFormatter.to_markdown(current_nodes_list)
            # 使用增量接口传入所有数据，效果等同于全量
            GLOBAL_VECTOR_STORE.process_incremental_update(docs, [])
        else:
            if not nodes_to_upsert and not ids_to_delete:
                logger.info("⚡ [Node] No changes detected.")
            else:
                logger.info(f"🔄 [Node] Syncing: {len(nodes_to_upsert)} changed, {len(ids_to_delete)} deleted.")
                docs_to_upsert = []
                if nodes_to_upsert:
                    docs_to_upsert = KnowledgeBaseFormatter.to_markdown(nodes_to_upsert)
                GLOBAL_VECTOR_STORE.process_incremental_update(docs_to_upsert, ids_to_delete)

        # 保存状态
        save_local_hashes(hash_file_path, new_hashes)

        CURRENT_STATUS = SystemStatus.READY
        STATUS_MESSAGE = "Ready"
        logger.info(f"✅ [Catalog] All sync tasks complete.")

    except Exception as e:
        CURRENT_STATUS = SystemStatus.ERROR
        STATUS_MESSAGE = str(e)
        logger.error(f"❌ [Catalog] Node scan failed: {e}")
        import traceback
        traceback.print_exc()


def start_scanner():
    if hasattr(sys, "_comfy_catalog_scanner_active"): return
    sys._comfy_catalog_scanner_active = True

    scan_thread = threading.Thread(target=background_indexing_task, name="ComfyUI_NodeScanner")
    scan_thread.daemon = True
    scan_thread.start()
    logger.info("🚀 [Catalog] Scanner thread initiated.")


start_scanner()

WEB_DIRECTORY = "./web"
NODE_CLASS_MAPPINGS = {}
__all__ = ["NODE_CLASS_MAPPINGS", "WEB_DIRECTORY", "GLOBAL_VECTOR_STORE", "get_system_status"]
