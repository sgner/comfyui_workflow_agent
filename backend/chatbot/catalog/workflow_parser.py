import os
import json
import glob


class WorkflowParser:
    def __init__(self, examples_dir):
        self.examples_dir = examples_dir

    def _extract_metadata_from_json(self, file_path):
        """深度解析工作流 JSON，提取关键信息"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return None

        # 兼容 API 格式和 UI 格式
        nodes = []
        if "nodes" in data:
            nodes = data["nodes"]  # UI 格式
        else:
            nodes = data.values()  # API 格式

        # 提取特征
        used_nodes = set()
        model_names = set()  # 关键！提取 ckpt_name, lora_name

        for node in nodes:
            # 1. 提取节点类型
            node_type = node.get("type") or node.get("class_type")
            if node_type:
                used_nodes.add(node_type)

            # 2. 提取参数中的模型名 (关键逻辑)
            # 检查 inputs 或 widgets_values
            inputs = node.get("inputs", {})
            widgets = node.get("widgets_values", [])

            # 检查常见的模型参数键名
            target_keys = ["ckpt_name", "model_name", "lora_name", "vae_name", "control_net_name"]

            # 从 inputs (API格式) 提取
            if isinstance(inputs, dict):
                for k, v in inputs.items():
                    if k in target_keys and isinstance(v, str):
                        model_names.add(v)

            # 从 widgets (UI格式) 提取 - 简单粗暴地把所有看起来像文件名的字符串都提取出来
            if isinstance(widgets, list):
                for w in widgets:
                    if isinstance(w, str) and (
                        w.endswith(".safetensors") or w.endswith(".ckpt") or "turbo" in w.lower()):
                        model_names.add(w)

        return {
            "filename": os.path.basename(file_path),
            "node_types": list(used_nodes),
            "models_used": list(model_names),
            "raw_json": json.dumps(data)  # 存下原始 JSON 方便后续提取
        }

    def scan(self):
        workflows = []
        # 扫描 .json 文件
        json_files = glob.glob(os.path.join(self.examples_dir, "*.json"))

        for json_file in json_files:
            meta = self._extract_metadata_from_json(json_file)
            if meta:
                workflows.append(meta)

        return workflows
