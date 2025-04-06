# encoding: utf-8
import logging
from telegram_notifier import TelegramNotifier
from utils.log import setup_logging

# ========== 主程序入口 ==========
if __name__ == "__main__":
    setup_logging()
    logging.info("启动Telegram监听服务")

    notifier = TelegramNotifier()
    with notifier.client:
        notifier.client.run_until_disconnected()
