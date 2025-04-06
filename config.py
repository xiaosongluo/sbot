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

# 非敏感信息可以继续硬编码或从其他配置文件中读取
TARGET_CHANNELS = [-1002450025950, "xiaosongluo", -1001456088978]
# 需要转发的关键词
KEY_WORDS = ["TGE", "xiaosongluo"]

# 代理配置
PROXY = ("http", "127.0.0.1", 7890)
