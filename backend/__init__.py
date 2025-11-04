# import os
# import sys
# import folder_paths
# import aiohttp
# from aiohttp import web
# from pathlib import Path
# import json
# import logging
# import traceback
#
# # 设置日志
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
# # 版本信息
# __version__ = "2.0.0"
#
# # ComfyUI Web服务器实例
# web_root = None
#
# # API路由
# routes = web.RouteTableDef()
#
# # 获取插件目录
# comfyui_base_dir = Path(folder_paths.__file__).parent
# plugin_dir = Path(__file__).parent.parent
# web_dir = plugin_dir / "web"
# ui_dir = plugin_dir / "ui"
#
# # 确保目录存在
# os.makedirs(web_dir, exist_ok=True)
# os.makedirs(ui_dir, exist_ok=True)
#
# # 初始化数据库和配置
# def init_config():
#     """初始化配置"""
#     try:
#         # 创建配置目录
#         config_dir = plugin_dir / "config"
#         os.makedirs(config_dir, exist_ok=True)
#
#         # 创建数据库目录
#         db_dir = plugin_dir / "db"
#         os.makedirs(db_dir, exist_ok=True)
#
#         # 创建日志目录
#         log_dir = plugin_dir / "logs"
#         os.makedirs(log_dir, exist_ok=True)
#
#         logger.info("配置初始化完成")
#         return True
#     except Exception as e:
#         logger.error(f"配置初始化失败: {str(e)}")
#         return False
#
# # 初始化API路由
# def init_api():
#     """初始化API路由"""
#     try:
#         # 导入控制器模块
#         from .controller import workflow_api, node_catalog_api, conversation_api, llm_api
#
#         # 注册路由
#         app = web.Application()
#         app.add_routes(workflow_api.routes)
#         app.add_routes(node_catalog_api.routes)
#         app.add_routes(conversation_api.routes)
#         app.add_routes(llm_api.routes)
#
#         # 静态文件路由
#         app.router.add_static('/web/', str(web_dir))
#         app.router.add_static('/ui/', str(ui_dir))
#
#         logger.info("API路由初始化完成")
#         return app
#     except Exception as e:
#         logger.error(f"API路由初始化失败: {str(e)}")
#         logger.error(traceback.format_exc())
#         return None
#
# # 注册ComfyUI扩展
# def register_extension():
#     """注册ComfyUI扩展"""
#     try:
#         # 注册节点
#         from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
#
#         # 注册前端资源
#         if web_root:
#             # 添加前端路由
#             web_root.add_route("GET", "/agent_nodepack", lambda request: web.FileResponse(ui_dir / "index.html"))
#             web_root.add_route("GET", "/agent_nodepack/{path:.*}", lambda request: web.FileResponse(ui_dir / request.match_info["path"]))
#
#         logger.info("ComfyUI扩展注册完成")
#         return True
#     except Exception as e:
#         logger.error(f"ComfyUI扩展注册失败: {str(e)}")
#         logger.error(traceback.format_exc())
#         return False
#
# # 启动服务
# def start_server():
#     """启动服务"""
#     try:
#         # 初始化配置
#         if not init_config():
#             return False
#
#         # 初始化API
#         app = init_api()
#         if not app:
#             return False
#
#         # 注册扩展
#         if not register_extension():
#             return False
#
#         # 启动API服务器
#         runner = web.AppRunner(app)
#         await runner.setup()
#         site = web.TCPSite(runner, 'localhost', 8188)
#         await site.start()
#
#         logger.info("Agent NodePack服务启动成功")
#         return True
#     except Exception as e:
#         logger.error(f"Agent NodePack服务启动失败: {str(e)}")
#         logger.error(traceback.format_exc())
#         return False
#
# # ComfyUI入口点
# async def start():
#     """ComfyUI入口点"""
#     global web_root
#
#     # 获取ComfyUI Web服务器实例
#     try:
#         import server
#         web_root = server.web_root
#     except:
#         logger.warning("无法获取ComfyUI Web服务器实例")
#
#     # 启动服务
#     await start_server()
#
# # 节点映射
# NODE_CLASS_MAPPINGS = {}
# NODE_DISPLAY_NAME_MAPPINGS = {}
#
# # 导出
# __all__ = [
#     "NODE_CLASS_MAPPINGS",
#     "NODE_DISPLAY_NAME_MAPPINGS",
#     "start"
# ]
