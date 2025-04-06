# encoding: utf-8
import logging
from logging.handlers import RotatingFileHandler


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    )

    # 文件处理器（保持UTF-8编码）
    file_handler = RotatingFileHandler(
        "sbot.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(module)s:%(lineno)d]: %(message)s"
        )
    )

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)