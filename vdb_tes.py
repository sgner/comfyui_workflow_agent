import os
import sys
import logging
import time

# =========================================================
# 1. 环境配置 (防止下载超时和遥测报错)
# =========================================================
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_SERVER_NOINTERACTIVE"] = "True"

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("TestVDB")

# =========================================================
# 2. 路径黑魔法 (确保能导入 backend 模块)
# =========================================================
# 获取当前脚本所在目录 (custom_nodes/comfyui_workflow_agent/)
current_dir = os.path.dirname(os.path.abspath(__file__))

# 将当前目录加入系统路径，这样就能直接导入 backend 包了
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    # ⚠️ 关键点：直接从 vdb.py 导入，避开 __init__.py 的复杂逻辑
    from backend.chatbot.catalog.vdb import ChromaVectorStore
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print(f"当前 sys.path: {sys.path}")
    print("请确保此脚本位于 'custom_nodes/comfyui_workflow_agent/' 根目录下")
    sys.exit(1)


# =========================================================
# 3. 辅助打印函数
# =========================================================
def print_results(results, title="Search Results"):
    print(f"\n🔎 {title}")
    print("-" * 60)

    if not results or not results['ids'] or not results['ids'][0]:
        print("   ❌ 未找到匹配项 (No matches found).")
        return

    ids = results['ids'][0]
    distances = results['distances'][0]
    metadatas = results['metadatas'][0]
    documents = results['documents'][0]

    for i, (doc_id, dist, meta, content) in enumerate(zip(ids, distances, metadatas, documents)):
        # 截断过长的内容
        preview = content.replace('\n', ' ')[:100] + "..."
        print(f"   🎯 Match {i + 1}: [{doc_id}]")
        print(f"      📏 距离 (越小越好): {dist:.4f}")
        print(f"      📄 元数据: {meta}")
        print(f"      📝 内容摘要: {preview}")
        print("-" * 30)


# =========================================================
# 4. 主测试逻辑
# =========================================================
def run_test():
    # 1. 确定数据库路径
    db_path = os.path.join(current_dir, "vector_db")

    print(f"📂 正在连接数据库: {db_path}")

    if not os.path.exists(db_path):
        print("❌ 错误: 数据库文件夹 'vector_db' 不存在！")
        print("请先启动一次 ComfyUI，让后台扫描任务自动建立数据库。")
        return

    # 2. 初始化 VDB
    try:
        start_time = time.time()
        store = ChromaVectorStore(db_path)
        print(f"✅ 数据库加载成功 (耗时: {time.time() - start_time:.2f}s)")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return

    # 3. 测试用例
    test_cases = [
        {
            "type": "workflow",
            "query": "wan2.2-i2v-5b-q8 使用wan2.2-i2v-5b-q8模型进行视频生成",
            "desc": "测试工作流检索 (关键词/模型名)"
        }
    ]

    # 4. 执行循环
    for case in test_cases:
        query = case['query']
        print(f"\n\n🧪 测试场景: {case['desc']}")
        print(f"🔑 查询词: '{query}'")

        if case['type'] == "workflow":
            # 测试工作流混合检索 (关键词+向量)
            # 阈值设为 0.6
            results = store.query_workflows(query, n=2, threshold=0.7)
            print_results(results, title="工作流检索结果")

        elif case['type'] == "node":
            # 测试节点检索
            # 阈值设为 0.55
            results = store.query_nodes(query, n_results=2, threshold=0.55)
            print_results(results, title="节点检索结果")


if __name__ == "__main__":
    run_test()
