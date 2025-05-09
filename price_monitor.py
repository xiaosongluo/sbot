# sbot/price_monitor.py
import asyncio
import logging
from datetime import datetime, timedelta
from config import DING_SECRET, DING_TOKEN, PRICE_CHECK_INTERVAL, PRICE_CHANGE_THRESHOLD
from utils.dingtalk import send_dingtalk_notification
import aiohttp

class PriceMonitor:
    def __init__(self):
        self.btc_last_price = None
        self.bnb_last_price = None
        self.last_checked = None
        self.price_history = {}  # 存储价格历史数据
        self.check_interval = PRICE_CHECK_INTERVAL  # 检查间隔（秒）
        self.threshold = PRICE_CHANGE_THRESHOLD  # 波动阈值（百分比）

    async def start_monitoring(self):
        """开始持续监控价格波动"""
        logging.info(f"价格监控服务已启动，检查间隔: {self.check_interval}秒，波动阈值: {self.threshold}%")
        while True:
            try:
                await self.check_prices()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logging.error(f"价格监控过程中发生错误: {str(e)}")
                await asyncio.sleep(60)  # 发生错误时等待更长时间

    async def check_prices(self):
        """检查BTC和BNB的价格波动"""
        current_time = datetime.now()
        
        # 获取当前价格
        btc_price, bnb_price = await self.fetch_current_prices()
        if btc_price is None or bnb_price is None:
            return
        
        # 更新价格历史
        self._update_price_history("BTC", btc_price, current_time)
        self._update_price_history("BNB", bnb_price, current_time)
        
        # 首次检查，只记录当前价格
        if self.last_checked is None:
            self.btc_last_price = btc_price
            self.bnb_last_price = bnb_price
            self.last_checked = current_time
            logging.info(f"首次价格检查完成: BTC=${btc_price}, BNB=${bnb_price}")
            return
        
        # 检查BTC波动
        btc_change = self._calculate_price_change(self.btc_last_price, btc_price)
        if abs(btc_change) >= self.threshold:
            await self._send_volatility_alert("BTC", btc_price, self.btc_last_price, btc_change)
        
        # 检查BNB波动
        bnb_change = self._calculate_price_change(self.bnb_last_price, bnb_price)
        if abs(bnb_change) >= self.threshold:
            await self._send_volatility_alert("BNB", bnb_price, self.bnb_last_price, bnb_change)
        
        # 更新最后检查价格和时间
        self.btc_last_price = btc_price
        self.bnb_last_price = bnb_price
        self.last_checked = current_time
        logging.info(f"价格检查完成: BTC=${btc_price} ({btc_change:.2f}%), BNB=${bnb_price} ({bnb_change:.2f}%)")

    async def fetch_current_prices(self):
        """从币安API获取BTC和BNB的当前价格"""
        try:
            async with aiohttp.ClientSession() as session:
                # 获取BTC价格
                async with session.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT") as response:
                    if response.status != 200:
                        logging.error(f"获取BTC价格失败，状态码: {response.status}")
                        return None, None
                    btc_data = await response.json()
                    btc_price = float(btc_data["price"])
                
                # 获取BNB价格
                async with session.get("https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT") as response:
                    if response.status != 200:
                        logging.error(f"获取BNB价格失败，状态码: {response.status}")
                        return None, None
                    bnb_data = await response.json()
                    bnb_price = float(bnb_data["price"])
                
                return btc_price, bnb_price
        except Exception as e:
            logging.error(f"获取价格时发生错误: {str(e)}")
            return None, None

    def _update_price_history(self, symbol, price, timestamp):
        """更新价格历史记录"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        # 记录价格和时间戳
        self.price_history[symbol].append((timestamp, price))
        
        # 只保留最近24小时的数据
        cutoff = timestamp - timedelta(hours=24)
        self.price_history[symbol] = [entry for entry in self.price_history[symbol] if entry[0] >= cutoff]

    def _calculate_price_change(self, old_price, new_price):
        """计算价格变化百分比"""
        if old_price == 0:
            return 0
        return ((new_price - old_price) / old_price) * 100

    async def _send_volatility_alert(self, symbol, current_price, last_price, change_percent):
        """发送价格波动警报"""
        trend = "上涨" if change_percent > 0 else "下跌"
        change_abs = abs(change_percent)
        
        # 构建Markdown格式的消息
        markdown_text = f"""
**{symbol}价格大幅波动通知**

📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
💰 当前价格：${current_price:.2f}
📊 变化幅度：{trend}{change_abs:.2f}%
📉 上次价格：${last_price:.2f}

**请关注市场动态！**
"""
        
        try:
            await asyncio.to_thread(
                send_dingtalk_notification, markdown_text, DING_SECRET, DING_TOKEN
            )
            logging.info(f"{symbol}价格波动通知已发送: {change_percent:.2f}%")
        except Exception as e:
            logging.error(f"发送{symbol}价格波动通知失败: {str(e)}")