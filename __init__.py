# import os
# import sys
# import json
# import logging
# import threading
# import time
# from typing import Dict, Any, List, Optional, Union
#
# # 添加插件根目录到Python路径
# plugin_dir = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(plugin_dir)
#
# try:
#     from .workflow_agent_nodes import NODE_CLASS_MAPPINGS as AGENT_NODE_MAPPINGS
#     from .agent_nodes import NODE_CLASS_MAPPINGS as NEW_AGENT_NODE_MAPPINGS
#     from .simple_nodes import NODE_CLASS_MAPPINGS as SIMPLE_NODE_MAPPINGS
#     from .app import app, socketio, init_app
#     from .core.config import get_config
#     from .agents.agent_factory import AgentFactory
# except ImportError as e:
#     print(f"导入模块失败: {str(e)}")
#     # 在ComfyUI环境中，可能需要不同的导入方式
#     pass
#
# # 配置日志
# logger = logging.getLogger(__name__)
#
# NODE_CLASS_MAPPINGS = {}
# NODE_CLASS_MAPPINGS.update(AGENT_NODE_MAPPINGS)
# NODE_CLASS_MAPPINGS.update(NEW_AGENT_NODE_MAPPINGS)
# NODE_CLASS_MAPPINGS.update(SIMPLE_NODE_MAPPINGS)
#
# # 全局变量
# web_server_thread = None
# web_server_running = False
#
# def start_web_server():
#     """启动Web服务器"""
#     global web_server_thread, web_server_running
#
#     if web_server_running:
#         return
#
#     def run_server():
#         try:
#             from .app import run_server
#             run_server(host='127.0.0.1', port=5000, debug=False)
#         except Exception as e:
#             logger.error(f"运行Web服务器失败: {str(e)}")
#
#     web_server_thread = threading.Thread(target=run_server, daemon=True)
#     web_server_thread.start()
#     web_server_running = True
#     logger.info("Web服务器已启动")
#
# # 插件初始化
# def init_plugin():
#     """初始化插件"""
#     try:
#         # 初始化配置
#         from .core.config import init_config
#         init_config()
#
#         # 初始化数据库
#         from .core.database import init_database
#         init_database()
#
#         # 启动Web服务器
#         start_web_server()
#
#         logger.info("Agent Node Pack插件初始化完成")
#
#     except Exception as e:
#         logger.error(f"插件初始化失败: {str(e)}")
#
# # ComfyUI插件入口
# WEB_DIRECTORY = "./frontend"
#
# # 在ComfyUI加载时初始化插件
# init_plugin()
#
# __all__ = ["NODE_CLASS_MAPPINGS"]
