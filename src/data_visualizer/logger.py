import logging
import sys
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    """
    A custom log formatter that adds color to log levels for console output.
    """
    LEVEL_COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA
    }

    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelno)
        record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)

def setup_logger():
    """
    Configures and returns a logger for the application.

    The logger will output to:
    1. The console with colored log levels.
    2. A file named 'app.log'.
    """
    logger = logging.getLogger("DataVisualizerApp")
    logger.setLevel(logging.INFO)

    # Prevent logs from being propagated to the root logger
    logger.propagate = False

    # If handlers are already present, do not add them again
    if logger.hasHandlers():
        return logger

    # --- Console Handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColoredFormatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # --- File Handler ---
    file_handler = logging.FileHandler("app.log", mode='w')
    file_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] (%(name)s:%(funcName)s) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

# Create a logger instance to be imported by other modules
log = setup_logger()