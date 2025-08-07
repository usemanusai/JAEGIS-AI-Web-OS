# ⚙️ Configuration Reference - JAEGIS AI Web OS

## Overview

JAEGIS AI Web OS provides extensive configuration options for customizing behavior, performance, and integration with external services.

## 📁 Configuration Files

### Primary Configuration (mcp_server.yaml)
`yaml
# AI Provider Settings
ai:
  preferred_provider: "openai"
  request_timeout: 120
  max_retries: 3
  fallback_providers: ["anthropic", "azure", "local"]
  
  # Provider-specific settings
  openai:
    model: "gpt-4"
    temperature: 0.7
    max_tokens: 4000
  
  anthropic:
    model: "claude-3-opus-20240229"
    temperature: 0.7
    max_tokens: 4000
  
  azure:
    deployment_name: "gpt-4"
    api_version: "2023-12-01-preview"

# Redis Caching Configuration
cache:
  enabled: true
  redis:
    url: "redis://localhost:6379"
    password: null
    db: 0
    max_connections: 20
    retry_on_timeout: true
  
  # TTL Settings (in seconds)
  ttl:
    documents: 3600        # 1 hour
    ai_responses: 7200     # 2 hours
    templates: 86400       # 24 hours
    builds: 1800           # 30 minutes
  
  # Compression Settings
  compression:
    enabled: true
    algorithm: "gzip"
    level: 6

# Document Processing
processing:
  max_chunk_size: 4000
  chunk_overlap_size: 200
  supported_formats: [".docx", ".pdf", ".md", ".txt", ".html", ".pptx", ".xlsx"]
  parallel_processing: true
  max_workers: 4
  
  # Format-specific settings
  pdf:
    extract_images: false
    preserve_layout: true
  
  docx:
    extract_tables: true
    preserve_formatting: true

# Logging Configuration
logging:
  level: "INFO"
  file_enabled: true
  rotation: "1 day"
  retention: "30 days"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # Log destinations
  handlers:
    - console
    - file
    - syslog  # Optional

# Template System
templates:
  default_framework: "nextjs"
  custom_templates_dir: "./custom_templates"
  
  # Framework-specific settings
  nextjs:
    version: "15"
    typescript: true
    tailwind: true
    app_router: true
  
  react:
    version: "18"
    typescript: true
    vite: true
  
  python:
    version: "3.8+"
    cli_framework: "click"
    testing_framework: "pytest"

# Security Settings
security:
  api_key_validation: true
  input_sanitization: true
  max_file_size_mb: 100
  allowed_file_types: [".docx", ".pdf", ".md", ".txt", ".html", ".pptx", ".xlsx"]
  
  # Rate limiting
  rate_limiting:
    enabled: true
    requests_per_minute: 60
    burst_limit: 10

# Performance Settings
performance:
  memory_limit_mb: 2048
  cpu_cores: 4
  io_timeout: 30
  
  # Optimization flags
  optimizations:
    enable_parallel_processing: true
    enable_memory_mapping: true
    enable_lazy_loading: true
`

## 🌍 Environment Variables

### Required Variables
`ash
# AI Provider API Keys (at least one required)
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export AZURE_OPENAI_API_KEY="your-azure-api-key"
export AZURE_OPENAI_ENDPOINT="your-azure-endpoint"

# Preferred AI Provider
export MCP_PREFERRED_AI_PROVIDER="openai"
`

### Optional Variables
`ash
# Redis Configuration
export REDIS_URL="redis://localhost:6379"
export REDIS_PASSWORD="your-redis-password"
export REDIS_DB="0"

# Processing Configuration
export MCP_MAX_CHUNK_SIZE="4000"
export MCP_CACHE_ENABLED="true"
export MCP_LOG_LEVEL="INFO"

# Build Configuration
export MCP_BUILD_TIMEOUT="1800"
export MCP_DEFAULT_OUTPUT_DIRECTORY="./output"
export MCP_PARALLEL_PROCESSING="true"

# Security Configuration
export MCP_MAX_FILE_SIZE_MB="100"
export MCP_RATE_LIMIT_ENABLED="true"
`

## 🎯 AI Provider Configuration

### OpenAI Configuration
`yaml
ai:
  openai:
    api_key: "\"
    model: "gpt-4"
    temperature: 0.7
    max_tokens: 4000
    top_p: 1.0
    frequency_penalty: 0.0
    presence_penalty: 0.0
    
    # Advanced settings
    timeout: 120
    max_retries: 3
    retry_delay: 1.0
`

### Anthropic Configuration
`yaml
ai:
  anthropic:
    api_key: "\"
    model: "claude-3-opus-20240229"
    temperature: 0.7
    max_tokens: 4000
    
    # Advanced settings
    timeout: 120
    max_retries: 3
    retry_delay: 1.0
`

### Azure OpenAI Configuration
`yaml
ai:
  azure:
    api_key: "\"
    endpoint: "\"
    deployment_name: "gpt-4"
    api_version: "2023-12-01-preview"
    temperature: 0.7
    max_tokens: 4000
`

## 🗄️ Cache Configuration

### Redis Settings
`yaml
cache:
  enabled: true
  redis:
    # Connection settings
    url: "redis://localhost:6379"
    password: null
    db: 0
    
    # Pool settings
    max_connections: 20
    retry_on_timeout: true
    socket_timeout: 5
    socket_connect_timeout: 5
    
    # Cluster settings (for production)
    cluster:
      enabled: false
      nodes:
        - "redis://node1:6379"
        - "redis://node2:6379"
        - "redis://node3:6379"
`

### TTL Management
`yaml
cache:
  ttl:
    # Document processing cache
    documents: 3600          # 1 hour
    
    # AI response cache
    ai_responses: 7200       # 2 hours
    
    # Template cache
    templates: 86400         # 24 hours
    
    # Build cache
    builds: 1800             # 30 minutes
    
    # User session cache
    user_sessions: 3600      # 1 hour
`

## 📊 Performance Tuning

### Memory Configuration
`yaml
performance:
  # Memory limits
  memory_limit_mb: 2048
  max_chunk_size: 4000
  chunk_overlap_size: 200
  
  # Processing limits
  max_workers: 4
  cpu_cores: 4
  io_timeout: 30
  
  # Optimization flags
  optimizations:
    enable_parallel_processing: true
    enable_memory_mapping: true
    enable_lazy_loading: true
    enable_compression: true
`

### Processing Optimization
`yaml
processing:
  # Parallel processing
  parallel_processing: true
  max_workers: 4
  
  # Chunk processing
  max_chunk_size: 4000
  chunk_overlap_size: 200
  batch_size: 10
  
  # Format-specific optimizations
  pdf:
    use_ocr: false
    extract_images: false
    preserve_layout: true
  
  docx:
    extract_tables: true
    preserve_formatting: true
    process_headers_footers: false
`

## 🔒 Security Configuration

### Input Validation
`yaml
security:
  # File validation
  max_file_size_mb: 100
  allowed_file_types:
    - ".docx"
    - ".pdf"
    - ".md"
    - ".txt"
    - ".html"
    - ".pptx"
    - ".xlsx"
  
  # Content validation
  input_sanitization: true
  api_key_validation: true
  
  # Rate limiting
  rate_limiting:
    enabled: true
    requests_per_minute: 60
    burst_limit: 10
    
  # Access control
  cors:
    enabled: true
    allowed_origins: ["*"]
    allowed_methods: ["GET", "POST"]
`

## 📝 Logging Configuration

### Log Levels and Formats
`yaml
logging:
  # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  level: "INFO"
  
  # Output configuration
  file_enabled: true
  console_enabled: true
  
  # File rotation
  rotation: "1 day"
  retention: "30 days"
  max_size_mb: 100
  
  # Format string
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # Structured logging
  structured: true
  json_format: true
  
  # Log destinations
  handlers:
    - console
    - file
    - syslog
`

## 🏗️ Template Configuration

### Framework Settings
`yaml
templates:
  # Default framework
  default_framework: "nextjs"
  
  # Custom templates directory
  custom_templates_dir: "./custom_templates"
  
  # Framework-specific configurations
  nextjs:
    version: "15"
    typescript: true
    tailwind: true
    app_router: true
    eslint: true
    prettier: true
    
  react:
    version: "18"
    typescript: true
    vite: true
    testing_library: true
    
  python:
    version: "3.8+"
    cli_framework: "click"
    testing_framework: "pytest"
    packaging: "setuptools"
    
  django:
    version: "4.2"
    rest_framework: true
    admin_interface: true
    
  fastapi:
    version: "0.104"
    async_support: true
    auto_docs: true
`

## 🔧 Development Configuration

### Development Mode Settings
`yaml
development:
  # Debug settings
  debug: true
  verbose_logging: true
  
  # Hot reloading
  hot_reload: true
  watch_files: true
  
  # Development server
  dev_server:
    host: "localhost"
    port: 8000
    auto_reload: true
    
  # Testing
  testing:
    auto_run_tests: false
    coverage_threshold: 80
`

## 📋 Configuration Validation

### Validate Configuration
`ash
# Validate configuration file
jaegis-ai-web-os config --validate

# Check specific section
jaegis-ai-web-os config --validate --section ai

# Show current configuration
jaegis-ai-web-os config --show

# Test AI provider connection
jaegis-ai-web-os test --provider openai
`

### Configuration Schema
`yaml
# Schema validation rules
schema:
  ai:
    required: ["preferred_provider"]
    properties:
      preferred_provider:
        type: string
        enum: ["openai", "anthropic", "azure", "local"]
      
  cache:
    properties:
      enabled:
        type: boolean
        default: true
      
  processing:
    properties:
      max_chunk_size:
        type: integer
        minimum: 1000
        maximum: 8000
`

## 🌐 Production Configuration

### Production Optimizations
`yaml
production:
  # Performance settings
  cache:
    enabled: true
    redis:
      cluster: true
      max_connections: 100
  
  # Security hardening
  security:
    rate_limiting:
      enabled: true
      strict_mode: true
    
    input_validation:
      strict: true
      sanitization: true
  
  # Monitoring
  monitoring:
    enabled: true
    metrics_endpoint: "/metrics"
    health_check_endpoint: "/health"
  
  # Logging
  logging:
    level: "WARNING"
    structured: true
    json_format: true
`

---

**Proper configuration ensures optimal performance, security, and reliability for JAEGIS AI Web OS in any environment.**