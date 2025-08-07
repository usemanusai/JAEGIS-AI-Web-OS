/**
 * Redis Vector Store
 * High-performance semantic indexing and retrieval using Redis 8 VSS
 */

import Redis from 'ioredis';
import { Logger } from '../../../utils/logger';
import { VectorConfiguration, SemanticChunk, ChunkMetadata } from '../VectorAwareMCPOrchestrator';

export interface VectorIndex {
  name: string;
  dimensions: number;
  algorithm: 'FLAT' | 'HNSW';
  distanceMetric: 'COSINE' | 'L2' | 'IP';
  initialCapacity: number;
  blockSize?: number;
  m?: number; // HNSW parameter
  efConstruction?: number; // HNSW parameter
  efRuntime?: number; // HNSW parameter
}

export interface VectorSearchOptions {
  k: number;
  scoreThreshold?: number;
  filter?: string;
  includeMetadata?: boolean;
  includeVectors?: boolean;
}

export interface VectorSearchResult {
  id: string;
  score: number;
  content: string;
  metadata: ChunkMetadata;
  vector?: number[];
}

export interface IndexStats {
  totalVectors: number;
  indexSize: number;
  memoryUsage: number;
  lastUpdated: Date;
  searchCount: number;
  averageSearchTime: number;
}

export class RedisVectorStore {
  private logger: Logger;
  private redis: Redis;
  private config: VectorConfiguration;
  private indices: Map<string, VectorIndex>;
  private initialized: boolean = false;

  // Index names for different types of content
  private readonly CODE_INDEX = 'jaegis:vectors:code';
  private readonly CONCEPT_INDEX = 'jaegis:vectors:concepts';
  private readonly DOCS_INDEX = 'jaegis:vectors:docs';
  private readonly API_INDEX = 'jaegis:vectors:api';

  constructor(redisUrl: string, config: VectorConfiguration) {
    this.logger = new Logger('RedisVectorStore');
    this.config = config;
    this.indices = new Map();
    
    // Initialize Redis connection
    this.redis = new Redis(redisUrl, {
      retryDelayOnFailover: 100,
      enableReadyCheck: false,
      maxRetriesPerRequest: 3,
      lazyConnect: true
    });

    this.setupRedisEventHandlers();
  }

  async initialize(): Promise<void> {
    try {
      this.logger.info('Initializing Redis Vector Store');
      
      // Connect to Redis
      await this.redis.connect();
      
      // Verify Redis modules
      await this.verifyRedisModules();
      
      // Create vector indices
      await this.createVectorIndices();
      
      this.initialized = true;
      this.logger.info('Redis Vector Store initialized successfully');
      
    } catch (error) {
      this.logger.error('Failed to initialize Redis Vector Store', error);
      throw error;
    }
  }

  /**
   * Store a semantic chunk with its vector embedding
   */
  async storeChunk(chunk: SemanticChunk, indexName?: string): Promise<void> {
    if (!this.initialized) {
      throw new Error('Redis Vector Store not initialized');
    }

    const targetIndex = indexName || this.getIndexForChunkType(chunk.type);
    
    try {
      // Prepare vector data
      const vectorData = {
        id: chunk.id,
        vector: Buffer.from(new Float32Array(chunk.vector).buffer),
        content: chunk.content,
        type: chunk.type,
        relevanceScore: chunk.relevanceScore,
        metadata: JSON.stringify(chunk.metadata)
      };

      // Store in Redis using HSET for the document and vector
      const pipeline = this.redis.pipeline();
      
      // Store document metadata
      pipeline.hset(`${targetIndex}:doc:${chunk.id}`, {
        content: chunk.content,
        type: chunk.type,
        relevanceScore: chunk.relevanceScore,
        metadata: JSON.stringify(chunk.metadata),
        createdAt: new Date().toISOString()
      });

      // Store vector using FT.ADD (if using RediSearch) or direct vector storage
      pipeline.call(
        'HSET',
        `${targetIndex}:vec:${chunk.id}`,
        'vector',
        vectorData.vector,
        'id',
        chunk.id
      );

      await pipeline.exec();
      
      this.logger.debug(`Stored chunk ${chunk.id} in index ${targetIndex}`);
      
    } catch (error) {
      this.logger.error(`Failed to store chunk ${chunk.id}`, error);
      throw error;
    }
  }

  /**
   * Search for similar vectors using VSS
   */
  async searchSimilar(
    queryVector: number[],
    options: VectorSearchOptions,
    indexName?: string
  ): Promise<VectorSearchResult[]> {
    if (!this.initialized) {
      throw new Error('Redis Vector Store not initialized');
    }

    const targetIndex = indexName || this.CODE_INDEX;
    
    try {
      const startTime = Date.now();
      
      // Convert query vector to buffer
      const queryBuffer = Buffer.from(new Float32Array(queryVector).buffer);
      
      // Build search query
      const searchQuery = this.buildVectorSearchQuery(queryBuffer, options, targetIndex);
      
      // Execute vector search
      const searchResults = await this.redis.call('FT.SEARCH', ...searchQuery) as any[];
      
      const searchTime = Date.now() - startTime;
      this.logger.debug(`Vector search completed in ${searchTime}ms`);
      
      // Parse results
      const results = await this.parseSearchResults(searchResults, options);
      
      // Update search statistics
      await this.updateSearchStats(targetIndex, searchTime);
      
      return results;
      
    } catch (error) {
      this.logger.error('Vector search failed', error);
      throw error;
    }
  }

  /**
   * Get chunk by ID
   */
  async getChunk(chunkId: string, indexName?: string): Promise<SemanticChunk | null> {
    if (!this.initialized) {
      throw new Error('Redis Vector Store not initialized');
    }

    const targetIndex = indexName || this.CODE_INDEX;
    
    try {
      // Get document data
      const docData = await this.redis.hgetall(`${targetIndex}:doc:${chunkId}`);
      
      if (!docData.content) {
        return null;
      }

      // Get vector data
      const vectorData = await this.redis.hget(`${targetIndex}:vec:${chunkId}`, 'vector');
      
      if (!vectorData) {
        return null;
      }

      // Convert buffer back to number array
      const vectorBuffer = Buffer.from(vectorData, 'binary');
      const vector = Array.from(new Float32Array(vectorBuffer.buffer));

      return {
        id: chunkId,
        content: docData.content,
        type: docData.type as any,
        relevanceScore: parseFloat(docData.relevanceScore),
        metadata: JSON.parse(docData.metadata),
        vector
      };
      
    } catch (error) {
      this.logger.error(`Failed to get chunk ${chunkId}`, error);
      return null;
    }
  }

  /**
   * Update chunk content and re-index
   */
  async updateChunk(chunkId: string, updates: Partial<SemanticChunk>, indexName?: string): Promise<void> {
    if (!this.initialized) {
      throw new Error('Redis Vector Store not initialized');
    }

    const targetIndex = indexName || this.CODE_INDEX;
    
    try {
      // Get existing chunk
      const existingChunk = await this.getChunk(chunkId, indexName);
      
      if (!existingChunk) {
        throw new Error(`Chunk ${chunkId} not found`);
      }

      // Merge updates
      const updatedChunk: SemanticChunk = {
        ...existingChunk,
        ...updates
      };

      // Re-store the updated chunk
      await this.storeChunk(updatedChunk, indexName);
      
      this.logger.debug(`Updated chunk ${chunkId} in index ${targetIndex}`);
      
    } catch (error) {
      this.logger.error(`Failed to update chunk ${chunkId}`, error);
      throw error;
    }
  }

  /**
   * Delete chunk from index
   */
  async deleteChunk(chunkId: string, indexName?: string): Promise<void> {
    if (!this.initialized) {
      throw new Error('Redis Vector Store not initialized');
    }

    const targetIndex = indexName || this.CODE_INDEX;
    
    try {
      const pipeline = this.redis.pipeline();
      
      // Delete document and vector data
      pipeline.del(`${targetIndex}:doc:${chunkId}`);
      pipeline.del(`${targetIndex}:vec:${chunkId}`);
      
      await pipeline.exec();
      
      this.logger.debug(`Deleted chunk ${chunkId} from index ${targetIndex}`);
      
    } catch (error) {
      this.logger.error(`Failed to delete chunk ${chunkId}`, error);
      throw error;
    }
  }

  /**
   * Get index statistics
   */
  async getIndexStats(indexName?: string): Promise<IndexStats> {
    const targetIndex = indexName || this.CODE_INDEX;
    
    try {
      // Get index info
      const indexInfo = await this.redis.call('FT.INFO', targetIndex) as any[];
      
      // Parse index info
      const stats = this.parseIndexInfo(indexInfo);
      
      // Get additional stats from our tracking
      const searchStats = await this.redis.hgetall(`${targetIndex}:stats`);
      
      return {
        totalVectors: stats.numDocs || 0,
        indexSize: stats.indexSize || 0,
        memoryUsage: stats.totalInvertedIndexBlocks || 0,
        lastUpdated: new Date(),
        searchCount: parseInt(searchStats.searchCount || '0'),
        averageSearchTime: parseFloat(searchStats.averageSearchTime || '0')
      };
      
    } catch (error) {
      this.logger.error(`Failed to get index stats for ${targetIndex}`, error);
      throw error;
    }
  }

  /**
   * Get total number of chunks across all indices
   */
  async getTotalChunks(): Promise<number> {
    try {
      const indices = [this.CODE_INDEX, this.CONCEPT_INDEX, this.DOCS_INDEX, this.API_INDEX];
      let total = 0;
      
      for (const index of indices) {
        try {
          const stats = await this.getIndexStats(index);
          total += stats.totalVectors;
        } catch (error) {
          // Index might not exist yet
          this.logger.debug(`Index ${index} not found or empty`);
        }
      }
      
      return total;
      
    } catch (error) {
      this.logger.error('Failed to get total chunks', error);
      return 0;
    }
  }

  /**
   * Get total index size
   */
  async getIndexSize(): Promise<number> {
    try {
      const indices = [this.CODE_INDEX, this.CONCEPT_INDEX, this.DOCS_INDEX, this.API_INDEX];
      let totalSize = 0;
      
      for (const index of indices) {
        try {
          const stats = await this.getIndexStats(index);
          totalSize += stats.indexSize;
        } catch (error) {
          // Index might not exist yet
          this.logger.debug(`Index ${index} not found or empty`);
        }
      }
      
      return totalSize;
      
    } catch (error) {
      this.logger.error('Failed to get total index size', error);
      return 0;
    }
  }

  /**
   * Optimize index performance
   */
  async optimizeIndex(indexName?: string): Promise<void> {
    const targetIndex = indexName || this.CODE_INDEX;
    
    try {
      // Trigger index optimization
      await this.redis.call('FT.OPTIMIZE', targetIndex);
      
      this.logger.info(`Optimized index ${targetIndex}`);
      
    } catch (error) {
      this.logger.error(`Failed to optimize index ${targetIndex}`, error);
      throw error;
    }
  }

  /**
   * Clear all data from an index
   */
  async clearIndex(indexName?: string): Promise<void> {
    const targetIndex = indexName || this.CODE_INDEX;
    
    try {
      // Drop and recreate index
      await this.redis.call('FT.DROPINDEX', targetIndex, 'DD');
      
      // Recreate the index
      const indexConfig = this.indices.get(targetIndex);
      if (indexConfig) {
        await this.createVectorIndex(indexConfig);
      }
      
      this.logger.info(`Cleared index ${targetIndex}`);
      
    } catch (error) {
      this.logger.error(`Failed to clear index ${targetIndex}`, error);
      throw error;
    }
  }

  // Private helper methods

  private setupRedisEventHandlers(): void {
    this.redis.on('connect', () => {
      this.logger.info('Connected to Redis');
    });

    this.redis.on('error', (error) => {
      this.logger.error('Redis connection error', error);
    });

    this.redis.on('close', () => {
      this.logger.warn('Redis connection closed');
    });
  }

  private async verifyRedisModules(): Promise<void> {
    try {
      const modules = await this.redis.call('MODULE', 'LIST') as any[];
      
      const requiredModules = ['search', 'ReJSON'];
      const loadedModules = modules.map(module => module[1]);
      
      for (const required of requiredModules) {
        if (!loadedModules.some(loaded => loaded.toLowerCase().includes(required.toLowerCase()))) {
          throw new Error(`Required Redis module not loaded: ${required}`);
        }
      }
      
      this.logger.info('All required Redis modules verified');
      
    } catch (error) {
      this.logger.error('Redis module verification failed', error);
      throw error;
    }
  }

  private async createVectorIndices(): Promise<void> {
    const indices = [
      {
        name: this.CODE_INDEX,
        dimensions: this.config.vectorDimensions,
        algorithm: 'HNSW' as const,
        distanceMetric: 'COSINE' as const,
        initialCapacity: 10000,
        m: 16,
        efConstruction: 200,
        efRuntime: 10
      },
      {
        name: this.CONCEPT_INDEX,
        dimensions: this.config.vectorDimensions,
        algorithm: 'FLAT' as const,
        distanceMetric: 'COSINE' as const,
        initialCapacity: 1000
      },
      {
        name: this.DOCS_INDEX,
        dimensions: this.config.vectorDimensions,
        algorithm: 'HNSW' as const,
        distanceMetric: 'COSINE' as const,
        initialCapacity: 5000,
        m: 16,
        efConstruction: 200,
        efRuntime: 10
      },
      {
        name: this.API_INDEX,
        dimensions: this.config.vectorDimensions,
        algorithm: 'FLAT' as const,
        distanceMetric: 'COSINE' as const,
        initialCapacity: 2000
      }
    ];

    for (const indexConfig of indices) {
      await this.createVectorIndex(indexConfig);
      this.indices.set(indexConfig.name, indexConfig);
    }
  }

  private async createVectorIndex(config: VectorIndex): Promise<void> {
    try {
      // Check if index already exists
      try {
        await this.redis.call('FT.INFO', config.name);
        this.logger.info(`Index ${config.name} already exists`);
        return;
      } catch (error) {
        // Index doesn't exist, create it
      }

      // Build index creation command
      const createCommand = [
        'FT.CREATE',
        config.name,
        'ON',
        'HASH',
        'PREFIX',
        '1',
        `${config.name}:vec:`,
        'SCHEMA',
        'vector',
        'VECTOR',
        config.algorithm,
        '6',
        'TYPE',
        'FLOAT32',
        'DIM',
        config.dimensions.toString(),
        'DISTANCE_METRIC',
        config.distanceMetric,
        'INITIAL_CAP',
        config.initialCapacity.toString()
      ];

      // Add algorithm-specific parameters
      if (config.algorithm === 'HNSW') {
        createCommand.push('M', (config.m || 16).toString());
        createCommand.push('EF_CONSTRUCTION', (config.efConstruction || 200).toString());
        createCommand.push('EF_RUNTIME', (config.efRuntime || 10).toString());
      }

      await this.redis.call(...createCommand);
      
      this.logger.info(`Created vector index: ${config.name}`);
      
    } catch (error) {
      this.logger.error(`Failed to create vector index ${config.name}`, error);
      throw error;
    }
  }

  private getIndexForChunkType(type: string): string {
    switch (type) {
      case 'CODE':
        return this.CODE_INDEX;
      case 'CONFIG':
        return this.CODE_INDEX;
      case 'DOCUMENTATION':
        return this.DOCS_INDEX;
      case 'COMMAND':
        return this.CODE_INDEX;
      default:
        return this.CODE_INDEX;
    }
  }

  private buildVectorSearchQuery(
    queryVector: Buffer,
    options: VectorSearchOptions,
    indexName: string
  ): string[] {
    const query = [
      indexName,
      `*=>[KNN ${options.k} @vector $BLOB AS score]`,
      'PARAMS',
      '2',
      'BLOB',
      queryVector,
      'SORTBY',
      'score',
      'LIMIT',
      '0',
      options.k.toString()
    ];

    if (options.scoreThreshold) {
      // Add score filtering if supported
      query.splice(2, 0, `@score:[0 ${options.scoreThreshold}]`);
    }

    return query;
  }

  private async parseSearchResults(
    searchResults: any[],
    options: VectorSearchOptions
  ): Promise<VectorSearchResult[]> {
    const results: VectorSearchResult[] = [];
    
    // Parse Redis search results format
    const numResults = searchResults[0];
    
    for (let i = 1; i < searchResults.length; i += 2) {
      const docId = searchResults[i];
      const fields = searchResults[i + 1];
      
      // Extract chunk ID from document ID
      const chunkId = docId.split(':').pop();
      
      // Get full chunk data
      const chunk = await this.getChunk(chunkId);
      
      if (chunk) {
        // Find score in fields
        let score = 0;
        for (let j = 0; j < fields.length; j += 2) {
          if (fields[j] === 'score') {
            score = parseFloat(fields[j + 1]);
            break;
          }
        }

        results.push({
          id: chunk.id,
          score,
          content: chunk.content,
          metadata: chunk.metadata,
          vector: options.includeVectors ? chunk.vector : undefined
        });
      }
    }

    return results.sort((a, b) => b.score - a.score);
  }

  private parseIndexInfo(indexInfo: any[]): any {
    const info: any = {};
    
    for (let i = 0; i < indexInfo.length; i += 2) {
      const key = indexInfo[i];
      const value = indexInfo[i + 1];
      info[key] = value;
    }
    
    return info;
  }

  private async updateSearchStats(indexName: string, searchTime: number): Promise<void> {
    try {
      const statsKey = `${indexName}:stats`;
      
      // Update search count and average time
      await this.redis.hincrby(statsKey, 'searchCount', 1);
      
      const currentAvg = parseFloat(await this.redis.hget(statsKey, 'averageSearchTime') || '0');
      const currentCount = parseInt(await this.redis.hget(statsKey, 'searchCount') || '1');
      
      const newAvg = (currentAvg * (currentCount - 1) + searchTime) / currentCount;
      await this.redis.hset(statsKey, 'averageSearchTime', newAvg.toString());
      
    } catch (error) {
      this.logger.warn('Failed to update search stats', error);
    }
  }

  /**
   * Cleanup and close connections
   */
  async cleanup(): Promise<void> {
    try {
      await this.redis.quit();
      this.logger.info('Redis Vector Store cleanup completed');
    } catch (error) {
      this.logger.error('Error during Redis Vector Store cleanup', error);
    }
  }
}

export default RedisVectorStore;