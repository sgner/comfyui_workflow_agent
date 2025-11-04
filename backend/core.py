import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 设置日志
logger = logging.getLogger(__name__)

# 获取插件目录
plugin_dir = Path(__file__).parent.parent
config_dir = plugin_dir / "config"
db_dir = plugin_dir / "db"

# 默认配置
DEFAULT_CONFIG = {
    "api": {
        "host": "localhost",
        "port": 8188,
        "prefix": "/agent_nodepack"
    },
    "llm": {
        "provider": "openai",
        "model": "gpt-4",
        "api_key": "",
        "base_url": "https://api.openai.com/v1",
        "timeout": 30
    },
    "workflow": {
        "max_nodes": 100,
        "max_connections": 200,
        "auto_save": True,
        "auto_backup": True
    },
    "node_catalog": {
        "auto_index": True,
        "index_interval": 3600,  # 1小时
        "use_fts": True
    },
    "logging": {
        "level": "INFO",
        "max_file_size": "10MB",
        "backup_count": 5
    }
}

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.config_file = config_dir / "config.json"
        self.config = DEFAULT_CONFIG.copy()
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并配置，保留默认值
                    self._merge_config(self.config, loaded_config)
                    logger.info("配置加载成功")
            else:
                self.save_config()
                logger.info("使用默认配置并已保存")
        except Exception as e:
            logger.error(f"配置加载失败: {str(e)}")
    
    def save_config(self):
        """保存配置"""
        try:
            os.makedirs(config_dir, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("配置保存成功")
        except Exception as e:
            logger.error(f"配置保存失败: {str(e)}")
    
    def _merge_config(self, default: Dict[str, Any], loaded: Dict[str, Any]):
        """递归合并配置"""
        for key, value in loaded.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_config(default[key], value)
            else:
                default[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()

# 全局配置管理器
config_manager = ConfigManager()

def get_config(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return config_manager.get(key, default)

def set_config(key: str, value: Any):
    """设置配置值"""
    config_manager.set(key, value)

# 环境变量处理
def load_env_vars():
    """加载环境变量"""
    env_mappings = {
        "AGENT_NODEPACK_API_HOST": "api.host",
        "AGENT_NODEPACK_API_PORT": "api.port",
        "AGENT_NODEPACK_LLM_PROVIDER": "llm.provider",
        "AGENT_NODEPACK_LLM_MODEL": "llm.model",
        "AGENT_NODEPACK_LLM_API_KEY": "llm.api_key",
        "AGENT_NODEPACK_LLM_BASE_URL": "llm.base_url",
        "AGENT_NODEPACK_LOG_LEVEL": "logging.level"
    }
    
    for env_var, config_key in env_mappings.items():
        value = os.getenv(env_var)
        if value is not None:
            # 类型转换
            if config_key.endswith('.port'):
                value = int(value)
            set_config(config_key, value)
            logger.info(f"从环境变量加载配置: {config_key} = {value}")

# 初始化环境变量
load_env_vars()

# 数据库配置
def get_db_path(db_name: str) -> str:
    """获取数据库路径"""
    return str(db_dir / f"{db_name}.db")

# 日志配置
def setup_logging():
    """设置日志"""
    log_level = get_config("logging.level", "INFO")
    log_dir = plugin_dir / "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 文件处理器
    file_handler = logging.FileHandler(
        log_dir / "agent_nodepack.log",
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # 设置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    logger.info("日志系统初始化完成")

# 初始化日志系统
setup_logging()