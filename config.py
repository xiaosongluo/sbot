from dotenv import load_dotenv
import os

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量中获取敏感信息
ENV = os.getenv("ENVIRONMENT", "DEV")
DING_SECRET = os.getenv("DING_SECRET")
DING_TOKEN = os.getenv("DING_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
DASHSCOPE_APP_ID = os.getenv("DASHSCOPE_APP_ID")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

# 代理配置
PROXY = ("http", "127.0.0.1", 7890)
