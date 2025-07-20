# sbot/price_monitor.py
import asyncio
import logging
from datetime import datetime, timedelta
from config import CONFIG_MANAGER
from utils.dingtalk import send_dingtalk_notification
import aiohttp


class PriceMonitor:
    def __init__(self):
        self.monitor_config = CONFIG_MANAGER.get("PRICE_MONITOR_CONFIG", {})
        self.price_symbols = list(self.monitor_config.keys())
        self.last_prices = {symbol: None for symbol in self.price_symbols}
        self.last_checked = {symbol: {} for symbol in self.price_symbols}
        self.price_history = {symbol: [] for symbol in self.price_symbols}
        self.proxy = self._get_proxy_config()
        self.active_tasks = []

    def _get_proxy_config(self):
        """根据环境变量获取代理配置"""
        if CONFIG_MANAGER.get("ENV") == "DEV" and CONFIG_MANAGER.get("PROXY"):
            scheme, host, port = CONFIG_MANAGER.get("PROXY")
            return f"{scheme}://{host}:{port}"
        return None

    async def start_monitoring(self):
        """开始持续监控价格波动"""
        logging.info(f"价格监控服务已启动，监控币种: {', '.join(self.price_symbols)}")
        
        # 为每个币种的每个策略创建监控任务
        for symbol, strategies in self.monitor_config.items():
            for strategy in strategies:
                task = asyncio.create_task(
                    self._monitor_strategy(symbol, strategy),
                    name=f"monitor_{symbol}_{strategy['interval']}"
                )
                self.active_tasks.append(task)
                logging.info(
                    f"启动{symbol}监控策略: 间隔{strategy['interval']}秒, "
                    f"上涨阈值{strategy['up_threshold']}%, 下跌阈值{strategy['down_threshold']}%"
                )
        
        # 如果没有任何监控任务，记录警告
        if not self.active_tasks:
            logging.warning("没有配置任何监控策略，价格监控服务将保持空闲状态")
        
        # 创建一个永不完成的任务，除非被取消
        # 无论是否有活动任务，都保持服务运行
        pending_forever = asyncio.create_task(asyncio.Event().wait())
        try:
            # 等待任务完成或被取消
            await pending_forever
        except asyncio.CancelledError:
            # 取消所有活动任务
            for task in self.active_tasks:
                if not task.done():
                    task.cancel()
            # 等待所有任务完成取消
            if self.active_tasks:
                await asyncio.gather(*self.active_tasks, return_exceptions=True)
            raise
        finally:
            if not pending_forever.done():
                pending_forever.cancel()

    async def _monitor_strategy(self, symbol, strategy):
        """执行单个监控策略"""
        while True:
            try:
                await self.check_prices(symbol, strategy)
                await asyncio.sleep(strategy["interval"])
            except Exception as e:
                logging.error(f"{symbol}监控策略执行出错: {str(e)}")
                await asyncio.sleep(60)

    async def check_prices(self, symbol, strategy):
        """检查指定交易对的价格波动"""
        current_time = datetime.now()
        
        # 获取当前价格
        price = await self.fetch_single_price(symbol)
        if price is None:
            return

        # 更新价格历史
        self._update_price_history(symbol, price, current_time)

        # 首次检查，只记录当前价格
        if self.last_prices[symbol] is None:
            self.last_prices[symbol] = price
            self.last_checked[symbol][strategy["interval"]] = current_time
            logging.info(f"首次价格检查完成: {symbol}=${price}")
            return

        # 检查波动
        old_price = self.last_prices[symbol]
        change = self._calculate_price_change(old_price, price)
        
        # 使用策略特定阈值判断
        if change >= strategy["up_threshold"] or change <= -strategy["down_threshold"]:
            await self._send_volatility_alert(symbol, price, old_price, change, strategy)

        # 更新最后检查价格和时间
        self.last_prices[symbol] = price
        self.last_checked[symbol][strategy["interval"]] = current_time
        logging.info(f"{symbol}价格检查完成: ${price} ({change:.2f}%)")

    async def fetch_current_prices(self):
        """从币安API批量获取所有交易对的当前价格"""
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
                            continue
                        data = await response.json()
                        current_prices[symbol] = float(data["price"])

                return current_prices
        except Exception as e:
            logging.error(f"获取价格时发生错误: {str(e)}")
            return None

    async def fetch_single_price(self, symbol):
        """从币安API获取单个交易对的当前价格"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
                async with session.get(url, proxy=self.proxy) as response:
                    if response.status != 200:
                        logging.error(
                            f"获取{symbol}价格失败，状态码: {response.status}"
                        )
                        return None
                    logging.info(f"获取{symbol}价格成功，数据: {await response.json()}")
                    data = await response.json()
                    return float(data["price"])
        except Exception as e:
            logging.error(f"获取{symbol}价格时发生错误: {str(e)}")
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
        
    def _format_time_interval(self, seconds):
        """将秒数转换为更易于理解的时间单位"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}分钟"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes == 0:
                return f"{hours}小时"
            return f"{hours}小时{minutes}分钟"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            if hours == 0:
                return f"{days}天"
            return f"{days}天{hours}小时"

    async def _send_volatility_alert(
        self, symbol, current_price, last_price, change_percent, strategy
    ):
        """发送价格波动警报"""
        if change_percent > 0:
            trend = "上涨"
            threshold = strategy["up_threshold"]
        else:
            trend = "下跌"
            threshold = strategy["down_threshold"]
        change_abs = abs(change_percent)

        # 构建Markdown格式的消息
        markdown_text = f"""
**{symbol}价格波动告警通知**\n
\n
📅 时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n
💰 当前价格：${current_price:.2f}\n
📊 变化幅度：{trend}{change_abs:.2f}% (超过{trend}阈值{threshold}%)\n
📉 上次价格：${last_price:.2f}\n
⏱️ 监控策略：每{self._format_time_interval(strategy['interval'])}检查\n
\n
**请及时关注市场变化！**
"""

        try:
            await asyncio.to_thread(
                send_dingtalk_notification,
                f"📢{symbol}价格{trend}告警",
                markdown_text,
                CONFIG_MANAGER.get("DING_SECRET"),
                CONFIG_MANAGER.get("DING_TOKEN"),
            )
            logging.info(f"{symbol}价格{trend}告警已发送: {change_percent:.2f}% (阈值:{threshold}%)")
        except Exception as e:
            logging.error(f"发送{symbol}价格波动通知失败: {str(e)}")