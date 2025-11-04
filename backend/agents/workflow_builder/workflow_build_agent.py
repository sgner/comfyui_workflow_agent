from langchain.agents import create_agent as lca
from langchain.chat_models import init_chat_model
import json
from tool_pack import get_current_workflow
from custom_nodes.agent_nodepack.backend.service import get_model_config_service
from langgraph.checkpoint.memory import InMemorySaver


def create_agent(language="中文"):
    """创建workflow_builder_agent"""
    try:
        agent = lca(model=_create_head(), tools=_create_body(), system_prompt=_system_message_set(language),
                    checkpointer=_create_memory())
        return agent
        # return model
    except ValueError as e:
        print(f"Model configuration error: {e}")
        # 返回错误信息而不是None，以便调用者能够处理
        return {"error": "model_config_error", "message": str(e)}
    except Exception as e:
        print("Error creating agent:", e)
        return {"error": "agent_creation_error", "message": f"Failed to create agent: {str(e)}"}


def _create_head():
    # 从数据库获取模型配置
    model_config_service = get_model_config_service()
    langchain_config = model_config_service.get_model_for_langchain()

    # 根据提供商初始化模型
    provider = langchain_config.get('provider', 'openai')
    model_name = langchain_config['model']
    model = init_chat_model(
        model=model_name,
        temperature=langchain_config.get('temperature', 0.3),
        max_tokens=langchain_config.get('max_tokens', 4096),
        timeout=langchain_config.get('timeout', 60),
        max_retries=langchain_config.get('max_retries', 3),
        api_key=langchain_config.get('api_key', ''),
        base_url=langchain_config.get('base_url', ''),
    )
    # 根据不同的提供商设置不同的参数
    if provider == 'openai':
        # 添加OpenAI特定参数
        if 'top_p' in langchain_config:
            model.top_p = langchain_config['top_p']
        if 'frequency_penalty' in langchain_config:
            model.frequency_penalty = langchain_config['frequency_penalty']
        if 'presence_penalty' in langchain_config:
            model.presence_penalty = langchain_config['presence_penalty']

    elif provider == 'anthropic':
        # 添加Anthropic特定参数
        if 'top_p' in langchain_config:
            model.top_p = langchain_config['top_p']
        if 'top_k' in langchain_config:
            model.top_k = langchain_config['top_k']

    elif provider == 'azure':
        # 添加Azure特定参数
        if 'api_version' in langchain_config:
            model.api_version = langchain_config['api_version']
        if 'deployment_name' in langchain_config:
            model.deployment_name = langchain_config['deployment_name']

    print(f"Initialized model: {model_name} from provider: {provider}")
    return model


def _create_body():
    """定义agent可以使用的工具"""
    # TODO: 实现工具函数
    # 工具:
    # - get_current_workflow: 获取当前工作流
    # - remove_node: 移除节点
    # - update_workflow: 更新工作流
    # - get_node_info: 获取节点信息
    # - rollback_workflow: 回滚工作流
    tools = [get_current_workflow]
    return tools


def _create_memory():
    return InMemorySaver()


def _create_action():
    """定义agent的工作流"""
    # TODO: 实现工作流逻辑
    # 这里可以定义agent的工作流程，例如:
    # 1. 获取当前工作流
    # 2. 分析用户需求
    # 3. 根据专家经验修改工作流
    # 4. 验证工作流完整性
    # 5. 返回修改后的工作流
    pass


def _system_message_set(language):
    return """
                   你是专业的ComfyUI工作流改写代理，擅长根据用户的具体需求对现有工作流进行智能修改和优化。
                   如果在history_messages里有用户的历史对话，请根据历史对话中的语言来决定返回的语言。否则使用{}作为返回的语言。

                   ## 主要处理场景
                   {}
                   """.format(language, json.dumps(_get_rewrite_export_schema())) + """

                   你可以根据用户的需求，从上面的专家经验中选择一个或多个经验，并结合经验内容进行工作流改写。

                   ## 复杂工作流处理原则
                   复杂工作流实际上是多个简单的功能性工作流的组合。例如：文生图→抠图取主体→图生图生成背景。
                   处理时先将复杂工作流拆解为独立的功能模块，结合功能模块之间的参数传递(例如：文生图最终的图片输出可以接入到抠图取主体的图片输入），再确保模块间数据流转正确。

                   ## 操作原则
                   - **保持兼容性**：确保修改后的工作流与现有comfyui节点兼容
                   - **优化连接**：根据节点之间对应的传参类型和专家经验参考，正确设置节点间的输入输出连接
                   - **连线完整性**：修改工作流时必须确保所有节点的连线关系完整，不遗漏任何必要的输入输出连接，不能有额外的连线和节点
                     * 检查每个节点的必需输入是否已连接
                     * 对于未连接的必需输入，优先寻找类型匹配的现有节点输出进行连接
                     * 如果找不到合适的现有输出，则创建适当的输入节点（如常量节点、加载节点等）
                     * 确保连接的参数类型完全匹配，避免类型不兼容的连接
                   - **连线检查**：在添加、删除或修改节点时，务必检查所有相关的输入和输出连接是否正确配置
                   - **连接关系维护**：修改节点时必须保持原有的连接逻辑，确保数据流向正确
                   - **类型严格匹配**：在进行任何连线操作时，必须严格验证输入输出类型匹配
                     * 在修改连线前，先使用get_node_info()获取节点的完整输入输出规格信息
                     * 仔细检查源节点的输出类型(output_type)与目标节点的输入类型(input_type)
                     * 如果类型不匹配，寻找正确的源节点或添加类型转换节点
                   - **性能考虑**：避免不必要的重复节点，优化工作流执行效率
                   - **用户友好**：保持工作流结构清晰，便于用户理解和后续修改
                   - **错误处理**：在修改过程中检查潜在的配置错误，提供修正建议

                   **Tool Usage Guidelines:**
                       - get_current_workflow(): Get current workflow from checkpoint or session
                       - remove_node(): Use for incompatible or problematic nodes
                       - update_workflow(): Use to save your changes (ALWAYS call this after you have made changes), you MUST pass argument `workflow_data` containing the FULL workflow JSON (as a JSON object or a JSON string). Never call `update_workflow` without `workflow_data`.
                       - get_node_info(): Get detailed node information and verify input/output types before connecting


                   ## 响应格式
                   返回api格式的workflow

                   # ComfyUI 背景知识（Background Knowledge for ComfyUI）：
                   # - ComfyUI 是一个基于节点的图形化工作流系统，广泛用于 AI 图像生成、模型推理等场景。每个节点代表一个操作（如加载模型、生成图像、处理参数等），节点之间通过输入输出端口（socket）进行数据流转。
                   # - 节点类型丰富，包括模型加载、图像处理、参数设置、常量输入、类型转换等。节点的输入输出类型（如 image, latent, model, string, int, float 等）必须严格匹配，错误的类型连接会导致工作流运行失败。
                   # - 典型的 ComfyUI 工作流由多个节点组成，节点间通过连线（connections）形成有向无环图（DAG），数据从输入节点流向输出节点。每个节点的必需输入（required input）必须有有效连接，否则会报错。
                   # - ComfyUI 支持多种模型系统（如 SDXL, Flux, wan2.1, wan2.2,Qwen_image），每种系统有其特定的模型文件和组件，模型节点的参数需与本地模型文件严格匹配。
                   # - 常见问题包括：节点未连接、输入输出类型不匹配、缺少必需参数、模型文件缺失、节点结构不兼容等。改写工作流时需特别注意这些结构性和参数性问题。
                   # - 工作流的每次修改都应保证整体结构的连贯性和可运行性，避免引入新的结构性错误。

                   始终以用户的实际需求为导向，提供专业、准确、高效的工作流改写服务。
                   """


def _get_rewrite_export_schema():
    """获取工作流改写导出模式"""
    return {
        "文生图": {
            "description": "文本生成图像工作流",
            "required_nodes": ["CheckpointLoaderSimple", "CLIPTextEncode", "KSampler", "VAEDecode", "SaveImage"],
            "workflow_template": {
                "nodes": [
                    {
                        "class_type": "CheckpointLoaderSimple",
                        "inputs": {"ckpt_name": "model_name.ckpt"}
                    },
                    {
                        "class_type": "CLIPTextEncode",
                        "inputs": {"text": "positive prompt", "clip": ["CheckpointLoaderSimple", 1]}
                    },
                    {
                        "class_type": "CLIPTextEncode",
                        "inputs": {"text": "negative prompt", "clip": ["CheckpointLoaderSimple", 1]}
                    },
                    {
                        "class_type": "KSampler",
                        "inputs": {
                            "seed": 42,
                            "steps": 20,
                            "cfg": 7.0,
                            "sampler_name": "euler",
                            "scheduler": "normal",
                            "denoise": 1.0,
                            "model": ["CheckpointLoaderSimple", 0],
                            "positive": ["CLIPTextEncode", 0],
                            "negative": ["CLIPTextEncode", 1],
                            "latent_image": ["EmptyLatentImage", 0]
                        }
                    },
                    {
                        "class_type": "EmptyLatentImage",
                        "inputs": {"width": 512, "height": 512, "batch_size": 1}
                    },
                    {
                        "class_type": "VAEDecode",
                        "inputs": {"samples": ["KSampler", 0], "vae": ["CheckpointLoaderSimple", 2]}
                    },
                    {
                        "class_type": "SaveImage",
                        "inputs": {"filename_prefix": "output_", "images": ["VAEDecode", 0]}
                    }
                ]
            }
        },
        "图生图": {
            "description": "图像到图像转换工作流",
            "required_nodes": ["CheckpointLoaderSimple", "CLIPTextEncode", "LoadImage", "VAEEncode", "KSampler",
                               "VAEDecode", "SaveImage"],
            "workflow_template": {
                "nodes": [
                    {
                        "class_type": "CheckpointLoaderSimple",
                        "inputs": {"ckpt_name": "model_name.ckpt"}
                    },
                    {
                        "class_type": "CLIPTextEncode",
                        "inputs": {"text": "positive prompt", "clip": ["CheckpointLoaderSimple", 1]}
                    },
                    {
                        "class_type": "CLIPTextEncode",
                        "inputs": {"text": "negative prompt", "clip": ["CheckpointLoaderSimple", 1]}
                    },
                    {
                        "class_type": "LoadImage",
                        "inputs": {"image": "input.png"}
                    },
                    {
                        "class_type": "VAEEncode",
                        "inputs": {"pixels": ["LoadImage", 0], "vae": ["CheckpointLoaderSimple", 2]}
                    },
                    {
                        "class_type": "KSampler",
                        "inputs": {
                            "seed": 42,
                            "steps": 20,
                            "cfg": 7.0,
                            "sampler_name": "euler",
                            "scheduler": "normal",
                            "denoise": 0.75,
                            "model": ["CheckpointLoaderSimple", 0],
                            "positive": ["CLIPTextEncode", 0],
                            "negative": ["CLIPTextEncode", 1],
                            "latent_image": ["VAEEncode", 0]
                        }
                    },
                    {
                        "class_type": "VAEDecode",
                        "inputs": {"samples": ["KSampler", 0], "vae": ["CheckpointLoaderSimple", 2]}
                    },
                    {
                        "class_type": "SaveImage",
                        "inputs": {"filename_prefix": "output_", "images": ["VAEDecode", 0]}
                    }
                ]
            }
        },
        "图像放大": {
            "description": "图像放大工作流",
            "required_nodes": ["LoadImage", "UpscaleModelLoader", "ImageUpscaleWithModel", "VAEEncode", "KSampler",
                               "VAEDecode", "SaveImage"],
            "workflow_template": {
                "nodes": [
                    {
                        "class_type": "LoadImage",
                        "inputs": {"image": "input.png"}
                    },
                    {
                        "class_type": "UpscaleModelLoader",
                        "inputs": {"model_name": "4x_NMKD-Siax_200k.pth"}
                    },
                    {
                        "class_type": "ImageUpscaleWithModel",
                        "inputs": {"upscale_model": ["UpscaleModelLoader", 0], "image": ["LoadImage", 0]}
                    },
                    {
                        "class_type": "CheckpointLoaderSimple",
                        "inputs": {"ckpt_name": "model_name.ckpt"}
                    },
                    {
                        "class_type": "CLIPTextEncode",
                        "inputs": {"text": "positive prompt", "clip": ["CheckpointLoaderSimple", 1]}
                    },
                    {
                        "class_type": "CLIPTextEncode",
                        "inputs": {"text": "negative prompt", "clip": ["CheckpointLoaderSimple", 1]}
                    },
                    {
                        "class_type": "VAEEncode",
                        "inputs": {"pixels": ["ImageUpscaleWithModel", 0], "vae": ["CheckpointLoaderSimple", 2]}
                    },
                    {
                        "class_type": "KSampler",
                        "inputs": {
                            "seed": 42,
                            "steps": 20,
                            "cfg": 7.0,
                            "sampler_name": "euler",
                            "scheduler": "normal",
                            "denoise": 0.35,
                            "model": ["CheckpointLoaderSimple", 0],
                            "positive": ["CLIPTextEncode", 0],
                            "negative": ["CLIPTextEncode", 1],
                            "latent_image": ["VAEEncode", 0]
                        }
                    },
                    {
                        "class_type": "VAEDecode",
                        "inputs": {"samples": ["KSampler", 0], "vae": ["CheckpointLoaderSimple", 2]}
                    },
                    {
                        "class_type": "SaveImage",
                        "inputs": {"filename_prefix": "upscaled_", "images": ["VAEDecode", 0]}
                    }
                ]
            }
        },
    }
