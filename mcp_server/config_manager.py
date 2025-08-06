"""
Configuration Management System

Enterprise-grade configuration management with environment-specific
settings, validation, and hot-reloading capabilities.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum

from loguru import logger
from dotenv import load_dotenv


class ConfigFormat(Enum):
    """Supported configuration formats."""
    JSON = "json"
    YAML = "yaml"
    ENV = "env"


@dataclass
class ConfigSchema:
    """Configuration schema definition."""
    key: str
    required: bool = False
    default: Any = None
    type_hint: type = str
    description: str = ""
    validation_func: Optional[callable] = None


@dataclass
class MCPServerConfig:
    """Main MCP Server configuration."""
    
    # AI Provider Settings
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    preferred_ai_provider: str = "openai"
    ai_request_timeout: int = 120
    ai_max_retries: int = 3
    
    # Document Processing
    max_chunk_size: int = 4000
    chunk_overlap_size: int = 200
    supported_formats: List[str] = field(default_factory=lambda: ['.docx', '.pdf', '.md', '.txt', '.html', '.pptx', '.xlsx'])
    
    # Code Generation
    default_output_directory: str = "./output"
    template_cache_enabled: bool = True
    template_cache_ttl: int = 3600  # 1 hour
    
    # Build Settings
    build_timeout: int = 1800  # 30 minutes
    parallel_builds: bool = False
    max_parallel_builds: int = 3
    
    # Logging
    log_level: str = "INFO"
    log_file_enabled: bool = True
    log_file_path: str = "logs/mcp_server.log"
    log_rotation: str = "1 day"
    log_retention: str = "30 days"
    
    # Caching
    cache_enabled: bool = True
    cache_directory: str = ".mcp_cache"
    cache_max_size_mb: int = 1024  # 1GB
    cache_ttl_hours: int = 24
    
    # Performance
    worker_threads: int = 4
    memory_limit_mb: int = 2048
    
    # Security
    allow_shell_commands: bool = True
    sandbox_mode: bool = False
    allowed_domains: List[str] = field(default_factory=list)
    
    # Development
    debug_mode: bool = False
    dry_run_default: bool = False
    verbose_output: bool = False


class ConfigManager:
    """Enterprise configuration manager."""
    
    def __init__(self, config_file: Optional[str] = None, environment: str = "development"):
        self.config_file = config_file
        self.environment = environment
        self.config = MCPServerConfig()
        self.schema = self._define_schema()
        self.watchers = []
        
        # Load configuration
        self._load_configuration()
        
        # Validate configuration
        self._validate_configuration()
        
        logger.info(f"Configuration loaded for environment: {environment}")
    
    def _define_schema(self) -> List[ConfigSchema]:
        """Define configuration schema for validation."""
        return [
            ConfigSchema("openai_api_key", required=False, type_hint=str, 
                        description="OpenAI API key for AI features"),
            ConfigSchema("anthropic_api_key", required=False, type_hint=str,
                        description="Anthropic API key for AI features"),
            ConfigSchema("preferred_ai_provider", required=False, default="openai", type_hint=str,
                        description="Preferred AI provider (openai, anthropic, local)"),
            ConfigSchema("max_chunk_size", required=False, default=4000, type_hint=int,
                        description="Maximum chunk size for document processing"),
            ConfigSchema("log_level", required=False, default="INFO", type_hint=str,
                        description="Logging level (DEBUG, INFO, WARNING, ERROR)"),
            ConfigSchema("cache_enabled", required=False, default=True, type_hint=bool,
                        description="Enable caching for improved performance"),
            ConfigSchema("build_timeout", required=False, default=1800, type_hint=int,
                        description="Build timeout in seconds"),
        ]
    
    def _load_configuration(self):
        """Load configuration from multiple sources."""
        
        # 1. Load from environment variables
        load_dotenv()
        self._load_from_environment()
        
        # 2. Load from config file if specified
        if self.config_file:
            self._load_from_file(self.config_file)
        else:
            # Try to find default config files
            self._load_default_config_files()
        
        # 3. Load environment-specific overrides
        self._load_environment_overrides()
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        env_prefix = "MCP_"
        
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                
                # Convert to appropriate type
                converted_value = self._convert_env_value(value)
                
                if hasattr(self.config, config_key):
                    setattr(self.config, config_key, converted_value)
                    logger.debug(f"Loaded from env: {config_key} = {converted_value}")
    
    def _load_from_file(self, file_path: str):
        """Load configuration from file."""
        config_path = Path(file_path)
        
        if not config_path.exists():
            logger.warning(f"Config file not found: {file_path}")
            return
        
        try:
            if config_path.suffix.lower() == '.json':
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
            elif config_path.suffix.lower() in ['.yaml', '.yml']:
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
            else:
                logger.warning(f"Unsupported config file format: {config_path.suffix}")
                return
            
            # Apply configuration
            self._apply_config_dict(file_config)
            logger.info(f"Loaded configuration from: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load config file {file_path}: {e}")
    
    def _load_default_config_files(self):
        """Load from default configuration files."""
        default_files = [
            "mcp_server.json",
            "mcp_server.yaml",
            "mcp_server.yml",
            ".mcp_server.json",
            ".mcp_server.yaml"
        ]
        
        for file_name in default_files:
            if Path(file_name).exists():
                self._load_from_file(file_name)
                break
    
    def _load_environment_overrides(self):
        """Load environment-specific configuration overrides."""
        env_files = [
            f"mcp_server.{self.environment}.json",
            f"mcp_server.{self.environment}.yaml",
            f".mcp_server.{self.environment}.json"
        ]
        
        for file_name in env_files:
            if Path(file_name).exists():
                self._load_from_file(file_name)
                logger.info(f"Applied {self.environment} environment overrides")
                break
    
    def _apply_config_dict(self, config_dict: Dict[str, Any]):
        """Apply configuration from dictionary."""
        for key, value in config_dict.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.debug(f"Applied config: {key} = {value}")
            else:
                logger.warning(f"Unknown configuration key: {key}")
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool, List]:
        """Convert environment variable string to appropriate type."""
        # Boolean conversion
        if value.lower() in ['true', 'yes', '1', 'on']:
            return True
        elif value.lower() in ['false', 'no', '0', 'off']:
            return False
        
        # Number conversion
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # List conversion (comma-separated)
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        
        # Default to string
        return value
    
    def _validate_configuration(self):
        """Validate configuration against schema."""
        errors = []
        warnings = []
        
        for schema_item in self.schema:
            value = getattr(self.config, schema_item.key, None)
            
            # Check required fields
            if schema_item.required and value is None:
                errors.append(f"Required configuration missing: {schema_item.key}")
            
            # Type validation
            if value is not None and not isinstance(value, schema_item.type_hint):
                try:
                    # Try to convert
                    converted_value = schema_item.type_hint(value)
                    setattr(self.config, schema_item.key, converted_value)
                    warnings.append(f"Converted {schema_item.key} to {schema_item.type_hint.__name__}")
                except (ValueError, TypeError):
                    errors.append(f"Invalid type for {schema_item.key}: expected {schema_item.type_hint.__name__}")
            
            # Custom validation
            if value is not None and schema_item.validation_func:
                try:
                    if not schema_item.validation_func(value):
                        errors.append(f"Validation failed for {schema_item.key}")
                except Exception as e:
                    errors.append(f"Validation error for {schema_item.key}: {e}")
        
        # Log warnings
        for warning in warnings:
            logger.warning(warning)
        
        # Raise errors if any
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validation passed")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return getattr(self.config, key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        if hasattr(self.config, key):
            setattr(self.config, key, value)
            logger.debug(f"Configuration updated: {key} = {value}")
        else:
            logger.warning(f"Unknown configuration key: {key}")
    
    def save_to_file(self, file_path: str, format_type: ConfigFormat = ConfigFormat.JSON):
        """Save current configuration to file."""
        config_dict = self._config_to_dict()
        
        try:
            if format_type == ConfigFormat.JSON:
                with open(file_path, 'w') as f:
                    json.dump(config_dict, f, indent=2, default=str)
            elif format_type == ConfigFormat.YAML:
                with open(file_path, 'w') as f:
                    yaml.dump(config_dict, f, default_flow_style=False)
            
            logger.info(f"Configuration saved to: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {file_path}: {e}")
            raise
    
    def _config_to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            key: getattr(self.config, key)
            for key in dir(self.config)
            if not key.startswith('_')
        }
    
    def reload(self):
        """Reload configuration from sources."""
        logger.info("Reloading configuration...")
        self._load_configuration()
        self._validate_configuration()
        logger.info("Configuration reloaded successfully")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary for display."""
        return {
            "environment": self.environment,
            "config_file": self.config_file,
            "ai_provider": self.config.preferred_ai_provider,
            "cache_enabled": self.config.cache_enabled,
            "log_level": self.config.log_level,
            "debug_mode": self.config.debug_mode
        }
