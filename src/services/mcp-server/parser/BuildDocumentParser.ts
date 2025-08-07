/**
 * Build Document Parser
 * Parses COMPLETE_BUILD_INSTRUCTIONS document into structured, executable steps
 */

import { Logger } from '../../../utils/logger';
import * as fs from 'fs/promises';
import * as path from 'path';
import { z } from 'zod';

export interface ParsedBuildDocument {
  metadata: BuildMetadata;
  steps: BuildStep[];
  dependencies: BuildDependency[];
  environment: EnvironmentConfig;
  validation: ValidationRule[];
}

export interface BuildMetadata {
  name: string;
  version: string;
  description: string;
  framework: string;
  targetPlatform: string[];
  estimatedBuildTime: number;
  requiredResources: ResourceRequirements;
}

export interface ResourceRequirements {
  minMemoryMB: number;
  minDiskSpaceGB: number;
  requiredTools: string[];
  optionalTools: string[];
}

export interface BuildStep {
  id: string;
  type: BuildStepType;
  description: string;
  command?: string;
  filePath?: string;
  content?: string;
  dependencies: string[];
  conditions: StepCondition[];
  timeout: number;
  retryCount: number;
  critical: boolean;
  rollbackSteps?: string[];
}

export enum BuildStepType {
  RUN_COMMAND = 'RUN_COMMAND',
  WRITE_FILE = 'WRITE_FILE',
  INSTALL_DEPENDENCY = 'INSTALL_DEPENDENCY',
  CREATE_DIRECTORY = 'CREATE_DIRECTORY',
  COPY_FILE = 'COPY_FILE',
  MODIFY_FILE = 'MODIFY_FILE',
  VALIDATE_STEP = 'VALIDATE_STEP',
  CONDITIONAL_STEP = 'CONDITIONAL_STEP'
}

export interface StepCondition {
  type: 'FILE_EXISTS' | 'COMMAND_SUCCESS' | 'ENV_VAR_SET' | 'CUSTOM';
  target: string;
  expected?: any;
  customValidator?: string;
}

export interface BuildDependency {
  name: string;
  version: string;
  type: 'npm' | 'pip' | 'apt' | 'brew' | 'docker' | 'binary';
  source?: string;
  installCommand?: string;
  verifyCommand?: string;
  optional: boolean;
}

export interface EnvironmentConfig {
  nodeVersion: string;
  pythonVersion?: string;
  dockerRequired: boolean;
  environmentVariables: Record<string, string>;
  systemRequirements: string[];
}

export interface ValidationRule {
  id: string;
  description: string;
  type: 'FILE_EXISTS' | 'COMMAND_OUTPUT' | 'PORT_ACCESSIBLE' | 'CUSTOM';
  target: string;
  expected: any;
  critical: boolean;
}

// Zod schemas for validation
const BuildStepSchema = z.object({
  id: z.string(),
  type: z.nativeEnum(BuildStepType),
  description: z.string(),
  command: z.string().optional(),
  filePath: z.string().optional(),
  content: z.string().optional(),
  dependencies: z.array(z.string()).default([]),
  conditions: z.array(z.any()).default([]),
  timeout: z.number().default(300000), // 5 minutes default
  retryCount: z.number().default(0),
  critical: z.boolean().default(false),
  rollbackSteps: z.array(z.string()).optional()
});

const ParsedBuildDocumentSchema = z.object({
  metadata: z.object({
    name: z.string(),
    version: z.string(),
    description: z.string(),
    framework: z.string(),
    targetPlatform: z.array(z.string()),
    estimatedBuildTime: z.number(),
    requiredResources: z.object({
      minMemoryMB: z.number(),
      minDiskSpaceGB: z.number(),
      requiredTools: z.array(z.string()),
      optionalTools: z.array(z.string())
    })
  }),
  steps: z.array(BuildStepSchema),
  dependencies: z.array(z.any()),
  environment: z.object({
    nodeVersion: z.string(),
    pythonVersion: z.string().optional(),
    dockerRequired: z.boolean(),
    environmentVariables: z.record(z.string()),
    systemRequirements: z.array(z.string())
  }),
  validation: z.array(z.any())
});

export class BuildDocumentParser {
  private logger: Logger;
  private initialized: boolean = false;

  constructor() {
    this.logger = new Logger('BuildDocumentParser');
  }

  async initialize(): Promise<void> {
    this.logger.info('Initializing Build Document Parser');
    this.initialized = true;
  }

  /**
   * Parse a build document from various sources
   */
  async parse(source: string | Buffer | ParsedBuildDocument): Promise<ParsedBuildDocument> {
    if (!this.initialized) {
      throw new Error('Parser not initialized');
    }

    try {
      let rawContent: string;

      // Handle different input types
      if (typeof source === 'string') {
        if (this.isFilePath(source)) {
          rawContent = await fs.readFile(source, 'utf-8');
        } else {
          rawContent = source;
        }
      } else if (Buffer.isBuffer(source)) {
        rawContent = source.toString('utf-8');
      } else {
        // Already parsed document
        return this.validateParsedDocument(source);
      }

      // Detect document format and parse accordingly
      const format = this.detectDocumentFormat(rawContent);
      let parsedDocument: ParsedBuildDocument;

      switch (format) {
        case 'DOCX':
          parsedDocument = await this.parseDocxContent(rawContent);
          break;
        case 'MARKDOWN':
          parsedDocument = await this.parseMarkdownContent(rawContent);
          break;
        case 'JSON':
          parsedDocument = await this.parseJsonContent(rawContent);
          break;
        case 'YAML':
          parsedDocument = await this.parseYamlContent(rawContent);
          break;
        default:
          throw new Error(`Unsupported document format: ${format}`);
      }

      // Validate and enhance the parsed document
      const validatedDocument = this.validateParsedDocument(parsedDocument);
      const enhancedDocument = await this.enhanceDocument(validatedDocument);

      this.logger.info(`Successfully parsed build document with ${enhancedDocument.steps.length} steps`);
      return enhancedDocument;

    } catch (error) {
      this.logger.error('Failed to parse build document', error);
      throw new Error(`Build document parsing failed: ${error.message}`);
    }
  }

  /**
   * Parse DOCX content (simulated - would use actual DOCX parser in production)
   */
  private async parseDocxContent(content: string): Promise<ParsedBuildDocument> {
    this.logger.info('Parsing DOCX content');
    
    // This would integrate with a real DOCX parser like mammoth.js
    // For now, we'll simulate parsing the COMPLETE_BUILD_INSTRUCTIONS
    
    return {
      metadata: {
        name: 'JAEGIS AI Web OS',
        version: '2.2.0',
        description: 'AI-powered Web Operating System with Redis integration',
        framework: 'Next.js 15',
        targetPlatform: ['web', 'docker'],
        estimatedBuildTime: 600000, // 10 minutes
        requiredResources: {
          minMemoryMB: 4096,
          minDiskSpaceGB: 10,
          requiredTools: ['node', 'npm', 'docker'],
          optionalTools: ['redis-cli', 'prisma']
        }
      },
      steps: await this.generateBaselineSteps(),
      dependencies: await this.generateBaseDependencies(),
      environment: {
        nodeVersion: '18.0.0',
        dockerRequired: true,
        environmentVariables: {
          'NODE_ENV': 'production',
          'NEXT_TELEMETRY_DISABLED': '1'
        },
        systemRequirements: ['Docker', 'Node.js 18+', 'Git']
      },
      validation: await this.generateValidationRules()
    };
  }

  /**
   * Parse Markdown content
   */
  private async parseMarkdownContent(content: string): Promise<ParsedBuildDocument> {
    this.logger.info('Parsing Markdown content');
    
    const lines = content.split('\n');
    const steps: BuildStep[] = [];
    let currentStep: Partial<BuildStep> | null = null;
    let stepCounter = 0;

    for (const line of lines) {
      const trimmedLine = line.trim();
      
      // Detect step headers
      if (trimmedLine.startsWith('##') || trimmedLine.startsWith('###')) {
        if (currentStep) {
          steps.push(this.finalizeStep(currentStep, stepCounter++));
        }
        currentStep = {
          description: trimmedLine.replace(/^#+\s*/, ''),
          dependencies: [],
          conditions: [],
          timeout: 300000,
          retryCount: 0,
          critical: false
        };
      }
      
      // Detect commands
      else if (trimmedLine.startsWith('```bash') || trimmedLine.startsWith('```sh')) {
        if (currentStep) {
          currentStep.type = BuildStepType.RUN_COMMAND;
        }
      }
      
      // Detect file operations
      else if (trimmedLine.includes('create file') || trimmedLine.includes('write to')) {
        if (currentStep) {
          currentStep.type = BuildStepType.WRITE_FILE;
        }
      }
      
      // Detect npm/package installations
      else if (trimmedLine.includes('npm install') || trimmedLine.includes('yarn add')) {
        if (currentStep) {
          currentStep.type = BuildStepType.INSTALL_DEPENDENCY;
          currentStep.command = trimmedLine;
        }
      }
    }

    // Finalize last step
    if (currentStep) {
      steps.push(this.finalizeStep(currentStep, stepCounter));
    }

    return {
      metadata: {
        name: 'Parsed Markdown Build',
        version: '1.0.0',
        description: 'Build instructions parsed from Markdown',
        framework: 'Unknown',
        targetPlatform: ['web'],
        estimatedBuildTime: steps.length * 30000, // 30s per step estimate
        requiredResources: {
          minMemoryMB: 2048,
          minDiskSpaceGB: 5,
          requiredTools: ['node', 'npm'],
          optionalTools: []
        }
      },
      steps,
      dependencies: [],
      environment: {
        nodeVersion: '18.0.0',
        dockerRequired: false,
        environmentVariables: {},
        systemRequirements: ['Node.js']
      },
      validation: []
    };
  }

  /**
   * Parse JSON content
   */
  private async parseJsonContent(content: string): Promise<ParsedBuildDocument> {
    try {
      const parsed = JSON.parse(content);
      return this.validateParsedDocument(parsed);
    } catch (error) {
      throw new Error(`Invalid JSON format: ${error.message}`);
    }
  }

  /**
   * Parse YAML content
   */
  private async parseYamlContent(content: string): Promise<ParsedBuildDocument> {
    // Would use yaml parser like js-yaml
    throw new Error('YAML parsing not yet implemented');
  }

  /**
   * Generate baseline build steps for JAEGIS OS v2.2.0
   */
  private async generateBaselineSteps(): Promise<BuildStep[]> {
    return [
      {
        id: 'init-project',
        type: BuildStepType.RUN_COMMAND,
        description: 'Initialize Next.js project',
        command: 'npx create-next-app@latest jaegis-os --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"',
        dependencies: [],
        conditions: [],
        timeout: 300000,
        retryCount: 2,
        critical: true
      },
      {
        id: 'install-dependencies',
        type: BuildStepType.INSTALL_DEPENDENCY,
        description: 'Install core dependencies',
        command: 'npm install @prisma/client prisma @next/font lucide-react @radix-ui/react-dialog @radix-ui/react-dropdown-menu',
        dependencies: ['init-project'],
        conditions: [],
        timeout: 300000,
        retryCount: 2,
        critical: true
      },
      {
        id: 'setup-prisma',
        type: BuildStepType.RUN_COMMAND,
        description: 'Initialize Prisma',
        command: 'npx prisma init',
        dependencies: ['install-dependencies'],
        conditions: [],
        timeout: 60000,
        retryCount: 1,
        critical: true
      },
      {
        id: 'create-prisma-schema',
        type: BuildStepType.WRITE_FILE,
        description: 'Create Prisma schema',
        filePath: 'prisma/schema.prisma',
        content: this.getPrismaSchemaContent(),
        dependencies: ['setup-prisma'],
        conditions: [],
        timeout: 30000,
        retryCount: 0,
        critical: true
      },
      {
        id: 'create-app-layout',
        type: BuildStepType.WRITE_FILE,
        description: 'Create main app layout',
        filePath: 'src/app/layout.tsx',
        content: this.getAppLayoutContent(),
        dependencies: ['create-prisma-schema'],
        conditions: [],
        timeout: 30000,
        retryCount: 0,
        critical: true
      },
      {
        id: 'create-desktop-component',
        type: BuildStepType.WRITE_FILE,
        description: 'Create desktop component',
        filePath: 'src/components/Desktop.tsx',
        content: this.getDesktopComponentContent(),
        dependencies: ['create-app-layout'],
        conditions: [],
        timeout: 30000,
        retryCount: 0,
        critical: true
      },
      {
        id: 'setup-docker',
        type: BuildStepType.WRITE_FILE,
        description: 'Create Dockerfile',
        filePath: 'Dockerfile',
        content: this.getDockerfileContent(),
        dependencies: ['create-desktop-component'],
        conditions: [],
        timeout: 30000,
        retryCount: 0,
        critical: false
      },
      {
        id: 'build-project',
        type: BuildStepType.RUN_COMMAND,
        description: 'Build the project',
        command: 'npm run build',
        dependencies: ['setup-docker'],
        conditions: [],
        timeout: 600000,
        retryCount: 1,
        critical: true
      }
    ];
  }

  /**
   * Generate base dependencies
   */
  private async generateBaseDependencies(): Promise<BuildDependency[]> {
    return [
      {
        name: 'node',
        version: '18.0.0',
        type: 'binary',
        verifyCommand: 'node --version',
        optional: false
      },
      {
        name: 'npm',
        version: '8.0.0',
        type: 'binary',
        verifyCommand: 'npm --version',
        optional: false
      },
      {
        name: 'docker',
        version: '20.0.0',
        type: 'binary',
        verifyCommand: 'docker --version',
        optional: true
      }
    ];
  }

  /**
   * Generate validation rules
   */
  private async generateValidationRules(): Promise<ValidationRule[]> {
    return [
      {
        id: 'check-build-output',
        description: 'Verify build output exists',
        type: 'FILE_EXISTS',
        target: '.next/BUILD_ID',
        expected: true,
        critical: true
      },
      {
        id: 'check-package-json',
        description: 'Verify package.json exists',
        type: 'FILE_EXISTS',
        target: 'package.json',
        expected: true,
        critical: true
      }
    ];
  }

  // Helper methods for content generation
  private getPrismaSchemaContent(): string {
    return `// This is your Prisma schema file,
// learn more about it in the docs: https://pris.ly/d/prisma-schema

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}

model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model GenerativeSession {
  id                    String   @id @default(cuid())
  name                  String
  masterPrompt          String
  status                String   @default("PENDING")
  logs                  String   @default("")
  parentSessionId       String?
  generatedArtifactPath String?
  createdAt            DateTime @default(now())
  updatedAt            DateTime @updatedAt
}`;
  }

  private getAppLayoutContent(): string {
    return `import './globals.css'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'JAEGIS AI Web OS',
  description: 'AI-powered Web Operating System',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}`;
  }

  private getDesktopComponentContent(): string {
    return `'use client'

import React from 'react'

export default function Desktop() {
  return (
    <div className="h-screen w-screen bg-gradient-to-br from-blue-900 to-purple-900 relative overflow-hidden">
      <div className="absolute inset-0 bg-black bg-opacity-20" />
      
      {/* Desktop Content */}
      <div className="relative z-10 h-full flex flex-col">
        <div className="flex-1 p-4">
          <h1 className="text-white text-4xl font-bold mb-4">
            JAEGIS AI Web OS
          </h1>
          <p className="text-white text-lg opacity-80">
            AI-Powered Operating System
          </p>
        </div>
        
        {/* Taskbar */}
        <div className="h-12 bg-black bg-opacity-50 backdrop-blur-sm border-t border-white border-opacity-20">
          <div className="h-full flex items-center px-4">
            <div className="text-white text-sm">
              JAEGIS OS v2.2.0
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}`;
  }

  private getDockerfileContent(): string {
    return `FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]`;
  }

  // Utility methods
  private isFilePath(str: string): boolean {
    return str.includes('/') || str.includes('\\') || str.endsWith('.docx') || str.endsWith('.md') || str.endsWith('.json');
  }

  private detectDocumentFormat(content: string): 'DOCX' | 'MARKDOWN' | 'JSON' | 'YAML' {
    if (content.trim().startsWith('{') || content.trim().startsWith('[')) {
      return 'JSON';
    }
    if (content.includes('---\n') || content.includes('---\r\n')) {
      return 'YAML';
    }
    if (content.includes('#') || content.includes('```')) {
      return 'MARKDOWN';
    }
    return 'DOCX'; // Default assumption
  }

  private finalizeStep(step: Partial<BuildStep>, index: number): BuildStep {
    return {
      id: step.id || `step-${index}`,
      type: step.type || BuildStepType.RUN_COMMAND,
      description: step.description || `Step ${index}`,
      command: step.command,
      filePath: step.filePath,
      content: step.content,
      dependencies: step.dependencies || [],
      conditions: step.conditions || [],
      timeout: step.timeout || 300000,
      retryCount: step.retryCount || 0,
      critical: step.critical || false,
      rollbackSteps: step.rollbackSteps
    };
  }

  private validateParsedDocument(document: any): ParsedBuildDocument {
    try {
      return ParsedBuildDocumentSchema.parse(document);
    } catch (error) {
      this.logger.error('Document validation failed', error);
      throw new Error(`Invalid build document structure: ${error.message}`);
    }
  }

  private async enhanceDocument(document: ParsedBuildDocument): Promise<ParsedBuildDocument> {
    // Add step IDs if missing
    document.steps.forEach((step, index) => {
      if (!step.id) {
        step.id = `step-${index + 1}`;
      }
    });

    // Validate step dependencies
    const stepIds = new Set(document.steps.map(s => s.id));
    document.steps.forEach(step => {
      step.dependencies = step.dependencies.filter(dep => stepIds.has(dep));
    });

    // Calculate estimated build time
    document.metadata.estimatedBuildTime = document.steps.reduce((total, step) => {
      return total + (step.timeout || 30000);
    }, 0);

    return document;
  }
}

export default BuildDocumentParser;