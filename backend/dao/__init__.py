"""
数据访问层模块
"""
from .model_config_dao import get_model_config_dao, ModelConfigDAO

__all__ = [
    "get_model_config_dao",
    "ModelConfigDAO",
]