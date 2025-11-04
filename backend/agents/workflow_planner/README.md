## 工作流规划助手
### 1. 主要功能
把输入的自然语言转为“工作流规划描述（Workflow Plan）而不是直接输出 JSON工作流。
例如，用户：帮我把图片放大两倍并去噪。LLM 输出：
```json
[
  {"goal": "放大图片", "node_type": "ImageUpscale", "scale": 2.0},
  {"goal": "去噪", "node_type": "ImageDenoise", "strength": 0.4}
]
 这层输出可以称为中间表示（Intermediate Representation, IR）。
 上述输出由大模型进行分析，得到了两种comfyui节点的信息分别是ImageUpscale和ImageDenoise
 那么就要将这些信息交给NodeMatherAgent,让它根据这个IR去节点库里匹配节点。
```

### 2. 工作流程
1. 分析自然语言得到IR
2. 通知NodeMatcherAgent根据IR匹配节点
3. 接收来自ValidatorAgent的信息分析得到IR

### 3. A2A消息格式：
```json
{
  "from": "PlannerAgent",
  "to": "NodeMatcherAgent",
  "intent": "MATCH_NODES",
  "task_id": "wf_2025_001",
  "payload": {
    "semantic_plan": [
  {"goal": "放大图片", "node_type": "ImageUpscale", "scale": 2.0},
  {"goal": "去噪", "node_type": "ImageDenoise", "strength": 0.4}
]
  },
  "metadata": {
    "timestamp": "2025-11-03T14:31:00Z",
    "trace_id": "abc123",
    "priority": "high"
  }
}
```

### 4. 交互流程
```mermaid
                                                                                  
                                                                            |
User ──► PlannerAgent ──► NodeMatcherAgent ──► BuilderAgent ──► ValidatorAgent ──► Output
             │                   │                    │                     │
             │                   │                    │                     └──▶ (valid JSON)
             │                   │                    └──▶ (workflow graph)
             │                   └──▶ (node mapping)
             └──▶ (semantic IR)

```
