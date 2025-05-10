# encoding: utf-8
import asyncio
import logging
from app.telegram_notifier import TelegramNotifier
from app.price_monitor import PriceMonitor
from utils.log import setup_logging

# ========== 主程序入口 ==========
if __name__ == "__main__":
    setup_logging()
    logging.info("启动Telegram监听服务和价格监控服务")

    notifier = TelegramNotifier()
    price_monitor = PriceMonitor()

    # 创建事件循环
    loop = asyncio.get_event_loop()
    
    try:
        # 启动Telegram客户端连接
        loop.run_until_complete(notifier.client.connect())
        
        # 检查是否已授权
        if not loop.run_until_complete(notifier.client.is_user_authorized()):
            logging.error("Telegram客户端未授权，请检查API_ID和API_HASH")
            exit(1)
        
        # 创建并启动后台任务
        monitor_task = loop.create_task(price_monitor.start_monitoring())
        
        # 运行Telegram客户端直到断开连接
        loop.run_until_complete(notifier.client.run_until_disconnected())
        
    except KeyboardInterrupt:
        logging.info("程序被用户中断，正在关闭...")
    except Exception as e:
        logging.error(f"主程序发生错误: {str(e)}")
    finally:
        # 清理资源
        if notifier.client.is_connected():
            loop.run_until_complete(notifier.client.disconnect())
        loop.close()
        logging.info("程序已关闭")