# encoding: utf-8
import asyncio
import logging
from config import CONFIG_MANAGER
from telegram_notifier import TelegramNotifier
from price_monitor import PriceMonitor
from utils.log import setup_logging


# ========== 主程序入口 ==========
async def main():
    setup_logging()
    logging.info("启动Telegram监听服务和价格监控服务")

    tasks = []
    if CONFIG_MANAGER.get('ENABLE_PRICE_MONITOR'):
        price_monitor = PriceMonitor()
        tasks.append(asyncio.create_task(price_monitor.run()))
    if CONFIG_MANAGER.get('ENABLE_TELEGRAM_LISTENER'):
        telegram_notifier = TelegramNotifier()
        tasks.append(asyncio.create_task(telegram_notifier.run()))

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logging.info("程序被用户中断，正在关闭...")
    except Exception as e:
        logging.error(f"主程序发生错误: {str(e)}")
    finally:
        # 清理资源
        for task in tasks:
            task.cancel()
        logging.info("程序已关闭")


if __name__ == "__main__":
    asyncio.run(main())
