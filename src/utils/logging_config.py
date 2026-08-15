from pathlib import Path
import logging


def configure_logging(log_path="logs/analysis.log"):
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("biosignal")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
