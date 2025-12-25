import os
import sys
import inspect
import json
import subprocess
import nodes
import folder_paths


class NodeScanner:
    def __init__(self):
        self.nodes_info = {}
        self.custom_nodes_path = folder_paths.get_folder_paths("custom_nodes")[0]

    def _get_git_info(self, directory):
        """获取目录的 Git 信息"""
        try:
            # 获取远程仓库 URL
            remote = subprocess.check_output(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=directory,
                stderr=subprocess.DEVNULL
            ).decode('utf-8').strip()
            return remote
        except Exception:
            return None

    def _get_readme(self, directory):
        for filename in os.listdir(directory):
            if filename.lower().endswith('.md'):
                try:
                    with open(os.path.join(directory, filename), 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read(9999)
                except:
                    pass
        return "No README found."

    def scan(self):
        """主扫描逻辑"""
        # 1. 获取所有已加载的节点映射
        mappings = nodes.NODE_CLASS_MAPPINGS
        display_names = nodes.NODE_DISPLAY_NAME_MAPPINGS

        scanned_data = []

        for node_id, node_class in mappings.items():
            node_data = {
                "id": node_id,
                "display_name": display_names.get(node_id, node_id),
                "category": getattr(node_class, "CATEGORY", "Unknown"),
                "input_types": [],
                "return_types": [],
                "description": getattr(node_class, "DESCRIPTION", ""),  # 部分节点有描述
                "file_path": "",
                "pack_name": "ComfyUI_Native",  # 默认为原生
                "github_url": "",
                "readme_snippet": ""
            }

            # 2. 内省：获取输入输出定义
            try:
                if hasattr(node_class, "INPUT_TYPES"):
                    inputs = node_class.INPUT_TYPES()
                    # 简化输入结构，只转为字符串描述供 LLM 阅读
                    node_data["input_types"] = json.dumps(inputs, default=str)

                if hasattr(node_class, "RETURN_TYPES"):
                    node_data["return_types"] = [str(t) for t in node_class.RETURN_TYPES]
            except Exception as e:
                print(f"[Catalog] Error inspecting node {node_id}: {e}")

            # 3. 定位文件路径，关联 Custom Node 包
            try:
                # 获取定义该类的文件路径
                node_file_path = sys.modules[node_class.__module__].__file__
                node_data["file_path"] = node_file_path

                # 判断是否在 custom_nodes 目录下
                if self.custom_nodes_path in node_file_path:
                    # 截取包名，例如 .../custom_nodes/ComfyUI-Manager/nodes.py -> ComfyUI-Manager
                    rel_path = os.path.relpath(node_file_path, self.custom_nodes_path)
                    pack_name = rel_path.split(os.sep)[0]
                    pack_dir = os.path.join(self.custom_nodes_path, pack_name)

                    node_data["pack_name"] = pack_name
                    node_data["github_url"] = self._get_git_info(pack_dir)
                    node_data["readme_snippet"] = self._get_readme(pack_dir)
                else:
                    node_data["readme_snippet"] = "Core ComfyUI Node"

            except Exception as e:
                pass  # 无法定位文件路径，保持默认

            scanned_data.append(node_data)

        return scanned_data
