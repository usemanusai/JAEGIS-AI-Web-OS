/**
 * Specification Generator
 * AI-powered generation of comprehensive system specifications from analysis data
 */

import { Logger } from '../../../utils/logger';
import { SystemAnalysis } from '../MCPServerOrchestrator';
import ZaiSDKClient from '../ai/ZaiSDKClient';
import { EventEmitter } from 'events';

export interface SpecificationOptions {
  format: 'markdown' | 'html' | 'pdf' | 'json';
  includeArchitecture: boolean;
  includeDiagrams: boolean;
  includeAPI: boolean;
  includeDeployment: boolean;
  includePerformance: boolean;
  includeSecurity: boolean;
  customSections: SpecificationSection[];
  template: 'standard' | 'technical' | 'executive' | 'developer';
  diagramStyle: 'mermaid' | 'plantuml' | 'ascii';
  detailLevel: 'summary' | 'detailed' | 'comprehensive';
  streaming: boolean;
}

export interface SpecificationSection {
  id: string;
  title: string;
  content?: string;
  template?: string;
  order: number;
  required: boolean;
}

export interface GenerationResult {
  specification: string;
  metadata: {
    generatedAt: Date;
    wordCount: number;
    sectionCount: number;
    diagramCount: number;
    processingTime: number;
    aiTokensUsed: number;
  };
  warnings: string[];
  suggestions: string[];
  artifacts: {
    diagrams: GeneratedDiagram[];
    attachments: GeneratedAttachment[];
  };
}

export interface GeneratedDiagram {
  id: string;
  title: string;
  type: 'architecture' | 'flow' | 'sequence' | 'component' | 'deployment';
  format: 'mermaid' | 'plantuml' | 'svg' | 'png';
  content: string;
  description: string;
}

export interface GeneratedAttachment {
  id: string;
  name: string;
  type: 'json' | 'yaml' | 'csv' | 'txt';
  content: string;
  description: string;
}

export class SpecificationGenerator extends EventEmitter {
  private logger: Logger;
  private zaiClient: ZaiSDKClient;
  private templates: Map<string, SpecificationTemplate>;
  private initialized: boolean = false;

  constructor(zaiClient: ZaiSDKClient) {
    super();
    this.logger = new Logger('SpecificationGenerator');
    this.zaiClient = zaiClient;
    this.templates = new Map();
  }

  async initialize(): Promise<void> {
    this.logger.info('Initializing Specification Generator');
    
    try {
      // Load specification templates
      await this.loadTemplates();
      
      this.initialized = true;
      this.logger.info('Specification Generator initialized successfully');
      
    } catch (error) {
      this.logger.error('Failed to initialize Specification Generator', error);
      throw error;
    }
  }

  /**
   * Generate comprehensive specification from system analysis
   */
  async generate(
    systemAnalysis: SystemAnalysis,
    options: Partial<SpecificationOptions> = {}
  ): Promise<GenerationResult> {
    if (!this.initialized) {
      throw new Error('Specification Generator not initialized');
    }

    const startTime = Date.now();
    const fullOptions: SpecificationOptions = {
      format: 'markdown',
      includeArchitecture: true,
      includeDiagrams: true,
      includeAPI: true,
      includeDeployment: true,
      includePerformance: true,
      includeSecurity: false,
      customSections: [],
      template: 'standard',
      diagramStyle: 'mermaid',
      detailLevel: 'detailed',
      streaming: false,
      ...options
    };

    this.logger.info(`Starting specification generation with template: ${fullOptions.template}`);

    try {
      // Get template
      const template = this.getTemplate(fullOptions.template);
      
      // Prepare generation context
      const context = await this.prepareGenerationContext(systemAnalysis, fullOptions);
      
      // Generate specification
      let result: GenerationResult;
      
      if (fullOptions.streaming) {
        result = await this.generateStreaming(context, template, fullOptions);
      } else {
        result = await this.generateBatch(context, template, fullOptions);
      }

      // Post-process and enhance
      result = await this.postProcessSpecification(result, fullOptions);
      
      // Update metadata
      result.metadata.processingTime = Date.now() - startTime;
      result.metadata.generatedAt = new Date();

      this.logger.info(`Specification generation completed in ${result.metadata.processingTime}ms`);
      return result;

    } catch (error) {
      this.logger.error('Specification generation failed', error);
      throw new Error(`Specification generation failed: ${error.message}`);
    }
  }

  /**
   * Generate specification with streaming
   */
  private async generateStreaming(
    context: GenerationContext,
    template: SpecificationTemplate,
    options: SpecificationOptions
  ): Promise<GenerationResult> {
    
    return new Promise((resolve, reject) => {
      let accumulatedContent = '';
      let currentSection = '';
      const warnings: string[] = [];
      const suggestions: string[] = [];
      const diagrams: GeneratedDiagram[] = [];
      let aiTokensUsed = 0;

      this.logger.info('Starting streaming specification generation');

      // Prepare streaming prompt
      const prompt = this.buildGenerationPrompt(context, template, options);

      // Start streaming generation
      this.zaiClient.generateFullStack({
        baseDocument: context.analysisDocument,
        masterPrompt: prompt,
        options: {
          framework: 'documentation',
          database: 'none',
          styling: 'markdown',
          features: ['streaming', 'diagrams'],
          streaming: true
        }
      }).then(response => {
        resolve({
          specification: accumulatedContent,
          metadata: {
            generatedAt: new Date(),
            wordCount: this.countWords(accumulatedContent),
            sectionCount: this.countSections(accumulatedContent),
            diagramCount: diagrams.length,
            processingTime: 0,
            aiTokensUsed: response.metadata.tokensUsed
          },
          warnings,
          suggestions,
          artifacts: {
            diagrams,
            attachments: []
          }
        });
      }).catch(reject);

      // Handle streaming chunks
      this.zaiClient.on('streamChunk', (chunk) => {
        switch (chunk.type) {
          case 'content':
            accumulatedContent += chunk.data.content;
            this.emit('specificationProgress', {
              section: currentSection,
              content: chunk.data.content,
              totalLength: accumulatedContent.length
            });
            break;
            
          case 'metadata':
            if (chunk.data.section) {
              currentSection = chunk.data.section;
            }
            if (chunk.data.diagram) {
              diagrams.push(chunk.data.diagram);
            }
            break;
            
          case 'progress':
            this.emit('generationProgress', chunk.data.progress);
            break;
        }
      });
    });
  }

  /**
   * Generate specification in batch mode
   */
  private async generateBatch(
    context: GenerationContext,
    template: SpecificationTemplate,
    options: SpecificationOptions
  ): Promise<GenerationResult> {
    
    this.logger.info('Starting batch specification generation');

    // Build generation prompt
    const prompt = this.buildGenerationPrompt(context, template, options);

    // Generate with Z.ai
    const response = await this.zaiClient.generateFullStack({
      baseDocument: context.analysisDocument,
      masterPrompt: prompt,
      options: {
        framework: 'documentation',
        database: 'none',
        styling: 'markdown',
        features: ['diagrams', 'comprehensive'],
        streaming: false
      }
    });

    // Parse generated content
    const specification = this.parseGeneratedSpecification(response.modifiedDocument);
    
    // Extract diagrams and attachments
    const diagrams = await this.extractDiagrams(specification, options.diagramStyle);
    const attachments = await this.generateAttachments(context.systemAnalysis);

    return {
      specification,
      metadata: {
        generatedAt: new Date(),
        wordCount: this.countWords(specification),
        sectionCount: this.countSections(specification),
        diagramCount: diagrams.length,
        processingTime: 0,
        aiTokensUsed: response.metadata.tokensUsed
      },
      warnings: response.warnings,
      suggestions: response.suggestions,
      artifacts: {
        diagrams,
        attachments
      }
    };
  }

  /**
   * Prepare generation context from system analysis
   */
  private async prepareGenerationContext(
    systemAnalysis: SystemAnalysis,
    options: SpecificationOptions
  ): Promise<GenerationContext> {
    
    // Convert system analysis to structured document format
    const analysisDocument = {
      metadata: systemAnalysis.metadata,
      steps: [], // Not applicable for specification generation
      dependencies: this.convertDependenciesToBuildFormat(systemAnalysis.architecture.dependencies),
      environment: this.extractEnvironmentInfo(systemAnalysis),
      validation: []
    };

    return {
      systemAnalysis,
      analysisDocument,
      options,
      timestamp: new Date()
    };
  }

  /**
   * Build generation prompt for AI
   */
  private buildGenerationPrompt(
    context: GenerationContext,
    template: SpecificationTemplate,
    options: SpecificationOptions
  ): string {
    
    const sections = template.sections.filter(section => {
      // Filter sections based on options
      if (!options.includeArchitecture && section.id.includes('architecture')) return false;
      if (!options.includeAPI && section.id.includes('api')) return false;
      if (!options.includeDeployment && section.id.includes('deployment')) return false;
      if (!options.includePerformance && section.id.includes('performance')) return false;
      if (!options.includeSecurity && section.id.includes('security')) return false;
      return true;
    });

    const prompt = `
# System Specification Generation Task

You are tasked with generating a comprehensive ${options.detailLevel} specification document for a JAEGIS AI Web OS system based on the provided system analysis.

## System Analysis Data:
${JSON.stringify(context.systemAnalysis, null, 2)}

## Specification Requirements:
- Format: ${options.format}
- Template: ${options.template}
- Detail Level: ${options.detailLevel}
- Include Diagrams: ${options.includeDiagrams}
- Diagram Style: ${options.diagramStyle}

## Required Sections:
${sections.map(section => `### ${section.title}\n${section.description}\n`).join('\n')}

## Generation Guidelines:

1. **Structure**: Follow the template structure exactly
2. **Accuracy**: Base all content on the provided system analysis data
3. **Clarity**: Write for ${this.getTargetAudience(options.template)} audience
4. **Completeness**: Cover all requested sections thoroughly
5. **Diagrams**: Generate ${options.diagramStyle} diagrams where appropriate

${options.includeDiagrams ? `
## Diagram Requirements:
- Use ${options.diagramStyle} syntax
- Include architecture overview diagram
- Add component relationship diagrams
- Create deployment diagrams if infrastructure data is available
- Ensure all diagrams are properly formatted and labeled
` : ''}

## Output Format:
Generate a complete ${options.format} document that can be immediately used as system documentation.

Begin generation now:
`;

    return prompt;
  }

  /**
   * Parse generated specification from AI response
   */
  private parseGeneratedSpecification(response: any): string {
    if (typeof response === 'string') {
      return response;
    }
    
    if (response.content) {
      return response.content;
    }
    
    if (response.specification) {
      return response.specification;
    }
    
    // Try to extract from steps if it's in build document format
    if (response.steps) {
      const contentSteps = response.steps.filter((step: any) => 
        step.type === 'WRITE_FILE' && step.filePath?.endsWith('.md')
      );
      
      if (contentSteps.length > 0) {
        return contentSteps.map((step: any) => step.content).join('\n\n');
      }
    }
    
    return JSON.stringify(response, null, 2);
  }

  /**
   * Extract diagrams from specification content
   */
  private async extractDiagrams(specification: string, diagramStyle: string): Promise<GeneratedDiagram[]> {
    const diagrams: GeneratedDiagram[] = [];
    
    if (diagramStyle === 'mermaid') {
      const mermaidRegex = /```mermaid\n([\s\S]*?)\n```/g;
      let match;
      let diagramIndex = 0;
      
      while ((match = mermaidRegex.exec(specification)) !== null) {
        diagrams.push({
          id: `diagram-${diagramIndex++}`,
          title: this.extractDiagramTitle(match[0]),
          type: this.detectDiagramType(match[1]),
          format: 'mermaid',
          content: match[1].trim(),
          description: this.generateDiagramDescription(match[1])
        });
      }
    }
    
    return diagrams;
  }

  /**
   * Generate additional attachments
   */
  private async generateAttachments(systemAnalysis: SystemAnalysis): Promise<GeneratedAttachment[]> {
    const attachments: GeneratedAttachment[] = [];
    
    // Generate API endpoints JSON
    if (systemAnalysis.architecture.apiEndpoints.length > 0) {
      attachments.push({
        id: 'api-endpoints',
        name: 'api-endpoints.json',
        type: 'json',
        content: JSON.stringify(systemAnalysis.architecture.apiEndpoints, null, 2),
        description: 'Complete list of API endpoints with parameters and responses'
      });
    }
    
    // Generate dependency graph
    if (systemAnalysis.architecture.dependencies.nodes.length > 0) {
      attachments.push({
        id: 'dependencies',
        name: 'dependencies.json',
        type: 'json',
        content: JSON.stringify(systemAnalysis.architecture.dependencies, null, 2),
        description: 'System dependency graph with nodes and relationships'
      });
    }
    
    // Generate performance metrics
    attachments.push({
      id: 'performance-metrics',
      name: 'performance-metrics.json',
      type: 'json',
      content: JSON.stringify(systemAnalysis.customizations.performanceMetrics, null, 2),
      description: 'System performance metrics and benchmarks'
    });
    
    return attachments;
  }

  /**
   * Post-process and enhance specification
   */
  private async postProcessSpecification(
    result: GenerationResult,
    options: SpecificationOptions
  ): Promise<GenerationResult> {
    
    // Add table of contents
    result.specification = this.addTableOfContents(result.specification);
    
    // Validate and fix diagram syntax
    if (options.includeDiagrams) {
      result.specification = await this.validateDiagramSyntax(result.specification, options.diagramStyle);
    }
    
    // Add metadata footer
    result.specification = this.addMetadataFooter(result.specification, result.metadata);
    
    // Format according to output format
    if (options.format !== 'markdown') {
      result.specification = await this.convertFormat(result.specification, options.format);
    }
    
    return result;
  }

  // Helper methods
  private getTemplate(templateName: string): SpecificationTemplate {
    const template = this.templates.get(templateName);
    if (!template) {
      throw new Error(`Template not found: ${templateName}`);
    }
    return template;
  }

  private getTargetAudience(template: string): string {
    switch (template) {
      case 'executive': return 'executive and business stakeholder';
      case 'technical': return 'technical architect and senior developer';
      case 'developer': return 'developer and implementation team';
      default: return 'general technical';
    }
  }

  private countWords(text: string): number {
    return text.split(/\s+/).filter(word => word.length > 0).length;
  }

  private countSections(text: string): number {
    return (text.match(/^#+\s/gm) || []).length;
  }

  private extractDiagramTitle(diagramBlock: string): string {
    const lines = diagramBlock.split('\n');
    for (const line of lines) {
      if (line.includes('title') || line.includes('Title')) {
        return line.replace(/.*title[:\s]*/i, '').trim();
      }
    }
    return 'System Diagram';
  }

  private detectDiagramType(content: string): 'architecture' | 'flow' | 'sequence' | 'component' | 'deployment' {
    if (content.includes('sequenceDiagram')) return 'sequence';
    if (content.includes('flowchart') || content.includes('graph')) return 'flow';
    if (content.includes('deployment') || content.includes('container')) return 'deployment';
    if (content.includes('component') || content.includes('class')) return 'component';
    return 'architecture';
  }

  private generateDiagramDescription(content: string): string {
    const type = this.detectDiagramType(content);
    return `${type.charAt(0).toUpperCase() + type.slice(1)} diagram showing system relationships and structure`;
  }

  private addTableOfContents(specification: string): string {
    const headers = specification.match(/^#+\s.+$/gm) || [];
    const toc = headers.map(header => {
      const level = header.match(/^#+/)?.[0].length || 1;
      const title = header.replace(/^#+\s/, '');
      const anchor = title.toLowerCase().replace(/[^a-z0-9]+/g, '-');
      const indent = '  '.repeat(level - 1);
      return `${indent}- [${title}](#${anchor})`;
    }).join('\n');

    return `# Table of Contents\n\n${toc}\n\n---\n\n${specification}`;
  }

  private addMetadataFooter(specification: string, metadata: any): string {
    const footer = `

---

## Document Metadata

- **Generated**: ${metadata.generatedAt.toISOString()}
- **Word Count**: ${metadata.wordCount}
- **Sections**: ${metadata.sectionCount}
- **Diagrams**: ${metadata.diagramCount}
- **Processing Time**: ${metadata.processingTime}ms

*This document was automatically generated by JAEGIS AI Web OS Specification Generator*
`;

    return specification + footer;
  }

  private async validateDiagramSyntax(specification: string, diagramStyle: string): Promise<string> {
    // Basic validation for Mermaid diagrams
    if (diagramStyle === 'mermaid') {
      // Add basic syntax validation and fixes
      return specification.replace(/```mermaid\n([\s\S]*?)\n```/g, (match, content) => {
        // Basic cleanup
        const cleanContent = content.trim();
        return `\`\`\`mermaid\n${cleanContent}\n\`\`\``;
      });
    }
    
    return specification;
  }

  private async convertFormat(specification: string, format: string): Promise<string> {
    // Placeholder for format conversion
    // In production, would use libraries like markdown-pdf, etc.
    switch (format) {
      case 'html':
        return `<html><body><div class="specification">${specification}</div></body></html>`;
      case 'json':
        return JSON.stringify({ specification, format: 'markdown' }, null, 2);
      default:
        return specification;
    }
  }

  private convertDependenciesToBuildFormat(dependencies: any): any[] {
    // Convert dependency graph to build document format
    return dependencies.nodes.map((node: any) => ({
      name: node.name,
      version: node.version || 'latest',
      type: 'npm',
      optional: false
    }));
  }

  private extractEnvironmentInfo(systemAnalysis: SystemAnalysis): any {
    return {
      nodeVersion: '18.0.0',
      dockerRequired: systemAnalysis.infrastructure.containers.length > 0,
      environmentVariables: {},
      systemRequirements: ['Docker', 'Node.js']
    };
  }

  private async loadTemplates(): Promise<void> {
    // Load specification templates
    const standardTemplate: SpecificationTemplate = {
      id: 'standard',
      name: 'Standard Technical Specification',
      description: 'Comprehensive technical specification for development teams',
      sections: [
        {
          id: 'overview',
          title: 'System Overview',
          description: 'High-level system description and purpose',
          order: 1,
          required: true
        },
        {
          id: 'architecture',
          title: 'Architecture',
          description: 'System architecture and component relationships',
          order: 2,
          required: true
        },
        {
          id: 'api',
          title: 'API Documentation',
          description: 'Complete API endpoint documentation',
          order: 3,
          required: false
        },
        {
          id: 'deployment',
          title: 'Deployment Guide',
          description: 'Deployment instructions and infrastructure requirements',
          order: 4,
          required: false
        },
        {
          id: 'performance',
          title: 'Performance Metrics',
          description: 'System performance characteristics and benchmarks',
          order: 5,
          required: false
        }
      ]
    };

    this.templates.set('standard', standardTemplate);
    
    // Add other templates (technical, executive, developer)
    // ... (implementation for other templates)
  }
}

// Supporting interfaces
interface GenerationContext {
  systemAnalysis: SystemAnalysis;
  analysisDocument: any;
  options: SpecificationOptions;
  timestamp: Date;
}

interface SpecificationTemplate {
  id: string;
  name: string;
  description: string;
  sections: TemplateSection[];
}

interface TemplateSection {
  id: string;
  title: string;
  description: string;
  order: number;
  required: boolean;
  template?: string;
}

export default SpecificationGenerator;