"""Logging configuration for STIX Agent."""
import logging
import sys
from pathlib import Path
from typing import Optional


class STIXAgentLogger:
    """Centralized logging for STIX Agent."""
    
    _logger: Optional[logging.Logger] = None
    _debug_mode: bool = False
    
    @classmethod
    def setup(
        cls,
        debug: bool = False,
        log_file: Optional[str] = None,
        log_level: str = "INFO"
    ):
        """Setup logger configuration.
        
        Args:
            debug: Enable debug mode (more verbose logging)
            log_file: Optional log file path
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        cls._debug_mode = debug
        
        # Create logger
        logger = logging.getLogger("stixagent")
        logger.setLevel(logging.DEBUG if debug else getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
        
        cls._logger = logger
        
        # Log initialization
        logger.info(f"Logger initialized (debug={debug}, level={log_level})")
        if debug:
            logger.debug("Debug mode enabled - detailed logging active")
    
    @classmethod
    def get_logger(cls) -> logging.Logger:
        """Get the logger instance."""
        if cls._logger is None:
            cls.setup()
        return cls._logger
    
    @classmethod
    def is_debug(cls) -> bool:
        """Check if debug mode is enabled."""
        return cls._debug_mode
    
    @classmethod
    def log_agent_step(cls, step: str, details: dict = None):
        """Log an agent step with details.
        
        Args:
            step: Step name/description
            details: Optional details dictionary
        """
        logger = cls.get_logger()
        if details:
            # Filter out complex objects for logging
            simple_details = {k: v for k, v in details.items() if not isinstance(v, (list, dict))}
            details_str = ", ".join([f"{k}={v}" for k, v in simple_details.items()])
            logger.info(f"[AGENT] {step} | {details_str}")
        else:
            logger.info(f"[AGENT] {step}")
    
    @classmethod
    def log_react_cycle(cls, cycle: str, state: dict = None):
        """Log ReAct cycle information.
        
        Args:
            cycle: Cycle type (think, act, observe)
            state: Optional state information
        """
        logger = cls.get_logger()
        if cls._debug_mode and state:
            state_str = ", ".join([f"{k}={v}" for k, v in state.items() if not isinstance(v, (list, dict))])
            logger.debug(f"[REACT-{cycle.upper()}] {state_str}")
        else:
            logger.debug(f"[REACT-{cycle.upper()}]")
    
    @classmethod
    def log_tool_call(cls, tool_name: str, args: dict = None, result: str = None):
        """Log tool call information.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            result: Tool result (truncated if long)
        """
        logger = cls.get_logger()
        if cls._debug_mode:
            args_str = f"args={args}" if args else ""
            result_preview = result[:200] + "..." if result and len(result) > 200 else result
            logger.debug(f"[TOOL] {tool_name} | {args_str} | result={result_preview}")
        else:
            logger.info(f"[TOOL] {tool_name} called")
    
    @classmethod
    def log_chunk_processing(cls, chunk_index: int, total_chunks: int, status: str):
        """Log chunk processing status.
        
        Args:
            chunk_index: Current chunk index
            total_chunks: Total number of chunks
            status: Processing status
        """
        logger = cls.get_logger()
        logger.info(f"[CHUNK] Processing {chunk_index}/{total_chunks} | {status}")


# Convenience functions
def get_logger() -> logging.Logger:
    """Get the logger instance."""
    return STIXAgentLogger.get_logger()

def setup_logging(debug: bool = False, log_file: Optional[str] = None):
    """Setup logging configuration."""
    STIXAgentLogger.setup(debug=debug, log_file=log_file)

def log_agent_step(step: str, details: dict = None):
    """Log an agent step."""
    STIXAgentLogger.log_agent_step(step, details)

def log_react_cycle(cycle: str, state: dict = None):
    """Log ReAct cycle."""
    STIXAgentLogger.log_react_cycle(cycle, state)

def log_tool_call(tool_name: str, args: dict = None, result: str = None):
    """Log tool call."""
    STIXAgentLogger.log_tool_call(tool_name, args, result)

def log_chunk_processing(chunk_index: int, total_chunks: int, status: str):
    """Log chunk processing."""
    STIXAgentLogger.log_chunk_processing(chunk_index, total_chunks, status)

