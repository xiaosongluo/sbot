# sbot/price_monitor.py
import asyncio
import logging
from datetime import datetime, timedelta
from config import CONFIG_MANAGER
from utils.dingtalk import send_dingtalk_notification
import aiohttp


class PriceMonitor:
    def __init__(self):
        self.price_symbols = CONFIG_MANAGER.get("PRICE_SYMBOLS")
        self.last_prices = {symbol: None for symbol in self.price_symbols}
        self.last_checked = None
        self.price_history = {
            symbol: [] for symbol in self.price_symbols
        }  # 存储价格历史数据
        self.check_interval = CONFIG_MANAGER.get(
            "PRICE_CHECK_INTERVAL"
        )  # 检查间隔（秒）
        self.threshold = CONFIG_MANAGER.get(
            "PRICE_CHANGE_THRESHOLD"
        )  # 波动阈值（百分比）
        self.proxy = self._get_proxy_config()

    def _get_proxy_config(self):
        """根据环境变量获取代理配置"""
        if CONFIG_MANAGER.get("ENV") == "DEV" and CONFIG_MANAGER.get("PROXY"):
            scheme, host, port = CONFIG_MANAGER.get("PROXY")
            return f"{scheme}://{host}:{port}"
        return None

    async def start_monitoring(self):
        """开始持续监控价格波动"""
        logging.info(
            f"价格监控服务已启动，检查间隔: {self.check_interval}秒，波动阈值: {self.threshold}%"
        )
        while True:
            try:
                await self.check_prices()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logging.error(f"价格监控过程中发生错误: {str(e)}")
                await asyncio.sleep(60)  # 发生错误时等待更长时间

    async def check_prices(self):
        """检查指定交易对的价格波动"""
        current_time = datetime.now()

        # 获取当前价格
        current_prices = await self.fetch_current_prices()
        if not current_prices:
            return

        # 更新价格历史
        for symbol, price in current_prices.items():
            self._update_price_history(symbol, price, current_time)

        # 首次检查，只记录当前价格
        if self.last_checked is None:
            self.last_prices = current_prices
            self.last_checked = current_time
            logging.info(
                f"首次价格检查完成: {', '.join([f'{symbol}=${price}' for symbol, price in current_prices.items()])}"
            )
            return

        # 检查每个交易对的波动
        for symbol, price in current_prices.items():
            old_price = self.last_prices[symbol]
            change = self._calculate_price_change(old_price, price)
            if abs(change) >= self.threshold:
                await self._send_volatility_alert(symbol, price, old_price, change)

                # 更新最后检查价格和时间
        self.last_prices = current_prices
        self.last_checked = current_time
        logging.info(
            f"价格检查完成: {', '.join([f'{symbol}=${price} ({change:.2f}%)' for symbol, price in current_prices.items()])}"
        )

    async def fetch_current_prices(self):
        """从币安API获取指定交易对的当前价格"""
        current_prices = {}
        try:
            async with aiohttp.ClientSession() as session:
                for symbol in self.price_symbols:
                    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
                    async with session.get(url, proxy=self.proxy) as response:
                        if response.status != 200:
                            logging.error(
                                f"获取{symbol}价格失败，状态码: {response.status}"
                            )
                            return None
                        data = await response.json()
                        current_prices[symbol] = float(data["price"])

                return current_prices
        except Exception as e:
            logging.error(f"获取价格时发生错误: {str(e)}")
            return None

    def _update_price_history(self, symbol, price, timestamp):
        """更新价格历史记录"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []

        # 记录价格和时间戳
        self.price_history[symbol].append((timestamp, price))

        # 只保留最近24小时的数据
        cutoff = timestamp - timedelta(hours=24)
        self.price_history[symbol] = [
            entry for entry in self.price_history[symbol] if entry[0] >= cutoff
        ]

    def _calculate_price_change(self, old_price, new_price):
        """计算价格变化百分比"""
        if old_price == 0:
            return 0
        return ((new_price - old_price) / old_price) * 100

    async def _send_volatility_alert(
        self, symbol, current_price, last_price, change_percent
    ):
        """发送价格波动警报"""
        trend = "上涨" if change_percent > 0 else "下跌"
        change_abs = abs(change_percent)

        # 构建Markdown格式的消息
        markdown_text = f"""
**{symbol}价格大幅波动通知**\n
\n
📅 时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n
💰 当前价格：${current_price:.2f}\n
📊 变化幅度：{trend}{change_abs:.2f}%\n
📉 上次价格：${last_price:.2f}\n
\n
**请关注市场动态！**
"""

        try:
            await asyncio.to_thread(
                send_dingtalk_notification,
                "📢市场价格同步通知",
                markdown_text,
                CONFIG_MANAGER.get("DING_SECRET"),
                CONFIG_MANAGER.get("DING_TOKEN"),
            )
            logging.info(f"{symbol}价格波动通知已发送: {change_percent:.2f}%")
        except Exception as e:
            logging.error(f"发送{symbol}价格波动通知失败: {str(e)}")
