from __future__ import annotations

import base64
import httpx
from langbot_plugin.api.definition.components.common.event_listener import EventListener
from langbot_plugin.api.entities import events, context
from langbot_plugin.api.entities.builtin.platform import message as platform_message

from .meme_request_handler import MemeRequestHandler


class DefaultEventListener(EventListener):
    def __init__(self):
        super().__init__()
        # 从配置中获取memeurl
        self.memeurl = None
        # 初始化表情包请求处理器，但暂时不传入memeurl参数
        # 将在initialize方法中重新设置meme_handler
        
    async def initialize(self):
        await super().initialize()

        self.memeurl = self.plugin.get_config().get("memeurl", None)
        # 初始化表情包请求处理器，传入memeurl参数
        self.meme_handler = MemeRequestHandler(self.memeurl)
        
        @self.handler(events.GroupMessageReceived)
        async def handler(event_context: context.EventContext):
            # 获取用户消息文本，并确保排除AT标记
            message_parts = []
            for element in event_context.event.message_chain:
                # 只保留普通文本部分，排除AT和其他非文本元素
                if hasattr(element, 'type') and element.type == 'Plain' and hasattr(element, 'text'):
                    message_parts.append(element.text)
            
            # 合并所有普通文本部分
            message_text = ''.join(message_parts)
            # print(f'event={event_context.event}')
            # 移除prevent_default()，允许其他处理器也能处理消息
            # 如果用户输入包含[Image]标记，剔除它
            if '[Image]' in message_text:
                message_text = message_text.replace('[Image]', '').strip()
            
            # 解析用户消息，格式：表情包关键词 文本内容
            parts = message_text.strip().split(" ", 1)
            if len(parts) < 1:
                await event_context.reply(
                    platform_message.MessageChain([
                        platform_message.Plain(text="请输入表情包关键词和文本内容，格式：表情包关键词 文本内容\n")
                    ])
                )
                return
            
            # 首先尝试匹配 keywords
            first_word = parts[0]
            meme_key = self.meme_handler.match_keyword(first_word)
            
            # 如果没有匹配到 keywords，回退使用第一个词作为 meme_key
            if meme_key is None:
                meme_key = first_word
            
            # 初始化texts列表
            texts = []
            
            # 检查meme_key是否存在于memes_info中，以及其是否需要多个文本
            if meme_key in self.meme_handler.memes_info:
                meme_info = self.meme_handler.memes_info[meme_key]
                # 如果有文本内容
                if len(parts) > 1:
                    # 默认以逗号分隔多个文本
                    texts = [t.strip() for t in parts[1].split(',')]
                    
                    # 检查文本数量是否符合要求
                    min_texts = meme_info.get('params_type', {}).get('min_texts', 0)
                    max_texts = meme_info.get('params_type', {}).get('max_texts', 0)
                    
                    # 如果文本数量不足，使用默认文本填充
                    if len(texts) < min_texts and 'default_texts' in meme_info.get('params_type', {}):
                        default_texts = meme_info['params_type']['default_texts']
                        # 只填充需要的数量
                        texts += default_texts[len(texts):min_texts]
                    
                    # 如果文本数量超过最大限制，截断
                    if max_texts > 0 and len(texts) > max_texts:
                        texts = texts[:max_texts]
                else:
                    # 没有提供文本，检查是否有默认文本
                    if 'default_texts' in meme_info.get('params_type', {}):
                        texts = meme_info['params_type']['default_texts']
            else:
                # 如果meme_key不在memes_info中，使用原来的处理方式
                if len(parts) > 1:
                    texts = [parts[1]]
                else:
                    texts = []
            
            # 初始化images列表并从消息链中提取图片的base64数据
            user_images = []  # 用户主动传入的图片
            at_target_id = None
            
            # 先检查消息链中是否有AT标记和用户传入的图片
            for element in event_context.event.message_chain:
                if hasattr(element, 'type'):
                    if element.type == 'At' and hasattr(element, 'target'):
                        # 记录AT的目标ID
                        at_target_id = element.target
                    elif element.type == 'Image' and hasattr(element, 'base64') and element.base64:
                        # 提取图片的base64数据
                        base64_data = element.base64
                        if ',' in base64_data:
                            base64_data = base64_data.split(',')[1]
                        img_bytes = base64.b64decode(base64_data)
                        user_images.append(img_bytes)
            
            # 获取表情包信息以确定所需图片数量
            required_images_count = 0
            if meme_key in self.meme_handler.memes_info:
                # 检查表情包是否需要图片，这里假设通过params_type来判断
                meme_info = self.meme_handler.memes_info[meme_key]
                # 尝试从表情包信息中获取所需图片数量，如果没有则默认为0
                required_images_count = meme_info.get('params_type', {}).get('max_images', 0)
            
            # 初始化最终的images列表
            images = []
            
            # 根据优先级和所需图片数量构建images列表
            # 优先级：1. @获取到的id头像 2. 用户主动传入的图片 3. sender_id头像
            
            # 首先，获取可能需要的头像（AT目标头像和发送者头像）
            at_avatar = None
            sender_avatar = None
            
            # 1. 获取AT目标头像（如果有）
            if at_target_id:
                try:
                    async with httpx.AsyncClient() as client:
                        img_url = f"http://q1.qlogo.cn/g?b=qq&nk={at_target_id}&s=100"
                        img_resp = await client.get(img_url)
                        img_resp.raise_for_status()
                        at_avatar = img_resp.content
                except Exception as e:
                    print(f"获取AT目标QQ头像时出错：{repr(e)}")
            
            # 2. 获取发送者头像（如果有且与AT目标不同）
            if hasattr(event_context.event, 'sender_id'):
                sender_id = event_context.event.sender_id
                if sender_id != at_target_id:
                    try:
                        async with httpx.AsyncClient() as client:
                            img_url = f"http://q1.qlogo.cn/g?b=qq&nk={sender_id}&s=100"
                            img_resp = await client.get(img_url)
                            img_resp.raise_for_status()
                            sender_avatar = img_resp.content
                    except Exception as e:
                        print(f"获取发送者QQ头像时出错：{repr(e)}")
            
            # 获取表情包信息以确定最小和最大图片数量
            min_images = 0
            max_images = 0
            if meme_key in self.meme_handler.memes_info:
                meme_info = self.meme_handler.memes_info[meme_key]
                min_images = meme_info.get('params_type', {}).get('min_images', 0)
                max_images = meme_info.get('params_type', {}).get('max_images', 0)
                required_images_count = max_images
            
            # 特殊处理最小图片数为2的情况
            if min_images == 2 and max_images == 2:
                # 情况1：用户提供了两张图，按照顺序传入
                if len(user_images) >= 2:
                    images = user_images[:2]
                # 情况2：用户提供了一张图，则sender_id的头像为图1，用户提供的为图2
                elif len(user_images) == 1 and sender_avatar:
                    images = [sender_avatar, user_images[0]]
                # 情况3：存在At，那么sender_id头像为图1，At头像为图2
                elif at_avatar and sender_avatar:
                    images = [sender_avatar, at_avatar]
                # 其他情况：尽量满足两张图片的需求
                else:
                    # 先添加发送者头像（如果有）
                    if sender_avatar:
                        images.append(sender_avatar)
                    # 添加用户传入的图片
                    images.extend(user_images[:1])  # 只取第一张
                    # 如果还不够两张，尝试添加AT头像
                    if len(images) < 2 and at_avatar:
                        images.append(at_avatar)
            else:
                # 原来的逻辑处理其他情况
                # 如果表情包信息中没有指定最大图片数量，或者指定为0，则允许任意数量
                if required_images_count <= 0:
                    # 对于需要多张图片的情况，按照优先级和原有逻辑处理
                    # 先添加AT头像（如果有）
                    if at_avatar:
                        images.append(at_avatar)
                    # 添加用户传入的图片
                    images.extend(user_images)
                    # 如果还需要更多图片，添加发送者头像
                    if sender_avatar and (len(images) == 0 or required_images_count <= 0):
                        images.append(sender_avatar)
                else:
                    # 对于只需要一张图片的情况，按照优先级选择一张图片
                    # 1. 优先使用AT头像
                    if at_avatar:
                        images.append(at_avatar)
                    # 2. 如果没有AT头像，使用用户传入的图片（如果有）
                    elif user_images:
                        images.append(user_images[0])  # 只取第一张
                    # 3. 最后使用发送者头像
                    elif sender_avatar:
                        images.append(sender_avatar)
            
            # 确保图片数量不超过所需数量
            if required_images_count > 0:
                images = images[:required_images_count]
            
            print(f'用户输入：{message_text}')
            print(f'解析后的关键词：{meme_key}')
            print(f'解析后的文本内容：{texts}')
            print(f'提取到的图片数量：{len(images)}')
            
            try:
                # 调用表情包请求处理器生成图片
                img_bytes = await self.meme_handler.generate_meme(meme_key, texts, images)
                
                # 将生成的图片转换为base64格式
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                
                # 发送生成的表情包
                await event_context.reply(
                    platform_message.MessageChain([
                        platform_message.Image(base64=img_base64)
                    ])
                )
                event_context.prevent_default()
            except ValueError as e:
                # 处理未找到表情包的情况
                await event_context.reply(
                    platform_message.MessageChain([
                        platform_message.Plain(text=str(e))
                    ])
                )
            except RuntimeError as e:
                # 处理其他运行时错误
                await event_context.reply(
                    platform_message.MessageChain([
                        platform_message.Plain(text=str(e))
                    ])
                )
            except Exception as e:
                # 处理未知错误
                # await event_context.reply(
                #     platform_message.MessageChain([
                #         platform_message.Plain(text=f"生成表情包时出错：{str(e)}")
                #     ])
                # )
                return
                
    # 匹配关键词，返回对应的meme key
    def _match_keyword(self, text):
        return self.meme_handler.match_keyword(text)