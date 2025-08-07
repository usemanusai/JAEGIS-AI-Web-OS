/**
 * Z.ai SDK Client
 * Production-ready integration with z-ai-web-dev-sdk for full-stack generation
 */

import { Logger } from '../../../utils/logger';
import { ParsedBuildDocument } from '../parser/BuildDocumentParser';
import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { EventEmitter } from 'events';

export interface ZaiGenerationRequest {
  baseDocument: ParsedBuildDocument;
  masterPrompt: string;
  options: ZaiGenerationOptions;
}

export interface ZaiGenerationOptions {
  framework: 'nextjs' | 'react' | 'vue' | 'angular';
  database: 'prisma' | 'mongodb' | 'postgresql' | 'mysql';
  styling: 'tailwind' | 'styled-components' | 'emotion' | 'css-modules';
  features: string[];
  complexity: 'simple' | 'moderate' | 'complex';
  performance: 'standard' | 'optimized' | 'enterprise';
  streaming: boolean;
  maxTokens?: number;
  temperature?: number;
}

export interface ZaiGenerationResponse {
  success: boolean;
  modifiedDocument: ParsedBuildDocument;
  generationId: string;
  metadata: {
    tokensUsed: number;
    processingTime: number;
    complexity: number;
    confidence: number;
  };
  warnings: string[];
  suggestions: string[];
}

export interface ZaiStreamChunk {
  type: 'progress' | 'content' | 'complete' | 'error';
  data: any;
  timestamp: Date;
}

export interface ZaiRateLimitInfo {
  requestsRemaining: number;
  resetTime: Date;
  dailyLimit: number;
  currentUsage: number;
}

export class ZaiSDKClient extends EventEmitter {
  private logger: Logger;
  private apiKey: string;
  private baseURL: string;
  private client: AxiosInstance;
  private rateLimitInfo: ZaiRateLimitInfo | null = null;
  private requestQueue: Array<() => Promise<any>> = [];
  private isProcessingQueue: boolean = false;
  private initialized: boolean = false;

  // Configuration
  private readonly MAX_RETRIES = 3;
  private readonly RETRY_DELAY_MS = 2000;
  private readonly REQUEST_TIMEOUT_MS = 300000; // 5 minutes
  private readonly MAX_CHUNK_SIZE = 50000; // 50KB chunks
  private readonly RATE_LIMIT_BUFFER = 5; // Keep 5 requests in reserve

  constructor(apiKey: string, baseURL: string = 'https://api.z.ai') {
    super();
    this.apiKey = apiKey;
    this.baseURL = baseURL;
    this.logger = new Logger('ZaiSDKClient');
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: this.REQUEST_TIMEOUT_MS,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        'User-Agent': 'JAEGIS-MCP-Server/1.0.0'
      }
    });

    this.setupInterceptors();
  }

  async initialize(): Promise<void> {
    this.logger.info('Initializing Z.ai SDK Client');
    
    try {
      // Validate API key and get rate limit info
      await this.validateApiKey();
      await this.getRateLimitInfo();
      
      this.initialized = true;
      this.logger.info('Z.ai SDK Client initialized successfully');
      
      // Start processing queue
      this.processRequestQueue();
      
    } catch (error) {
      this.logger.error('Failed to initialize Z.ai SDK Client', error);
      throw new Error(`Z.ai SDK initialization failed: ${error.message}`);
    }
  }

  /**
   * Generate full-stack application modifications
   */
  async generateFullStack(request: ZaiGenerationRequest): Promise<ZaiGenerationResponse> {
    if (!this.initialized) {
      throw new Error('Z.ai SDK Client not initialized');
    }

    this.logger.info('Starting full-stack generation request');
    
    try {
      // Validate request
      this.validateGenerationRequest(request);
      
      // Check rate limits
      await this.checkRateLimit();
      
      // Prepare request payload
      const payload = await this.prepareGenerationPayload(request);
      
      // Execute generation with retry logic
      const response = await this.executeWithRetry(async () => {
        if (request.options.streaming) {
          return await this.generateFullStackStreaming(payload);
        } else {
          return await this.generateFullStackBatch(payload);
        }
      });

      this.logger.info(`Full-stack generation completed: ${response.generationId}`);
      return response;

    } catch (error) {
      this.logger.error('Full-stack generation failed', error);
      throw new Error(`Generation failed: ${error.message}`);
    }
  }

  /**
   * Generate with streaming response
   */
  private async generateFullStackStreaming(payload: any): Promise<ZaiGenerationResponse> {
    return new Promise((resolve, reject) => {
      const generationId = this.generateRequestId();
      let accumulatedResponse = '';
      let metadata = {};
      
      this.logger.info(`Starting streaming generation: ${generationId}`);

      const streamRequest = this.client.post('/v1/generate/fullstack/stream', payload, {
        responseType: 'stream',
        headers: {
          'X-Generation-ID': generationId,
          'Accept': 'text/event-stream'
        }
      });

      streamRequest.then(response => {
        response.data.on('data', (chunk: Buffer) => {
          try {
            const lines = chunk.toString().split('\n');
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                const streamChunk: ZaiStreamChunk = {
                  type: data.type,
                  data: data.data,
                  timestamp: new Date()
                };

                this.emit('streamChunk', streamChunk);

                switch (data.type) {
                  case 'progress':
                    this.logger.debug(`Generation progress: ${data.data.progress}%`);
                    break;
                    
                  case 'content':
                    accumulatedResponse += data.data.content;
                    break;
                    
                  case 'metadata':
                    metadata = { ...metadata, ...data.data };
                    break;
                    
                  case 'complete':
                    const modifiedDocument = this.parseGeneratedDocument(accumulatedResponse);
                    resolve({
                      success: true,
                      modifiedDocument,
                      generationId,
                      metadata: metadata as any,
                      warnings: data.data.warnings || [],
                      suggestions: data.data.suggestions || []
                    });
                    break;
                    
                  case 'error':
                    reject(new Error(data.data.message));
                    break;
                }
              }
            }
          } catch (parseError) {
            this.logger.warn('Failed to parse stream chunk', parseError);
          }
        });

        response.data.on('end', () => {
          this.logger.debug('Stream ended');
        });

        response.data.on('error', (error: Error) => {
          this.logger.error('Stream error', error);
          reject(error);
        });

      }).catch(reject);

      // Set timeout for streaming
      setTimeout(() => {
        reject(new Error('Streaming generation timeout'));
      }, this.REQUEST_TIMEOUT_MS);
    });
  }

  /**
   * Generate with batch response
   */
  private async generateFullStackBatch(payload: any): Promise<ZaiGenerationResponse> {
    const generationId = this.generateRequestId();
    
    this.logger.info(`Starting batch generation: ${generationId}`);

    const response = await this.client.post('/v1/generate/fullstack', payload, {
      headers: {
        'X-Generation-ID': generationId
      }
    });

    if (!response.data.success) {
      throw new Error(response.data.error || 'Generation failed');
    }

    const modifiedDocument = this.parseGeneratedDocument(response.data.modifiedDocument);

    return {
      success: true,
      modifiedDocument,
      generationId,
      metadata: response.data.metadata,
      warnings: response.data.warnings || [],
      suggestions: response.data.suggestions || []
    };
  }

  /**
   * Validate API key
   */
  private async validateApiKey(): Promise<void> {
    try {
      const response = await this.client.get('/v1/auth/validate');
      
      if (!response.data.valid) {
        throw new Error('Invalid API key');
      }
      
      this.logger.info('API key validated successfully');
      
    } catch (error) {
      if (error.response?.status === 401) {
        throw new Error('Invalid or expired API key');
      }
      throw error;
    }
  }

  /**
   * Get current rate limit information
   */
  private async getRateLimitInfo(): Promise<ZaiRateLimitInfo> {
    try {
      const response = await this.client.get('/v1/auth/rate-limit');
      
      this.rateLimitInfo = {
        requestsRemaining: response.data.requestsRemaining,
        resetTime: new Date(response.data.resetTime),
        dailyLimit: response.data.dailyLimit,
        currentUsage: response.data.currentUsage
      };

      this.logger.debug('Rate limit info updated', this.rateLimitInfo);
      return this.rateLimitInfo;
      
    } catch (error) {
      this.logger.warn('Failed to get rate limit info', error);
      throw error;
    }
  }

  /**
   * Check if we can make a request within rate limits
   */
  private async checkRateLimit(): Promise<void> {
    if (!this.rateLimitInfo) {
      await this.getRateLimitInfo();
    }

    if (this.rateLimitInfo!.requestsRemaining <= this.RATE_LIMIT_BUFFER) {
      const waitTime = this.rateLimitInfo!.resetTime.getTime() - Date.now();
      
      if (waitTime > 0) {
        this.logger.warn(`Rate limit approaching, waiting ${waitTime}ms`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        await this.getRateLimitInfo();
      }
    }
  }

  /**
   * Execute request with retry logic
   */
  private async executeWithRetry<T>(operation: () => Promise<T>): Promise<T> {
    let lastError: Error;
    
    for (let attempt = 1; attempt <= this.MAX_RETRIES; attempt++) {
      try {
        return await operation();
        
      } catch (error) {
        lastError = error;
        
        if (attempt === this.MAX_RETRIES) {
          break;
        }

        // Check if error is retryable
        if (this.isRetryableError(error)) {
          const delay = this.RETRY_DELAY_MS * Math.pow(2, attempt - 1); // Exponential backoff
          this.logger.warn(`Request failed (attempt ${attempt}/${this.MAX_RETRIES}), retrying in ${delay}ms`, error);
          await new Promise(resolve => setTimeout(resolve, delay));
        } else {
          throw error;
        }
      }
    }

    throw lastError!;
  }

  /**
   * Check if error is retryable
   */
  private isRetryableError(error: any): boolean {
    if (error.response) {
      const status = error.response.status;
      return status >= 500 || status === 429; // Server errors or rate limiting
    }
    
    return error.code === 'ECONNRESET' || error.code === 'ETIMEDOUT';
  }

  /**
   * Validate generation request
   */
  private validateGenerationRequest(request: ZaiGenerationRequest): void {
    if (!request.baseDocument) {
      throw new Error('Base document is required');
    }
    
    if (!request.masterPrompt || request.masterPrompt.trim().length === 0) {
      throw new Error('Master prompt is required');
    }
    
    if (request.masterPrompt.length > 50000) {
      throw new Error('Master prompt too long (max 50,000 characters)');
    }
    
    if (!request.options.framework) {
      throw new Error('Framework option is required');
    }
  }

  /**
   * Prepare generation payload
   */
  private async prepareGenerationPayload(request: ZaiGenerationRequest): Promise<any> {
    const payload = {
      baseDocument: this.sanitizeDocument(request.baseDocument),
      masterPrompt: this.sanitizePrompt(request.masterPrompt),
      options: {
        ...request.options,
        clientVersion: '1.0.0',
        timestamp: new Date().toISOString()
      }
    };

    // Handle large documents with chunking
    if (JSON.stringify(payload).length > this.MAX_CHUNK_SIZE) {
      return await this.chunkLargePayload(payload);
    }

    return payload;
  }

  /**
   * Sanitize document for security
   */
  private sanitizeDocument(document: ParsedBuildDocument): ParsedBuildDocument {
    // Remove potentially dangerous commands or file paths
    const sanitized = JSON.parse(JSON.stringify(document));
    
    sanitized.steps = sanitized.steps.map((step: any) => {
      if (step.command) {
        // Remove dangerous commands
        const dangerousPatterns = [
          /rm\s+-rf/,
          /sudo/,
          /chmod\s+777/,
          /curl.*\|\s*sh/,
          /wget.*\|\s*sh/
        ];
        
        for (const pattern of dangerousPatterns) {
          if (pattern.test(step.command)) {
            this.logger.warn(`Potentially dangerous command sanitized: ${step.command}`);
            step.command = `# SANITIZED: ${step.command}`;
          }
        }
      }
      
      return step;
    });

    return sanitized;
  }

  /**
   * Sanitize prompt for security
   */
  private sanitizePrompt(prompt: string): string {
    // Remove potential injection attempts
    return prompt
      .replace(/```[\s\S]*?```/g, '[CODE_BLOCK]') // Replace code blocks
      .replace(/<script[\s\S]*?<\/script>/gi, '[SCRIPT_REMOVED]') // Remove scripts
      .trim();
  }

  /**
   * Handle large payload chunking
   */
  private async chunkLargePayload(payload: any): Promise<any> {
    // Implementation for handling large payloads
    this.logger.info('Chunking large payload for processing');
    
    // For now, return the payload as-is
    // In production, implement proper chunking strategy
    return payload;
  }

  /**
   * Parse generated document response
   */
  private parseGeneratedDocument(response: any): ParsedBuildDocument {
    try {
      if (typeof response === 'string') {
        return JSON.parse(response);
      }
      return response;
    } catch (error) {
      throw new Error(`Failed to parse generated document: ${error.message}`);
    }
  }

  /**
   * Generate unique request ID
   */
  private generateRequestId(): string {
    return `zai_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Setup axios interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        this.logger.debug(`Making request to: ${config.url}`);
        return config;
      },
      (error) => {
        this.logger.error('Request interceptor error', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        // Update rate limit info from headers
        this.updateRateLimitFromHeaders(response.headers);
        return response;
      },
      (error) => {
        if (error.response) {
          this.updateRateLimitFromHeaders(error.response.headers);
          this.logger.error(`API error: ${error.response.status} - ${error.response.data?.message || error.message}`);
        } else {
          this.logger.error('Network error', error);
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Update rate limit info from response headers
   */
  private updateRateLimitFromHeaders(headers: any): void {
    if (headers['x-ratelimit-remaining']) {
      if (!this.rateLimitInfo) {
        this.rateLimitInfo = {
          requestsRemaining: 0,
          resetTime: new Date(),
          dailyLimit: 0,
          currentUsage: 0
        };
      }
      
      this.rateLimitInfo.requestsRemaining = parseInt(headers['x-ratelimit-remaining']);
      
      if (headers['x-ratelimit-reset']) {
        this.rateLimitInfo.resetTime = new Date(parseInt(headers['x-ratelimit-reset']) * 1000);
      }
    }
  }

  /**
   * Process request queue for rate limiting
   */
  private async processRequestQueue(): Promise<void> {
    if (this.isProcessingQueue || this.requestQueue.length === 0) {
      return;
    }

    this.isProcessingQueue = true;

    while (this.requestQueue.length > 0) {
      await this.checkRateLimit();
      
      const request = this.requestQueue.shift();
      if (request) {
        try {
          await request();
        } catch (error) {
          this.logger.error('Queued request failed', error);
        }
      }

      // Small delay between requests
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    this.isProcessingQueue = false;
  }

  /**
   * Get current rate limit status
   */
  getRateLimitStatus(): ZaiRateLimitInfo | null {
    return this.rateLimitInfo;
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/v1/health');
      return response.data.status === 'healthy';
    } catch (error) {
      this.logger.error('Health check failed', error);
      return false;
    }
  }
}

export default ZaiSDKClient;