/**
 * Semantic Retriever
 * RAG workflow implementation for intelligent context retrieval
 */

import { Logger } from '../../../utils/logger';
import { RedisVectorStore, VectorSearchOptions, VectorSearchResult } from './RedisVectorStore';
import { VectorConfiguration, SemanticChunk, RetrievedContext } from '../VectorAwareMCPOrchestrator';

export interface RetrievalOptions {
  maxChunks: number;
  scoreThreshold: number;
  diversityFactor: number;
  contextWindow: number;
  includeMetadata: boolean;
  adaptiveRetrieval: boolean;
  multiModalRetrieval: boolean;
}

export interface RetrievalStrategy {
  name: string;
  description: string;
  scoreWeight: number;
  diversityWeight: number;
  recencyWeight: number;
  complexityWeight: number;
}

export interface QueryAnalysis {
  complexity: number;
  intent: QueryIntent;
  domains: string[];
  keywords: string[];
  technicalTerms: string[];
  suggestedStrategy: string;
}

export enum QueryIntent {
  CODE_GENERATION = 'CODE_GENERATION',
  CONFIGURATION = 'CONFIGURATION',
  DOCUMENTATION = 'DOCUMENTATION',
  DEBUGGING = 'DEBUGGING',
  ARCHITECTURE = 'ARCHITECTURE',
  DEPLOYMENT = 'DEPLOYMENT',
  MIXED = 'MIXED'
}

export interface RetrievalMetrics {
  queryTime: number;
  totalCandidates: number;
  finalResults: number;
  averageRelevance: number;
  diversityScore: number;
  cacheHit: boolean;
  strategyUsed: string;
}

export class SemanticRetriever {
  private logger: Logger;
  private vectorStore: RedisVectorStore;
  private config: VectorConfiguration;
  private embeddingService: EmbeddingService;
  private queryCache: Map<string, CachedRetrievalResult>;
  private retrievalStrategies: Map<string, RetrievalStrategy>;
  private metrics: RetrievalMetrics[];
  private initialized: boolean = false;

  // Cache settings
  private readonly CACHE_TTL_MS = 300000; // 5 minutes
  private readonly MAX_CACHE_SIZE = 1000;

  constructor(vectorStore: RedisVectorStore, config: VectorConfiguration) {
    this.logger = new Logger('SemanticRetriever');
    this.vectorStore = vectorStore;
    this.config = config;
    this.embeddingService = new EmbeddingService();
    this.queryCache = new Map();
    this.retrievalStrategies = new Map();
    this.metrics = [];
  }

  async initialize(): Promise<void> {
    try {
      this.logger.info('Initializing Semantic Retriever');
      
      await this.embeddingService.initialize();
      this.initializeRetrievalStrategies();
      this.startCacheCleanup();
      
      this.initialized = true;
      this.logger.info('Semantic Retriever initialized successfully');
      
    } catch (error) {
      this.logger.error('Failed to initialize Semantic Retriever', error);
      throw error;
    }
  }

  /**
   * Vectorize user prompt text
   */
  async vectorizeText(text: string): Promise<number[]> {
    if (!this.initialized) {
      throw new Error('Semantic Retriever not initialized');
    }

    try {
      this.logger.debug('Vectorizing user prompt');
      const vector = await this.embeddingService.generateEmbedding(text);
      return vector;
      
    } catch (error) {
      this.logger.error('Failed to vectorize text', error);
      throw error;
    }
  }

  /**
   * Retrieve relevant chunks using vector similarity search
   */
  async retrieveRelevantChunks(
    queryVector: number[],
    maxChunks: number,
    options: Partial<RetrievalOptions> = {}
  ): Promise<RetrievedContext> {
    if (!this.initialized) {
      throw new Error('Semantic Retriever not initialized');
    }

    const startTime = Date.now();
    const fullOptions: RetrievalOptions = {
      maxChunks,
      scoreThreshold: this.config.similarityThreshold,
      diversityFactor: 0.3,
      contextWindow: 2,
      includeMetadata: true,
      adaptiveRetrieval: true,
      multiModalRetrieval: true,
      ...options
    };

    try {
      this.logger.debug(`Retrieving relevant chunks with options: ${JSON.stringify(fullOptions)}`);

      // Check cache first
      const cacheKey = this.generateCacheKey(queryVector, fullOptions);
      const cachedResult = this.getCachedResult(cacheKey);
      
      if (cachedResult) {
        this.logger.debug('Returning cached retrieval result');
        return this.enhanceCachedResult(cachedResult, startTime);
      }

      // Perform retrieval
      const retrievalResult = await this.performRetrieval(queryVector, fullOptions);
      
      // Cache the result
      this.cacheResult(cacheKey, retrievalResult);
      
      // Update metrics
      const metrics: RetrievalMetrics = {
        queryTime: Date.now() - startTime,
        totalCandidates: retrievalResult.totalCandidates,
        finalResults: retrievalResult.chunks.length,
        averageRelevance: this.calculateAverageRelevance(retrievalResult.chunks),
        diversityScore: this.calculateDiversityScore(retrievalResult.chunks),
        cacheHit: false,
        strategyUsed: retrievalResult.strategyUsed
      };
      
      this.metrics.push(metrics);
      
      return {
        chunks: retrievalResult.chunks,
        totalRelevanceScore: retrievalResult.totalRelevanceScore,
        retrievalTime: Date.now() - startTime,
        queryVector
      };

    } catch (error) {
      this.logger.error('Failed to retrieve relevant chunks', error);
      throw error;
    }
  }

  /**
   * Analyze query to determine optimal retrieval strategy
   */
  async analyzeQuery(queryText: string): Promise<QueryAnalysis> {
    const analysis: QueryAnalysis = {
      complexity: 0,
      intent: QueryIntent.MIXED,
      domains: [],
      keywords: [],
      technicalTerms: [],
      suggestedStrategy: 'balanced'
    };

    // Calculate complexity
    analysis.complexity = this.calculateQueryComplexity(queryText);
    
    // Determine intent
    analysis.intent = this.determineQueryIntent(queryText);
    
    // Extract domains and keywords
    analysis.domains = this.extractDomains(queryText);
    analysis.keywords = this.extractKeywords(queryText);
    analysis.technicalTerms = this.extractTechnicalTerms(queryText);
    
    // Suggest strategy
    analysis.suggestedStrategy = this.suggestRetrievalStrategy(analysis);

    return analysis;
  }

  /**
   * Perform the actual retrieval with strategy selection
   */
  private async performRetrieval(
    queryVector: number[],
    options: RetrievalOptions
  ): Promise<RetrievalResult> {
    
    // Determine retrieval strategy
    const strategy = this.selectRetrievalStrategy(options);
    
    this.logger.debug(`Using retrieval strategy: ${strategy.name}`);

    let allResults: VectorSearchResult[] = [];
    let totalCandidates = 0;

    // Multi-modal retrieval if enabled
    if (options.multiModalRetrieval) {
      const indices = ['jaegis:vectors:code', 'jaegis:vectors:docs', 'jaegis:vectors:api'];
      
      for (const indexName of indices) {
        try {
          const searchOptions: VectorSearchOptions = {
            k: Math.ceil(options.maxChunks * 1.5), // Get more candidates for filtering
            scoreThreshold: options.scoreThreshold,
            includeMetadata: options.includeMetadata,
            includeVectors: false
          };

          const results = await this.vectorStore.searchSimilar(queryVector, searchOptions, indexName);
          allResults.push(...results);
          totalCandidates += results.length;
          
        } catch (error) {
          this.logger.warn(`Failed to search index ${indexName}`, error);
        }
      }
    } else {
      // Single index retrieval
      const searchOptions: VectorSearchOptions = {
        k: options.maxChunks * 2,
        scoreThreshold: options.scoreThreshold,
        includeMetadata: options.includeMetadata,
        includeVectors: false
      };

      allResults = await this.vectorStore.searchSimilar(queryVector, searchOptions);
      totalCandidates = allResults.length;
    }

    // Apply strategy-specific filtering and ranking
    const filteredResults = this.applyStrategyFiltering(allResults, strategy, options);
    
    // Apply diversity filtering
    const diverseResults = this.applyDiversityFiltering(filteredResults, options.diversityFactor);
    
    // Limit to max chunks
    const finalResults = diverseResults.slice(0, options.maxChunks);
    
    // Convert to semantic chunks
    const chunks = await this.convertToSemanticChunks(finalResults);
    
    return {
      chunks,
      totalRelevanceScore: this.calculateTotalRelevanceScore(chunks),
      totalCandidates,
      strategyUsed: strategy.name
    };
  }

  /**
   * Apply strategy-specific filtering and ranking
   */
  private applyStrategyFiltering(
    results: VectorSearchResult[],
    strategy: RetrievalStrategy,
    options: RetrievalOptions
  ): VectorSearchResult[] {
    
    return results
      .map(result => ({
        ...result,
        adjustedScore: this.calculateAdjustedScore(result, strategy)
      }))
      .sort((a, b) => b.adjustedScore - a.adjustedScore)
      .filter(result => result.adjustedScore >= options.scoreThreshold);
  }

  /**
   * Apply diversity filtering to avoid redundant results
   */
  private applyDiversityFiltering(
    results: VectorSearchResult[],
    diversityFactor: number
  ): VectorSearchResult[] {
    
    if (diversityFactor === 0) {
      return results;
    }

    const diverseResults: VectorSearchResult[] = [];
    const usedCategories = new Set<string>();
    const usedLanguages = new Set<string>();

    for (const result of results) {
      const category = result.metadata.category;
      const language = result.metadata.language || 'unknown';
      
      // Calculate diversity penalty
      let diversityPenalty = 0;
      if (usedCategories.has(category)) diversityPenalty += 0.1;
      if (usedLanguages.has(language)) diversityPenalty += 0.05;
      
      // Apply penalty
      const adjustedScore = result.score * (1 - diversityPenalty * diversityFactor);
      
      if (adjustedScore >= 0.1) { // Minimum threshold after penalty
        diverseResults.push({
          ...result,
          score: adjustedScore
        });
        
        usedCategories.add(category);
        usedLanguages.add(language);
      }
    }

    return diverseResults.sort((a, b) => b.score - a.score);
  }

  /**
   * Convert search results to semantic chunks
   */
  private async convertToSemanticChunks(results: VectorSearchResult[]): Promise<SemanticChunk[]> {
    const chunks: SemanticChunk[] = [];
    
    for (const result of results) {
      chunks.push({
        id: result.id,
        content: result.content,
        type: this.inferChunkType(result.metadata),
        relevanceScore: result.score,
        metadata: result.metadata,
        vector: result.vector || []
      });
    }
    
    return chunks;
  }

  /**
   * Initialize retrieval strategies
   */
  private initializeRetrievalStrategies(): void {
    const strategies: RetrievalStrategy[] = [
      {
        name: 'balanced',
        description: 'Balanced approach for general queries',
        scoreWeight: 0.7,
        diversityWeight: 0.2,
        recencyWeight: 0.05,
        complexityWeight: 0.05
      },
      {
        name: 'precision',
        description: 'High precision for specific technical queries',
        scoreWeight: 0.9,
        diversityWeight: 0.05,
        recencyWeight: 0.025,
        complexityWeight: 0.025
      },
      {
        name: 'exploration',
        description: 'Diverse results for exploratory queries',
        scoreWeight: 0.5,
        diversityWeight: 0.4,
        recencyWeight: 0.05,
        complexityWeight: 0.05
      },
      {
        name: 'code_focused',
        description: 'Optimized for code generation tasks',
        scoreWeight: 0.8,
        diversityWeight: 0.1,
        recencyWeight: 0.05,
        complexityWeight: 0.05
      }
    ];

    for (const strategy of strategies) {
      this.retrievalStrategies.set(strategy.name, strategy);
    }
  }

  /**
   * Select optimal retrieval strategy
   */
  private selectRetrievalStrategy(options: RetrievalOptions): RetrievalStrategy {
    if (!options.adaptiveRetrieval) {
      return this.retrievalStrategies.get('balanced')!;
    }

    // Strategy selection logic based on options and context
    if (options.maxChunks <= 5) {
      return this.retrievalStrategies.get('precision')!;
    } else if (options.diversityFactor > 0.5) {
      return this.retrievalStrategies.get('exploration')!;
    } else {
      return this.retrievalStrategies.get('balanced')!;
    }
  }

  /**
   * Calculate adjusted score based on strategy
   */
  private calculateAdjustedScore(result: VectorSearchResult, strategy: RetrievalStrategy): number {
    let adjustedScore = result.score * strategy.scoreWeight;
    
    // Add complexity bonus
    const complexity = result.metadata.complexity || 0;
    adjustedScore += (complexity / 100) * strategy.complexityWeight;
    
    // Add recency bonus (if timestamp available)
    // This would require timestamp metadata
    
    return adjustedScore;
  }

  // Helper methods for query analysis

  private calculateQueryComplexity(queryText: string): number {
    let complexity = 0;
    
    // Length factor
    complexity += Math.min(queryText.length / 100, 5);
    
    // Technical terms
    const technicalTerms = ['implement', 'configure', 'deploy', 'optimize', 'integrate'];
    complexity += technicalTerms.filter(term => queryText.toLowerCase().includes(term)).length;
    
    // Multiple requirements
    const requirements = queryText.split(/and|also|additionally|furthermore/i).length - 1;
    complexity += requirements * 2;
    
    return Math.min(complexity, 10);
  }

  private determineQueryIntent(queryText: string): QueryIntent {
    const lowerText = queryText.toLowerCase();
    
    if (lowerText.includes('implement') || lowerText.includes('code') || lowerText.includes('function')) {
      return QueryIntent.CODE_GENERATION;
    } else if (lowerText.includes('configure') || lowerText.includes('setup') || lowerText.includes('config')) {
      return QueryIntent.CONFIGURATION;
    } else if (lowerText.includes('document') || lowerText.includes('explain') || lowerText.includes('how')) {
      return QueryIntent.DOCUMENTATION;
    } else if (lowerText.includes('debug') || lowerText.includes('fix') || lowerText.includes('error')) {
      return QueryIntent.DEBUGGING;
    } else if (lowerText.includes('architecture') || lowerText.includes('design') || lowerText.includes('structure')) {
      return QueryIntent.ARCHITECTURE;
    } else if (lowerText.includes('deploy') || lowerText.includes('production') || lowerText.includes('server')) {
      return QueryIntent.DEPLOYMENT;
    }
    
    return QueryIntent.MIXED;
  }

  private extractDomains(queryText: string): string[] {
    const domains = [];
    const lowerText = queryText.toLowerCase();
    
    const domainKeywords = {
      'frontend': ['react', 'ui', 'component', 'interface'],
      'backend': ['api', 'server', 'database', 'endpoint'],
      'devops': ['docker', 'deploy', 'ci/cd', 'kubernetes'],
      'database': ['prisma', 'sql', 'query', 'schema'],
      'ai': ['ai', 'ml', 'embedding', 'vector']
    };

    for (const [domain, keywords] of Object.entries(domainKeywords)) {
      if (keywords.some(keyword => lowerText.includes(keyword))) {
        domains.push(domain);
      }
    }
    
    return domains;
  }

  private extractKeywords(queryText: string): string[] {
    // Simple keyword extraction
    return queryText
      .toLowerCase()
      .split(/\s+/)
      .filter(word => word.length > 3)
      .filter(word => !['the', 'and', 'for', 'with', 'that', 'this'].includes(word))
      .slice(0, 10);
  }

  private extractTechnicalTerms(queryText: string): string[] {
    const technicalTerms = [
      'react', 'nextjs', 'prisma', 'docker', 'redis', 'api', 'component',
      'database', 'authentication', 'deployment', 'configuration', 'optimization'
    ];
    
    const lowerText = queryText.toLowerCase();
    return technicalTerms.filter(term => lowerText.includes(term));
  }

  private suggestRetrievalStrategy(analysis: QueryAnalysis): string {
    if (analysis.intent === QueryIntent.CODE_GENERATION) {
      return 'code_focused';
    } else if (analysis.complexity > 7) {
      return 'exploration';
    } else if (analysis.technicalTerms.length > 3) {
      return 'precision';
    }
    
    return 'balanced';
  }

  private inferChunkType(metadata: any): 'CODE' | 'CONFIG' | 'DOCUMENTATION' | 'COMMAND' {
    if (metadata.language && metadata.language !== 'text') {
      return 'CODE';
    } else if (metadata.category === 'configuration') {
      return 'CONFIG';
    } else if (metadata.category === 'documentation') {
      return 'DOCUMENTATION';
    } else if (metadata.category === 'commands') {
      return 'COMMAND';
    }
    
    return 'DOCUMENTATION';
  }

  // Cache management methods

  private generateCacheKey(queryVector: number[], options: RetrievalOptions): string {
    const vectorHash = this.hashVector(queryVector);
    const optionsHash = this.hashObject(options);
    return `${vectorHash}_${optionsHash}`;
  }

  private hashVector(vector: number[]): string {
    // Simple hash for vector (in production, use proper hashing)
    return vector.slice(0, 10).map(v => Math.round(v * 1000)).join('_');
  }

  private hashObject(obj: any): string {
    return Buffer.from(JSON.stringify(obj)).toString('base64').slice(0, 16);
  }

  private getCachedResult(cacheKey: string): CachedRetrievalResult | null {
    const cached = this.queryCache.get(cacheKey);
    
    if (!cached) {
      return null;
    }

    // Check if cache is still valid
    const age = Date.now() - cached.timestamp;
    if (age > this.CACHE_TTL_MS) {
      this.queryCache.delete(cacheKey);
      return null;
    }

    return cached;
  }

  private cacheResult(cacheKey: string, result: RetrievalResult): void {
    // Implement cache size limit
    if (this.queryCache.size >= this.MAX_CACHE_SIZE) {
      // Remove oldest entry
      const oldestKey = this.queryCache.keys().next().value;
      this.queryCache.delete(oldestKey);
    }

    this.queryCache.set(cacheKey, {
      result,
      timestamp: Date.now()
    });
  }

  private enhanceCachedResult(cached: CachedRetrievalResult, startTime: number): RetrievedContext {
    return {
      chunks: cached.result.chunks,
      totalRelevanceScore: cached.result.totalRelevanceScore,
      retrievalTime: Date.now() - startTime,
      queryVector: [] // Vector not stored in cache
    };
  }

  private startCacheCleanup(): void {
    setInterval(() => {
      const now = Date.now();
      for (const [key, cached] of this.queryCache.entries()) {
        const age = now - cached.timestamp;
        if (age > this.CACHE_TTL_MS) {
          this.queryCache.delete(key);
        }
      }
    }, 60000); // Cleanup every minute
  }

  // Metrics and utility methods

  private calculateAverageRelevance(chunks: SemanticChunk[]): number {
    if (chunks.length === 0) return 0;
    return chunks.reduce((sum, chunk) => sum + chunk.relevanceScore, 0) / chunks.length;
  }

  private calculateDiversityScore(chunks: SemanticChunk[]): number {
    const categories = new Set(chunks.map(chunk => chunk.metadata.category));
    const languages = new Set(chunks.map(chunk => chunk.metadata.language).filter(Boolean));
    
    return (categories.size + languages.size) / (chunks.length + 1);
  }

  private calculateTotalRelevanceScore(chunks: SemanticChunk[]): number {
    return chunks.reduce((sum, chunk) => sum + chunk.relevanceScore, 0);
  }

  /**
   * Get retrieval performance metrics
   */
  getAverageRetrievalTime(): number {
    if (this.metrics.length === 0) return 0;
    return this.metrics.reduce((sum, metric) => sum + metric.queryTime, 0) / this.metrics.length;
  }

  /**
   * Get cache hit rate
   */
  getCacheHitRate(): number {
    if (this.metrics.length === 0) return 0;
    const cacheHits = this.metrics.filter(metric => metric.cacheHit).length;
    return cacheHits / this.metrics.length;
  }

  /**
   * Clear cache and metrics
   */
  clearCache(): void {
    this.queryCache.clear();
    this.metrics.length = 0;
    this.logger.info('Semantic retriever cache and metrics cleared');
  }
}

// Supporting interfaces
interface RetrievalResult {
  chunks: SemanticChunk[];
  totalRelevanceScore: number;
  totalCandidates: number;
  strategyUsed: string;
}

interface CachedRetrievalResult {
  result: RetrievalResult;
  timestamp: number;
}

// Embedding service (placeholder - would integrate with actual service)
class EmbeddingService {
  async initialize(): Promise<void> {
    // Initialize embedding model
  }

  async generateEmbedding(text: string): Promise<number[]> {
    // Generate embedding vector
    // This would integrate with OpenAI embeddings API or local model
    return new Array(1536).fill(0).map(() => Math.random() - 0.5);
  }
}

export default SemanticRetriever;