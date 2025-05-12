import os
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class EnvFileHandler(FileSystemEventHandler):
    def __init__(self, reload_callback):
        self.reload_callback = reload_callback

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".env"):
            print("检测到.env文件变更,重新加载配置...")
            self.reload_callback()


class ConfigManager:
    def __init__(self):
        self.config = {}
        self.load_config()
        self.observer = None
        self.start_watching()

    def load_config(self):
        load_dotenv(override=True)  # 强制重新加载.env
        self.config = {
            # 基础配置
            "ENV": os.getenv("ENV", "DEV"),
            "DING_SECRET": os.getenv("DING_SECRET"),
            "DING_TOKEN": os.getenv("DING_TOKEN"),
            "API_ID": int(os.getenv("API_ID")),
            "API_HASH": os.getenv("API_HASH"),
            "DASHSCOPE_APP_ID": os.getenv("DASHSCOPE_APP_ID"),
            "DASHSCOPE_API_KEY": os.getenv("DASHSCOPE_API_KEY"),
            "PROXY": ("http", "127.0.0.1", 7890),
            # 控制任务启停的配置项
            "ENABLE_PRICE_MONITOR": os.getenv("ENABLE_PRICE_MONITOR", "True").lower()
            == "true",
            "ENABLE_TELEGRAM_LISTENER": os.getenv(
                "ENABLE_TELEGRAM_LISTENER", "True"
            ).lower()
            == "true",
            # 价格监控参数配置
            "PRICE_CHECK_INTERVAL": int(os.getenv("PRICE_CHECK_INTERVAL", 60)),
            "PRICE_CHANGE_THRESHOLD": float(os.getenv("PRICE_CHANGE_THRESHOLD", 1.0)),
            "PRICE_SYMBOLS": os.getenv("PRICE_SYMBOLS", "BTCUSDT,BNBUSDT").split(","),
        }

    def get(self, key, default=None):
        return self.config.get(key, default)

    def start_watching(self):
        event_handler = EnvFileHandler(self.load_config)
        self.observer = Observer()
        self.observer.schedule(event_handler, path=".", recursive=False)
        self.observer.start()

    def stop_watching(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()


# 使用单例模式创建全局配置管理器
CONFIG_MANAGER = ConfigManager()
