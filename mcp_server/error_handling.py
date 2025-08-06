"""
Enhanced Error Handling System

Comprehensive error handling with graceful degradation,
recovery mechanisms, and detailed error reporting.
"""

import sys
import traceback
import functools
from typing import Any, Callable, Optional, Dict, List, Type
from dataclasses import dataclass
from enum import Enum
from contextlib import contextmanager

from loguru import logger


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    VALIDATION = "validation"
    NETWORK = "network"
    FILE_IO = "file_io"
    AI_PROVIDER = "ai_provider"
    TEMPLATE = "template"
    BUILD = "build"
    CONFIGURATION = "configuration"
    SYSTEM = "system"


@dataclass
class ErrorContext:
    """Context information for errors."""
    operation: str
    component: str
    user_data: Dict[str, Any]
    system_state: Dict[str, Any]
    recovery_suggestions: List[str]


@dataclass
class MCPError:
    """Structured error information."""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: str
    context: ErrorContext
    original_exception: Optional[Exception] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            import time
            self.timestamp = time.time()


class MCPException(Exception):
    """Base exception for MCP Server."""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.SYSTEM,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 context: Optional[ErrorContext] = None,
                 original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.context = context
        self.original_exception = original_exception


class ValidationError(MCPException):
    """Validation-related errors."""
    
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(message, ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM, **kwargs)
        self.field = field


class NetworkError(MCPException):
    """Network-related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.NETWORK, ErrorSeverity.HIGH, **kwargs)


class AIProviderError(MCPException):
    """AI provider-related errors."""
    
    def __init__(self, message: str, provider: str = None, **kwargs):
        super().__init__(message, ErrorCategory.AI_PROVIDER, ErrorSeverity.HIGH, **kwargs)
        self.provider = provider


class BuildError(MCPException):
    """Build process errors."""
    
    def __init__(self, message: str, build_step: str = None, **kwargs):
        super().__init__(message, ErrorCategory.BUILD, ErrorSeverity.HIGH, **kwargs)
        self.build_step = build_step


class ErrorHandler:
    """Centralized error handling system."""
    
    def __init__(self):
        self.error_history: List[MCPError] = []
        self.recovery_strategies: Dict[ErrorCategory, List[Callable]] = {}
        self.error_callbacks: List[Callable] = []
        
        # Register default recovery strategies
        self._register_default_strategies()
    
    def handle_error(self, error: Exception, context: Optional[ErrorContext] = None,
                    suppress: bool = False) -> Optional[MCPError]:
        """Handle an error with appropriate response."""
        
        # Create structured error
        mcp_error = self._create_mcp_error(error, context)
        
        # Log the error
        self._log_error(mcp_error)
        
        # Store in history
        self.error_history.append(mcp_error)
        
        # Notify callbacks
        for callback in self.error_callbacks:
            try:
                callback(mcp_error)
            except Exception as e:
                logger.error(f"Error callback failed: {e}")
        
        # Attempt recovery
        recovery_attempted = self._attempt_recovery(mcp_error)
        
        # Re-raise if not suppressed and no recovery
        if not suppress and not recovery_attempted:
            if isinstance(error, MCPException):
                raise error
            else:
                raise MCPException(
                    str(error),
                    category=mcp_error.category,
                    severity=mcp_error.severity,
                    context=context,
                    original_exception=error
                )
        
        return mcp_error
    
    def _create_mcp_error(self, error: Exception, context: Optional[ErrorContext]) -> MCPError:
        """Create structured error from exception."""
        
        # Determine category and severity
        if isinstance(error, MCPException):
            category = error.category
            severity = error.severity
        else:
            category = self._classify_error(error)
            severity = self._assess_severity(error, category)
        
        # Generate error ID
        import hashlib
        import time
        error_id = hashlib.md5(f"{type(error).__name__}:{str(error)[:100]}:{time.time()}".encode()).hexdigest()[:8]
        
        # Create context if not provided
        if context is None:
            context = self._create_default_context(error)
        
        return MCPError(
            error_id=error_id,
            category=category,
            severity=severity,
            message=str(error),
            details=self._get_error_details(error),
            context=context,
            original_exception=error
        )
    
    def _classify_error(self, error: Exception) -> ErrorCategory:
        """Classify error by type."""
        error_type = type(error).__name__.lower()
        
        if 'validation' in error_type or 'value' in error_type:
            return ErrorCategory.VALIDATION
        elif 'network' in error_type or 'connection' in error_type or 'timeout' in error_type:
            return ErrorCategory.NETWORK
        elif 'file' in error_type or 'io' in error_type or 'permission' in error_type:
            return ErrorCategory.FILE_IO
        elif 'config' in error_type:
            return ErrorCategory.CONFIGURATION
        else:
            return ErrorCategory.SYSTEM
    
    def _assess_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Assess error severity."""
        error_type = type(error).__name__.lower()
        
        # Critical errors
        if 'memory' in error_type or 'system' in error_type:
            return ErrorSeverity.CRITICAL
        
        # High severity
        if category in [ErrorCategory.NETWORK, ErrorCategory.AI_PROVIDER, ErrorCategory.BUILD]:
            return ErrorSeverity.HIGH
        
        # Medium severity
        if category in [ErrorCategory.VALIDATION, ErrorCategory.CONFIGURATION]:
            return ErrorSeverity.MEDIUM
        
        # Default to low
        return ErrorSeverity.LOW
    
    def _get_error_details(self, error: Exception) -> str:
        """Get detailed error information."""
        details = []
        
        # Exception type and message
        details.append(f"Exception Type: {type(error).__name__}")
        details.append(f"Message: {str(error)}")
        
        # Traceback
        if hasattr(error, '__traceback__') and error.__traceback__:
            tb_lines = traceback.format_tb(error.__traceback__)
            details.append("Traceback:")
            details.extend(tb_lines)
        
        return "\n".join(details)
    
    def _create_default_context(self, error: Exception) -> ErrorContext:
        """Create default error context."""
        return ErrorContext(
            operation="unknown",
            component="mcp_server",
            user_data={},
            system_state={
                "python_version": sys.version,
                "error_type": type(error).__name__
            },
            recovery_suggestions=self._get_recovery_suggestions(error)
        )
    
    def _get_recovery_suggestions(self, error: Exception) -> List[str]:
        """Get recovery suggestions for error."""
        suggestions = []
        error_str = str(error).lower()
        
        if 'network' in error_str or 'connection' in error_str:
            suggestions.extend([
                "Check internet connection",
                "Verify API endpoints are accessible",
                "Try again in a few moments"
            ])
        elif 'permission' in error_str or 'access' in error_str:
            suggestions.extend([
                "Check file permissions",
                "Run with appropriate privileges",
                "Verify file paths are correct"
            ])
        elif 'api' in error_str or 'key' in error_str:
            suggestions.extend([
                "Verify API key is set correctly",
                "Check API key permissions",
                "Ensure API service is available"
            ])
        else:
            suggestions.append("Check logs for more details")
        
        return suggestions
    
    def _log_error(self, mcp_error: MCPError):
        """Log error with appropriate level."""
        log_message = f"[{mcp_error.error_id}] {mcp_error.message}"
        
        if mcp_error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif mcp_error.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif mcp_error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Log details at debug level
        logger.debug(f"Error details for {mcp_error.error_id}:\n{mcp_error.details}")
    
    def _attempt_recovery(self, mcp_error: MCPError) -> bool:
        """Attempt to recover from error."""
        strategies = self.recovery_strategies.get(mcp_error.category, [])
        
        for strategy in strategies:
            try:
                if strategy(mcp_error):
                    logger.info(f"Recovery successful for error {mcp_error.error_id}")
                    return True
            except Exception as e:
                logger.warning(f"Recovery strategy failed: {e}")
        
        return False
    
    def _register_default_strategies(self):
        """Register default recovery strategies."""
        
        # Network error recovery
        def network_recovery(error: MCPError) -> bool:
            # Could implement retry logic, fallback endpoints, etc.
            return False
        
        # AI provider error recovery
        def ai_provider_recovery(error: MCPError) -> bool:
            # Could implement provider fallback
            return False
        
        # File I/O error recovery
        def file_io_recovery(error: MCPError) -> bool:
            # Could implement alternative file paths, permission fixes, etc.
            return False
        
        self.recovery_strategies[ErrorCategory.NETWORK] = [network_recovery]
        self.recovery_strategies[ErrorCategory.AI_PROVIDER] = [ai_provider_recovery]
        self.recovery_strategies[ErrorCategory.FILE_IO] = [file_io_recovery]
    
    def register_recovery_strategy(self, category: ErrorCategory, strategy: Callable):
        """Register a custom recovery strategy."""
        if category not in self.recovery_strategies:
            self.recovery_strategies[category] = []
        self.recovery_strategies[category].append(strategy)
    
    def register_error_callback(self, callback: Callable):
        """Register an error callback."""
        self.error_callbacks.append(callback)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics."""
        if not self.error_history:
            return {"total_errors": 0}
        
        # Count by category
        category_counts = {}
        severity_counts = {}
        
        for error in self.error_history:
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "by_category": category_counts,
            "by_severity": severity_counts,
            "recent_errors": [
                {
                    "id": error.error_id,
                    "category": error.category.value,
                    "severity": error.severity.value,
                    "message": error.message[:100]
                }
                for error in self.error_history[-5:]  # Last 5 errors
            ]
        }


# Global error handler instance
error_handler = ErrorHandler()


def handle_errors(category: ErrorCategory = ErrorCategory.SYSTEM,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 suppress: bool = False,
                 operation: str = None):
    """Decorator for automatic error handling."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = ErrorContext(
                    operation=operation or func.__name__,
                    component=func.__module__,
                    user_data={"args": str(args)[:100], "kwargs": str(kwargs)[:100]},
                    system_state={},
                    recovery_suggestions=[]
                )
                
                error_handler.handle_error(e, context, suppress)
                
                if suppress:
                    return None
                else:
                    raise
        
        return wrapper
    return decorator


@contextmanager
def error_context(operation: str, component: str = "mcp_server", 
                 user_data: Optional[Dict] = None):
    """Context manager for error handling."""
    try:
        yield
    except Exception as e:
        context = ErrorContext(
            operation=operation,
            component=component,
            user_data=user_data or {},
            system_state={},
            recovery_suggestions=[]
        )
        error_handler.handle_error(e, context)
        raise
