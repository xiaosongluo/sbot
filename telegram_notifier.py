# encoding: utf-8
import asyncio
from datetime import datetime
import logging
import traceback
from telethon import TelegramClient, events
from telethon.errors import RPCError
from config import CONFIG_MANAGER
import strategy.base
import strategy.pannews


class TelegramNotifier:
    def __init__(self):
        env = CONFIG_MANAGER.get("ENV")
        if env == "DEV":
            self.client = TelegramClient(
                "user_session",
                CONFIG_MANAGER.get("API_ID"),
                CONFIG_MANAGER.get("API_HASH"),
                proxy=CONFIG_MANAGER.get("PROXY"),
            )
        elif env == "PROD":
            self.client = TelegramClient(
                "user_session",
                CONFIG_MANAGER.get("API_ID"),
                CONFIG_MANAGER.get("API_HASH"),
            )
        else:
            raise ValueError(f"不支持的环境: {env}")

    async def start_notifier(self):
        # 实例化
        base_handler = strategy.base.BaseHandler()
        pannews_handler = strategy.pannews.PANNewsHandler()

        # 定义不同频道的处理策略
        self.channel_handlers = {
            1636146879: base_handler.handle_message,  # xiaosongluo
            7995411861: base_handler.handle_message,  # cqulxs
            -1002450025950: base_handler.handle_message,  # Binance Wallet Anncouncements
            # -1001456088978: pannews_handler.handle_message,  # PANNews
            # 默认处理函数
            # "default": strategy.default.default_handler,
        }
        # 从 channel_handlers 中形成 TARGET_CHANNELS
        self.TARGET_CHANNELS = list(self.channel_handlers.keys())
        if "default" in self.TARGET_CHANNELS:
            self.TARGET_CHANNELS.remove("default")

        # 初始化事件监听
        self.client.add_event_handler(
            self.on_channel_message, events.NewMessage(chats=self.TARGET_CHANNELS)
        )

        await self.client.connect()
        if not await self.client.is_user_authorized():
            logging.error("Telegram客户端未授权，请检查API_ID和API_HASH")
            exit(1)
        await self.client.run_until_disconnected()

        while True:
            try:
                utc_now = datetime.now()
                logging.info(f"Telegram 事件监听中: {utc_now}")
                await asyncio.sleep(60)
            except Exception as e:
                logging.error(f"Telegram 事件监听过程中发生错误: {str(e)}")
                await asyncio.sleep(60)  # 发生错误时等待更长时间

    async def on_channel_message(self, event):
        """处理频道消息"""
        try:
            chat_id = (
                event.chat_id if isinstance(event.chat_id, int) else str(event.chat_id)
            )
            logging.info(f"chat_id 转换: 转换前{event.chat_id}，转换后{chat_id}")
            handler = self.channel_handlers.get(chat_id)
            logging.info(f"handler锁定: {handler.__qualname__}")
            if handler is not None:
                await handler(event)
        except RPCError as e:
            logging.error(f"网络错误: {str(e)}, 10秒后重试")
            await asyncio.sleep(10)
            await self.on_channel_message(event)
        except Exception as e:
            # 打印详细的堆栈信息
            stack_info = traceback.format_exc()
            logging.error(f"处理消息失败: {str(e)}\n{stack_info}")
