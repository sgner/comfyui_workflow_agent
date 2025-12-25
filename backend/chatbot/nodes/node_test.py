import re
#
from llm import intent_node
from custom_nodes.comfyui_workflow_agent.backend.chatbot.nodes.llm import router
from custom_nodes.comfyui_workflow_agent.backend.chatbot.state import BaseState

if __name__ == '__main__':
    state: BaseState = {
        "messages": [],
        "user_input": "我需要一个使用z-image-turbo_q6的基本工作流",
        "current_workflow": ''' ''',
        "intent_result": {},
        "retrieved_knowledge": []
    }

    print(router(state))

# import json
#
#
# class ComfyUIParser:
#     def __init__(self):
#         # 定义提取规则
#         self.rules = {
#             # === 模型类 ===
#             "checkpoints": {
#                 "class_types": ["CheckpointLoaderSimple", "CheckpointLoader", "Load Checkpoint", "UNETLoader",
#                                 "SeedVR2LoadDiTModel"],
#                 "fields": ["ckpt_name", "unet_name", "model"],
#                 "widget_index": 0
#             },
#             "loras": {
#                 "class_types": ["LoraLoader", "LoraLoader|pysssss", "CR LoRA Stack", "LoraLoaderModelOnly"],
#                 "fields": ["lora_name"],
#                 "widget_index": 0
#             },
#             "vaes": {
#                 "class_types": ["VAELoader", "SeedVR2LoadVAEModel"],
#                 "fields": ["vae_name", "model"],
#                 "widget_index": 0
#             },
#             "controlnets": {
#                 "class_types": ["ControlNetLoader", "ControlNetLoaderAdvanced"],
#                 "fields": ["control_net_name"],
#                 "widget_index": 0
#             },
#             "ip_adapters": {
#                 "class_types": ["IPAdapterLoader", "IPAdapterModelLoader"],
#                 "fields": ["ipadapter_file"],
#                 "widget_index": 0
#             },
#             # === 核心输入 ===
#             "input_images": {
#                 "class_types": ["LoadImage", "LoadImageMask"],
#                 "fields": ["image"],
#                 "widget_index": 0
#             },
#             # === 提示词 (静态文本) ===
#             "prompts": {
#                 "class_types": ["CLIPTextEncode", "CLIPTextEncodeSDXL", "ShowText|pysssss", "Text box"],
#                 "fields": ["text"],
#                 "widget_index": 0  # 或者是 inputs['text']
#             },
#             # === 分辨率设置 (EmptyLatent) ===
#             "latent_size": {
#                 "class_types": ["EmptyLatentImage", "EmptyLatentImageSDXL"],
#                 "fields": ["width", "height", "batch_size"],
#                 "widget_index": [0, 1, 2]  # 这里需要特殊处理，因为有多个值
#             },
#             # === 参数控制 (Int/Float) ===
#             # 在你的工作流中，ImpactInt 控制了分辨率，PrimitiveFloat 控制了降噪
#             "parameters": {
#                 "class_types": ["ImpactInt", "PrimitiveFloat", "PrimitiveInt"],
#                 "fields": ["value"],
#                 "widget_index": 0
#             }
#         }
#
#     def _clean_json_string(self, json_str):
#         if not json_str: return "{}"
#         return json_str.strip()
#
#     def _get_node_value(self, node, fields, widget_index=0):
#         """提取值的通用方法"""
#         inputs = node.get("inputs")
#         widgets = node.get("widgets_values")
#
#         # 1. 尝试从 inputs (API格式) 提取
#         if inputs and isinstance(inputs, dict):
#             # 特殊处理：如果 fields 是列表且 widget_index 也是列表（用于提取多个值，如 width/height）
#             if isinstance(widget_index, list):
#                 result = {}
#                 for idx, field in enumerate(fields):
#                     if field in inputs:
#                         result[field] = inputs[field]
#                 return result if result else None
#
#             # 常规单值提取
#             for field in fields:
#                 if field in inputs:
#                     val = inputs[field]
#                     if isinstance(val, list): return None  # 忽略连线引用
#                     return val
#
#         # 2. 尝试从 widgets (UI格式) 提取
#         if widgets and isinstance(widgets, list):
#             # 特殊处理：多值提取 (如 EmptyLatentImage 的 width, height, batch)
#             if isinstance(widget_index, list):
#                 result = {}
#                 for i, idx in enumerate(widget_index):
#                     if len(widgets) > idx:
#                         field_name = fields[i] if i < len(fields) else f"param_{i}"
#                         result[field_name] = widgets[idx]
#                 return result if result else None
#
#             # 常规单值提取
#             if len(widgets) > widget_index:
#                 val = widgets[widget_index]
#                 if isinstance(val, (str, int, float)):
#                     return val
#         return None
#
#     def _parse_sampler(self, node, class_type):
#         """解析采样器 (保持不变)"""
#         sampler_info = {}
#         if "KSampler" in class_type:
#             inputs = node.get("inputs")
#             widgets = node.get("widgets_values", [])
#
#             if inputs and isinstance(inputs, dict):
#                 sampler_info = {
#                     "seed": inputs.get("seed"),
#                     "steps": inputs.get("steps"),
#                     "cfg": inputs.get("cfg"),
#                     "sampler_name": inputs.get("sampler_name"),
#                     "scheduler": inputs.get("scheduler"),
#                     "denoise": inputs.get("denoise")
#                 }
#             elif widgets and isinstance(widgets, list) and len(widgets) >= 7:
#                 try:
#                     sampler_info = {
#                         "seed": widgets[0],
#                         "steps": widgets[2],
#                         "cfg": widgets[3],
#                         "sampler_name": widgets[4],
#                         "scheduler": widgets[5],
#                         "denoise": widgets[6]
#                     }
#                 except:
#                     pass
#         return {k: v for k, v in sampler_info.items() if v is not None}
#
#     def parse(self, json_workflow):
#         try:
#             data = json.loads(self._clean_json_string(json_workflow))
#         except json.JSONDecodeError as e:
#             return json.dumps({"error": str(e)}, ensure_ascii=False)
#
#         # 统一节点列表
#         nodes_list = []
#         if isinstance(data, dict):
#             if "nodes" in data:
#                 nodes_list = data["nodes"]
#             else:
#                 for k, v in data.items():
#                     if isinstance(v, dict) and "class_type" in v:
#                         v["id"] = k
#                         nodes_list.append(v)
#
#         result = {
#             "checkpoints": set(),
#             "loras": set(),
#             "vaes": set(),
#             "input_images": set(),
#             "prompts": [],  # 提示词可能有多个，且内容较长，用列表
#             "latent_setup": [],  # 分辨率设置
#             "key_parameters": [],  # 关键参数(ImpactInt等)
#             "samplers": []
#         }
#
#         for node in nodes_list:
#             node_type = node.get("type") or node.get("class_type")
#             if not node_type: continue
#
#             # 1. 匹配通用规则
#             for category, rule in self.rules.items():
#                 if node_type in rule["class_types"]:
#                     val = self._get_node_value(node, rule["fields"], rule.get("widget_index", 0))
#
#                     if val:
#                         # 根据类别分类处理
#                         if category in ["checkpoints", "loras", "vaes", "input_images"]:
#                             result[category].add(str(val))
#                         elif category == "prompts":
#                             # 只保留非空的、长度大于1的字符串，过滤掉一些默认的空节点
#                             if isinstance(val, str) and len(val.strip()) > 1:
#                                 result[category].append({"node_id": node.get("id"), "text": val})
#                         elif category == "latent_setup":
#                             result[category].append(val)
#                         elif category == "parameters":
#                             # 记录 ImpactInt/Float 的值，这通常是分辨率或Denosie
#                             result["key_parameters"].append({
#                                 "node_id": node.get("id"),
#                                 "type": node_type,
#                                 "value": val
#                             })
#
#             # 2. 匹配采样器
#             if "KSampler" in node_type:
#                 sampler_data = self._parse_sampler(node, node_type)
#                 if sampler_data:
#                     sampler_data["node_id"] = node.get("id")
#                     result["samplers"].append(sampler_data)
#
#         # 格式化输出 (Set转List)
#         final_output = {k: list(v) if isinstance(v, set) else v for k, v in result.items()}
#         return json.dumps(final_output, indent=4, ensure_ascii=False)
#
#
# # ====================
# # 测试部分
# # ====================
# if __name__ == "__main__":
#     # 使用你之前提供的 JSON 字符串
#     input_json_str = r'''{"id":"4974fc5a-06c8-4469-a902-b0db1822b7b9","revision":0,"last_node_id":101,"last_link_id":138,"nodes":[{"id":16,"type":"SeedVR2LoadVAEModel","pos":[1667.5127881262897,1662.0619264713005],"size":[263.64483642578125,298],"flags":{},"order":0,"mode":0,"inputs":[{"label":"torch编译参数","localized_name":"torch_compile_args","name":"torch_compile_args","shape":7,"type":"TORCH_COMPILE_ARGS","link":null},{"localized_name":"模型","name":"model","type":"COMBO","widget":{"name":"model"},"link":null},{"localized_name":"设备","name":"device","type":"COMBO","widget":{"name":"device"},"link":null},{"localized_name":"分块编码","name":"encode_tiled","shape":7,"type":"BOOLEAN","widget":{"name":"encode_tiled"},"link":null},{"localized_name":"编码块大小","name":"encode_tile_size","shape":7,"type":"INT","widget":{"name":"encode_tile_size"},"link":null},{"localized_name":"编码块重叠","name":"encode_tile_overlap","shape":7,"type":"INT","widget":{"name":"encode_tile_overlap"},"link":null},{"localized_name":"分块解码","name":"decode_tiled","shape":7,"type":"BOOLEAN","widget":{"name":"decode_tiled"},"link":null},{"localized_name":"解码块大小","name":"decode_tile_size","shape":7,"type":"INT","widget":{"name":"decode_tile_size"},"link":null},{"localized_name":"解码块重叠","name":"decode_tile_overlap","shape":7,"type":"INT","widget":{"name":"decode_tile_overlap"},"link":null},{"localized_name":"区块调试","name":"tile_debug","shape":7,"type":"COMBO","widget":{"name":"tile_debug"},"link":null},{"localized_name":"卸载设备","name":"offload_device","shape":7,"type":"COMBO","widget":{"name":"offload_device"},"link":null},{"label":"cache_model","localized_name":"缓存模型","name":"cache_model","shape":7,"type":"BOOLEAN","widget":{"name":"cache_model"},"link":null}],"outputs":[{"label":"vae","localized_name":"SEEDVR2_VAE","name":"SEEDVR2_VAE","type":"SEEDVR2_VAE","links":[19]}],"properties":{"cnr_id":"seedvr2_videoupscaler","ver":"912ab4a5da8bb3590c4659f8f19160a7bd88a656","Node name for S&R":"SeedVR2LoadVAEModel","widget_ue_connectable":{"encode_tiled":true,"encode_tile_overlap":true,"cache_model":true,"encode_tile_size":true,"decode_tiled":true,"decode_tile_size":true,"tile_debug":true,"offload_device":true,"model":true,"decode_tile_overlap":true,"device":true},"ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.5.1"},"ttNbgOverride":{"bgcolor":"#535","groupcolor":"#a1309b","color":"#323"}},"widgets_values":["ema_vae_fp16.safetensors","cuda:0",true,1024,128,true,1024,128,"false","cpu",false],"color":"#323","bgcolor":"#535"},{"id":21,"type":"ImageScaleBy","pos":[1656.9815381262897,1300.7258287540153],"size":[226.9215087890625,82],"flags":{},"order":53,"mode":0,"inputs":[{"label":"图像","localized_name":"图像","name":"image","type":"IMAGE","link":91},{"localized_name":"缩放算法","name":"upscale_method","type":"COMBO","widget":{"name":"upscale_method"},"link":null},{"localized_name":"缩放系数","name":"scale_by","type":"FLOAT","widget":{"name":"scale_by"},"link":null}],"outputs":[{"label":"图像","localized_name":"图像","name":"IMAGE","type":"IMAGE","links":[17]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"ImageScaleBy","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["lanczos",0.5000000000000001],"color":"#323","bgcolor":"#535"},{"id":40,"type":"Fast Groups Bypasser (rgthree)","pos":[1740.540216463687,2565.4231968878316],"size":[342.0193786621094,226],"flags":{},"order":1,"mode":0,"inputs":[],"outputs":[{"label":"可选连接","name":"OPT_CONNECTION","type":"*"}],"properties":{"matchColors":"","matchTitle":"（2）","showNav":true,"showAllGraphs":true,"sort":"position","customSortAlphabet":"","toggleRestriction":"default","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"color":"#322","bgcolor":"#533"},{"id":6,"type":"VAEEncode","pos":[323.5988476966031,1508.952658282824],"size":[140,46],"flags":{},"order":37,"mode":0,"inputs":[{"label":"图像","localized_name":"像素","name":"pixels","type":"IMAGE","link":2},{"label":"VAE","localized_name":"vae","name":"vae","type":"VAE","link":64}],"outputs":[{"label":"Latent","localized_name":"Latent","name":"LATENT","type":"LATENT","links":[9]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"VAEEncode","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":[]},{"id":54,"type":"Reroute","pos":[231.51815922004062,1616.6594301334098],"size":[75,26],"flags":{},"order":22,"mode":0,"inputs":[{"name":"","type":"*","link":63}],"outputs":[{"name":"","type":"VAE","links":[64,65]}],"properties":{"showOutputText":false,"horizontal":false,"ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}}},{"id":53,"type":"Reroute","pos":[705.3567822669147,1616.011297809191],"size":[75,26],"flags":{},"order":30,"mode":0,"inputs":[{"name":"","type":"*","link":65}],"outputs":[{"name":"","type":"VAE","links":[62]}],"properties":{"showOutputText":false,"horizontal":false,"ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}}},{"id":4,"type":"ConditioningZeroOut","pos":[353.2111523841031,1323.5794664493278],"size":[140,26],"flags":{"collapsed":true},"order":41,"mode":0,"inputs":[{"label":"条件","localized_name":"条件","name":"conditioning","type":"CONDITIONING","link":1}],"outputs":[{"label":"条件","localized_name":"条件","name":"CONDITIONING","type":"CONDITIONING","links":[8]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"ConditioningZeroOut","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":[]},{"id":9,"type":"CLIPTextEncode","pos":[-184.42507808464597,1290.6389185062126],"size":[408.8636474609375,144.1272735595703],"flags":{},"order":39,"mode":0,"inputs":[{"label":"CLIP","localized_name":"clip","name":"clip","type":"CLIP","link":77},{"localized_name":"文本","name":"text","type":"STRING","widget":{"name":"text"},"link":105}],"outputs":[{"label":"条件","localized_name":"条件","name":"CONDITIONING","type":"CONDITIONING","links":[1,7]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"CLIPTextEncode","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":[""],"color":"#232","bgcolor":"#353"},{"id":60,"type":"Reroute","pos":[-2025.0416552330837,1901.6341920963005],"size":[75,26],"flags":{},"order":20,"mode":0,"inputs":[{"name":"","type":"*","link":72}],"outputs":[{"name":"","type":"IMAGE","links":[73]}],"properties":{"showOutputText":false,"horizontal":false,"ue_properties":{"widget_ue_connectable":{},"version":"7.2.2","input_ue_unconnectable":{}}}},{"id":61,"type":"Reroute","pos":[-419.8959643151147,1893.777624713488],"size":[75,26],"flags":{},"order":28,"mode":0,"inputs":[{"name":"","type":"*","link":73}],"outputs":[{"name":"","type":"IMAGE","links":[74]}],"properties":{"showOutputText":false,"horizontal":false,"ue_properties":{"widget_ue_connectable":{},"version":"7.2.2","input_ue_unconnectable":{}}}},{"id":7,"type":"LayerUtility: ImageScaleByAspectRatio V2","pos":[-204.93728511589597,1515.3532167545036],"size":[303.68515625,330],"flags":{},"order":34,"mode":0,"inputs":[{"label":"图像","localized_name":"image","name":"image","shape":7,"type":"IMAGE","link":74},{"label":"遮罩","localized_name":"mask","name":"mask","shape":7,"type":"MASK","link":null},{"localized_name":"aspect_ratio","name":"aspect_ratio","type":"COMBO","widget":{"name":"aspect_ratio"},"link":null},{"localized_name":"proportional_width","name":"proportional_width","type":"INT","widget":{"name":"proportional_width"},"link":null},{"localized_name":"proportional_height","name":"proportional_height","type":"INT","widget":{"name":"proportional_height"},"link":null},{"localized_name":"fit","name":"fit","type":"COMBO","widget":{"name":"fit"},"link":null},{"localized_name":"method","name":"method","type":"COMBO","widget":{"name":"method"},"link":null},{"localized_name":"round_to_multiple","name":"round_to_multiple","type":"COMBO","widget":{"name":"round_to_multiple"},"link":null},{"localized_name":"scale_to_side","name":"scale_to_side","type":"COMBO","widget":{"name":"scale_to_side"},"link":null},{"localized_name":"scale_to_length","name":"scale_to_length","type":"INT","widget":{"name":"scale_to_length"},"link":21},{"localized_name":"background_color","name":"background_color","type":"STRING","widget":{"name":"background_color"},"link":null}],"outputs":[{"label":"图像","localized_name":"image","name":"image","type":"IMAGE","links":[2]},{"label":"遮罩","localized_name":"mask","name":"mask","type":"MASK"},{"label":"原始大小","localized_name":"original_size","name":"original_size","type":"BOX"},{"localized_name":"width","name":"width","type":"INT"},{"localized_name":"height","name":"height","type":"INT"}],"properties":{"cnr_id":"comfyui_layerstyle","ver":"90f4bfb38aaf121292f429b20eff07c6c121697e","Node name for S&R":"LayerUtility: ImageScaleByAspectRatio V2","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["original",1,1,"crop","lanczos","8","longest",1536,"#000000"],"color":"rgba(38, 73, 116, 0.7)"},{"id":62,"type":"Reroute","pos":[-1690.0389391686303,1168.4129701724723],"size":[75,26],"flags":{},"order":21,"mode":0,"inputs":[{"name":"","type":"*","link":75}],"outputs":[{"name":"","type":"CLIP","links":[76]}],"properties":{"showOutputText":false,"horizontal":false,"ue_properties":{"widget_ue_connectable":{},"version":"7.2.2","input_ue_unconnectable":{}}}},{"id":63,"type":"Reroute","pos":[-276.6522509362085,1178.1783205142692],"size":[75,26],"flags":{},"order":29,"mode":0,"inputs":[{"name":"","type":"*","link":76}],"outputs":[{"name":"","type":"CLIP","links":[77]}],"properties":{"showOutputText":false,"horizontal":false,"ue_properties":{"widget_ue_connectable":{},"version":"7.2.2","input_ue_unconnectable":{}}}},{"id":65,"type":"LayerUtility: ImageReelComposit","pos":[3197.2481396887915,1304.6863924136833],"size":[285.46160888671875,195.6546173095703],"flags":{},"order":62,"mode":0,"inputs":[{"label":"reel_1","localized_name":"reel_1","name":"reel_1","type":"Reel","link":79},{"label":"reel_2","localized_name":"reel_2","name":"reel_2","shape":7,"type":"Reel","link":null},{"label":"reel_3","localized_name":"reel_3","name":"reel_3","shape":7,"type":"Reel","link":null},{"label":"reel_4","localized_name":"reel_4","name":"reel_4","shape":7,"type":"Reel","link":null},{"localized_name":"font_file","name":"font_file","type":"COMBO","widget":{"name":"font_file"},"link":null},{"localized_name":"font_size","name":"font_size","type":"INT","widget":{"name":"font_size"},"link":null},{"localized_name":"border","name":"border","type":"INT","widget":{"name":"border"},"link":null},{"localized_name":"color_theme","name":"color_theme","type":"COMBO","widget":{"name":"color_theme"},"link":null}],"outputs":[{"label":"image1","localized_name":"image1","name":"image1","type":"IMAGE","links":[78]}],"properties":{"cnr_id":"comfyui_layerstyle","ver":"90f4bfb38aaf121292f429b20eff07c6c121697e","Node name for S&R":"LayerUtility: ImageReelComposit","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["Alibaba-PuHuiTi-Heavy.ttf",40,8,"light"],"color":"#322","bgcolor":"#533"},{"id":66,"type":"LayerUtility: ImageReel","pos":[2913.7593701575415,1301.9559961429313],"size":[270,238],"flags":{},"order":61,"mode":0,"inputs":[{"label":"image1","localized_name":"image1","name":"image1","type":"IMAGE","link":80},{"label":"image2","localized_name":"image2","name":"image2","shape":7,"type":"IMAGE","link":98},{"label":"image3","localized_name":"image3","name":"image3","shape":7,"type":"IMAGE","link":null},{"label":"image4","localized_name":"image4","name":"image4","shape":7,"type":"IMAGE","link":null},{"localized_name":"image1_text","name":"image1_text","type":"STRING","widget":{"name":"image1_text"},"link":null},{"localized_name":"image2_text","name":"image2_text","type":"STRING","widget":{"name":"image2_text"},"link":null},{"localized_name":"image3_text","name":"image3_text","type":"STRING","widget":{"name":"image3_text"},"link":null},{"localized_name":"image4_text","name":"image4_text","type":"STRING","widget":{"name":"image4_text"},"link":null},{"localized_name":"reel_height","name":"reel_height","type":"INT","widget":{"name":"reel_height"},"link":null},{"localized_name":"border","name":"border","type":"INT","widget":{"name":"border"},"link":null}],"outputs":[{"label":"reel","localized_name":"reel","name":"reel","type":"Reel","links":[79]}],"properties":{"cnr_id":"comfyui_layerstyle","ver":"90f4bfb38aaf121292f429b20eff07c6c121697e","Node name for S&R":"LayerUtility: ImageReel","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["original","Final Effect","image3","image4",2048,32],"color":"#322","bgcolor":"#533"},{"id":11,"type":"SaveImage","pos":[1047.2657178137897,1294.0383325687126],"size":[504.82568359375,638.3176879882812],"flags":{},"order":52,"mode":0,"inputs":[{"label":"图像","localized_name":"图片","name":"images","type":"IMAGE","link":90},{"localized_name":"文件名前缀","name":"filename_prefix","type":"STRING","widget":{"name":"filename_prefix"},"link":null}],"outputs":[],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"SaveImage","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["ComfyUI"],"color":"#2a363b","bgcolor":"#3f5159"},{"id":20,"type":"Image Comparer (rgthree)","pos":[2351.7852490637897,1313.4250360599235],"size":[480.3896789550781,778.5012817382812],"flags":{},"order":60,"mode":0,"inputs":[{"dir":3,"label":"图像_A","name":"image_a","type":"IMAGE","link":97},{"dir":3,"label":"图像_B","name":"image_b","type":"IMAGE","link":92}],"outputs":[],"properties":{"cnr_id":"rgthree-comfy","ver":"2b9eb36d3e1741e88dbfccade0e08137f7fa2bfb","comparer_mode":"Slide","widget_ue_connectable":{},"ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.4.1"}},"widgets_values":[[{"name":"A","selected":true,"url":"/api/view?filename=rgthree.compare._temp_lkfdi_00001_.png&type=temp&subfolder=&rand=0.32516950047197124"},{"name":"B","selected":true,"url":"/api/view?filename=rgthree.compare._temp_lkfdi_00002_.png&type=temp&subfolder=&rand=0.5764020263421392"}]],"color":"#323","bgcolor":"#535"},{"id":64,"type":"PreviewImage","pos":[3546.3091748450415,1304.1505685916618],"size":[2076.970947265625,1597.979248046875],"flags":{},"order":63,"mode":0,"inputs":[{"label":"图像","localized_name":"图像","name":"images","type":"IMAGE","link":78}],"outputs":[],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"PreviewImage","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":[],"color":"#322","bgcolor":"#533"},{"id":12,"type":"LoadImage","pos":[-2540.7402636315214,1290.6874567142204],"size":[341.04779052734375,476.4586486816406],"flags":{},"order":2,"mode":0,"inputs":[{"localized_name":"图像","name":"image","type":"COMBO","widget":{"name":"image"},"link":null},{"localized_name":"选择文件上传","name":"upload","type":"IMAGEUPLOAD","widget":{"name":"upload"},"link":null}],"outputs":[{"label":"图像","localized_name":"图像","name":"IMAGE","type":"IMAGE","links":[70,72,80]},{"label":"遮罩","localized_name":"遮罩","name":"MASK","type":"MASK"}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"LoadImage","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["67b73d41bb3cc75add18f1a5cdeb497a.jpg","image"],"color":"#322","bgcolor":"#533"},{"id":70,"type":"VRAMCleanup","pos":[796.3085892482977,1393.988426023976],"size":[210,82],"flags":{},"order":48,"mode":0,"inputs":[{"label":"任意","localized_name":"anything","name":"anything","type":"*","link":94},{"localized_name":"卸载模型","name":"offload_model","type":"BOOLEAN","widget":{"name":"offload_model"},"link":null},{"localized_name":"清理显存缓存","name":"offload_cache","type":"BOOLEAN","widget":{"name":"offload_cache"},"link":null}],"outputs":[{"label":"输出","localized_name":"output","name":"output","type":"*","links":[89]}],"properties":{"cnr_id":"comfyui_memory_cleanup","ver":"1.1.1","Node name for S&R":"VRAMCleanup","ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.2.2"}},"widgets_values":[true,true],"color":"#322","bgcolor":"#533"},{"id":15,"type":"VAEDecode","pos":[803.3492139075397,1306.578390704699],"size":[140,46],"flags":{},"order":46,"mode":0,"inputs":[{"label":"Latent","localized_name":"Latent","name":"samples","type":"LATENT","link":14},{"label":"VAE","localized_name":"vae","name":"vae","type":"VAE","link":62}],"outputs":[{"label":"图像","localized_name":"图像","name":"IMAGE","type":"IMAGE","links":[94]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"VAEDecode","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":[]},{"id":71,"type":"RAMCleanup","pos":[801.6099263092528,1531.7760676512316],"size":[210,130],"flags":{},"order":50,"mode":0,"inputs":[{"label":"任意","localized_name":"anything","name":"anything","type":"*","link":89},{"localized_name":"清理文件缓存","name":"clean_file_cache","type":"BOOLEAN","widget":{"name":"clean_file_cache"},"link":null},{"localized_name":"清理进程内存","name":"clean_processes","type":"BOOLEAN","widget":{"name":"clean_processes"},"link":null},{"localized_name":"清理未使用的 DLL","name":"clean_dlls","type":"BOOLEAN","widget":{"name":"clean_dlls"},"link":null},{"localized_name":"重试次数","name":"retry_times","type":"INT","widget":{"name":"retry_times"},"link":null}],"outputs":[{"label":"输出","localized_name":"output","name":"output","type":"*","links":[90,91,92]}],"properties":{"cnr_id":"comfyui_memory_cleanup","ver":"1.1.1","Node name for S&R":"RAMCleanup","ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.2.2"}},"widgets_values":[true,true,true,3],"color":"#322","bgcolor":"#533"},{"id":18,"type":"SeedVR2VideoUpscaler","pos":[1970.2710889075397,1304.00354252965],"size":[343.1535339355469,386],"flags":{},"order":56,"mode":0,"inputs":[{"label":"图像","localized_name":"image","name":"image","type":"IMAGE","link":17},{"label":"dit","localized_name":"dit","name":"dit","type":"SEEDVR2_DIT","link":18},{"label":"vae","localized_name":"vae","name":"vae","type":"SEEDVR2_VAE","link":19},{"localized_name":"种子","name":"seed","type":"INT","widget":{"name":"seed"},"link":null},{"localized_name":"分辨率","name":"resolution","type":"INT","widget":{"name":"resolution"},"link":null},{"localized_name":"最大分辨率","name":"max_resolution","type":"INT","widget":{"name":"max_resolution"},"link":null},{"localized_name":"批次大小","name":"batch_size","type":"INT","widget":{"name":"batch_size"},"link":null},{"localized_name":"统一批次大小","name":"uniform_batch_size","type":"BOOLEAN","widget":{"name":"uniform_batch_size"},"link":null},{"localized_name":"色彩校正","name":"color_correction","type":"COMBO","widget":{"name":"color_correction"},"link":null},{"localized_name":"时间重叠","name":"temporal_overlap","shape":7,"type":"INT","widget":{"name":"temporal_overlap"},"link":null},{"localized_name":"前置帧数","name":"prepend_frames","shape":7,"type":"INT","widget":{"name":"prepend_frames"},"link":null},{"localized_name":"输入噪声比例","name":"input_noise_scale","shape":7,"type":"FLOAT","widget":{"name":"input_noise_scale"},"link":null},{"localized_name":"潜空间噪声比例","name":"latent_noise_scale","shape":7,"type":"FLOAT","widget":{"name":"latent_noise_scale"},"link":null},{"localized_name":"卸载设备","name":"offload_device","shape":7,"type":"COMBO","widget":{"name":"offload_device"},"link":null},{"localized_name":"启用调试","name":"enable_debug","shape":7,"type":"BOOLEAN","widget":{"name":"enable_debug"},"link":null}],"outputs":[{"label":"image","localized_name":"图像","name":"IMAGE","type":"IMAGE","links":[99]}],"properties":{"cnr_id":"seedvr2_videoupscaler","ver":"912ab4a5da8bb3590c4659f8f19160a7bd88a656","Node name for S&R":"SeedVR2VideoUpscaler","widget_ue_connectable":{"color_correction":true,"batch_size":true,"seed":true,"uniform_batch_size":true,"enable_debug":true,"latent_noise_scale":true,"prepend_frames":true,"offload_device":true,"temporal_overlap":true,"input_noise_scale":true,"resolution":true,"max_resolution":true},"ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.5.1"},"ttNbgOverride":{"bgcolor":"#535","groupcolor":"#a1309b","color":"#323"}},"widgets_values":[1496648304,"randomize",2048,4096,5,false,"lab",0,0,0,0,"cpu",false],"color":"#323","bgcolor":"#535"},{"id":3,"type":"CLIPLoader","pos":[-2000.2846972252712,1441.0607820621208],"size":[270,106],"flags":{},"order":3,"mode":0,"inputs":[{"localized_name":"CLIP名称","name":"clip_name","type":"COMBO","widget":{"name":"clip_name"},"link":null},{"localized_name":"类型","name":"type","type":"COMBO","widget":{"name":"type"},"link":null},{"localized_name":"设备","name":"device","shape":7,"type":"COMBO","widget":{"name":"device"},"link":null}],"outputs":[{"label":"CLIP","localized_name":"CLIP","name":"CLIP","type":"CLIP","links":[75]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"CLIPLoader","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["qwen_3_4b.safetensors","qwen_image","default"]},{"id":2,"type":"UNETLoader","pos":[-2000.1479784752712,1289.0198885074333],"size":[270,82],"flags":{},"order":4,"mode":0,"inputs":[{"localized_name":"UNet名称","name":"unet_name","type":"COMBO","widget":{"name":"unet_name"},"link":null},{"localized_name":"数据类型","name":"weight_dtype","type":"COMBO","widget":{"name":"weight_dtype"},"link":null}],"outputs":[{"label":"模型","localized_name":"模型","name":"MODEL","type":"MODEL","links":[6]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"UNETLoader","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["z-image-turbo-fp8-e4m3fn.safetensors","default"]},{"id":5,"type":"VAELoader","pos":[-1997.8052050377712,1617.9616762271598],"size":[267.5206604003906,58.41322326660156],"flags":{},"order":5,"mode":0,"inputs":[{"localized_name":"vae名称","name":"vae_name","type":"COMBO","widget":{"name":"vae_name"},"link":null}],"outputs":[{"localized_name":"VAE","name":"VAE","type":"VAE","links":[63]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"VAELoader","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["ae.safetensors"]},{"id":58,"type":"ShowText|pysssss","pos":[-842.8796710804982,1304.104629715921],"size":[386.3988135623156,265.10736380582705],"flags":{},"order":36,"mode":0,"inputs":[{"localized_name":"文本","name":"text","type":"STRING","link":107}],"outputs":[{"label":"字符串","localized_name":"字符串","name":"STRING","shape":6,"type":"STRING","links":[105]}],"properties":{"cnr_id":"comfyui-custom-scripts","ver":"f2838ed5e59de4d73cde5c98354b87a8d3200190","Node name for S&R":"ShowText|pysssss","widget_ue_connectable":{},"ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.4.1"}},"widgets_values":["一位黑发及腰、眉目清冷的东方女性居于画面中央，身着浅色刺绣长袍，衣纹细腻，绣有龙凤云纹，衣领高耸，显露出古典而神秘的气质。她佩戴着一对繁复的水晶吊坠耳环，耳环垂坠如流光，与她冷艳的面容形成视觉张力。她的目光直视镜头，眼神深邃而略带疏离，唇色淡雅，面部无妆却透出天然的精致感，皮肤白皙如瓷，发丝柔顺垂落，遮掩部分脸颊，增添一丝朦胧美感。\n\n背景为深邃的黑色，衬托出她与身后盘旋的两条巨龙。龙身以蓝银为主色调，鳞片如金属般闪耀，龙首狰狞，张口吐息，龙须飘逸，姿态凶猛而优雅。一条龙呈蓝银色，另一条则为红金相间，两者缠绕交错，仿佛在她身后形成守护或压迫之势。龙形细节丰富，鳞片纹理清晰，龙爪锋利，龙目如炬，与人物形成强烈的视觉对比，同时营造出一种神话与现实交织的奇幻氛围。\n\n构图上，人物居中，龙形环绕，形成“人龙共生”的视觉中心。画面采用近景特写，聚焦于人物面部与上半身，背景龙形虽大却模糊边缘，以虚化处理突出主体。视觉引导线从人物的发丝、耳环、衣领自然延伸至背景龙形，形成一种动态的包围感，引导观者视线在人物与龙之间来回游走，增强画面张力。\n\n光影处理极为讲究，主光源来自左前方，柔和地打在人物面部，勾勒出轮廓与五官，同时在龙形身上制造高光与阴影，增强立体感。背景深黑，仅在龙身与人物衣饰处有微妙的冷光反射，营造出神秘、高冷、略带危险的氛围。整体色调偏冷，以蓝、银、黑为主，点缀红金龙纹，形成强烈的视觉冲击，同时保持画面的高雅与艺术感。\n\n此图像呈现一种“东方神话与现代美学融合”的风格，具有强烈的视觉冲击力与艺术深度，适合用于概念艺术、奇幻题材或高端时尚摄影，其氛围既神秘又优雅，既危险又迷人，是视觉与情感的双重盛宴。"],"color":"#223","bgcolor":"#335"},{"id":68,"type":"RAMCleanup","pos":[-1251.2219733161483,1442.032715624764],"size":[210,130],"flags":{},"order":33,"mode":0,"inputs":[{"label":"任意","localized_name":"anything","name":"anything","type":"*","link":85},{"localized_name":"清理文件缓存","name":"clean_file_cache","type":"BOOLEAN","widget":{"name":"clean_file_cache"},"link":null},{"localized_name":"清理进程内存","name":"clean_processes","type":"BOOLEAN","widget":{"name":"clean_processes"},"link":null},{"localized_name":"清理未使用的 DLL","name":"clean_dlls","type":"BOOLEAN","widget":{"name":"clean_dlls"},"link":null},{"localized_name":"重试次数","name":"retry_times","type":"INT","widget":{"name":"retry_times"},"link":null}],"outputs":[{"label":"输出","localized_name":"output","name":"output","type":"*","links":[107]}],"properties":{"cnr_id":"comfyui_memory_cleanup","ver":"1.1.1","Node name for S&R":"RAMCleanup","ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.2.2"}},"widgets_values":[true,true,true,3],"color":"#322","bgcolor":"#533"},{"id":69,"type":"VRAMCleanup","pos":[-1250.2534317169575,1315.872981426579],"size":[210,82],"flags":{},"order":27,"mode":0,"inputs":[{"label":"任意","localized_name":"anything","name":"anything","type":"*","link":106},{"localized_name":"卸载模型","name":"offload_model","type":"BOOLEAN","widget":{"name":"offload_model"},"link":null},{"localized_name":"清理显存缓存","name":"offload_cache","type":"BOOLEAN","widget":{"name":"offload_cache"},"link":null}],"outputs":[{"label":"输出","localized_name":"output","name":"output","type":"*","links":[85]}],"properties":{"cnr_id":"comfyui_memory_cleanup","ver":"1.1.1","Node name for S&R":"VRAMCleanup","ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.2.2"}},"widgets_values":[true,true],"color":"#322","bgcolor":"#533"},{"id":17,"type":"SaveImage","pos":[1961.8008740637897,1726.954138385363],"size":[368.4798278808594,370.19122314453125],"flags":{},"order":59,"mode":0,"inputs":[{"label":"图像","localized_name":"图片","name":"images","type":"IMAGE","link":96},{"localized_name":"文件名前缀","name":"filename_prefix","type":"STRING","widget":{"name":"filename_prefix"},"link":null}],"outputs":[],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"SaveImage","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["ComfyUI"]},{"id":72,"type":"RAMCleanup","pos":[2629.8316039175397,2169.2679200772013],"size":[210,130],"flags":{},"order":58,"mode":0,"inputs":[{"label":"任意","localized_name":"anything","name":"anything","type":"*","link":95},{"localized_name":"清理文件缓存","name":"clean_file_cache","type":"BOOLEAN","widget":{"name":"clean_file_cache"},"link":null},{"localized_name":"清理进程内存","name":"clean_processes","type":"BOOLEAN","widget":{"name":"clean_processes"},"link":null},{"localized_name":"清理未使用的 DLL","name":"clean_dlls","type":"BOOLEAN","widget":{"name":"clean_dlls"},"link":null},{"localized_name":"重试次数","name":"retry_times","type":"INT","widget":{"name":"retry_times"},"link":null}],"outputs":[{"label":"输出","localized_name":"output","name":"output","type":"*","links":[96,97,98]}],"properties":{"cnr_id":"comfyui_memory_cleanup","ver":"1.1.1","Node name for S&R":"RAMCleanup","ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.2.2"}},"widgets_values":[true,true,true,3],"color":"#322","bgcolor":"#533"},{"id":74,"type":"SeedVR2LoadVAEModel","pos":[1635.0486697259494,-2.7290664177828603],"size":[263.64483642578125,298],"flags":{},"order":6,"mode":4,"inputs":[{"label":"torch编译参数","localized_name":"torch_compile_args","name":"torch_compile_args","shape":7,"type":"TORCH_COMPILE_ARGS","link":null},{"label":"model","localized_name":"模型","name":"model","type":"COMBO","widget":{"name":"model"},"link":null},{"label":"device","localized_name":"设备","name":"device","type":"COMBO","widget":{"name":"device"},"link":null},{"label":"encode_tiled","localized_name":"分块编码","name":"encode_tiled","shape":7,"type":"BOOLEAN","widget":{"name":"encode_tiled"},"link":null},{"label":"encode_tile_size","localized_name":"编码块大小","name":"encode_tile_size","shape":7,"type":"INT","widget":{"name":"encode_tile_size"},"link":null},{"label":"encode_tile_overlap","localized_name":"编码块重叠","name":"encode_tile_overlap","shape":7,"type":"INT","widget":{"name":"encode_tile_overlap"},"link":null},{"label":"decode_tiled","localized_name":"分块解码","name":"decode_tiled","shape":7,"type":"BOOLEAN","widget":{"name":"decode_tiled"},"link":null},{"label":"decode_tile_size","localized_name":"解码块大小","name":"decode_tile_size","shape":7,"type":"INT","widget":{"name":"decode_tile_size"},"link":null},{"label":"decode_tile_overlap","localized_name":"解码块重叠","name":"decode_tile_overlap","shape":7,"type":"INT","widget":{"name":"decode_tile_overlap"},"link":null},{"label":"tile_debug","localized_name":"区块调试","name":"tile_debug","shape":7,"type":"COMBO","widget":{"name":"tile_debug"},"link":null},{"label":"offload_device","localized_name":"卸载设备","name":"offload_device","shape":7,"type":"COMBO","widget":{"name":"offload_device"},"link":null},{"label":"cache_model","localized_name":"缓存模型","name":"cache_model","shape":7,"type":"BOOLEAN","widget":{"name":"cache_model"},"link":null}],"outputs":[{"label":"vae","localized_name":"SEEDVR2_VAE","name":"SEEDVR2_VAE","type":"SEEDVR2_VAE","links":[111]}],"properties":{"cnr_id":"seedvr2_videoupscaler","ver":"912ab4a5da8bb3590c4659f8f19160a7bd88a656","Node name for S&R":"SeedVR2LoadVAEModel","ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.5.1"},"widget_ue_connectable":{"encode_tiled":true,"encode_tile_overlap":true,"cache_model":true,"encode_tile_size":true,"decode_tiled":true,"decode_tile_size":true,"tile_debug":true,"offload_device":true,"model":true,"decode_tile_overlap":true,"device":true},"ttNbgOverride":{"bgcolor":"#535","groupcolor":"#a1309b","color":"#323"}},"widgets_values":["ema_vae_fp16.safetensors","cuda:0",true,1024,128,true,1024,128,"false","cpu",false],"color":"#323","bgcolor":"#535"},{"id":80,"type":"CLIPLoader","pos":[-764.6194210943622,-235.86261896905228],"size":[270,106],"flags":{},"order":7,"mode":4,"inputs":[{"localized_name":"CLIP名称","name":"clip_name","type":"COMBO","widget":{"name":"clip_name"},"link":null},{"localized_name":"类型","name":"type","type":"COMBO","widget":{"name":"type"},"link":null},{"localized_name":"设备","name":"device","shape":7,"type":"COMBO","widget":{"name":"device"},"link":null}],"outputs":[{"label":"CLIP","localized_name":"CLIP","name":"CLIP","type":"CLIP","links":[123]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"CLIPLoader","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["qwen_3_4b.safetensors","qwen_image","default"],"color":"#2a363b","bgcolor":"#3f5159"},{"id":81,"type":"KSampler","pos":[509.08284941345073,-370.2257247429782],"size":[270,474],"flags":{},"order":35,"mode":4,"inputs":[{"label":"模型","localized_name":"模型","name":"model","type":"MODEL","link":114},{"label":"正面条件","localized_name":"正面条件","name":"positive","type":"CONDITIONING","link":115},{"label":"负面条件","localized_name":"负面条件","name":"negative","type":"CONDITIONING","link":116},{"label":"Latent","localized_name":"Latent图像","name":"latent_image","type":"LATENT","link":117},{"localized_name":"种子","name":"seed","type":"INT","widget":{"name":"seed"},"link":null},{"localized_name":"步数","name":"steps","type":"INT","widget":{"name":"steps"},"link":null},{"localized_name":"cfg","name":"cfg","type":"FLOAT","widget":{"name":"cfg"},"link":null},{"localized_name":"采样器名称","name":"sampler_name","type":"COMBO","widget":{"name":"sampler_name"},"link":null},{"localized_name":"调度器","name":"scheduler","type":"COMBO","widget":{"name":"scheduler"},"link":null},{"localized_name":"降噪","name":"denoise","type":"FLOAT","widget":{"name":"denoise"},"link":null}],"outputs":[{"label":"Latent","localized_name":"Latent","name":"LATENT","type":"LATENT","links":[118]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"KSampler","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":[277718179183202,"randomize",10,1,"euler","simple",1]},{"id":83,"type":"SaveImage","pos":[1015.6232546868878,-368.34616617974575],"size":[556.3636474609375,647.272705078125],"flags":{},"order":44,"mode":4,"inputs":[{"label":"图像","localized_name":"图片","name":"images","type":"IMAGE","link":135},{"localized_name":"文件名前缀","name":"filename_prefix","type":"STRING","widget":{"name":"filename_prefix"},"link":null}],"outputs":[],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"SaveImage","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["ComfyUI"]},{"id":84,"type":"EmptyLatentImage","pos":[229.40456572204403,-214.4257293206149],"size":[270,106],"flags":{},"order":32,"mode":4,"inputs":[{"localized_name":"宽度","name":"width","type":"INT","widget":{"name":"width"},"link":121},{"localized_name":"高度","name":"height","type":"INT","widget":{"name":"height"},"link":122},{"localized_name":"批量大小","name":"batch_size","type":"INT","widget":{"name":"batch_size"},"link":null}],"outputs":[{"label":"Latent","localized_name":"Latent","name":"LATENT","type":"LATENT","links":[117]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"EmptyLatentImage","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":[1920,1080,1]},{"id":85,"type":"CLIPTextEncode","pos":[-337.1629696783466,-380.49188380059536],"size":[400,200],"flags":{},"order":23,"mode":4,"inputs":[{"label":"CLIP","localized_name":"clip","name":"clip","type":"CLIP","link":123},{"localized_name":"文本","name":"text","type":"STRING","widget":{"name":"text"},"link":null}],"outputs":[{"label":"条件","localized_name":"条件","name":"CONDITIONING","type":"CONDITIONING","links":[115,127]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"CLIPTextEncode","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["极具真实感的特写人像，一位满脸皱纹的藏族老奶奶，阳光侧打在脸上，清晰可见的毛孔和皮肤纹理，眼神深邃，背景是模糊的雪山，8k分辨率，电影级布光，哈苏相机拍摄，85mm镜头。"],"color":"#233","bgcolor":"#355"},{"id":88,"type":"Fast Groups Bypasser (rgthree)","pos":[2954.4432009759494,-263.62723688897427],"size":[342.0193786621094,226],"flags":{},"order":8,"mode":4,"inputs":[],"outputs":[{"label":"可选连接","name":"OPT_CONNECTION","type":"*"}],"properties":{"matchColors":"","matchTitle":"（1）","showNav":true,"showAllGraphs":true,"sort":"position","customSortAlphabet":"","toggleRestriction":"default","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"color":"#322","bgcolor":"#533"},{"id":90,"type":"Reroute","pos":[84.99593535095028,91.45815892401379],"size":[75,26],"flags":{},"order":24,"mode":4,"inputs":[{"name":"","type":"*","widget":{"name":"value"},"link":125}],"outputs":[{"name":"","type":"INT","links":[121]}],"properties":{"showOutputText":false,"horizontal":false,"ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}}},{"id":92,"type":"Reroute","pos":[74.96108427673153,195.5721420783102],"size":[75,26],"flags":{},"order":25,"mode":4,"inputs":[{"name":"","type":"*","widget":{"name":"value"},"link":126}],"outputs":[{"name":"","type":"INT","links":[122]}],"properties":{"showOutputText":false,"horizontal":false,"ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}}},{"id":93,"type":"ConditioningZeroOut","pos":[268.7871951165753,-348.5929427605563],"size":[140,26],"flags":{"collapsed":true},"order":31,"mode":4,"inputs":[{"label":"条件","localized_name":"条件","name":"conditioning","type":"CONDITIONING","link":127}],"outputs":[{"label":"条件","localized_name":"条件","name":"CONDITIONING","type":"CONDITIONING","links":[116]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"ConditioningZeroOut","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":[]},{"id":94,"type":"ImageScaleBy","pos":[1644.2146853509494,-363.5468993645602],"size":[226.9215087890625,82],"flags":{},"order":45,"mode":4,"inputs":[{"label":"图像","localized_name":"图像","name":"image","type":"IMAGE","link":136},{"localized_name":"缩放算法","name":"upscale_method","type":"COMBO","widget":{"name":"upscale_method"},"link":null},{"localized_name":"缩放系数","name":"scale_by","type":"FLOAT","widget":{"name":"scale_by"},"link":null}],"outputs":[{"label":"图像","localized_name":"图像","name":"IMAGE","type":"IMAGE","links":[109]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"ImageScaleBy","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["lanczos",0.5000000000000001],"color":"#323","bgcolor":"#535"},{"id":79,"type":"UNETLoader","pos":[-766.7894040045185,-381.0815253716403],"size":[270,82],"flags":{},"order":9,"mode":4,"inputs":[{"localized_name":"UNet名称","name":"unet_name","type":"COMBO","widget":{"name":"unet_name"},"link":null},{"localized_name":"数据类型","name":"weight_dtype","type":"COMBO","widget":{"name":"weight_dtype"},"link":null}],"outputs":[{"label":"模型","localized_name":"模型","name":"MODEL","type":"MODEL","links":[114]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"UNETLoader","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["z-image-turbo-fp8-e4m3fn.safetensors","default"],"color":"#432","bgcolor":"#653"},{"id":73,"type":"VRAMCleanup","pos":[2400.057800671869,2179.309728798473],"size":[210,82],"flags":{},"order":57,"mode":0,"inputs":[{"label":"任意","localized_name":"anything","name":"anything","type":"*","link":99},{"localized_name":"卸载模型","name":"offload_model","type":"BOOLEAN","widget":{"name":"offload_model"},"link":null},{"localized_name":"清理显存缓存","name":"offload_cache","type":"BOOLEAN","widget":{"name":"offload_cache"},"link":null}],"outputs":[{"label":"输出","localized_name":"output","name":"output","type":"*","links":[95]}],"properties":{"cnr_id":"comfyui_memory_cleanup","ver":"1.1.1","Node name for S&R":"VRAMCleanup","ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.2.2"}},"widgets_values":[true,true],"color":"#322","bgcolor":"#533"},{"id":75,"type":"SaveImage","pos":[1929.3382205071994,62.16314549627941],"size":[372.94695419262916,270],"flags":{},"order":54,"mode":4,"inputs":[{"label":"图像","localized_name":"图片","name":"images","type":"IMAGE","link":130},{"localized_name":"文件名前缀","name":"filename_prefix","type":"STRING","widget":{"name":"filename_prefix"},"link":null}],"outputs":[],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"SaveImage","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["ComfyUI"]},{"id":97,"type":"RAMCleanup","pos":[2642.818572070762,379.75476789286984],"size":[210,130],"flags":{},"order":51,"mode":4,"inputs":[{"label":"任意","localized_name":"anything","name":"anything","type":"*","link":129},{"localized_name":"清理文件缓存","name":"clean_file_cache","type":"BOOLEAN","widget":{"name":"clean_file_cache"},"link":null},{"localized_name":"清理进程内存","name":"clean_processes","type":"BOOLEAN","widget":{"name":"clean_processes"},"link":null},{"localized_name":"清理未使用的 DLL","name":"clean_dlls","type":"BOOLEAN","widget":{"name":"clean_dlls"},"link":null},{"localized_name":"重试次数","name":"retry_times","type":"INT","widget":{"name":"retry_times"},"link":null}],"outputs":[{"label":"输出","localized_name":"output","name":"output","type":"*","links":[130,131]}],"properties":{"cnr_id":"comfyui_memory_cleanup","ver":"1.1.1","Node name for S&R":"RAMCleanup","ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.2.2"}},"widgets_values":[true,true,true,3],"color":"#322","bgcolor":"#533"},{"id":76,"type":"SeedVR2VideoUpscaler","pos":[1937.8084353509494,-360.787540004819],"size":[343.1535339355469,386],"flags":{},"order":47,"mode":4,"inputs":[{"label":"图像","localized_name":"image","name":"image","type":"IMAGE","link":109},{"label":"dit","localized_name":"dit","name":"dit","type":"SEEDVR2_DIT","link":110},{"label":"vae","localized_name":"vae","name":"vae","type":"SEEDVR2_VAE","link":111},{"label":"seed","localized_name":"种子","name":"seed","type":"INT","widget":{"name":"seed"},"link":null},{"label":"resolution","localized_name":"分辨率","name":"resolution","type":"INT","widget":{"name":"resolution"},"link":null},{"label":"max_resolution","localized_name":"最大分辨率","name":"max_resolution","type":"INT","widget":{"name":"max_resolution"},"link":null},{"label":"batch_size","localized_name":"批次大小","name":"batch_size","type":"INT","widget":{"name":"batch_size"},"link":null},{"label":"uniform_batch_size","localized_name":"统一批次大小","name":"uniform_batch_size","type":"BOOLEAN","widget":{"name":"uniform_batch_size"},"link":null},{"label":"color_correction","localized_name":"色彩校正","name":"color_correction","type":"COMBO","widget":{"name":"color_correction"},"link":null},{"label":"temporal_overlap","localized_name":"时间重叠","name":"temporal_overlap","shape":7,"type":"INT","widget":{"name":"temporal_overlap"},"link":null},{"label":"prepend_frames","localized_name":"前置帧数","name":"prepend_frames","shape":7,"type":"INT","widget":{"name":"prepend_frames"},"link":null},{"label":"input_noise_scale","localized_name":"输入噪声比例","name":"input_noise_scale","shape":7,"type":"FLOAT","widget":{"name":"input_noise_scale"},"link":null},{"label":"latent_noise_scale","localized_name":"潜空间噪声比例","name":"latent_noise_scale","shape":7,"type":"FLOAT","widget":{"name":"latent_noise_scale"},"link":null},{"label":"offload_device","localized_name":"卸载设备","name":"offload_device","shape":7,"type":"COMBO","widget":{"name":"offload_device"},"link":null},{"label":"enable_debug","localized_name":"启用调试","name":"enable_debug","shape":7,"type":"BOOLEAN","widget":{"name":"enable_debug"},"link":null}],"outputs":[{"label":"image","localized_name":"图像","name":"IMAGE","type":"IMAGE","links":[132]}],"properties":{"cnr_id":"seedvr2_videoupscaler","ver":"912ab4a5da8bb3590c4659f8f19160a7bd88a656","Node name for S&R":"SeedVR2VideoUpscaler","ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.5.1"},"widget_ue_connectable":{"color_correction":true,"batch_size":true,"seed":true,"uniform_batch_size":true,"enable_debug":true,"latent_noise_scale":true,"prepend_frames":true,"offload_device":true,"temporal_overlap":true,"input_noise_scale":true,"resolution":true,"max_resolution":true},"ttNbgOverride":{"bgcolor":"#535","groupcolor":"#a1309b","color":"#323"}},"widgets_values":[526134514,"randomize",2048,4096,5,false,"lab",0,0,0,0,"cpu",false],"color":"#323","bgcolor":"#535"},{"id":96,"type":"VRAMCleanup","pos":[2413.044768825091,389.7965766141414],"size":[210,82],"flags":{},"order":49,"mode":4,"inputs":[{"label":"任意","localized_name":"anything","name":"anything","type":"*","link":132},{"localized_name":"卸载模型","name":"offload_model","type":"BOOLEAN","widget":{"name":"offload_model"},"link":null},{"localized_name":"清理显存缓存","name":"offload_cache","type":"BOOLEAN","widget":{"name":"offload_cache"},"link":null}],"outputs":[{"label":"输出","localized_name":"output","name":"output","type":"*","links":[129]}],"properties":{"cnr_id":"comfyui_memory_cleanup","ver":"1.1.1","Node name for S&R":"VRAMCleanup","ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.2.2"}},"widgets_values":[true,true],"color":"#322","bgcolor":"#533"},{"id":98,"type":"VRAMCleanup","pos":[507.2132436166516,170.2271198827623],"size":[210,82],"flags":{},"order":40,"mode":4,"inputs":[{"label":"任意","localized_name":"anything","name":"anything","type":"*","link":137},{"localized_name":"卸载模型","name":"offload_model","type":"BOOLEAN","widget":{"name":"offload_model"},"link":null},{"localized_name":"清理显存缓存","name":"offload_cache","type":"BOOLEAN","widget":{"name":"offload_cache"},"link":null}],"outputs":[{"label":"输出","localized_name":"output","name":"output","type":"*","links":[133]}],"properties":{"cnr_id":"comfyui_memory_cleanup","ver":"1.1.1","Node name for S&R":"VRAMCleanup","ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.2.2"}},"widgets_values":[true,true],"color":"#322","bgcolor":"#533"},{"id":99,"type":"RAMCleanup","pos":[736.9870468623225,160.18531116149077],"size":[210,130],"flags":{},"order":42,"mode":4,"inputs":[{"label":"任意","localized_name":"anything","name":"anything","type":"*","link":133},{"localized_name":"清理文件缓存","name":"clean_file_cache","type":"BOOLEAN","widget":{"name":"clean_file_cache"},"link":null},{"localized_name":"清理进程内存","name":"clean_processes","type":"BOOLEAN","widget":{"name":"clean_processes"},"link":null},{"localized_name":"清理未使用的 DLL","name":"clean_dlls","type":"BOOLEAN","widget":{"name":"clean_dlls"},"link":null},{"localized_name":"重试次数","name":"retry_times","type":"INT","widget":{"name":"retry_times"},"link":null}],"outputs":[{"label":"输出","localized_name":"output","name":"output","type":"*","links":[134,135,136]}],"properties":{"cnr_id":"comfyui_memory_cleanup","ver":"1.1.1","Node name for S&R":"RAMCleanup","ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.2.2"}},"widgets_values":[true,true,true,3],"color":"#322","bgcolor":"#533"},{"id":82,"type":"VAEDecode","pos":[806.0553835931378,-360.3187270623141],"size":[140,46],"flags":{},"order":38,"mode":4,"inputs":[{"label":"Latent","localized_name":"Latent","name":"samples","type":"LATENT","link":118},{"label":"VAE","localized_name":"vae","name":"vae","type":"VAE","link":119}],"outputs":[{"label":"图像","localized_name":"图像","name":"IMAGE","type":"IMAGE","links":[137]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"VAEDecode","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":[]},{"id":23,"type":"ImpactInt","pos":[-1987.2221972252712,1788.0622316470817],"size":[246.74497985839844,58],"flags":{},"order":10,"mode":0,"inputs":[{"localized_name":"值","name":"value","type":"INT","widget":{"name":"value"},"link":null}],"outputs":[{"label":"整数","localized_name":"整数","name":"INT","type":"INT","links":[21]}],"properties":{"cnr_id":"comfyui-impact-pack","ver":"705698faf242851881abd7d1e1774baa3cf47136","Node name for S&R":"ImpactInt","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":[1280],"color":"#223","bgcolor":"#335"},{"id":89,"type":"ImpactInt","pos":[-760.6024533209247,93.95565648260754],"size":[270,58],"flags":{},"order":11,"mode":4,"inputs":[{"localized_name":"值","name":"value","type":"INT","widget":{"name":"value"},"link":null}],"outputs":[{"label":"整数","localized_name":"整数","name":"INT","type":"INT","links":[125]}],"properties":{"cnr_id":"comfyui-impact-pack","ver":"61bd8397a18e7e7668e6a24e95168967768c2bed","Node name for S&R":"ImpactInt","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":[1280],"color":"#233","bgcolor":"#355"},{"id":91,"type":"ImpactInt","pos":[-759.0800839361591,201.26092381659146],"size":[270,58],"flags":{},"order":12,"mode":4,"inputs":[{"localized_name":"值","name":"value","type":"INT","widget":{"name":"value"},"link":null}],"outputs":[{"label":"整数","localized_name":"整数","name":"INT","type":"INT","links":[126]}],"properties":{"cnr_id":"comfyui-impact-pack","ver":"61bd8397a18e7e7668e6a24e95168967768c2bed","Node name for S&R":"ImpactInt","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":[720],"color":"#233","bgcolor":"#355"},{"id":86,"type":"VAELoader","pos":[-765.400365918581,-61.57177882012661],"size":[270,58],"flags":{},"order":13,"mode":4,"inputs":[{"localized_name":"vae名称","name":"vae_name","type":"COMBO","widget":{"name":"vae_name"},"link":null}],"outputs":[{"localized_name":"VAE","name":"VAE","type":"VAE","links":[124]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"VAELoader","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":["ae.safetensors"],"color":"#322","bgcolor":"#533"},{"id":77,"type":"SeedVR2LoadDiTModel","pos":[1634.3870486321994,-240.62301020440384],"size":[247.66464233398438,202],"flags":{},"order":14,"mode":4,"inputs":[{"label":"torch编译参数","localized_name":"torch_compile_args","name":"torch_compile_args","shape":7,"type":"TORCH_COMPILE_ARGS","link":null},{"label":"model","localized_name":"模型","name":"model","type":"COMBO","widget":{"name":"model"},"link":null},{"label":"device","localized_name":"设备","name":"device","type":"COMBO","widget":{"name":"device"},"link":null},{"label":"blocks_to_swap","localized_name":"要交换的块","name":"blocks_to_swap","shape":7,"type":"INT","widget":{"name":"blocks_to_swap"},"link":null},{"label":"swap_io_components","localized_name":"交换输入输出组件","name":"swap_io_components","shape":7,"type":"BOOLEAN","widget":{"name":"swap_io_components"},"link":null},{"label":"offload_device","localized_name":"卸载设备","name":"offload_device","shape":7,"type":"COMBO","widget":{"name":"offload_device"},"link":null},{"label":"cache_model","localized_name":"缓存模型","name":"cache_model","shape":7,"type":"BOOLEAN","widget":{"name":"cache_model"},"link":null},{"label":"attention_mode","localized_name":"注意力模式","name":"attention_mode","shape":7,"type":"COMBO","widget":{"name":"attention_mode"},"link":null}],"outputs":[{"label":"dit","localized_name":"SEEDVR2_DIT","name":"SEEDVR2_DIT","type":"SEEDVR2_DIT","links":[110]}],"properties":{"cnr_id":"seedvr2_videoupscaler","ver":"912ab4a5da8bb3590c4659f8f19160a7bd88a656","Node name for S&R":"SeedVR2LoadDiTModel","ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.5.1"},"widget_ue_connectable":{"attention_mode":true,"swap_io_components":true,"cache_model":true,"offload_device":true,"model":true,"device":true,"blocks_to_swap":true},"ttNbgOverride":{"bgcolor":"#535","groupcolor":"#a1309b","color":"#323"}},"widgets_values":["seedvr2_ema_3b_fp16.safetensors","cuda:0",32,true,"cpu","sdpa","sdpa"],"color":"#323","bgcolor":"#535"},{"id":19,"type":"SeedVR2LoadDiTModel","pos":[1666.8511670325397,1424.1681276431755],"size":[247.66464233398438,202],"flags":{},"order":15,"mode":0,"inputs":[{"label":"torch编译参数","localized_name":"torch_compile_args","name":"torch_compile_args","shape":7,"type":"TORCH_COMPILE_ARGS","link":null},{"localized_name":"模型","name":"model","type":"COMBO","widget":{"name":"model"},"link":null},{"localized_name":"设备","name":"device","type":"COMBO","widget":{"name":"device"},"link":null},{"localized_name":"要交换的块","name":"blocks_to_swap","shape":7,"type":"INT","widget":{"name":"blocks_to_swap"},"link":null},{"localized_name":"交换输入输出组件","name":"swap_io_components","shape":7,"type":"BOOLEAN","widget":{"name":"swap_io_components"},"link":null},{"localized_name":"卸载设备","name":"offload_device","shape":7,"type":"COMBO","widget":{"name":"offload_device"},"link":null},{"label":"cache_model","localized_name":"缓存模型","name":"cache_model","shape":7,"type":"BOOLEAN","widget":{"name":"cache_model"},"link":null},{"localized_name":"注意力模式","name":"attention_mode","shape":7,"type":"COMBO","widget":{"name":"attention_mode"},"link":null}],"outputs":[{"label":"dit","localized_name":"SEEDVR2_DIT","name":"SEEDVR2_DIT","type":"SEEDVR2_DIT","links":[18]}],"properties":{"cnr_id":"seedvr2_videoupscaler","ver":"912ab4a5da8bb3590c4659f8f19160a7bd88a656","Node name for S&R":"SeedVR2LoadDiTModel","widget_ue_connectable":{"attention_mode":true,"swap_io_components":true,"cache_model":true,"offload_device":true,"model":true,"device":true,"blocks_to_swap":true},"ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.5.1"},"ttNbgOverride":{"bgcolor":"#535","groupcolor":"#a1309b","color":"#323"}},"widgets_values":["seedvr2_ema_3b_fp16.safetensors","cuda:0",32,true,"cpu","sdpa","sdpa"],"color":"#323","bgcolor":"#535"},{"id":87,"type":"Reroute","pos":[792.9204338449376,-59.770542615569575],"size":[75,26],"flags":{},"order":26,"mode":4,"inputs":[{"name":"","type":"*","link":124}],"outputs":[{"name":"","type":"VAE","links":[119]}],"properties":{"showOutputText":false,"horizontal":false,"ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}}},{"id":59,"type":"Qwen3_VQA","pos":[-1639.9269948173353,1298.6193113612424],"size":[236.15203857421875,509.9371337890625],"flags":{},"order":19,"mode":0,"inputs":[{"label":"source_path","localized_name":"source_path","name":"source_path","shape":7,"type":"PATH","link":null},{"label":"image","localized_name":"image","name":"image","shape":7,"type":"IMAGE","link":70},{"localized_name":"text","name":"text","type":"STRING","widget":{"name":"text"},"link":null},{"localized_name":"model","name":"model","type":"COMBO","widget":{"name":"model"},"link":null},{"localized_name":"quantization","name":"quantization","type":"COMBO","widget":{"name":"quantization"},"link":null},{"localized_name":"keep_model_loaded","name":"keep_model_loaded","type":"BOOLEAN","widget":{"name":"keep_model_loaded"},"link":null},{"localized_name":"temperature","name":"temperature","type":"FLOAT","widget":{"name":"temperature"},"link":null},{"localized_name":"max_new_tokens","name":"max_new_tokens","type":"INT","widget":{"name":"max_new_tokens"},"link":null},{"localized_name":"min_pixels","name":"min_pixels","type":"INT","widget":{"name":"min_pixels"},"link":null},{"localized_name":"max_pixels","name":"max_pixels","type":"INT","widget":{"name":"max_pixels"},"link":null},{"localized_name":"seed","name":"seed","type":"INT","widget":{"name":"seed"},"link":null},{"localized_name":"attention","name":"attention","type":"COMBO","widget":{"name":"attention"},"link":null}],"outputs":[{"label":"STRING","localized_name":"字符串","name":"STRING","type":"STRING","links":[66,106]}],"properties":{"aux_id":"IuvenisSapiens/ComfyUI_Qwen3-VL-Instruct","ver":"70cc35edacfd5979cbe7a15caf56bd2f715bc3b5","Node name for S&R":"Qwen3_VQA","widget_ue_connectable":{},"ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.4"}},"widgets_values":["你是一位专业的AI图像生成提示词工程师。请详细描述这张图像主体、前景、中景、背景、构图、视觉引导、光影氛围等细节并创作出具有深度、氛围和艺术感或日常业余设备拍摄的图像提示词。\n\n要求：中文提示词，不用出现对图像水印的描述，不要出现无关的文字和符号，不需要总结，限制在800字以内","Qwen3-VL-4B-Instruct","none",false,0.7,2048,200704,1003520,10,"randomize","eager"],"color":"#223","bgcolor":"#335"},{"id":78,"type":"Image Comparer (rgthree)","pos":[2312.6678103509485,-346.04205469903286],"size":[558.0059986220799,653.9801357976957],"flags":{},"order":55,"mode":4,"inputs":[{"dir":3,"label":"图像_A","name":"image_a","type":"IMAGE","link":131},{"dir":3,"label":"图像_B","name":"image_b","type":"IMAGE","link":134}],"outputs":[],"properties":{"cnr_id":"rgthree-comfy","ver":"2b9eb36d3e1741e88dbfccade0e08137f7fa2bfb","comparer_mode":"Slide","ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{},"version":"7.4.1"},"widget_ue_connectable":{}},"widgets_values":[[{"name":"A","selected":true,"url":"/api/view?filename=rgthree.compare._temp_hmrpb_00001_.png&type=temp&subfolder=&rand=0.5756752948739643"},{"name":"B","selected":true,"url":"/api/view?filename=rgthree.compare._temp_hmrpb_00002_.png&type=temp&subfolder=&rand=0.5441427833017864"}]],"color":"#323","bgcolor":"#535"},{"id":8,"type":"KSampler","pos":[499.3854687903531,1296.1953569522575],"size":[270,474],"flags":{},"order":43,"mode":0,"inputs":[{"label":"模型","localized_name":"模型","name":"model","type":"MODEL","link":6},{"label":"正面条件","localized_name":"正面条件","name":"positive","type":"CONDITIONING","link":7},{"label":"负面条件","localized_name":"负面条件","name":"negative","type":"CONDITIONING","link":8},{"label":"Latent","localized_name":"Latent图像","name":"latent_image","type":"LATENT","link":9},{"localized_name":"种子","name":"seed","type":"INT","widget":{"name":"seed"},"link":null},{"localized_name":"步数","name":"steps","type":"INT","widget":{"name":"steps"},"link":null},{"localized_name":"cfg","name":"cfg","type":"FLOAT","widget":{"name":"cfg"},"link":null},{"localized_name":"采样器名称","name":"sampler_name","type":"COMBO","widget":{"name":"sampler_name"},"link":null},{"localized_name":"调度器","name":"scheduler","type":"COMBO","widget":{"name":"scheduler"},"link":null},{"localized_name":"降噪","name":"denoise","type":"FLOAT","widget":{"name":"denoise"},"link":138}],"outputs":[{"label":"Latent","localized_name":"Latent","name":"LATENT","type":"LATENT","links":[14]}],"properties":{"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"KSampler","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"widgets_values":[615049998535620,"randomize",10,1,"euler","simple",0.9000000000000001]},{"id":95,"type":"Fast Groups Bypasser (rgthree)","pos":[-2062.939273661036,-457.9019014402056],"size":[839.0631275777178,279.2439074502072],"flags":{},"order":18,"mode":0,"inputs":[],"outputs":[{"label":"可选连接","name":"OPT_CONNECTION","type":"*","links":null}],"properties":{"matchColors":"","matchTitle":"图1","showNav":true,"showAllGraphs":true,"sort":"position","customSortAlphabet":"","toggleRestriction":"default","ue_properties":{"version":"7.2.2","widget_ue_connectable":{},"input_ue_unconnectable":{}}},"color":"#322","bgcolor":"#533"},{"id":101,"type":"Note","pos":[-2003.298725626044,2171.122730785146],"size":[290.6102879343889,129.2219986327973],"flags":{},"order":16,"mode":0,"inputs":[],"outputs":[],"properties":{},"widgets_values":["注意！！！！\n1：代表全部靠提示词去生成\n\n数值越低重绘幅度越低，对于原图的参考就越多\n\n这个需要大家根据自己的需求去自己调整"],"color":"#322","bgcolor":"#533"},{"id":100,"type":"PrimitiveFloat","pos":[-1989.008541570573,2033.9708241210235],"size":[270,58],"flags":{},"order":17,"mode":0,"inputs":[{"localized_name":"值","name":"value","type":"FLOAT","widget":{"name":"value"},"link":null}],"outputs":[{"localized_name":"浮点","name":"FLOAT","type":"FLOAT","links":[138]}],"properties":{"ue_properties":{"widget_ue_connectable":{},"input_ue_unconnectable":{}},"cnr_id":"comfy-core","ver":"0.3.75","Node name for S&R":"PrimitiveFloat"},"widgets_values":[0.6]}],"links":[[1,9,0,4,0,"CONDITIONING"],[2,7,0,6,0,"IMAGE"],[6,2,0,8,0,"MODEL"],[7,9,0,8,1,"CONDITIONING"],[8,4,0,8,2,"CONDITIONING"],[9,6,0,8,3,"LATENT"],[14,8,0,15,0,"LATENT"],[17,21,0,18,0,"IMAGE"],[18,19,0,18,1,"SEEDVR2_DIT"],[19,16,0,18,2,"SEEDVR2_VAE"],[21,23,0,7,9,"INT"],[62,53,0,15,1,"VAE"],[63,5,0,54,0,"*"],[64,54,0,6,1,"VAE"],[65,54,0,53,0,"*"],[70,12,0,59,1,"IMAGE"],[72,12,0,60,0,"*"],[73,60,0,61,0,"*"],[74,61,0,7,0,"IMAGE"],[75,3,0,62,0,"*"],[76,62,0,63,0,"*"],[77,63,0,9,0,"CLIP"],[78,65,0,64,0,"IMAGE"],[79,66,0,65,0,"Reel"],[80,12,0,66,0,"IMAGE"],[85,69,0,68,0,"*"],[89,70,0,71,0,"*"],[90,71,0,11,0,"IMAGE"],[91,71,0,21,0,"IMAGE"],[92,71,0,20,1,"IMAGE"],[94,15,0,70,0,"*"],[95,73,0,72,0,"*"],[96,72,0,17,0,"IMAGE"],[97,72,0,20,0,"IMAGE"],[98,72,0,66,1,"IMAGE"],[99,18,0,73,0,"*"],[105,58,0,9,1,"STRING"],[106,59,0,69,0,"*"],[107,68,0,58,0,"STRING"],[109,94,0,76,0,"IMAGE"],[110,77,0,76,1,"SEEDVR2_DIT"],[111,74,0,76,2,"SEEDVR2_VAE"],[114,79,0,81,0,"MODEL"],[115,85,0,81,1,"CONDITIONING"],[116,93,0,81,2,"CONDITIONING"],[117,84,0,81,3,"LATENT"],[118,81,0,82,0,"LATENT"],[119,87,0,82,1,"VAE"],[121,90,0,84,0,"INT"],[122,92,0,84,1,"INT"],[123,80,0,85,0,"CLIP"],[124,86,0,87,0,"*"],[125,89,0,90,0,"*"],[126,91,0,92,0,"*"],[127,85,0,93,0,"CONDITIONING"],[129,96,0,97,0,"*"],[130,97,0,75,0,"IMAGE"],[131,97,0,78,0,"IMAGE"],[132,76,0,96,0,"*"],[133,98,0,99,0,"*"],[134,99,0,78,1,"IMAGE"],[135,99,0,83,0,"IMAGE"],[136,99,0,94,0,"IMAGE"],[137,82,0,98,0,"*"],[138,100,0,8,9,"FLOAT"]],"groups":[{"id":23,"title":"自动反推洗图1+放大","bounding":[-2946.3650889977316,631.614828664395,9337.742562199108,2498.4438141748424],"color":"#3f789e","font_size":300,"flags":{}},{"id":1,"title":"最长边边长","bounding":[-2010.8694140221462,1700.8394533267692,296.031982421875,175.39956665039062],"color":"#3f789e","font_size":24,"flags":{}},{"id":3,"title":"二次放大 | SeedVR2（2）","bounding":[1656.9097607825397,1227.2589956393913,1211.5377450616488,1135.5266186188617],"color":"#3f789e","font_size":24,"flags":{}},{"id":10,"title":"二次放大开关","bounding":[1662.521173494937,2395.7089024542374,505.2044677734375,454.7159423828125],"color":"#A88","font_size":80,"flags":{}},{"id":13,"title":"参考图片","bounding":[-2548.561430623709,1210.139227496691,378.0328369140625,590.095703125],"color":"#3f789e","font_size":24,"flags":{}},{"id":14,"title":"模型加载","bounding":[-2010.2846972252712,1215.4198709598259,290.13671875,470.95501708984375],"color":"#3f789e","font_size":24,"flags":{}},{"id":15,"title":"提示词","bounding":[-215.60989253777097,1209.5026765933708,471.636962890625,255.19061279296875],"color":"#3f789e","font_size":24,"flags":{}},{"id":16,"title":"采样过程","bounding":[313.5989697669156,1222.5953336826042,708.5112865931851,731.3278998339731],"color":"#3f789e","font_size":24,"flags":{}},{"id":17,"title":"一次输出","bounding":[1037.2657178137897,1220.438326465197,524.82568359375,721.9176635742188],"color":"#3f789e","font_size":24,"flags":{}},{"id":18,"title":"B站/YouTube:Work-Fisher","bounding":[-344.7071461246863,-2020.5999987745095,3507.641277833336,420.1266293479473],"color":"#8AA","font_size":300,"flags":{}},{"id":19,"title":"搬运我的流前，请先给我点点关注","bounding":[-1028.4491530032872,-2489.694260170281,4737.474944094628,407.1287324129512],"color":"#A88","font_size":300,"flags":{}},{"id":20,"title":"Z-IMAGE：小而美图像模型合集：文生图、自动反推洗图","bounding":[-2479.543892202953,-1533.5574689422488,7745.617739457479,415.0666499562535],"color":"#8AA","font_size":300,"flags":{}},{"id":21,"title":"Describe Image/反推图片","bounding":[-1680.7135607506616,1213.4762369266227,1244.0499267578125,652.1148681640625],"color":"#3f789e","font_size":24,"flags":{}},{"id":22,"title":"最终对比","bounding":[2903.7593701575415,1228.355967151232,2767.45947265625,1700.7789306640625],"color":"#3f789e","font_size":24,"flags":{}},{"id":31,"title":"文生图1","bounding":[-996.6466541923473,-983.7799041230098,4881.690576519771,1555.2965937521867],"color":"#3f789e","font_size":300,"flags":{}},{"id":24,"title":"二次放大 | SeedVR2（1）","bounding":[1624.4456423821994,-437.53208308038086,1258.569478504217,1012.2161672464596],"color":"#3f789e","font_size":24,"flags":{}},{"id":25,"title":"模型加载","bounding":[-776.7894040045185,-454.6814818840919,292.16998291015625,461.1095886230469],"color":"#3f789e","font_size":24,"flags":{}},{"id":26,"title":"尺寸修改","bounding":[-772.3609982427997,20.355650379091912,291.7585144042969,254.79794311523438],"color":"#8AA","font_size":24,"flags":{}},{"id":27,"title":"Group","bounding":[219.40462675720028,-448.7526259880958,747.0554445866901,751.864651133937],"color":"#3f789e","font_size":24,"flags":{}},{"id":28,"title":"一次出图","bounding":[1005.6232546868878,-441.9461837273536,576.3636474609375,730.8727416992188],"color":"#3f789e","font_size":24,"flags":{}},{"id":29,"title":"提示词","bounding":[-347.1629696783466,-454.0918822747169,420.0000305175781,283.6000061035156],"color":"#3f789e","font_size":24,"flags":{}},{"id":30,"title":"二次放大开关","bounding":[2876.4244021478244,-433.34135584649414,505.2044677734375,454.7159423828125],"color":"#A88","font_size":80,"flags":{}},{"id":32,"title":"总开关","bounding":[-2135.6267933115223,-949.334541006483,989.3292818115006,829.3961617825116],"color":"#A88","font_size":300,"flags":{}},{"id":33,"title":"重绘幅度","bounding":[-2005.7002728408952,1950.036843378804,296.031982421875,175.39956665039062],"color":"#3f789e","font_size":24,"flags":{}}],"config":{},"extra":{"0246.VERSION":[0,0,4],"ue_links":[],"links_added_by_ue":[],"ds":{"scale":0.8954302432552572,"offset":[3131.7503736297303,-1650.1750879358467]},"frontendVersion":"1.23.0","VHS_latentpreview":false,"VHS_latentpreviewrate":0,"VHS_MetadataImage":true,"VHS_KeepIntermediate":true,"workflowRendererVersion":"LG"},"version":0.4}'''
#     # (为了节省空间，这里省略长字符串，实际运行请将你的JSON字符串传进去)
#
#     # 假设你已经定义了 input_json_str
#     parser = ComfyUIParser()
#     print(parser.parse(input_json_str))

#
# import os
# import sys
# import json
# import logging
#
# # =========================================================
# # 1. 环境配置 (必须与 __init__.py 保持一致)
# # =========================================================
# # 强制使用国内镜像，防止 test 脚本运行时下载模型超时
# os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
# # 禁用 Chroma 遥测
# os.environ["ANONYMIZED_TELEMETRY"] = "False"
# os.environ["CHROMA_SERVER_NOINTERACTIVE"] = "True"
#
# # 配置简单的日志
# logging.basicConfig(level=logging.ERROR)  # 只显示错误，保持输出清爽
#
# # =========================================================
# # 2. 路径黑魔法 (确保能导入 backend 模块)
# # =========================================================
# current_dir = base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# if current_dir not in sys.path:
#     sys.path.append(current_dir)
#
# try:
#     from backend.chatbot.catalog.vdb import ChromaVectorStore
# except ImportError as e:
#     print(f"❌ Import Error: {e}")
#     print("请确保此脚本位于 'custom_nodes/comfyui_workflow_agent/' 目录下")
#     sys.exit(1)
#
#
# # =========================================================
# # 3. 模拟 Agent 的匹配逻辑
# # =========================================================
# def run_matcher_test():
#     # 1. 定位数据库
#     db_path = os.path.join(current_dir, "vector_db")
#     print(f"📂 Loading Vector DB from: {db_path}")
#
#     if not os.path.exists(db_path):
#         print("❌ Error: 数据库不存在！请先启动 ComfyUI 让后台扫描任务完成一次。")
#         return
#
#     # 2. 初始化连接
#     try:
#         store = ChromaVectorStore(db_path)
#         print("✅ DB Connected successfully.\n")
#     except Exception as e:
#         print(f"❌ DB Connection Failed: {e}")
#         return
#
#     # 3. 定义测试用例 (模拟 router.py 输出的 JSON)
#     test_cases = {'user_intent': {'core_function': '建立一个使用z-image-turbo模型的基本工作流', 'type': 'new_workflow', 'details': ['使用z-image-turbo模型', '生成基本工作流'], 'clarification_needed': False}, 'current_workflow_summary': {'base_model': '未定义', 'key_nodes': [], 'workflow_stage': '无活动工作流', 'input_output': {'input': '无', 'output': '无'}, 'potential_issues': ['当前尚未配置任何模型或节点']}, 'planning_suggestions': {'integration_point': '新工作流的起点', 'expected_nodes': ['ModelLoader-z-image-turbo', 'Sampler', 'Output'], 'parameters_guidelines': {'model': 'z-image-turbo基准模型', 'sampler_config': '标准设置'}, 'dependencies': ['z-image-turbo模型']}, 'notes': '将初始化一个带有z-image-turbo模型的基础工作流'}
#
#     # 模拟 Search Agent 的查询构建逻辑
#     # 策略：综合 Agent 建议的节点名 + 用户意图细节
#     results = store.query_nodes(json.dumps(test_cases), n_results=2)
#
#     if results and results['documents']:
#         # 打印前 2 个匹配结果
#         print(results)
#     else:
#         print("   ⚠️ No matches found.")
#         print("=" * 60 + "\n")
#
#
# if __name__ == "__main__":
#     run_matcher_test()


# import os
# import sys
# import logging
#
# # =========================================================
# # 1. 环境配置 (保持与 __init__.py 一致)
# # =========================================================
# os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
# os.environ["ANONYMIZED_TELEMETRY"] = "False"
# os.environ["CHROMA_SERVER_NOINTERACTIVE"] = "True"
#
# # 配置日志只显示关键信息
# logging.basicConfig(level=logging.ERROR)
#
# # =========================================================
# # 2. 路径黑魔法 (确保能导入 backend)
# # =========================================================
# current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# if current_dir not in sys.path:
#     sys.path.append(current_dir)
#
# try:
#     from custom_nodes.comfyui_workflow_agent.backend.chatbot.catalog.vdb import ChromaVectorStore
# except ImportError as e:
#     print(f"❌ Import Error: {e}")
#     print("请确保脚本位于 'custom_nodes/comfyui_workflow_agent/' 目录下")
#     sys.exit(1)
#
#
# # =========================================================
# # 3. 辅助打印函数
# # =========================================================
# def print_results(title, results, type="node"):
#     print(f"\n🔎 Query: [{title}]")
#     print("-" * 60)
#
#     if not results or not results['ids'] or not results['ids'][0]:
#         print("   ❌ No matches found.")
#         return
#
#     # Chroma 返回的是列表的列表 (batch result)
#     ids = results['ids'][0]
#     distances = results['distances'][0] if results['distances'] else [0] * len(ids)
#     metadatas = results['metadatas'][0]
#     documents = results['documents'][0]
#
#     for i, (doc_id, dist, meta, content) in enumerate(zip(ids, distances, metadatas, documents)):
#         score = 1 - dist  # 简单的相似度转换，仅供参考
#         print(f"   🎯 Match {i + 1} (ID: {doc_id}) | Distance: {dist:.4f}")
#
#         if type == "workflow":
#             print(f"         all: {meta,'N/A'}")
#             print(f"      📄 File: {meta.get('filename', 'N/A')}")
#             print(f"      🧩 Models: {meta.get('models', 'N/A')[:100]}...")
#         else:
#             print(f"      📦 Pack: {meta.get('pack_name', 'N/A')}")
#             print(f"      🏷️ Category: {meta.get('category', 'N/A')}")
#
#         # 打印内容摘要
#         snippet = content.replace('\n', ' ')[:150]
#         print(f"      📝 Content: {snippet}...\n")
#
#
# # =========================================================
# # 4. 主测试逻辑
# # =========================================================
# def run_test():
#     # 1. 连接数据库
#     db_path = os.path.join(current_dir, "vector_db")
#     print(f"📂 Connecting to DB at: {db_path}")
#
#     if not os.path.exists(db_path):
#         print("❌ Error: 数据库目录不存在！请先启动 ComfyUI 并等待扫描完成。")
#         return
#
#     try:
#         store = ChromaVectorStore(db_path)
#         print("✅ DB Connected.\n")
#     except Exception as e:
#         print(f"❌ DB Init Failed: {e}")
#         return
#
#     # ==========================================
#     # 测试场景 A: 检索工作流 (Workflow)
#     # ==========================================
#     print("=" * 20 + " TESTING WORKFLOW RETRIEVAL " + "=" * 20)
#
#     # 假设你放了一个叫 z_image_turbo.json 的文件在 example_workflows 里
#     # 即使你还没放，这里也可以搜搜看
#     wf_queries = [
#         "z-image-turbo basic workflow",
#         "WanVideo image to video(i2v)",
#     ]
#
#     for q in wf_queries:
#         # 使用我们在 vdb.py 里写的 query_workflows
#         results = store.query_workflows(q, n=1)
#         print_results(q, results, type="workflow")
#
#     # ==========================================
#     # 测试场景 B: 检索节点 (Node)
#     # ==========================================
#     print("\n" + "=" * 20 + " TESTING NODE RETRIEVAL " + "=" * 20)
#
#     node_queries = [
#         "WanVideoSampler settings",  # 测试具体的参数查询
#         "Load Image from path",  # 测试功能描述查询
#         "CheckpointLoaderSimple",  # 测试精确名称查询
#         "Add Canny ControlNet"  # 测试意图查询
#     ]
#
#     for q in node_queries:
#         # 使用 query_nodes
#         results = store.query_nodes(q, n_results=2)
#         print_results(q, results, type="node")
#
#
# if __name__ == "__main__":
#     run_test()
