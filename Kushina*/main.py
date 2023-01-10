import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, MutableMapping

import aiorun
import colorlog
import dotenv

from . import DEFAULT_CONFIG_PATH
from .core import Kushina
from .util.config import TelegramConfig

log = logging.getLogger("launch")


def _level_check(level: str) -> int:
    _str_to_lvl = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
    }
    if level not in _str_to_lvl:
        return logging.INFO

    return _str_to_lvl[level]


def _setup_log() -> None:
    """Configures logging"""
    level = _level_check(os.environ.get("LOG_LEVEL", "info").upper())
    logging.root.setLevel(level)

    # Color log config
    log_color: bool = os.environ.get("LOG_COLOR") in {"enable", 1, "1", "true"}

    file_format = "[ %(asctime)s: %(levelname)-8s ] %(name)-15s - %(message)s"
    logfile = logging.FileHandler("Anjani.log")
    formatter = logging.Formatter(file_format, datefmt="%H:%M:%S")
    logfile.setFormatter(formatter)
    logfile.setLevel(level)

    if log_color:
        formatter = colorlog.ColoredFormatter(
            "  %(log_color)s%(levelname)-8s%(reset)s  |  "
            "%(name)-15s  |  %(log_color)s%(message)s%(reset)s"
        )
    else:
        formatter = logging.Formatter("  %(levelname)-8s  |  %(name)-15s  |  %(message)s")
    stream = logging.StreamHandler()
    stream.setLevel(level)
    stream.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(stream)
    root.addHandler(logfile)

    # Logging necessary for selected libs
    aiorun.logger.disabled = True
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("pyrogram").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def start() -> None:
    """Main entry point for the bot."""
    config_path = Path(DEFAULT_CONFIG_PATH)
    if config_path.is_file():
        dotenv.load_dotenv(config_path)

    _setup_log()
    log.info(
        "Running on Python %s.%s.%s",
        sys.version_info.major,
        sys.version_info.minor,
        sys.version_info.micro,
    )
    log.info("Loading code")

    if sys.platform == "win32":
        policy = asyncio.WindowsProactorEventLoopPolicy()
        asyncio.set_event_loop_policy(policy)
    else:
        try:
            import uvloop
        except ImportError:
            pass
        else:
            uvloop.install()
            log.info("Using uvloop event loop")

    log.info("Initializing bot")
    loop = asyncio.new_event_loop()

    # Initialize config
    config_data: MutableMapping[str, Any] = {
        "api_id": os.environ.get("API_ID"),
        "api_hash": os.environ.get("API_HASH"),
        "bot_token": os.environ.get("BOT_TOKEN"),
        "db_uri": os.environ.get("DB_URI"),
        "download_path": os.environ.get("DOWNLOAD_PATH"),
        "owner_id": os.environ.get("OWNER_ID"),
        "sw_api": os.environ.get("SW_API"),
        "log_channel": os.environ.get("LOG_CHANNEL"),
        "login_url": os.environ.get("LOGIN_URL"),
    }
    config: TelegramConfig[str, str] = TelegramConfig(config_data)
    if any(key not in config for key in {"api_id", "api_hash", "bot_token", "db_uri"}):
        return log.error("Configuration must be done correctly before running the bot.")

    aiorun.run(Kushina.init_and_run(config, loop=loop), loop=loop)
