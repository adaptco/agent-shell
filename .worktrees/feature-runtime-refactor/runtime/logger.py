import logging
from logging.handlers import RotatingFileHandler
from runtime.config import resolve_path


def get_logger(cfg):
    logger = logging.getLogger("agent_shell")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    log_path = resolve_path(cfg, cfg["logging"]["path"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_path,
        maxBytes=cfg["logging"]["max_bytes"],
        backupCount=cfg["logging"]["backup_count"],
        encoding="utf-8",
    )
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)
    return logger
