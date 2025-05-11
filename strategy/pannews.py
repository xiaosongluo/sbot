# encoding: utf-8
from http import HTTPStatus
import json
import logging
from os import linesep
from config import CONFIG_MANAGER
from strategy.base import BaseHandler
from dashscope import Application


class PANNewsHandler(BaseHandler):
    def __init__(self):
        pass

    async def handle_message(self, event):
        # 处理消息的逻辑
        logging.info(f"Handling PANNews message: {event}")

        content = self._parse_message(event)
        markdown_text = self._format_message(content)
        msg = event.message

        analysis_result = await self._analyze_content(msg.text)

        if analysis_result:
            try:
                # 解析 JSON 字符串
                result_dict = json.loads(
                    analysis_result.text.strip("```json\n").strip("```")
                )
                if result_dict is not None:
                    if (
                        # 有影响 & 强相关 & 当前发生的
                        result_dict.get("result") != "NONE"
                        and result_dict.get("relevance") == "STRONG"
                        and result_dict.get("tense") == "PRESENT"
                        and result_dict.get("analysis") != "NONE"
                    ):
                        await self._send_notification(
                            markdown_text
                            + f"\n分析结果: {result_dict['result']}\n分析详情: {result_dict['analysis']}"
                        )
                    else:
                        logging.info(f"非关注信息: {content.replace(linesep, ' ')}")
            except (json.JSONDecodeError, KeyError) as e:
                logging.error(f"解析分析结果时出错: {e}")
        else:
            logging.info(f"非关注信息: {content.replace(linesep, ' ')}")

    async def _analyze_content(self, content):
        try:
            logging.info(f"Handling PANNews message LLM prompt: {content}")
            response = Application.call(
                api_key=CONFIG_MANAGER.get("DASHSCOPE_API_KEY"),
                app_id=CONFIG_MANAGER.get("DASHSCOPE_APP_ID"),
                prompt=content,
            )
            if response.status_code != HTTPStatus.OK:
                logging.error(f"request_id={response.request_id}")
                logging.error(f"code={response.status_code}")
                logging.error(f"message={response.message}")
                logging.error(
                    "请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code"
                )
                return None
            else:
                try:
                    logging.info(
                        f"Handling PANNews message LLM raw result: {response.output}"
                    )
                    return response.output
                except AttributeError:
                    logging.error("无法从响应中获取输出信息。")
                    return None
        except Exception as e:
            logging.error(f"调用百炼模型时发生错误: {e}")
            return None
