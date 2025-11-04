"""
模型配置服务
"""

import os
from typing import Dict, List, Optional, Any, Tuple
from custom_nodes.agent_nodepack.backend.dao.model_config_dao import get_model_config_dao


class ModelConfigService:
    """模型配置服务"""

    def __init__(self):
        self.dao = get_model_config_dao()
        self._env_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')

    def _read_env_file(self) -> Dict[str, str]:
        """
        读取.env文件内容

        Returns:
            环境变量字典
        """
        env_vars = {}
        try:
            if os.path.exists(self._env_file_path):
                with open(self._env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
        except Exception as e:
            print(f"Error reading .env file: {e}")

        return env_vars

    def _get_config_from_env(self, provider: str) -> Dict[str, str]:
        """
        从环境变量和.env文件获取配置

        Args:
            provider: 提供商名称

        Returns:
            包含api_key和base_url的配置字典
        """
        config = {}

        # 读取.env文件
        env_vars = self._read_env_file()

        # 根据提供商确定环境变量名
        if provider.lower() == 'openai':
            api_key_env = 'OPENAI_API_KEY'
            base_url_env = 'OPENAI_BASE_URL'
        elif provider.lower() == 'anthropic':
            api_key_env = 'ANTHROPIC_API_KEY'
            base_url_env = 'ANTHROPIC_BASE_URL'
        elif provider.lower() == 'azure':
            api_key_env = 'AZURE_OPENAI_API_KEY'
            base_url_env = 'AZURE_OPENAI_ENDPOINT'
        else:
            return config

        # 优先从环境变量获取，其次从.env文件获取
        api_key = os.environ.get(api_key_env) or env_vars.get(api_key_env)
        base_url = os.environ.get(base_url_env) or env_vars.get(base_url_env)

        if api_key:
            config['api_key'] = api_key
        if base_url:
            config['base_url'] = base_url

        return config

    def _parse_model(self, model: str) -> Tuple[str, str]:
        """
        解析model字段，提取provider和model_name
        
        Args:
            model: 格式为"provider:model_name"的字符串
            
        Returns:
            (provider, model_name) 元组
        """
        if ':' in model:
            parts = model.split(':', 1)
            return parts[0], parts[1]
        else:
            # 如果没有冒号，默认为openai
            return 'openai', model

    def get_active_model_config(self) -> Optional[Dict[str, Any]]:
        """
        获取当前激活的模型配置

        Returns:
            当前激活的模型配置字典，如果没有则返回None
        """
        return self.dao.get_active_model_config()

    def get_model_config(self, model: str) -> Optional[Dict[str, Any]]:
        """
        获取指定模型配置

        Args:
            model: 模型标识，格式为"provider:model_name"

        Returns:
            模型配置字典，如果不存在则返回None
        """
        return self.dao.get_model_config(model)

    def set_active_model(self, model: str) -> bool:
        """
        设置激活的模型

        Args:
            model: 模型标识，格式为"provider:model_name"

        Returns:
            是否设置成功
        """
        return self.dao.set_active_model(model)

    def list_model_configs(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出模型配置

        Args:
            provider: 提供商名称，如果为None则列出所有提供商的配置

        Returns:
            模型配置列表
        """
        return self.dao.list_model_configs(provider)

    def update_model_config(self, model: str, config: Dict[str, Any]) -> bool:
        """
        更新模型配置

        Args:
            model: 模型标识，格式为"provider:model_name"
            config: 新的配置字典

        Returns:
            是否更新成功
        """
        return self.dao.update_model_config(model, config)

    def add_model_config(self, config: Dict[str, Any]) -> int:
        """
        添加模型配置

        Args:
            config: 模型配置字典，应包含model字段（格式为"provider:model_name"）

        Returns:
            新增配置的ID
        """
        return self.dao.add_model_config(config)

    def delete_model_config(self, model: str) -> bool:
        """
        删除模型配置

        Args:
            model: 模型标识，格式为"provider:model_name"

        Returns:
            是否删除成功
        """
        return self.dao.delete_model_config(model)

    def updateorset(self, model: str, config: Dict[str, Any]) -> bool:
        """
        更新或设置模型配置

        Args:
            model: 模型标识，格式为"provider:model_name"
            config: 配置字典

        Returns:
            是否操作成功
        """
        # 检查配置是否已存在
        existing_config = self.get_model_config(model)

        if existing_config:
            # 如果配置存在，则更新
            return self.update_model_config(model, config)
        else:
            # 如果配置不存在，则添加新配置
            # 确保配置中包含model字段
            if 'model' not in config:
                config['model'] = model

            try:
                self.add_model_config(config)
                return True
            except Exception as e:
                print(f"Error adding model config: {e}")
                return False

    def get_model_for_langchain(self) -> Dict[str, Any]:
        """
        获取适合LangChain使用的模型配置

        Returns:
            适合LangChain使用的模型配置字典

        Raises:
            ValueError: 当没有找到任何有效的模型配置时
        """
        config = self.get_active_model_config()
        default_model = 'openai:gpt-3.5-turbo'  # 默认模型

        if not config:
            # 如果没有激活的配置，使用默认的OpenAI配置
            config = self.get_model_config(default_model)
            if not config:
                # 创建一个基本配置
                config = {
                    'model': default_model,
                    'temperature': 0.7,
                    'max_tokens': 4096,
                    'timeout': 60,
                    'max_retries': 3,
                    'extra_params': {}
                }
                self.updateorset(default_model, config)
        else:
            # 检查数据库配置中是否有api_key和base_url
            if not config.get('api_key') or not config.get('base_url'):
                missing_configs = []
                if not config.get('api_key'):
                    missing_configs.append('api_key')
                if not config.get('base_url'):
                    missing_configs.append('base_url')
                raise ValueError(
                    f"缺失配置项: {', '.join(missing_configs)}. 你必须先进行配置才可以使用")

        # 转换为LangChain需要的格式
        provider, model_name = self._parse_model(config['model'])
        langchain_config = {
            'model': model_name,
            'temperature': config.get('temperature', 0.7),
            'max_tokens': config.get('max_tokens', 4096),
            'timeout': config.get('timeout', 60),
            'max_retries': config.get('max_retries', 3),
            'provider': provider
        }

        # 根据提供商添加特定参数
        if provider == 'openai':
            langchain_config['api_key'] = config.get('api_key', '')
            langchain_config['base_url'] = config.get('base_url', 'https://api.openai.com/v1')

            # 添加额外参数
            extra_params = config.get('extra_params', {})
            if 'top_p' in extra_params:
                langchain_config['top_p'] = extra_params['top_p']
            if 'frequency_penalty' in extra_params:
                langchain_config['frequency_penalty'] = extra_params['frequency_penalty']
            if 'presence_penalty' in extra_params:
                langchain_config['presence_penalty'] = extra_params['presence_penalty']

        elif provider == 'anthropic':
            langchain_config['api_key'] = config.get('api_key', '')
            langchain_config['base_url'] = config.get('base_url', 'https://api.anthropic.com')

            # 添加额外参数
            extra_params = config.get('extra_params', {})
            if 'top_p' in extra_params:
                langchain_config['top_p'] = extra_params['top_p']
            if 'top_k' in extra_params:
                langchain_config['top_k'] = extra_params['top_k']

        elif provider == 'azure':
            langchain_config['api_key'] = config.get('api_key', '')
            langchain_config['azure_endpoint'] = config.get('base_url', '')

            # 添加额外参数
            extra_params = config.get('extra_params', {})
            if 'api_version' in extra_params:
                langchain_config['api_version'] = extra_params['api_version']
            if 'deployment_name' in extra_params:
                langchain_config['deployment_name'] = extra_params['deployment_name']

        return langchain_config


# 全局实例
_model_config_service = None


def get_model_config_service() -> ModelConfigService:
    """获取模型配置服务实例"""
    global _model_config_service
    if _model_config_service is None:
        _model_config_service = ModelConfigService()
    return _model_config_service
