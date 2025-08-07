/**
 * System Introspection Engine
 * Analyzes running JAEGIS OS instances to extract comprehensive system information
 */

import { Logger } from '../../../utils/logger';
import { MCPServerConfig, SystemAnalysis, ComponentInfo, DependencyGraph, APIEndpoint, DatabaseSchema, ContainerInfo, Feature, FileModification, ConfigChange, PerformanceMetrics } from '../MCPServerOrchestrator';
import { DockerScanner } from './DockerScanner';
import { CodebaseAnalyzer } from './CodebaseAnalyzer';
import { DataAggregator } from './DataAggregator';
import * as fs from 'fs/promises';
import * as path from 'path';

export interface IntrospectionOptions {
  includeContainerAnalysis: boolean;
  includeCodebaseAnalysis: boolean;
  includePerformanceMetrics: boolean;
  includeSecurityAnalysis: boolean;
  analysisDepth: 'shallow' | 'deep' | 'comprehensive';
  cacheResults: boolean;
  maxAnalysisTime: number; // milliseconds
}

export interface IntrospectionResult {
  systemAnalysis: SystemAnalysis;
  analysisTime: number;
  cacheHit: boolean;
  warnings: string[];
  recommendations: string[];
}

export class SystemIntrospector {
  private logger: Logger;
  private config: MCPServerConfig;
  private dockerScanner: DockerScanner;
  private codebaseAnalyzer: CodebaseAnalyzer;
  private dataAggregator: DataAggregator;
  private analysisCache: Map<string, { analysis: SystemAnalysis; timestamp: Date; checksum: string }>;
  private initialized: boolean = false;

  // Cache settings
  private readonly CACHE_TTL_MS = 300000; // 5 minutes
  private readonly MAX_CACHE_SIZE = 100;

  constructor(config: MCPServerConfig) {
    this.config = config;
    this.logger = new Logger('SystemIntrospector');
    this.analysisCache = new Map();
    
    this.dockerScanner = new DockerScanner(config);
    this.codebaseAnalyzer = new CodebaseAnalyzer(config);
    this.dataAggregator = new DataAggregator(config);
  }

  async initialize(): Promise<void> {
    this.logger.info('Initializing System Introspector');
    
    try {
      await this.dockerScanner.initialize();
      await this.codebaseAnalyzer.initialize();
      await this.dataAggregator.initialize();
      
      this.initialized = true;
      this.logger.info('System Introspector initialized successfully');
      
      // Start cache cleanup interval
      this.startCacheCleanup();
      
    } catch (error) {
      this.logger.error('Failed to initialize System Introspector', error);
      throw error;
    }
  }

  /**
   * Analyze a running system to extract comprehensive information
   */
  async analyze(
    systemTarget: string, 
    options: Partial<IntrospectionOptions> = {}
  ): Promise<IntrospectionResult> {
    if (!this.initialized) {
      throw new Error('System Introspector not initialized');
    }

    const startTime = Date.now();
    const fullOptions: IntrospectionOptions = {
      includeContainerAnalysis: true,
      includeCodebaseAnalysis: true,
      includePerformanceMetrics: true,
      includeSecurityAnalysis: false,
      analysisDepth: 'deep',
      cacheResults: true,
      maxAnalysisTime: 300000, // 5 minutes
      ...options
    };

    this.logger.info(`Starting system analysis for target: ${systemTarget}`);

    try {
      // Check cache first
      const cacheKey = this.generateCacheKey(systemTarget, fullOptions);
      const cachedResult = await this.getCachedAnalysis(cacheKey, systemTarget);
      
      if (cachedResult) {
        this.logger.info('Returning cached analysis result');
        return {
          systemAnalysis: cachedResult,
          analysisTime: Date.now() - startTime,
          cacheHit: true,
          warnings: [],
          recommendations: []
        };
      }

      // Perform fresh analysis
      const analysisResult = await this.performAnalysis(systemTarget, fullOptions);
      
      // Cache the result
      if (fullOptions.cacheResults) {
        await this.cacheAnalysis(cacheKey, analysisResult.systemAnalysis, systemTarget);
      }

      const totalTime = Date.now() - startTime;
      this.logger.info(`System analysis completed in ${totalTime}ms`);

      return {
        ...analysisResult,
        analysisTime: totalTime,
        cacheHit: false
      };

    } catch (error) {
      this.logger.error('System analysis failed', error);
      throw new Error(`System analysis failed: ${error.message}`);
    }
  }

  /**
   * Perform the actual system analysis
   */
  private async performAnalysis(
    systemTarget: string, 
    options: IntrospectionOptions
  ): Promise<{ systemAnalysis: SystemAnalysis; warnings: string[]; recommendations: string[] }> {
    
    const warnings: string[] = [];
    const recommendations: string[] = [];
    
    // Initialize analysis structure
    const systemAnalysis: SystemAnalysis = {
      metadata: {
        analysisDate: new Date().toISOString(),
        osVersion: 'Unknown',
        deploymentEnvironment: 'Unknown',
        containerRuntime: 'Unknown'
      },
      architecture: {
        components: [],
        dependencies: { nodes: [], edges: [] },
        apiEndpoints: [],
        databaseSchema: { models: [], relations: [], indexes: [] }
      },
      infrastructure: {
        containers: [],
        volumes: [],
        networks: [],
        services: []
      },
      customizations: {
        addedFeatures: [],
        modifiedFiles: [],
        configurationChanges: [],
        performanceMetrics: {
          buildTime: 0,
          bundleSize: 0,
          memoryUsage: 0,
          cpuUsage: 0,
          responseTime: 0
        }
      }
    };

    // Step 1: Container Analysis
    if (options.includeContainerAnalysis) {
      try {
        this.logger.info('Analyzing container infrastructure');
        const containerData = await this.dockerScanner.scanSystem(systemTarget);
        
        systemAnalysis.infrastructure.containers = containerData.containers;
        systemAnalysis.infrastructure.volumes = containerData.volumes;
        systemAnalysis.infrastructure.networks = containerData.networks;
        systemAnalysis.infrastructure.services = containerData.services;
        
        // Extract metadata from containers
        if (containerData.containers.length > 0) {
          const mainContainer = containerData.containers[0];
          systemAnalysis.metadata.containerRuntime = 'Docker';
          systemAnalysis.metadata.deploymentEnvironment = this.detectDeploymentEnvironment(mainContainer);
          
          // Try to extract OS version from container labels or environment
          systemAnalysis.metadata.osVersion = this.extractOSVersion(mainContainer);
        }
        
      } catch (error) {
        warnings.push(`Container analysis failed: ${error.message}`);
        this.logger.warn('Container analysis failed', error);
      }
    }

    // Step 2: Codebase Analysis
    if (options.includeCodebaseAnalysis) {
      try {
        this.logger.info('Analyzing codebase structure');
        const codebaseData = await this.codebaseAnalyzer.analyzeCodebase(systemTarget, {
          depth: options.analysisDepth,
          includeComponents: true,
          includeDependencies: true,
          includeAPI: true,
          includeDatabase: true
        });
        
        systemAnalysis.architecture.components = codebaseData.components;
        systemAnalysis.architecture.dependencies = codebaseData.dependencies;
        systemAnalysis.architecture.apiEndpoints = codebaseData.apiEndpoints;
        systemAnalysis.architecture.databaseSchema = codebaseData.databaseSchema;
        systemAnalysis.customizations.addedFeatures = codebaseData.features;
        systemAnalysis.customizations.modifiedFiles = codebaseData.modifications;
        systemAnalysis.customizations.configurationChanges = codebaseData.configChanges;
        
      } catch (error) {
        warnings.push(`Codebase analysis failed: ${error.message}`);
        this.logger.warn('Codebase analysis failed', error);
      }
    }

    // Step 3: Performance Metrics
    if (options.includePerformanceMetrics) {
      try {
        this.logger.info('Collecting performance metrics');
        const performanceData = await this.collectPerformanceMetrics(systemTarget);
        systemAnalysis.customizations.performanceMetrics = performanceData;
        
      } catch (error) {
        warnings.push(`Performance metrics collection failed: ${error.message}`);
        this.logger.warn('Performance metrics collection failed', error);
      }
    }

    // Step 4: Data Aggregation and Enhancement
    try {
      this.logger.info('Aggregating and enhancing analysis data');
      const enhancedAnalysis = await this.dataAggregator.aggregate(systemAnalysis);
      
      // Generate recommendations
      recommendations.push(...this.generateRecommendations(enhancedAnalysis));
      
      return {
        systemAnalysis: enhancedAnalysis,
        warnings,
        recommendations
      };
      
    } catch (error) {
      warnings.push(`Data aggregation failed: ${error.message}`);
      this.logger.warn('Data aggregation failed', error);
      
      return {
        systemAnalysis,
        warnings,
        recommendations
      };
    }
  }

  /**
   * Collect performance metrics from the running system
   */
  private async collectPerformanceMetrics(systemTarget: string): Promise<PerformanceMetrics> {
    const metrics: PerformanceMetrics = {
      buildTime: 0,
      bundleSize: 0,
      memoryUsage: 0,
      cpuUsage: 0,
      responseTime: 0
    };

    try {
      // Get container stats if it's a Docker target
      if (systemTarget.startsWith('container:')) {
        const containerId = systemTarget.replace('container:', '');
        const containerStats = await this.dockerScanner.getContainerStats(containerId);
        
        if (containerStats) {
          metrics.memoryUsage = containerStats.memoryUsage;
          metrics.cpuUsage = containerStats.cpuUsage;
        }
      }

      // Try to get build metrics from the system
      const buildMetrics = await this.extractBuildMetrics(systemTarget);
      if (buildMetrics) {
        metrics.buildTime = buildMetrics.buildTime;
        metrics.bundleSize = buildMetrics.bundleSize;
      }

      // Measure response time
      const responseTime = await this.measureResponseTime(systemTarget);
      if (responseTime) {
        metrics.responseTime = responseTime;
      }

    } catch (error) {
      this.logger.warn('Failed to collect some performance metrics', error);
    }

    return metrics;
  }

  /**
   * Extract build metrics from the system
   */
  private async extractBuildMetrics(systemTarget: string): Promise<{ buildTime: number; bundleSize: number } | null> {
    try {
      // Try to find build artifacts or logs
      // This would depend on the specific system structure
      return null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Measure system response time
   */
  private async measureResponseTime(systemTarget: string): Promise<number | null> {
    try {
      // If it's a web service, try to ping it
      if (systemTarget.includes('http')) {
        const startTime = Date.now();
        // Would make actual HTTP request here
        const endTime = Date.now();
        return endTime - startTime;
      }
      return null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Detect deployment environment from container info
   */
  private detectDeploymentEnvironment(container: ContainerInfo): string {
    // Check labels and environment variables for deployment hints
    const env = container.environment;
    const image = container.image.toLowerCase();

    if (env.NODE_ENV === 'production') return 'Production';
    if (env.NODE_ENV === 'development') return 'Development';
    if (env.NODE_ENV === 'staging') return 'Staging';
    
    if (image.includes('prod')) return 'Production';
    if (image.includes('dev')) return 'Development';
    if (image.includes('staging')) return 'Staging';
    
    return 'Unknown';
  }

  /**
   * Extract OS version from container
   */
  private extractOSVersion(container: ContainerInfo): string {
    // Try to extract version from environment or labels
    const env = container.environment;
    
    if (env.JAEGIS_VERSION) return env.JAEGIS_VERSION;
    if (env.APP_VERSION) return env.APP_VERSION;
    
    // Try to extract from image tag
    const imageTag = container.image.split(':')[1];
    if (imageTag && imageTag !== 'latest') {
      return imageTag;
    }
    
    return 'Unknown';
  }

  /**
   * Generate recommendations based on analysis
   */
  private generateRecommendations(analysis: SystemAnalysis): string[] {
    const recommendations: string[] = [];

    // Performance recommendations
    if (analysis.customizations.performanceMetrics.memoryUsage > 1000) {
      recommendations.push('Consider optimizing memory usage - current usage is high');
    }

    if (analysis.customizations.performanceMetrics.responseTime > 2000) {
      recommendations.push('Response time is slow - consider performance optimization');
    }

    // Architecture recommendations
    if (analysis.architecture.components.length > 50) {
      recommendations.push('Large number of components detected - consider modularization');
    }

    if (analysis.architecture.apiEndpoints.length > 100) {
      recommendations.push('Many API endpoints detected - consider API versioning strategy');
    }

    // Security recommendations
    if (analysis.infrastructure.containers.some(c => c.environment.NODE_ENV === 'development')) {
      recommendations.push('Development environment detected in production - review configuration');
    }

    return recommendations;
  }

  /**
   * Cache management
   */
  private generateCacheKey(systemTarget: string, options: IntrospectionOptions): string {
    const optionsHash = Buffer.from(JSON.stringify(options)).toString('base64');
    return `${systemTarget}_${optionsHash}`;
  }

  private async getCachedAnalysis(cacheKey: string, systemTarget: string): Promise<SystemAnalysis | null> {
    const cached = this.analysisCache.get(cacheKey);
    
    if (!cached) {
      return null;
    }

    // Check if cache is still valid
    const age = Date.now() - cached.timestamp.getTime();
    if (age > this.CACHE_TTL_MS) {
      this.analysisCache.delete(cacheKey);
      return null;
    }

    // Verify system hasn't changed (simplified checksum check)
    const currentChecksum = await this.generateSystemChecksum(systemTarget);
    if (currentChecksum !== cached.checksum) {
      this.analysisCache.delete(cacheKey);
      return null;
    }

    return cached.analysis;
  }

  private async cacheAnalysis(cacheKey: string, analysis: SystemAnalysis, systemTarget: string): Promise<void> {
    // Implement cache size limit
    if (this.analysisCache.size >= this.MAX_CACHE_SIZE) {
      // Remove oldest entry
      const oldestKey = this.analysisCache.keys().next().value;
      this.analysisCache.delete(oldestKey);
    }

    const checksum = await this.generateSystemChecksum(systemTarget);
    
    this.analysisCache.set(cacheKey, {
      analysis,
      timestamp: new Date(),
      checksum
    });
  }

  private async generateSystemChecksum(systemTarget: string): Promise<string> {
    // Generate a simple checksum based on system state
    // In production, this would be more sophisticated
    return `${systemTarget}_${Date.now()}`;
  }

  private startCacheCleanup(): void {
    setInterval(() => {
      const now = Date.now();
      for (const [key, cached] of this.analysisCache.entries()) {
        const age = now - cached.timestamp.getTime();
        if (age > this.CACHE_TTL_MS) {
          this.analysisCache.delete(key);
        }
      }
    }, 60000); // Cleanup every minute
  }

  /**
   * Get analysis cache statistics
   */
  getCacheStats(): { size: number; hitRate: number; oldestEntry: Date | null } {
    let oldestEntry: Date | null = null;
    
    for (const cached of this.analysisCache.values()) {
      if (!oldestEntry || cached.timestamp < oldestEntry) {
        oldestEntry = cached.timestamp;
      }
    }

    return {
      size: this.analysisCache.size,
      hitRate: 0, // Would need to track hits/misses for accurate calculation
      oldestEntry
    };
  }

  /**
   * Clear analysis cache
   */
  clearCache(): void {
    this.analysisCache.clear();
    this.logger.info('Analysis cache cleared');
  }
}

export default SystemIntrospector;