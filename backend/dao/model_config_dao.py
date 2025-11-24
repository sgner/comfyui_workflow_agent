"""
模型配置数据访问对象
"""

import os
import sqlite3
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


class ModelConfigDAO:
    """模型配置数据访问对象"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化模型配置DAO

        Args:
            db_path: 数据库路径，如果为None则使用默认路径
        """
        if db_path is None:
            # 默认数据库路径
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "model_config.db"

        self.db_path = str(db_path)
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 检查是否需要迁移旧表结构
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='model_config'")
            table_exists = cursor.fetchone() is not None

            if table_exists:
                # 检查表结构是否需要迁移
                cursor.execute("PRAGMA table_info(model_config)")
                columns = [column[1] for column in cursor.fetchall()]

                # 如果旧表结构存在provider和model_name字段，则进行迁移
                if 'provider' in columns and 'model_name' in columns and 'model' not in columns:
                    print("正在迁移数据库表结构...")
                    # 创建新表结构
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS model_config_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            model TEXT NOT NULL UNIQUE,
                            api_key TEXT,
                            base_url TEXT,
                            temperature REAL DEFAULT 0.7,
                            max_tokens INTEGER DEFAULT 4096,
                            timeout INTEGER DEFAULT 60,
                            max_retries INTEGER DEFAULT 3,
                            is_active BOOLEAN DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')

                    # 迁移数据
                    cursor.execute('''
                        INSERT INTO model_config_new (model, api_key, base_url, temperature, max_tokens, timeout, max_retries, is_active, created_at)
                        SELECT provider || ':' || model_name, api_key, base_url, temperature, max_tokens, timeout, max_retries, is_active, created_at
                        FROM model_config
                    ''')

                    # 删除旧表并重命名新表
                    cursor.execute('DROP TABLE model_config')
                    cursor.execute('ALTER TABLE model_config_new RENAME TO model_config')

                    # 迁移model_params表
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS model_params_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            config_id INTEGER NOT NULL,
                            param_name TEXT NOT NULL,
                            param_value TEXT,
                            param_type TEXT DEFAULT 'string',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (config_id) REFERENCES model_config (id) ON DELETE CASCADE
                        )
                    ''')

                    # 迁移model_params数据
                    cursor.execute('''
                        INSERT INTO model_params_new (config_id, param_name, param_value, param_type, created_at)
                        SELECT config_id, param_name, param_value, param_type, created_at
                        FROM model_params
                    ''')

                    # 删除旧表并重命名新表
                    cursor.execute('DROP TABLE model_params')
                    cursor.execute('ALTER TABLE model_params_new RENAME TO model_params')

                    print("数据库表结构迁移完成")

            # 创建模型配置表（新结构）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL UNIQUE,
                    api_key TEXT,
                    base_url TEXT,
                    temperature REAL DEFAULT 0.7,
                    max_tokens INTEGER DEFAULT 4096,
                    timeout INTEGER DEFAULT 60,
                    max_retries INTEGER DEFAULT 3,
                    is_active BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 创建模型参数表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_params (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_id INTEGER NOT NULL,
                    param_name TEXT NOT NULL,
                    param_value TEXT,
                    param_type TEXT DEFAULT 'string',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (config_id) REFERENCES model_config (id) ON DELETE CASCADE
                )
            ''')

            conn.commit()

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

    def add_model_config(self, config: Dict[str, Any]) -> int:
        """
        添加模型配置

        Args:
            config: 模型配置字典，应包含model字段（格式为"provider:model_name"）

        Returns:
            新增配置的ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO model_config (
                    model, api_key, base_url, temperature,
                    max_tokens, timeout, max_retries, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                config.get('model'),
                config.get('api_key'),
                config.get('base_url'),
                config.get('temperature', 0.7),
                config.get('max_tokens', 4096),
                config.get('timeout', 60),
                config.get('max_retries', 3),
                config.get('is_active', False)
            ))

            config_id = cursor.lastrowid

            # 添加额外参数
            if 'extra_params' in config:
                for param_name, param_value in config['extra_params'].items():
                    param_type = type(param_value).__name__
                    cursor.execute('''
                        INSERT INTO model_params (config_id, param_name, param_value, param_type)
                        VALUES (?, ?, ?, ?)
                    ''', (config_id, param_name, json.dumps(param_value), param_type))

            conn.commit()
            return config_id

    def get_model_config(self, model: str) -> Optional[Dict[str, Any]]:
        """
        获取模型配置

        Args:
            model: 模型标识，格式为"provider:model_name"

        Returns:
            模型配置字典，如果不存在则返回None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM model_config
                WHERE model = ?
            ''', (model,))

            row = cursor.fetchone()
            if not row:
                return None

            config = dict(row)

            # 解析model字段，添加provider和model_name字段以保持兼容性
            provider, model_name = self._parse_model(config['model'])
            config['provider'] = provider
            config['model_name'] = model_name

            # 获取额外参数
            cursor.execute('''
                SELECT param_name, param_value, param_type
                FROM model_params
                WHERE config_id = ?
            ''', (config['id'],))

            extra_params = {}
            for param_row in cursor.fetchall():
                param_name = param_row['param_name']
                param_value = json.loads(param_row['param_value'])
                extra_params[param_name] = param_value

            config['extra_params'] = extra_params

            # 移除不需要的字段
            config.pop('id', None)

            return config

    def get_active_model_config(self) -> Optional[Dict[str, Any]]:
        """
        获取当前激活的模型配置

        Returns:
            当前激活的模型配置字典，如果没有则返回None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM model_config WHERE is_active = 1
            ''')

            row = cursor.fetchone()
            if not row:
                return None

            config = dict(row)

            # 解析model字段，添加provider和model_name字段以保持兼容性
            provider, model_name = self._parse_model(config['model'])
            config['provider'] = provider
            config['model_name'] = model_name

            # 获取额外参数
            cursor.execute('''
                SELECT param_name, param_value, param_type
                FROM model_params
                WHERE config_id = ?
            ''', (config['id'],))

            extra_params = {}
            for param_row in cursor.fetchall():
                param_name = param_row['param_name']
                param_value = json.loads(param_row['param_value'])
                extra_params[param_name] = param_value

            config['extra_params'] = extra_params

            # 移除不需要的字段
            config.pop('id', None)

            return config

    def update_model_config(self, model: str, config: Dict[str, Any]) -> bool:
        """
        更新模型配置

        Args:
            model: 模型标识，格式为"provider:model_name"
            config: 新的配置字典

        Returns:
            是否更新成功
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 更新主配置
            cursor.execute('''
                UPDATE model_config
                SET api_key = ?, base_url = ?, temperature = ?,
                    max_tokens = ?, timeout = ?, max_retries = ?,
                    is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE model = ?
            ''', (
                config.get('api_key'),
                config.get('base_url'),
                config.get('temperature', 0.7),
                config.get('max_tokens', 4096),
                config.get('timeout', 60),
                config.get('max_retries', 3),
                config.get('is_active', False),
                model
            ))

            if cursor.rowcount == 0:
                return False

            # 获取配置ID
            cursor.execute('''
                SELECT id FROM model_config
                WHERE model = ?
            ''', (model,))

            config_id = cursor.fetchone()[0]

            # 删除旧的额外参数
            cursor.execute('''
                DELETE FROM model_params WHERE config_id = ?
            ''', (config_id,))

            # 添加新的额外参数
            if 'extra_params' in config:
                for param_name, param_value in config['extra_params'].items():
                    param_type = type(param_value).__name__
                    cursor.execute('''
                        INSERT INTO model_params (config_id, param_name, param_value, param_type)
                        VALUES (?, ?, ?, ?)
                    ''', (config_id, param_name, json.dumps(param_value), param_type))

            conn.commit()
            return True

    def set_active_model(self, model: str) -> bool:
        """
        设置激活的模型

        Args:
            model: 模型标识，格式为"provider:model_name"

        Returns:
            是否设置成功
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 先取消所有模型的激活状态
            cursor.execute('''
                UPDATE model_config SET is_active = 0
            ''')

            # 设置指定模型为激活状态
            cursor.execute('''
                UPDATE model_config
                SET is_active = 1, updated_at = CURRENT_TIMESTAMP
                WHERE model = ?
            ''', (model,))

            conn.commit()
            return cursor.rowcount > 0

    def list_model_configs(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出模型配置

        Args:
            provider: 提供商名称，如果为None则列出所有提供商的配置

        Returns:
            模型配置列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if provider:
                # 查询指定provider的所有模型
                cursor.execute('''
                    SELECT * FROM model_config WHERE model LIKE ?
                ''', (f"{provider}:%",))
            else:
                cursor.execute('''
                    SELECT * FROM model_config
                ''')

            configs = []
            for row in cursor.fetchall():
                config = dict(row)

                # 解析model字段，添加provider和model_name字段以保持兼容性
                model_provider, model_name = self._parse_model(config['model'])
                config['provider'] = model_provider
                config['model_name'] = model_name

                # 获取额外参数
                cursor.execute('''
                    SELECT param_name, param_value, param_type
                    FROM model_params
                    WHERE config_id = ?
                ''', (config['id'],))

                extra_params = {}
                for param_row in cursor.fetchall():
                    param_name = param_row['param_name']
                    param_value = json.loads(param_row['param_value'])
                    extra_params[param_name] = param_value

                config['extra_params'] = extra_params

                # 移除不需要的字段
                config.pop('id', None)

                configs.append(config)

            return configs

    def delete_model_config(self, model: str) -> bool:
        """
        删除模型配置

        Args:
            model: 模型标识，格式为"provider:model_name"

        Returns:
            是否删除成功
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM model_config
                WHERE model = ?
            ''', (model,))

            conn.commit()
            return cursor.rowcount > 0

    def init_default_configs(self):
        """初始化默认配置"""
        # OpenAI 默认配置
        openai_config = {
            'model': 'openai:gpt-3.5-turbo',
            'api_key': '',
            'base_url': 'https://api.openai.com/v1',
            'temperature': 0.7,
            'max_tokens': 4096,
            'timeout': 60,
            'max_retries': 3,
            'is_active': True,
            'extra_params': {
                'top_p': 1.0,
                'frequency_penalty': 0.0,
                'presence_penalty': 0.0
            }
        }

        # Anthropic 默认配置
        anthropic_config = {
            'model': 'anthropic:claude-3-sonnet-20240229',
            'api_key': '',
            'base_url': 'https://api.anthropic.com',
            'temperature': 0.7,
            'max_tokens': 4096,
            'timeout': 60,
            'max_retries': 3,
            'is_active': False,
            'extra_params': {
                'top_p': 1.0,
                'top_k': 40
            }
        }

        # Azure OpenAI 默认配置
        azure_config = {
            'model': 'azure:gpt-35-turbo',
            'api_key': '',
            'base_url': 'https://your-resource.openai.azure.com/',
            'temperature': 0.7,
            'max_tokens': 4096,
            'timeout': 60,
            'max_retries': 3,
            'is_active': False,
            'extra_params': {
                'api_version': '2023-12-01-preview',
                'deployment_name': 'gpt-35-turbo'
            }
        }

        # 检查是否已有配置
        if not self.get_model_config('openai:gpt-3.5-turbo'):
            self.add_model_config(openai_config)

        if not self.get_model_config('anthropic:claude-3-sonnet-20240229'):
            self.add_model_config(anthropic_config)

        if not self.get_model_config('azure:gpt-35-turbo'):
            self.add_model_config(azure_config)


# 全局实例
_model_config_dao = None


def get_model_config_dao() -> ModelConfigDAO:
    """获取模型配置DAO实例"""
    global _model_config_dao
    if _model_config_dao is None:
        _model_config_dao = ModelConfigDAO()
        _model_config_dao.init_default_configs()
    return _model_config_dao
