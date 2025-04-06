# encoding: utf-8
import asyncio
import logging
from os import linesep

from config import DING_SECRET, DING_TOKEN
from utils.dingtalk import send_dingtalk_notification

# 需要转发的关键词
KEY_WORDS = ["TGE", "xiaosongluo"]

class BaseHandler:
    def __init__(self):
        pass

    async def handle_message(self, event):
        content = self._parse_message(event)

        if any(keyword in content for keyword in KEY_WORDS):
            markdown_text = self._format_message(content)
            await self._send_notification(markdown_text)
        else:
            logging.info(f"非关注信息: {content.replace(linesep, ' ')}")

    def _parse_message(self, event):
        """解析消息内容"""
        msg = event.message
        content = [
            f"📅 时间：{event.date.strftime('%Y-%m-%d %H:%M')}\n",
            f"🔔 来源：{event.chat_id}\n",
        ]

        if msg.text:
            content.append(f"📝 内容：\n{msg.text}\n")
        else:
            content.append("📝 内容：[消息包含非文本内容]")

        content.extend(self._parse_media(msg))
        return "\n".join(content)

    def _parse_media(self, msg):
        """解析多媒体内容"""
        media_info = []
        if msg.media:
            if msg.photo and msg.photo.sizes:
                size = msg.photo.sizes[-1]
                media_info.append(f"🖼 图片：{size.w}x{size.h}\n")
            elif msg.document:
                media_info.append(f"📎 文件：{msg.document.attributes[0].file_name}\n")
            elif msg.video:
                media_info.append(f"🎥 视频：{msg.video.duration}秒\n")
        return media_info

    def _format_message(self, content):
        """格式化消息内容"""
        return f"**Telegram 频道更新**\n\n{content}\n"

    async def _send_notification(self, markdown_text):
        """发送钉钉通知"""
        try:
            await asyncio.to_thread(
                send_dingtalk_notification, markdown_text, DING_SECRET, DING_TOKEN
            )
            logging.info("钉钉通知发送成功")
        except Exception as e:
            logging.error(f"钉钉通知发送失败: {str(e)}")
