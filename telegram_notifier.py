# encoding: utf-8
import asyncio
import logging
import traceback
from telethon import TelegramClient, events
from telethon.errors import RPCError
from config import ENV, API_ID, API_HASH, PROXY
import strategy.default


class TelegramNotifier:
    def __init__(self):
        if ENV == "DEV":
            self.client = TelegramClient("user_session", API_ID, API_HASH, proxy=PROXY)
        elif ENV == "PROD":
            self.client = TelegramClient("user_session", API_ID, API_HASH)
        else:
            raise ValueError(f"不支持的环境: {ENV}")

        # 定义不同频道的处理策略
        self.channel_handlers = {
            # 默认处理函数
            -1002450025950: strategy.default.default_handler,
            "xiaosongluo": strategy.default.default_handler,
            -1001456088978: strategy.default.default_handler,
            # 默认处理函数
            "default": strategy.default.default_handler,
        }

        # 从 channel_handlers 中形成 TARGET_CHANNELS
        self.TARGET_CHANNELS = list(self.channel_handlers.keys())
        if "default" in self.TARGET_CHANNELS:
            self.TARGET_CHANNELS.remove("default")

        # 初始化事件监听
        self.client.add_event_handler(
            self.on_channel_message, events.NewMessage(chats=self.TARGET_CHANNELS)
        )

    async def on_channel_message(self, event):
        """处理频道消息"""
        try:
            chat_id = (
                event.chat_id if isinstance(event.chat_id, int) else str(event.chat_id)
            )
            handler = self.channel_handlers.get(
                chat_id, self.channel_handlers["default"]
            )
            await handler(event)
        except RPCError as e:
            logging.error(f"网络错误: {str(e)}，10秒后重试")
            await asyncio.sleep(10)
            await self.on_channel_message(event)
        except Exception as e:
            # 打印详细的堆栈信息
            stack_info = traceback.format_exc()
            logging.error(f"处理消息失败: {str(e)}\n{stack_info}")
