class KnowledgeBaseFormatter:
    @staticmethod
    def to_markdown(scanned_data):
        """将扫描结果转换为 Markdown 列表"""
        md_docs = []

        for node in scanned_data:
            # 构建富含语义的文本块
            content = f"""
# Node: {node['display_name']} (ID: {node['id']})
- **Category**: {node['category']}
- **Package**: {node['pack_name']}
- **Github**: {node['github_url'] or 'N/A'}

## Inputs
{node['input_types']}

## Outputs
{', '.join(node['return_types'])}

## Description
{node['description']}

## Context (From README)
{node['readme_snippet'][:1000]}... (truncated)
"""
            content = content.strip()

            metadata = {
                "node_id": node['id'],
                "pack_name": node['pack_name'],
                "category": node['category']
            }

            md_docs.append({"content": content, "metadata": metadata})

        return md_docs
