/**
 * Vector Build Document Parser
 * Parses build documents into semantic chunks and indexes them in Redis vector store
 */

import { Logger } from '../../../utils/logger';
import { RedisVectorStore } from '../vector/RedisVectorStore';
import { SemanticChunk, ChunkMetadata } from '../VectorAwareMCPOrchestrator';
import * as fs from 'fs/promises';
import * as path from 'path';

export interface VectorParsingOptions {
  chunkSize: number;
  chunkOverlap: number;
  preserveCodeBlocks: boolean;
  extractMetadata: boolean;
  generateEmbeddings: boolean;
  indexImmediately: boolean;
}

export interface ParsedVectorDocument {
  chunks: SemanticChunk[];
  metadata: DocumentMetadata;
  statistics: ParsingStatistics;
}

export interface DocumentMetadata {
  name: string;
  version: string;
  description: string;
  framework: string;
  totalChunks: number;
  codeChunks: number;
  configChunks: number;
  docChunks: number;
  commandChunks: number;
  processingTime: number;
}

export interface ParsingStatistics {
  totalLines: number;
  totalCharacters: number;
  averageChunkSize: number;
  complexityScore: number;
  languageDistribution: Record<string, number>;
  categoryDistribution: Record<string, number>;
}

export interface CodeBlock {
  language: string;
  content: string;
  startLine: number;
  endLine: number;
  context: string;
}

export interface ConfigSection {
  type: string;
  content: string;
  filePath?: string;
  description: string;
}

export class VectorBuildDocumentParser {
  private logger: Logger;
  private vectorStore: RedisVectorStore;
  private initialized: boolean = false;

  // Embedding service (would integrate with OpenAI or local model)
  private embeddingService: EmbeddingService;

  constructor(vectorStore: RedisVectorStore) {
    this.logger = new Logger('VectorBuildDocumentParser');
    this.vectorStore = vectorStore;
    this.embeddingService = new EmbeddingService();
  }

  async initialize(): Promise<void> {
    this.logger.info('Initializing Vector Build Document Parser');
    
    try {
      await this.embeddingService.initialize();
      this.initialized = true;
      this.logger.info('Vector Build Document Parser initialized successfully');
    } catch (error) {
      this.logger.error('Failed to initialize Vector Build Document Parser', error);
      throw error;
    }
  }

  /**
   * Parse and index a build document
   */
  async parseAndIndex(
    documentContent: string,
    options: Partial<VectorParsingOptions> = {}
  ): Promise<ParsedVectorDocument> {
    if (!this.initialized) {
      throw new Error('Vector Build Document Parser not initialized');
    }

    const startTime = Date.now();
    const fullOptions: VectorParsingOptions = {
      chunkSize: 1000,
      chunkOverlap: 200,
      preserveCodeBlocks: true,
      extractMetadata: true,
      generateEmbeddings: true,
      indexImmediately: true,
      ...options
    };

    this.logger.info('Starting vector parsing and indexing of build document');

    try {
      // Step 1: Extract structured content
      const structuredContent = await this.extractStructuredContent(documentContent);
      
      // Step 2: Create semantic chunks
      const chunks = await this.createSemanticChunks(structuredContent, fullOptions);
      
      // Step 3: Generate embeddings for chunks
      if (fullOptions.generateEmbeddings) {
        await this.generateEmbeddings(chunks);
      }
      
      // Step 4: Index chunks in vector store
      if (fullOptions.indexImmediately) {
        await this.indexChunks(chunks);
      }

      // Step 5: Generate metadata and statistics
      const metadata = this.generateDocumentMetadata(chunks, Date.now() - startTime);
      const statistics = this.generateParsingStatistics(documentContent, chunks);

      const result: ParsedVectorDocument = {
        chunks,
        metadata,
        statistics
      };

      this.logger.info(`Vector parsing completed: ${chunks.length} chunks created in ${Date.now() - startTime}ms`);
      return result;

    } catch (error) {
      this.logger.error('Vector parsing failed', error);
      throw error;
    }
  }

  /**
   * Extract structured content from document
   */
  private async extractStructuredContent(content: string): Promise<StructuredContent> {
    const structuredContent: StructuredContent = {
      codeBlocks: [],
      configSections: [],
      documentationSections: [],
      commandSequences: [],
      metadata: {}
    };

    // Extract code blocks
    structuredContent.codeBlocks = this.extractCodeBlocks(content);
    
    // Extract configuration sections
    structuredContent.configSections = this.extractConfigSections(content);
    
    // Extract documentation sections
    structuredContent.documentationSections = this.extractDocumentationSections(content);
    
    // Extract command sequences
    structuredContent.commandSequences = this.extractCommandSequences(content);

    return structuredContent;
  }

  /**
   * Extract code blocks from document
   */
  private extractCodeBlocks(content: string): CodeBlock[] {
    const codeBlocks: CodeBlock[] = [];
    const lines = content.split('\n');
    let inCodeBlock = false;
    let currentBlock: Partial<CodeBlock> = {};
    let blockStartLine = 0;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Detect code block start
      const codeBlockMatch = line.match(/^```(\w+)?/);
      if (codeBlockMatch && !inCodeBlock) {
        inCodeBlock = true;
        blockStartLine = i;
        currentBlock = {
          language: codeBlockMatch[1] || 'text',
          content: '',
          startLine: i + 1,
          context: this.extractContext(lines, i, 3)
        };
        continue;
      }
      
      // Detect code block end
      if (line.trim() === '```' && inCodeBlock) {
        inCodeBlock = false;
        currentBlock.endLine = i;
        
        if (currentBlock.content && currentBlock.content.trim().length > 0) {
          codeBlocks.push(currentBlock as CodeBlock);
        }
        currentBlock = {};
        continue;
      }
      
      // Collect code block content
      if (inCodeBlock) {
        currentBlock.content += line + '\n';
      }
    }

    return codeBlocks;
  }

  /**
   * Extract configuration sections
   */
  private extractConfigSections(content: string): ConfigSection[] {
    const configSections: ConfigSection[] = [];
    
    // Look for common configuration patterns
    const configPatterns = [
      { type: 'package.json', pattern: /package\.json[\s\S]*?```json([\s\S]*?)```/g },
      { type: 'prisma.schema', pattern: /schema\.prisma[\s\S]*?```prisma([\s\S]*?)```/g },
      { type: 'dockerfile', pattern: /Dockerfile[\s\S]*?```dockerfile([\s\S]*?)```/g },
      { type: 'env', pattern: /\.env[\s\S]*?```(?:bash|env)?([\s\S]*?)```/g },
      { type: 'yaml', pattern: /\.ya?ml[\s\S]*?```ya?ml([\s\S]*?)```/g }
    ];

    for (const pattern of configPatterns) {
      let match;
      while ((match = pattern.pattern.exec(content)) !== null) {
        configSections.push({
          type: pattern.type,
          content: match[1].trim(),
          description: this.extractConfigDescription(content, match.index)
        });
      }
    }

    return configSections;
  }

  /**
   * Extract documentation sections
   */
  private extractDocumentationSections(content: string): DocumentationSection[] {
    const sections: DocumentationSection[] = [];
    const lines = content.split('\n');
    
    let currentSection: Partial<DocumentationSection> = {};
    let sectionContent = '';
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Detect headers
      const headerMatch = line.match(/^(#{1,6})\s+(.+)$/);
      if (headerMatch) {
        // Save previous section
        if (currentSection.title && sectionContent.trim()) {
          sections.push({
            ...currentSection,
            content: sectionContent.trim(),
            endLine: i - 1
          } as DocumentationSection);
        }
        
        // Start new section
        currentSection = {
          level: headerMatch[1].length,
          title: headerMatch[2],
          startLine: i,
          content: ''
        };
        sectionContent = '';
        continue;
      }
      
      // Collect section content (skip code blocks)
      if (!line.startsWith('```')) {
        sectionContent += line + '\n';
      }
    }
    
    // Save last section
    if (currentSection.title && sectionContent.trim()) {
      sections.push({
        ...currentSection,
        content: sectionContent.trim(),
        endLine: lines.length - 1
      } as DocumentationSection);
    }

    return sections;
  }

  /**
   * Extract command sequences
   */
  private extractCommandSequences(content: string): CommandSequence[] {
    const sequences: CommandSequence[] = [];
    const codeBlocks = this.extractCodeBlocks(content);
    
    for (const block of codeBlocks) {
      if (['bash', 'sh', 'shell', 'cmd'].includes(block.language.toLowerCase())) {
        const commands = block.content
          .split('\n')
          .filter(line => line.trim() && !line.trim().startsWith('#'))
          .map(line => line.trim());
        
        if (commands.length > 0) {
          sequences.push({
            commands,
            description: block.context,
            startLine: block.startLine,
            endLine: block.endLine
          });
        }
      }
    }

    return sequences;
  }

  /**
   * Create semantic chunks from structured content
   */
  private async createSemanticChunks(
    structuredContent: StructuredContent,
    options: VectorParsingOptions
  ): Promise<SemanticChunk[]> {
    const chunks: SemanticChunk[] = [];
    let chunkId = 0;

    // Process code blocks
    for (const codeBlock of structuredContent.codeBlocks) {
      const chunk = await this.createChunkFromCodeBlock(codeBlock, chunkId++);
      chunks.push(chunk);
    }

    // Process configuration sections
    for (const configSection of structuredContent.configSections) {
      const chunk = await this.createChunkFromConfigSection(configSection, chunkId++);
      chunks.push(chunk);
    }

    // Process documentation sections
    for (const docSection of structuredContent.documentationSections) {
      const docChunks = await this.createChunksFromDocumentationSection(docSection, chunkId, options);
      chunks.push(...docChunks);
      chunkId += docChunks.length;
    }

    // Process command sequences
    for (const commandSeq of structuredContent.commandSequences) {
      const chunk = await this.createChunkFromCommandSequence(commandSeq, chunkId++);
      chunks.push(chunk);
    }

    return chunks;
  }

  /**
   * Create chunk from code block
   */
  private async createChunkFromCodeBlock(codeBlock: CodeBlock, id: number): Promise<SemanticChunk> {
    const metadata: ChunkMetadata = {
      lineNumbers: [codeBlock.startLine, codeBlock.endLine],
      language: codeBlock.language,
      category: 'code',
      tags: this.extractCodeTags(codeBlock),
      complexity: this.calculateCodeComplexity(codeBlock.content),
      dependencies: this.extractDependencies(codeBlock.content)
    };

    return {
      id: `chunk_${id}`,
      content: codeBlock.content,
      type: 'CODE',
      relevanceScore: 0, // Will be calculated during retrieval
      metadata,
      vector: [] // Will be populated by embedding service
    };
  }

  /**
   * Create chunk from configuration section
   */
  private async createChunkFromConfigSection(configSection: ConfigSection, id: number): Promise<SemanticChunk> {
    const metadata: ChunkMetadata = {
      category: 'configuration',
      tags: [configSection.type, 'config'],
      complexity: this.calculateConfigComplexity(configSection.content),
      dependencies: []
    };

    return {
      id: `chunk_${id}`,
      content: configSection.content,
      type: 'CONFIG',
      relevanceScore: 0,
      metadata,
      vector: []
    };
  }

  /**
   * Create chunks from documentation section
   */
  private async createChunksFromDocumentationSection(
    docSection: DocumentationSection,
    startId: number,
    options: VectorParsingOptions
  ): Promise<SemanticChunk[]> {
    const chunks: SemanticChunk[] = [];
    
    // Split large documentation sections into smaller chunks
    const contentChunks = this.splitTextIntoChunks(docSection.content, options.chunkSize, options.chunkOverlap);
    
    for (let i = 0; i < contentChunks.length; i++) {
      const metadata: ChunkMetadata = {
        lineNumbers: [docSection.startLine, docSection.endLine],
        category: 'documentation',
        tags: ['docs', `level-${docSection.level}`, ...this.extractDocTags(docSection.title)],
        complexity: this.calculateTextComplexity(contentChunks[i]),
        dependencies: []
      };

      chunks.push({
        id: `chunk_${startId + i}`,
        content: contentChunks[i],
        type: 'DOCUMENTATION',
        relevanceScore: 0,
        metadata,
        vector: []
      });
    }

    return chunks;
  }

  /**
   * Create chunk from command sequence
   */
  private async createChunkFromCommandSequence(commandSeq: CommandSequence, id: number): Promise<SemanticChunk> {
    const metadata: ChunkMetadata = {
      lineNumbers: [commandSeq.startLine, commandSeq.endLine],
      category: 'commands',
      tags: ['shell', 'commands', ...this.extractCommandTags(commandSeq.commands)],
      complexity: commandSeq.commands.length,
      dependencies: this.extractCommandDependencies(commandSeq.commands)
    };

    return {
      id: `chunk_${id}`,
      content: commandSeq.commands.join('\n'),
      type: 'COMMAND',
      relevanceScore: 0,
      metadata,
      vector: []
    };
  }

  /**
   * Generate embeddings for chunks
   */
  private async generateEmbeddings(chunks: SemanticChunk[]): Promise<void> {
    this.logger.info(`Generating embeddings for ${chunks.length} chunks`);
    
    for (const chunk of chunks) {
      try {
        // Create embedding text by combining content with metadata
        const embeddingText = this.createEmbeddingText(chunk);
        
        // Generate embedding
        const embedding = await this.embeddingService.generateEmbedding(embeddingText);
        chunk.vector = embedding;
        
      } catch (error) {
        this.logger.warn(`Failed to generate embedding for chunk ${chunk.id}`, error);
        // Use zero vector as fallback
        chunk.vector = new Array(1536).fill(0);
      }
    }
  }

  /**
   * Index chunks in vector store
   */
  private async indexChunks(chunks: SemanticChunk[]): Promise<void> {
    this.logger.info(`Indexing ${chunks.length} chunks in vector store`);
    
    for (const chunk of chunks) {
      try {
        await this.vectorStore.storeChunk(chunk);
      } catch (error) {
        this.logger.warn(`Failed to index chunk ${chunk.id}`, error);
      }
    }
  }

  // Helper methods for content analysis

  private extractContext(lines: string[], lineIndex: number, contextSize: number): string {
    const start = Math.max(0, lineIndex - contextSize);
    const end = Math.min(lines.length, lineIndex + contextSize + 1);
    return lines.slice(start, end).join('\n');
  }

  private extractConfigDescription(content: string, matchIndex: number): string {
    const beforeMatch = content.substring(0, matchIndex);
    const lines = beforeMatch.split('\n');
    
    // Look for description in previous lines
    for (let i = lines.length - 1; i >= Math.max(0, lines.length - 5); i--) {
      const line = lines[i].trim();
      if (line && !line.startsWith('#') && line.length > 10) {
        return line;
      }
    }
    
    return 'Configuration section';
  }

  private extractCodeTags(codeBlock: CodeBlock): string[] {
    const tags = [codeBlock.language];
    
    // Add framework-specific tags
    if (codeBlock.content.includes('import React')) tags.push('react');
    if (codeBlock.content.includes('prisma')) tags.push('prisma');
    if (codeBlock.content.includes('npm install')) tags.push('npm');
    if (codeBlock.content.includes('docker')) tags.push('docker');
    
    return tags;
  }

  private extractDocTags(title: string): string[] {
    const tags = [];
    const lowerTitle = title.toLowerCase();
    
    if (lowerTitle.includes('install')) tags.push('installation');
    if (lowerTitle.includes('config')) tags.push('configuration');
    if (lowerTitle.includes('api')) tags.push('api');
    if (lowerTitle.includes('deploy')) tags.push('deployment');
    
    return tags;
  }

  private extractCommandTags(commands: string[]): string[] {
    const tags = [];
    const allCommands = commands.join(' ').toLowerCase();
    
    if (allCommands.includes('npm')) tags.push('npm');
    if (allCommands.includes('docker')) tags.push('docker');
    if (allCommands.includes('git')) tags.push('git');
    if (allCommands.includes('prisma')) tags.push('prisma');
    
    return tags;
  }

  private extractDependencies(content: string): string[] {
    const dependencies = [];
    
    // Extract import statements
    const importMatches = content.match(/import.*from\s+['"]([^'"]+)['"]/g);
    if (importMatches) {
      dependencies.push(...importMatches.map(match => match.split('from')[1].trim().replace(/['"]/g, '')));
    }
    
    return dependencies;
  }

  private extractCommandDependencies(commands: string[]): string[] {
    const dependencies = [];
    
    for (const command of commands) {
      if (command.includes('npm install')) {
        const packages = command.replace('npm install', '').trim().split(' ');
        dependencies.push(...packages.filter(pkg => pkg && !pkg.startsWith('-')));
      }
    }
    
    return dependencies;
  }

  private calculateCodeComplexity(content: string): number {
    // Simple complexity calculation based on various factors
    let complexity = 0;
    
    complexity += (content.match(/if|else|while|for|switch/g) || []).length * 2;
    complexity += (content.match(/function|class|interface/g) || []).length * 3;
    complexity += (content.match(/import|require/g) || []).length;
    complexity += Math.floor(content.split('\n').length / 10);
    
    return Math.min(complexity, 100);
  }

  private calculateConfigComplexity(content: string): number {
    const lines = content.split('\n').filter(line => line.trim());
    return Math.min(lines.length, 50);
  }

  private calculateTextComplexity(content: string): number {
    const words = content.split(/\s+/).length;
    const sentences = content.split(/[.!?]+/).length;
    return Math.min(Math.floor(words / 10) + sentences, 50);
  }

  private splitTextIntoChunks(text: string, chunkSize: number, overlap: number): string[] {
    const chunks = [];
    const words = text.split(/\s+/);
    
    for (let i = 0; i < words.length; i += chunkSize - overlap) {
      const chunk = words.slice(i, i + chunkSize).join(' ');
      if (chunk.trim()) {
        chunks.push(chunk);
      }
    }
    
    return chunks;
  }

  private createEmbeddingText(chunk: SemanticChunk): string {
    // Combine content with metadata for better embeddings
    const metadataText = [
      `Type: ${chunk.type}`,
      `Category: ${chunk.metadata.category}`,
      `Tags: ${chunk.metadata.tags.join(', ')}`,
      chunk.metadata.language ? `Language: ${chunk.metadata.language}` : '',
    ].filter(Boolean).join('. ');
    
    return `${metadataText}. Content: ${chunk.content}`;
  }

  private generateDocumentMetadata(chunks: SemanticChunk[], processingTime: number): DocumentMetadata {
    const typeCount = chunks.reduce((acc, chunk) => {
      acc[chunk.type] = (acc[chunk.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      name: 'JAEGIS AI Web OS Build Instructions',
      version: '2.2.0-vector',
      description: 'Vector-indexed build instructions for JAEGIS OS',
      framework: 'Next.js 15',
      totalChunks: chunks.length,
      codeChunks: typeCount.CODE || 0,
      configChunks: typeCount.CONFIG || 0,
      docChunks: typeCount.DOCUMENTATION || 0,
      commandChunks: typeCount.COMMAND || 0,
      processingTime
    };
  }

  private generateParsingStatistics(content: string, chunks: SemanticChunk[]): ParsingStatistics {
    const lines = content.split('\n');
    const avgChunkSize = chunks.reduce((sum, chunk) => sum + chunk.content.length, 0) / chunks.length;
    
    const languageDistribution = chunks.reduce((acc, chunk) => {
      const lang = chunk.metadata.language || 'unknown';
      acc[lang] = (acc[lang] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const categoryDistribution = chunks.reduce((acc, chunk) => {
      acc[chunk.metadata.category] = (acc[chunk.metadata.category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      totalLines: lines.length,
      totalCharacters: content.length,
      averageChunkSize: Math.round(avgChunkSize),
      complexityScore: chunks.reduce((sum, chunk) => sum + chunk.metadata.complexity, 0) / chunks.length,
      languageDistribution,
      categoryDistribution
    };
  }
}

// Supporting interfaces
interface StructuredContent {
  codeBlocks: CodeBlock[];
  configSections: ConfigSection[];
  documentationSections: DocumentationSection[];
  commandSequences: CommandSequence[];
  metadata: Record<string, any>;
}

interface DocumentationSection {
  level: number;
  title: string;
  content: string;
  startLine: number;
  endLine: number;
}

interface CommandSequence {
  commands: string[];
  description: string;
  startLine: number;
  endLine: number;
}

// Embedding service interface
class EmbeddingService {
  async initialize(): Promise<void> {
    // Initialize embedding model (OpenAI, local model, etc.)
  }

  async generateEmbedding(text: string): Promise<number[]> {
    // Generate embedding vector
    // This would integrate with OpenAI embeddings API or local model
    return new Array(1536).fill(0).map(() => Math.random() - 0.5);
  }
}

export default VectorBuildDocumentParser;