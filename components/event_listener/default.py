from __future__ import annotations

import base64
import httpx
import logging
from langbot_plugin.api.definition.components.common.event_listener import EventListener
from langbot_plugin.api.entities import events, context
from langbot_plugin.api.entities.builtin.platform import message as platform_message

from .meme_request_handler import MemeRequestHandler

# 创建logger实例
logger = logging.getLogger(__name__)


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
            # logger.info(f'原始消息链={event_context.event.message_chain}')
            logger.info(f'event={event_context.event}')
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
            
            # 先获取表情包信息以确定是否需要图片
            max_images = 0
            min_images = 0
            if meme_key in self.meme_handler.memes_info:
                meme_info = self.meme_handler.memes_info[meme_key]
                min_images = meme_info.get('params_type', {}).get('min_images', 0)
                max_images = meme_info.get('params_type', {}).get('max_images', 0)
            
            # 初始化最终的images列表
            images = []

            # 只有当表情包需要图片时才处理图片相关逻辑
            if max_images > 0:
                # 初始化并从消息链中提取图片和AT信息
                user_images = []  # 用户主动传入的图片
                at_target_id = None

                # 检查消息链中是否有AT标记和用户传入的图片
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

                # 新的优先级规则：
                # 1. 最高优先级：用户主动传入的图片（按顺序）
                # 2. 其次：被at用户的头像
                # 3. 最后：sender的头像
                # 特殊规则（需要2张图片时）：
                #   - 用户传了2张：使用用户的两张图
                #   - 用户传了1张：图1=sender头像，图2=用户图片
                #   - 没传图有at：图1=sender头像，图2=被at用户头像
                #   - 没传图没at：图1=sender头像，图2=sender头像

                # 首先，获取可能需要的头像（AT目标头像和发送者头像）
                at_avatar = None
                sender_avatar = None
                sender_id = None

                # 1. 获取发送者头像
                if hasattr(event_context.event, 'sender_id'):
                    sender_id = event_context.event.sender_id
                    try:
                        async with httpx.AsyncClient() as client:
                            img_url = f"http://q1.qlogo.cn/g?b=qq&nk={sender_id}&s=100"
                            img_resp = await client.get(img_url)
                            img_resp.raise_for_status()
                            sender_avatar = img_resp.content
                    except Exception as e:
                        logger.error(f"获取发送者QQ头像时出错：{repr(e)}")

                # 2. 获取AT目标头像（如果有且与发送者不同）
                if at_target_id and at_target_id != sender_id:
                    try:
                        async with httpx.AsyncClient() as client:
                            img_url = f"http://q1.qlogo.cn/g?b=qq&nk={at_target_id}&s=100"
                            img_resp = await client.get(img_url)
                            img_resp.raise_for_status()
                            at_avatar = img_resp.content
                    except Exception as e:
                        logger.error(f"获取AT目标QQ头像时出错：{repr(e)}")

                # 根据所需图片数量应用不同的优先级规则
                if max_images == 1:
                    # 需要1张图片时的优先级：用户图片 > 被at用户头像 > sender头像
                    if user_images:
                        images = [user_images[0]]
                    elif at_avatar:
                        images = [at_avatar]
                    elif sender_avatar:
                        images = [sender_avatar]
                elif max_images == 2:
                    # 需要2张图片时的特殊规则
                    if len(user_images) >= 2:
                        # 用户传了2张图：使用用户的两张图
                        images = [user_images[0], user_images[1]]
                    elif len(user_images) == 1:
                        # 用户传了1张图：图1=sender头像，图2=用户图片
                        if sender_avatar:
                            images = [sender_avatar, user_images[0]]
                        else:
                            images = [user_images[0]]
                    elif at_avatar:
                        # 没传图有at：图1=sender头像，图2=被at用户头像
                        if sender_avatar:
                            images = [sender_avatar, at_avatar]
                        else:
                            images = [at_avatar]
                    elif sender_avatar:
                        # 没传图没at：图1=sender头像，图2=sender头像
                        images = [sender_avatar, sender_avatar]
                else:
                    # 其他情况（max_images > 2）
                    # 优先级：用户图片 > 被at用户头像 > sender头像
                    # 先添加所有用户传入的图片
                    images.extend(user_images)
                    # 如果还需要更多图片，添加被at用户头像
                    if at_avatar and len(images) < max_images:
                        images.append(at_avatar)
                    # 如果还需要更多图片，添加sender头像
                    if sender_avatar and len(images) < max_images:
                        images.append(sender_avatar)

                # 确保图片数量不超过所需数量
                images = images[:max_images]

            logger.info(f'用户输入：{message_text}')
            logger.info(f'解析后的关键词：{meme_key}')
            logger.info(f'解析后的文本内容：{texts}')
            logger.info(f'提取到的图片数量：{len(images)}')

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