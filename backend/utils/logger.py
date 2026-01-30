"""
Logging configuration for the VeoMaster automation platform.
Provides comprehensive logging with file rotation and formatted output.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
import traceback

# Import config for log directory
from config import LOGS_DIR

class CustomFormatter(logging.Formatter):
    """
    Custom formatter with colors for console output and detailed formatting.
    """
    
    # ANSI color codes
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    # Format with timestamp, level, module, and message
    DETAILED_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    SIMPLE_FORMAT = "%(levelname)s: %(message)s"
    
    FORMATS = {
        logging.DEBUG: grey + DETAILED_FORMAT + reset,
        logging.INFO: blue + DETAILED_FORMAT + reset,
        logging.WARNING: yellow + DETAILED_FORMAT + reset,
        logging.ERROR: red + DETAILED_FORMAT + reset,
        logging.CRITICAL: bold_red + DETAILED_FORMAT + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.DETAILED_FORMAT)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)


class Logger:
    """
    Centralized logging manager for the application.
    Handles file and console logging with rotation.
    """
    
    _instances = {}
    
    def __init__(self, name: str, log_file: str = "automation.log", level=logging.INFO):
        """
        Initialize logger with file and console handlers.
        
        Args:
            name: Logger name (usually module name)
            log_file: Name of the log file
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.name = name
        self.logger = logging.getLogger(name)
        
        # Only add handlers if they don't exist (prevent duplicate logs)
        if not self.logger.handlers:
            self.logger.setLevel(level)
            self.logger.propagate = False
            
            # Create logs directory if it doesn't exist
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            
            # File handler with rotation (10MB max, keep 5 backups)
            log_path = LOGS_DIR / log_file
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            
            # Console handler with colors
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(CustomFormatter())
            
            # Add handlers
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, exc_info=False, **kwargs):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info, extra=kwargs)
    
    def critical(self, message: str, exc_info=False, **kwargs):
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info, extra=kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, extra=kwargs)
    
    def log_request(self, method: str, path: str, status_code: int, duration_ms: float):
        """Log API request details"""
        self.info(
            f"{method} {path} - Status: {status_code} - Duration: {duration_ms:.2f}ms"
        )
    
    def log_automation_step(self, job_id: str, video_id: str, step: str, status: str, details: str = ""):
        """Log automation workflow steps"""
        self.info(
            f"[Job: {job_id[:8]}] [Video: {video_id[:8]}] {step} - {status} {details}"
        )
    
    def log_error_with_context(self, error: Exception, context: dict = None):
        """Log error with full context and traceback"""
        error_details = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
        }
        if context:
            error_details.update(context)
        
        self.error(
            f"Error occurred: {error_details['error_type']} - {error_details['error_message']}",
            exc_info=True
        )


def get_logger(name: str, log_file: str = "automation.log", level=logging.INFO) -> Logger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name (usually __name__ from the calling module)
        log_file: Name of the log file
        level: Logging level
    
    Returns:
        Logger instance
    """
    key = f"{name}:{log_file}"
    if key not in Logger._instances:
        Logger._instances[key] = Logger(name, log_file, level)
    return Logger._instances[key]


# Convenience function for API request logging
def log_api_request(method: str, path: str, status_code: int, duration_ms: float):
    """Log API request (used by middleware)"""
    logger = get_logger("api", "api.log")
    logger.log_request(method, path, status_code, duration_ms)


# Convenience function for automation logging
def log_automation_event(job_id: str, video_id: str, step: str, status: str, details: str = ""):
    """Log automation workflow events"""
    logger = get_logger("automation", "automation.log")
    logger.log_automation_step(job_id, video_id, step, status, details)
