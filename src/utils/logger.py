import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

def get_logger(name: str, level: int = None) -> logging.Logger:
    """
    Get a configured logger instance with file and console handlers.
    
    Args:
        name (str): Name of the logger.
        level (int): Logging level. If None, reads from LOG_LEVEL env var or defaults to INFO.
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.hasHandlers():
        return logger
    
    # Determine logging level
    if level is None:
        level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
        level = getattr(logging, level_name, logging.INFO)
    
    logger.setLevel(level)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation (keeps log files manageable)
    log_file = logs_dir / 'app.log'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Error log file (only ERROR and CRITICAL)
    error_log_file = logs_dir / 'error.log'
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # Debug log file (only when debug level is enabled)
    if level <= logging.DEBUG:
        debug_log_file = logs_dir / 'debug.log'
        debug_handler = RotatingFileHandler(
            debug_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3,  # Fewer backups for debug as they can be verbose
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        logger.addHandler(debug_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)  # Use the same level as the logger
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Log the logger creation
    logger.info(f"Logger '{name}' initialized with level {logging.getLevelName(level)}")
    
    return logger