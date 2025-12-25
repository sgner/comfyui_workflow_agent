import os
import uuid
import logging
import chromadb
from chromadb.config import Settings
import re
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # 国内最快的 HuggingFace 镜像
os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "120"
os.environ["HF_HUB_ETAG_TIMEOUT"] = "60"
logger = logging.getLogger("WorkflowAgent")


class ChromaVectorStore:
    def __init__(self, persist_directory):
        """
        初始化 ChromaDB 向量库
        :param persist_directory: 数据库持久化路径
        """
        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)

        self.persist_directory = persist_directory
        self.node_collection_name = "comfyui_nodes_catalog"

        # 1. 检查必要依赖
        try:
            from chromadb.utils import embedding_functions
            import sentence_transformers  # 确保已安装
        except ImportError:
            raise ImportError("Missing dependencies. Please run: pip install chromadb sentence-transformers")

        # 2. 初始化客户端 (带冲突解决机制)
        # ComfyUI 重载时可能会导致旧的 Client 对象未释放，再次初始化会报错
        try:
            self.client = chromadb.PersistentClient(path=persist_directory)
        except ValueError as e:
            if "already exists" in str(e):
                logger.warning("⚠️ Chroma Client conflict detected. Attaching to existing session...")
                try:
                    # 尝试连接到已存在的系统会话
                    self.client = chromadb.Client(Settings(
                        is_persistent=True,
                        persist_directory=persist_directory
                    ))
                except Exception as sub_e:
                    logger.error(f"❌ Failed to recover Chroma Client: {sub_e}")
                    raise e
            else:
                raise e

        # 3. 初始化 Embedding 模型 (CPU模式，不占显存)
        logger.info("📦 [Catalog] Loading embedding model (all-MiniLM-L6-v2)...")
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        local_model_path = os.path.join(base_path, "models", "all-MiniLM-L6-v2")
        model_name_or_path = local_model_path if os.path.exists(local_model_path) else "all-MiniLM-L6-v2"

        if os.path.exists(local_model_path):
            logger.info(f"   -> Using local model at: {local_model_path}")
        else:
            logger.info(f"   -> Local model not found, trying to download 'all-MiniLM-L6-v2'...")

        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name_or_path,
            device="cpu"
        )

        # 4. 获取或创建集合
        self.node_collection = self.client.get_or_create_collection(
            name=self.node_collection_name,
            embedding_function=self.embedding_fn
        )

        self.workflow_collection = self.client.get_or_create_collection(
            name="comfyui_workflows_gallery",
            embedding_function=self.embedding_fn
        )

    def process_incremental_update(self, docs_to_upsert, ids_to_delete):
        """
        执行增量更新
        :param docs_to_upsert: 需要新增或更新的文档列表 (List[Dict])
        :param ids_to_delete: 需要删除的节点 ID 列表 (List[str])
        """
        try:
            # === 1. 删除操作 ===
            if ids_to_delete:
                logger.info(f"🗑️ [Catalog] Deleting {len(ids_to_delete)} obsolete nodes from DB...")
                # 确保 ID 是字符串列表
                safe_ids = [str(i) for i in ids_to_delete]
                self.node_collection.delete(ids=safe_ids)

            # === 2. 更新/插入操作 (Upsert) ===
            if docs_to_upsert:
                count = len(docs_to_upsert)
                logger.info(f"🔄 [Catalog] Upserting {count} nodes to DB...")

                # 提取数据
                ids = []
                documents = []
                metadatas = []

                for doc in docs_to_upsert:
                    # 确保 ID 是字符串
                    node_id = str(doc['metadata'].get('node_id', uuid.uuid4()))
                    ids.append(node_id)

                    documents.append(doc['content'])

                    # 清洗 metadata，确保没有复杂对象 (Chroma 不支持 List/Dict 作为 value)
                    safe_meta = {}
                    for k, v in doc['metadata'].items():
                        if isinstance(v, (str, int, float, bool)):
                            safe_meta[k] = v
                        else:
                            safe_meta[k] = str(v)  # 强转为字符串
                    metadatas.append(safe_meta)

                # 批处理写入 (防止 SQLite 锁死或内存溢出)
                batch_size = 50
                for i in range(0, count, batch_size):
                    end = min(i + batch_size, count)
                    self.node_collection.upsert(
                        ids=ids[i:end],
                        documents=documents[i:end],
                        metadatas=metadatas[i:end]
                    )
                    # logger.info(f"   Batch {i}-{end} written.")

            logger.info("✅ [Catalog] DB Update successful.")
            return True

        except Exception as e:
            logger.error(f"❌ [Catalog] Update failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def query_nodes(self, query_text, n_results=5, where_filter=None, threshold=0.55):
        """
        查询节点 (带阈值过滤)
        :param threshold: 距离阈值，默认 0.55。越小越严格。
                          0.3 = 非常相似
                          0.5 = 相关
                          >0.7 = 基本不相关
        """
        try:
            results = self.node_collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_filter
            )

            return self._filter_results(results, threshold)

        except Exception as e:
            logger.error(f"❌ [Catalog] Node query failed: {e}")
            return None

    def reset_and_rebuild(self, documents):
        """
        [灾难恢复用] 强制清空并全量重建
        """
        try:
            logger.warning("🔥 [Catalog] Performing full DB reset...")
            try:
                self.client.delete_collection(self.node_collection_name)
            except:
                pass

            self.node_collection = self.client.create_collection(
                name=self.node_collection_name,
                embedding_function=self.embedding_fn
            )

            # 复用增量逻辑进行全量写入
            self.process_incremental_update(documents, [])

        except Exception as e:
            logger.error(f"❌ [Catalog] Reset failed: {e}")

    def process_workflow_update(self, workflows_to_upsert, filenames_to_delete):
        """
            工作流增量更新
            :param workflows_to_upsert: 需要更新/新增的工作流数据列表 (来自 Scanner)
            :param filenames_to_delete: 需要删除的文件名列表
            """
        try:
            # 1. 删除
            if filenames_to_delete:
                logger.info(f"🗑️ [Workflow] Removing {len(filenames_to_delete)} templates...")
                self.workflow_collection.delete(ids=filenames_to_delete)

            # 2. 更新/新增
            if workflows_to_upsert:
                logger.info(f"🔄 [Workflow] Upserting {len(workflows_to_upsert)} templates...")

                ids = []
                docs = []
                metadatas = []

                for wf in workflows_to_upsert:
                    filename = wf['filename']
                    ids.append(filename)

                    # 构建富含语义的 Embedding 文本
                    content = f"""
    # Workflow Template: {filename}
    ## Models Used
    {', '.join(wf['models_used'])}

    ## Key Nodes
    {', '.join(wf['node_types'])}

    ## Description
    This is a reference workflow containing {len(wf['node_types'])} nodes.
    It is optimized for models: {', '.join(wf['models_used'])}.
    """
                    docs.append(content)

                    # 扁平化 Metadata (Chroma 不支持列表)
                    metadatas.append({
                        "filename": filename,
                        "models": ", ".join(wf['models_used'])[:1000],  # 防止过长
                        "nodes": ", ".join(wf['node_types'])[:1000]
                    })

                # 批量写入
                if ids:
                    self.workflow_collection.upsert(
                        ids=ids,
                        documents=docs,
                        metadatas=metadatas
                    )

            logger.info("✅ [Workflow] Gallery updated successfully.")
            return True

        except Exception as e:
            logger.error(f"❌ [Workflow] Update failed: {e}")
            return False

    def query_workflows(self, query, n=5, threshold=0.6):
        """
        混合检索：向量检索 + 关键词检索
        """
        combined_results = {
            'ids': [[]],
            'distances': [[]],
            'metadatas': [[]],
            'documents': [[]]
        }

        seen_ids = set()

        # -------------------------------------------------
        # 1. 关键词检索 (Keyword Search) - 优先
        # -------------------------------------------------
        kw_results = self._keyword_search_workflows(query)
        if kw_results:
            for i, doc_id in enumerate(kw_results['ids']):
                if doc_id not in seen_ids:
                    combined_results['ids'][0].append(doc_id)
                    combined_results['distances'][0].append(0.0)  # 强制置顶
                    combined_results['metadatas'][0].append(kw_results['metadatas'][i])
                    combined_results['documents'][0].append(kw_results['documents'][i])
                    seen_ids.add(doc_id)

            logger.info(f"🔍 [Hybrid] Keyword match found {len(kw_results['ids'])} items.")

        # -------------------------------------------------
        # 2. 向量检索 (Vector Search) - 补充
        # -------------------------------------------------
        try:
            vec_results = self.workflow_collection.query(
                query_texts=[query],
                n_results=n
            )

            # 过滤并合并
            filtered_vec = self._filter_results(vec_results, threshold)
            if filtered_vec:
                for i, doc_id in enumerate(filtered_vec['ids'][0]):
                    if doc_id not in seen_ids:
                        combined_results['ids'][0].append(doc_id)
                        combined_results['distances'][0].append(filtered_vec['distances'][0][i])
                        combined_results['metadatas'][0].append(filtered_vec['metadatas'][0][i])
                        combined_results['documents'][0].append(filtered_vec['documents'][0][i])
                        seen_ids.add(doc_id)

        except Exception as e:
            logger.error(f"❌ [Workflow] Vector query failed: {e}")

        # -------------------------------------------------
        # 3. 截断结果
        # -------------------------------------------------
        # 只返回前 N 个
        if len(combined_results['ids'][0]) > n:
            combined_results['ids'][0] = combined_results['ids'][0][:n]
            combined_results['distances'][0] = combined_results['distances'][0][:n]
            combined_results['metadatas'][0] = combined_results['metadatas'][0][:n]
            combined_results['documents'][0] = combined_results['documents'][0][:n]

        # 如果列表为空，返回 None
        if not combined_results['ids'][0]:
            return None

        return combined_results

    def _filter_results(self, results, threshold):
        """
        内部方法：根据距离阈值过滤 Chroma 返回的原始结果
        """
        if not results or not results['ids'] or not results['distances']:
            return None

        # Chroma 返回的是 Batch 列表 [[id1, id2...]]，我们只处理 Batch 0
        original_ids = results['ids'][0]
        original_distances = results['distances'][0]
        original_metadatas = results['metadatas'][0]
        original_documents = results['documents'][0]

        # 筛选合格的索引
        valid_indices = [
            i for i, dist in enumerate(original_distances)
            if dist < threshold
        ]

        if not valid_indices:
            return None  # 如果没有一个合格的，直接返回 None

        # 重构返回结构
        filtered_ids = [original_ids[i] for i in valid_indices]
        filtered_distances = [original_distances[i] for i in valid_indices]
        filtered_metadatas = [original_metadatas[i] for i in valid_indices]
        filtered_documents = [original_documents[i] for i in valid_indices]

        # 保持 Chroma 的返回格式 (Batch List)
        return {
            'ids': [filtered_ids],
            'distances': [filtered_distances],
            'metadatas': [filtered_metadatas],
            'documents': [filtered_documents]
        }

    def get_nodes_by_ids(self, node_ids):
        """
        根据节点 ID 列表获取节点的详细定义 (非向量搜索，而是精确主键查找)
        :param node_ids: 节点 ID 列表，如 ['KSampler', 'SaveImage']
        :return: Chroma GetResult 字典
        """
        try:
            # 过滤空值和重复值
            unique_ids = list(set([nid.strip() for nid in node_ids if nid and nid.strip()]))

            if not unique_ids:
                return None

            # 使用 Chroma 的 get 方法直接通过 ID 获取
            results = self.node_collection.get(
                ids=unique_ids,
                include=['documents', 'metadatas']
            )
            return results
        except Exception as e:
            logger.error(f"❌ [Catalog] Get nodes by ID failed: {e}")
            return None

    def _keyword_search_workflows(self, query):
        """
        [辅助方法] 改进版：基于分词的关键词检索
        解决 "长句搜不到短词" 的问题
        """
        try:
            all_data = self.workflow_collection.get(include=['metadatas', 'documents'])

            if not all_data['ids']:
                return None

            hits = {
                'ids': [],
                'distances': [],
                'metadatas': [],
                'documents': []
            }

            # 1. 预处理查询词：提取潜在的关键词
            # 逻辑：提取所有由字母、数字、横杠、点、下划线组成的序列 (通常是模型名、文件名、版本号)
            # 例如: "使用 z-image-turbo q8" -> ['z-image-turbo', 'q8']
            query_lower = query.lower()

            # 正则提取英文/数字关键词 (过滤掉纯中文描述，因为metadata里通常只有英文模型名)
            potential_keywords = set(re.findall(r'[a-zA-Z0-9\-\._]+', query_lower))

            # 过滤掉太短的词 (如 "v1", "a" 等容易误判的，视情况调整)
            keywords = [k for k in potential_keywords if len(k) >= 2]

            # 如果没提取到英文关键词，回退到按空格分割 (针对纯中文环境的补充)
            if not keywords:
                keywords = query_lower.split()

            if not keywords:
                return None

            # 2. 遍历匹配
            for idx, meta in enumerate(all_data['metadatas']):
                # 拼接目标的搜索域
                filename = meta.get('filename', '').lower()
                models = meta.get('models', '').lower()
                # 还可以加入 nodes 列表辅助匹配
                nodes = meta.get('nodes', '').lower()

                target_text = f"{filename} {models} {nodes}"

                # 3. 核心匹配逻辑：只要命中【任何一个】关键长词，就算匹配
                # 也可以改为【命中所有】或者【打分制】
                is_hit = False
                for kw in keywords:
                    # 排除一些无意义的常用词 (可根据需要扩展)
                    if kw in ["json", "workflow", "comfyui", "model", "use", "create"]:
                        continue

                    if kw in target_text:
                        is_hit = True
                        break  # 命中一个核心词即可，比如命中了 "z-image-turbo"

                if is_hit:
                    hits['ids'].append(all_data['ids'][idx])
                    hits['metadatas'].append(meta)
                    hits['documents'].append(all_data['documents'][idx])
                    hits['distances'].append(0.0)  # 关键词命中，置顶

            return hits if hits['ids'] else None

        except Exception as e:
            logger.error(f"❌ [Workflow] Keyword search failed: {e}")
            return None
