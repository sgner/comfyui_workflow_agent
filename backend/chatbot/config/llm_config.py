from custom_nodes.comfyui_workflow_agent.backend.service import get_model_config_service
from langchain.chat_models import init_chat_model


def llm_config():
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
