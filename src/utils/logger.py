"""로깅 유틸리티"""
import logging


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"mintobot.{name}")
