# encoding: utf-8
import asyncio
from telethon import TelegramClient, events
from telethon.errors import RPCError
import traceback
import strategy.default

import logging
from logging.handlers import RotatingFileHandler

# ========== 导入模块 ==========
from config import (
    ENV,
    API_ID,
    API_HASH,
    TARGET_CHANNELS,
    PROXY,
)


# ========== 日志配置 ==========
def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 控制台处理器（恢复默认换行符）
    console_handler = logging.StreamHandler()
    # 移除该行或设置为默认值
    # console_handler.terminator = ''
    console_handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)s: %(message)s"
        )
    )

    # 文件处理器（保持UTF-8编码）
    file_handler = RotatingFileHandler(
        "telegram_notifier.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(module)s:%(lineno)d]: %(message)s"
        )
    )

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


# ========== 消息处理器 ==========
class TelegramNotifier:
    def __init__(self):
        if ENV == "DEV":
            self.client = TelegramClient("user_session", API_ID, API_HASH, proxy=PROXY)
        elif ENV == "PROD":
            self.client = TelegramClient("user_session", API_ID, API_HASH)
        else:
            raise ValueError(f"不支持的环境: {ENV}")

        # 初始化事件监听
        self.client.add_event_handler(
            self.on_channel_message, events.NewMessage(chats=TARGET_CHANNELS)
        )

        # 定义不同频道的处理策略
        self.channel_handlers = {
            # 可以根据需要添加更多频道的处理函数
            # 例如：-1002450025950: self.handle_channel_1,
            #       "xiaosongluo": self.handle_channel_2,
            #       -1001456088978: self.handle_channel_3,
            # 默认处理函数
            "default": strategy.default.default_handler
        }

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


# ========== 主程序入口 ==========
if __name__ == "__main__":
    setup_logging()
    logging.info("启动Telegram监听服务")

    notifier = TelegramNotifier()
    with notifier.client:
        notifier.client.run_until_disconnected()
