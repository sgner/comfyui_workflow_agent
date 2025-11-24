**其他语言版本: [English](README.md), [中文](README_CN.md).**

# comfyui-workflow-agent

一个为ComfyUI设计的智能代理，提供工作流生成、调试、优化和参数测试等功能。

## 主要问题和解决方案
| 问题         | 解决方案                                      |
| ---------- | ----------------------------------------- |
| JSON 太大太复杂 | 拆分为中间 IR + 增量生成                           |
| 节点依赖复杂     | 图结构管理（Node Graph）                         |
| 节点参数繁琐     | Node Registry + 自动补全                      |
| 模型难直接输出    | 只生成结构性指令（DSL）                             |
| 可维护性差      | 多 Agent 分层协作（Builder / Validator / Fixer） |

让大模型不要生成 JSON，而是生成“构建 JSON 的操作”。

用程序保证结构正确性，用多 Agent 协作保证任务完成度。

最终 JSON 只是结果，而不是生成目标。

## 流程
```text
用户输入: “帮我做一个图片去噪再放大的流程”
↓
LLM → 输出语义IR（中间步骤描述）
↓
Node Matcher → 匹配 ComfyUI 实际节点
↓
Graph Builder → 拼装成合法工作流JSON
↓
Validator → 校验并修正
↓
输出可导入 ComfyUI 的最终 JSON

```



## 许可证

MIT License
