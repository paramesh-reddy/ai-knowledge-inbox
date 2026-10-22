"""Secret-safe logging configuration."""
import logging
import re
import sys
from typing import Optional


class SecretMaskingFilter(logging.Filter):
    """Filters out potential API keys and secrets from log messages."""

    SECRET_PATTERN = re.compile(r"(AIza[0-9A-Za-z-_]{35}|key-[0-9a-zA-Z]{20,})")

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.SECRET_PATTERN.sub("[REDACTED_SECRET]", record.msg)
        return True


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configures root logger with secret scrubbing filter."""
    logger = logging.getLogger("ai_knowledge_inbox")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SecretMaskingFilter())
        logger.addHandler(handler)

    return logger


logger = setup_logging()
