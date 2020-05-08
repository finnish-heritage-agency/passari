import logging

from passari.config import CONFIG


logging.basicConfig(level=CONFIG["logging"]["level"])
logger = logging.getLogger("passari")
