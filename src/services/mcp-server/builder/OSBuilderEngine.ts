/**
 * OS Builder Engine
 * Executes parsed build steps to create deployable OS instances
 */

import { Logger } from '../../../utils/logger';
import { ParsedBuildDocument, BuildStep, BuildStepType, ValidationRule } from '../parser/BuildDocumentParser';
import { MCPServerConfig } from '../MCPServerOrchestrator';
import * as fs from 'fs/promises';
import * as path from 'path';
import { spawn, exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export interface BuildOptions {
  sessionId: string;
  workspaceDir: string;
  onProgress?: (progress: number) => void;
  onLog?: (message: string, level?: 'INFO' | 'WARN' | 'ERROR') => void;
  enableSandbox?: boolean;
  dockerImage?: string;
  environmentVariables?: Record<string, string>;
  timeout?: number;
}

export interface BuildResult {
  success: boolean;
  artifactPath: string;
  executedSteps: string[];
  failedStep?: string;
  error?: string;
  buildTime: number;
  logs: BuildLog[];
  metrics: BuildMetrics;
}

export interface BuildLog {
  timestamp: Date;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  step?: string;
  message: string;
  data?: any;
}

export interface BuildMetrics {
  totalSteps: number;
  executedSteps: number;
  failedSteps: number;
  skippedSteps: number;
  buildTime: number;
  resourceUsage: {
    maxMemoryMB: number;
    maxCpuPercent: number;
    diskUsageMB: number;
  };
}

export interface StepExecutionContext {
  workspaceDir: string;
  sessionId: string;
  environmentVariables: Record<string, string>;
  previousSteps: string[];
  rollbackStack: RollbackAction[];
}

export interface RollbackAction {
  type: 'DELETE_FILE' | 'RESTORE_FILE' | 'RUN_COMMAND' | 'REVERT_DIRECTORY';
  target: string;
  data?: any;
}

export class OSBuilderEngine {
  private logger: Logger;
  private config: MCPServerConfig;
  private activeBuildSessions: Map<string, AbortController>;
  private initialized: boolean = false;

  constructor(config: MCPServerConfig) {
    this.config = config;
    this.logger = new Logger('OSBuilderEngine');
    this.activeBuildSessions = new Map();
  }

  async initialize(): Promise<void> {
    this.logger.info('Initializing OS Builder Engine');
    
    // Ensure workspace directory exists
    await fs.mkdir(this.config.workspaceDir, { recursive: true });
    
    // Verify required tools
    await this.verifyBuildEnvironment();
    
    this.initialized = true;
    this.logger.info('OS Builder Engine initialized successfully');
  }

  /**
   * Build an OS from parsed build document
   */
  async build(document: ParsedBuildDocument, options: BuildOptions): Promise<BuildResult> {
    if (!this.initialized) {
      throw new Error('OS Builder Engine not initialized');
    }

    const startTime = Date.now();
    const abortController = new AbortController();
    this.activeBuildSessions.set(options.sessionId, abortController);

    const buildResult: BuildResult = {
      success: false,
      artifactPath: '',
      executedSteps: [],
      buildTime: 0,
      logs: [],
      metrics: {
        totalSteps: document.steps.length,
        executedSteps: 0,
        failedSteps: 0,
        skippedSteps: 0,
        buildTime: 0,
        resourceUsage: {
          maxMemoryMB: 0,
          maxCpuPercent: 0,
          diskUsageMB: 0
        }
      }
    };

    try {
      this.log(buildResult, 'INFO', `Starting build for session: ${options.sessionId}`);
      
      // Setup build environment
      await this.setupBuildEnvironment(options);
      
      // Create execution context
      const context: StepExecutionContext = {
        workspaceDir: options.workspaceDir,
        sessionId: options.sessionId,
        environmentVariables: {
          ...document.environment.environmentVariables,
          ...options.environmentVariables
        },
        previousSteps: [],
        rollbackStack: []
      };

      // Execute build steps sequentially
      const totalSteps = document.steps.length;
      for (let i = 0; i < totalSteps; i++) {
        if (abortController.signal.aborted) {
          throw new Error('Build cancelled by user');
        }

        const step = document.steps[i];
        const progress = (i / totalSteps) * 100;
        
        options.onProgress?.(progress);
        this.log(buildResult, 'INFO', `Executing step ${i + 1}/${totalSteps}: ${step.description}`);

        try {
          // Check step conditions
          const conditionsMet = await this.checkStepConditions(step, context);
          if (!conditionsMet) {
            this.log(buildResult, 'WARN', `Skipping step ${step.id}: conditions not met`);
            buildResult.metrics.skippedSteps++;
            continue;
          }

          // Check dependencies
          const dependenciesMet = this.checkStepDependencies(step, context.previousSteps);
          if (!dependenciesMet) {
            throw new Error(`Step dependencies not met for: ${step.id}`);
          }

          // Execute the step
          await this.executeStep(step, context, buildResult);
          
          buildResult.executedSteps.push(step.id);
          context.previousSteps.push(step.id);
          buildResult.metrics.executedSteps++;

          this.log(buildResult, 'INFO', `Completed step: ${step.id}`);

        } catch (stepError) {
          buildResult.metrics.failedSteps++;
          buildResult.failedStep = step.id;
          
          if (step.critical) {
            this.log(buildResult, 'ERROR', `Critical step failed: ${step.id} - ${stepError.message}`);
            
            // Attempt rollback
            await this.performRollback(context.rollbackStack, buildResult);
            throw stepError;
          } else {
            this.log(buildResult, 'WARN', `Non-critical step failed: ${step.id} - ${stepError.message}`);
            buildResult.metrics.skippedSteps++;
          }
        }
      }

      // Validate build result
      await this.validateBuild(document.validation, options.workspaceDir, buildResult);

      // Finalize build
      buildResult.artifactPath = await this.finalizeBuild(options.workspaceDir, options.sessionId);
      buildResult.success = true;
      
      options.onProgress?.(100);
      this.log(buildResult, 'INFO', 'Build completed successfully');

    } catch (error) {
      buildResult.success = false;
      buildResult.error = error.message;
      this.log(buildResult, 'ERROR', `Build failed: ${error.message}`);
      
      // Cleanup on failure
      await this.cleanupFailedBuild(options.workspaceDir);
      
    } finally {
      buildResult.buildTime = Date.now() - startTime;
      buildResult.metrics.buildTime = buildResult.buildTime;
      
      this.activeBuildSessions.delete(options.sessionId);
      
      // Collect final metrics
      await this.collectBuildMetrics(options.workspaceDir, buildResult.metrics);
    }

    return buildResult;
  }

  /**
   * Cancel an active build session
   */
  async cancelBuild(sessionId: string): Promise<void> {
    const abortController = this.activeBuildSessions.get(sessionId);
    if (abortController) {
      abortController.abort();
      this.logger.info(`Build cancelled for session: ${sessionId}`);
    }
  }

  /**
   * Execute a single build step
   */
  private async executeStep(
    step: BuildStep, 
    context: StepExecutionContext, 
    buildResult: BuildResult
  ): Promise<void> {
    const timeout = step.timeout || 300000; // 5 minutes default
    
    return new Promise(async (resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error(`Step timeout: ${step.id}`));
      }, timeout);

      try {
        switch (step.type) {
          case BuildStepType.RUN_COMMAND:
            await this.executeCommand(step, context, buildResult);
            break;
            
          case BuildStepType.WRITE_FILE:
            await this.writeFile(step, context, buildResult);
            break;
            
          case BuildStepType.INSTALL_DEPENDENCY:
            await this.installDependency(step, context, buildResult);
            break;
            
          case BuildStepType.CREATE_DIRECTORY:
            await this.createDirectory(step, context, buildResult);
            break;
            
          case BuildStepType.COPY_FILE:
            await this.copyFile(step, context, buildResult);
            break;
            
          case BuildStepType.MODIFY_FILE:
            await this.modifyFile(step, context, buildResult);
            break;
            
          case BuildStepType.VALIDATE_STEP:
            await this.validateStep(step, context, buildResult);
            break;
            
          default:
            throw new Error(`Unsupported step type: ${step.type}`);
        }
        
        clearTimeout(timer);
        resolve();
        
      } catch (error) {
        clearTimeout(timer);
        
        // Retry logic
        if (step.retryCount > 0) {
          this.log(buildResult, 'WARN', `Retrying step ${step.id} (${step.retryCount} attempts remaining)`);
          step.retryCount--;
          
          // Wait before retry
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          try {
            await this.executeStep(step, context, buildResult);
            resolve();
          } catch (retryError) {
            reject(retryError);
          }
        } else {
          reject(error);
        }
      }
    });
  }

  /**
   * Execute a shell command
   */
  private async executeCommand(
    step: BuildStep, 
    context: StepExecutionContext, 
    buildResult: BuildResult
  ): Promise<void> {
    if (!step.command) {
      throw new Error('No command specified for RUN_COMMAND step');
    }

    this.log(buildResult, 'DEBUG', `Executing command: ${step.command}`);

    try {
      const { stdout, stderr } = await execAsync(step.command, {
        cwd: context.workspaceDir,
        env: { ...process.env, ...context.environmentVariables },
        maxBuffer: 1024 * 1024 * 10 // 10MB buffer
      });

      if (stdout) {
        this.log(buildResult, 'DEBUG', `Command output: ${stdout}`);
      }
      if (stderr) {
        this.log(buildResult, 'WARN', `Command stderr: ${stderr}`);
      }

      // Add rollback action if needed
      if (step.rollbackSteps) {
        context.rollbackStack.push({
          type: 'RUN_COMMAND',
          target: step.rollbackSteps.join(' && '),
          data: { originalCommand: step.command }
        });
      }

    } catch (error) {
      this.log(buildResult, 'ERROR', `Command failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Write a file to the filesystem
   */
  private async writeFile(
    step: BuildStep, 
    context: StepExecutionContext, 
    buildResult: BuildResult
  ): Promise<void> {
    if (!step.filePath || !step.content) {
      throw new Error('File path and content required for WRITE_FILE step');
    }

    const fullPath = path.resolve(context.workspaceDir, step.filePath);
    const directory = path.dirname(fullPath);

    try {
      // Ensure directory exists
      await fs.mkdir(directory, { recursive: true });

      // Check if file already exists for rollback
      let existingContent: string | null = null;
      try {
        existingContent = await fs.readFile(fullPath, 'utf-8');
      } catch {
        // File doesn't exist, that's fine
      }

      // Write the file
      await fs.writeFile(fullPath, step.content, 'utf-8');
      
      this.log(buildResult, 'DEBUG', `File written: ${step.filePath}`);

      // Add rollback action
      if (existingContent !== null) {
        context.rollbackStack.push({
          type: 'RESTORE_FILE',
          target: fullPath,
          data: { content: existingContent }
        });
      } else {
        context.rollbackStack.push({
          type: 'DELETE_FILE',
          target: fullPath
        });
      }

    } catch (error) {
      this.log(buildResult, 'ERROR', `Failed to write file ${step.filePath}: ${error.message}`);
      throw error;
    }
  }

  /**
   * Install a dependency
   */
  private async installDependency(
    step: BuildStep, 
    context: StepExecutionContext, 
    buildResult: BuildResult
  ): Promise<void> {
    if (!step.command) {
      throw new Error('No install command specified for INSTALL_DEPENDENCY step');
    }

    // This is essentially a command execution with dependency-specific logging
    this.log(buildResult, 'INFO', `Installing dependency: ${step.description}`);
    await this.executeCommand(step, context, buildResult);
  }

  /**
   * Create a directory
   */
  private async createDirectory(
    step: BuildStep, 
    context: StepExecutionContext, 
    buildResult: BuildResult
  ): Promise<void> {
    if (!step.filePath) {
      throw new Error('Directory path required for CREATE_DIRECTORY step');
    }

    const fullPath = path.resolve(context.workspaceDir, step.filePath);

    try {
      await fs.mkdir(fullPath, { recursive: true });
      this.log(buildResult, 'DEBUG', `Directory created: ${step.filePath}`);

      // Add rollback action
      context.rollbackStack.push({
        type: 'REVERT_DIRECTORY',
        target: fullPath
      });

    } catch (error) {
      this.log(buildResult, 'ERROR', `Failed to create directory ${step.filePath}: ${error.message}`);
      throw error;
    }
  }

  /**
   * Copy a file
   */
  private async copyFile(
    step: BuildStep, 
    context: StepExecutionContext, 
    buildResult: BuildResult
  ): Promise<void> {
    // Implementation for file copying
    throw new Error('COPY_FILE step not yet implemented');
  }

  /**
   * Modify an existing file
   */
  private async modifyFile(
    step: BuildStep, 
    context: StepExecutionContext, 
    buildResult: BuildResult
  ): Promise<void> {
    // Implementation for file modification
    throw new Error('MODIFY_FILE step not yet implemented');
  }

  /**
   * Validate a step
   */
  private async validateStep(
    step: BuildStep, 
    context: StepExecutionContext, 
    buildResult: BuildResult
  ): Promise<void> {
    // Implementation for step validation
    this.log(buildResult, 'INFO', `Validating step: ${step.description}`);
  }

  /**
   * Check if step conditions are met
   */
  private async checkStepConditions(step: BuildStep, context: StepExecutionContext): Promise<boolean> {
    for (const condition of step.conditions) {
      switch (condition.type) {
        case 'FILE_EXISTS':
          const filePath = path.resolve(context.workspaceDir, condition.target);
          try {
            await fs.access(filePath);
          } catch {
            return false;
          }
          break;
          
        case 'COMMAND_SUCCESS':
          try {
            await execAsync(condition.target, { cwd: context.workspaceDir });
          } catch {
            return false;
          }
          break;
          
        case 'ENV_VAR_SET':
          if (!context.environmentVariables[condition.target]) {
            return false;
          }
          break;
      }
    }
    return true;
  }

  /**
   * Check if step dependencies are met
   */
  private checkStepDependencies(step: BuildStep, completedSteps: string[]): boolean {
    return step.dependencies.every(dep => completedSteps.includes(dep));
  }

  /**
   * Perform rollback actions
   */
  private async performRollback(rollbackStack: RollbackAction[], buildResult: BuildResult): Promise<void> {
    this.log(buildResult, 'INFO', 'Performing rollback...');
    
    // Execute rollback actions in reverse order
    for (let i = rollbackStack.length - 1; i >= 0; i--) {
      const action = rollbackStack[i];
      
      try {
        switch (action.type) {
          case 'DELETE_FILE':
            await fs.unlink(action.target);
            break;
            
          case 'RESTORE_FILE':
            await fs.writeFile(action.target, action.data.content, 'utf-8');
            break;
            
          case 'RUN_COMMAND':
            await execAsync(action.target);
            break;
            
          case 'REVERT_DIRECTORY':
            await fs.rmdir(action.target, { recursive: true });
            break;
        }
      } catch (error) {
        this.log(buildResult, 'WARN', `Rollback action failed: ${error.message}`);
      }
    }
  }

  /**
   * Validate the build result
   */
  private async validateBuild(
    validationRules: ValidationRule[], 
    workspaceDir: string, 
    buildResult: BuildResult
  ): Promise<void> {
    this.log(buildResult, 'INFO', 'Validating build result...');
    
    for (const rule of validationRules) {
      try {
        switch (rule.type) {
          case 'FILE_EXISTS':
            const filePath = path.resolve(workspaceDir, rule.target);
            await fs.access(filePath);
            break;
            
          case 'COMMAND_OUTPUT':
            const { stdout } = await execAsync(rule.target, { cwd: workspaceDir });
            if (stdout.trim() !== rule.expected) {
              throw new Error(`Validation failed: expected ${rule.expected}, got ${stdout.trim()}`);
            }
            break;
            
          case 'PORT_ACCESSIBLE':
            // Implementation for port accessibility check
            break;
        }
        
        this.log(buildResult, 'DEBUG', `Validation passed: ${rule.description}`);
        
      } catch (error) {
        const message = `Validation failed: ${rule.description} - ${error.message}`;
        
        if (rule.critical) {
          this.log(buildResult, 'ERROR', message);
          throw new Error(message);
        } else {
          this.log(buildResult, 'WARN', message);
        }
      }
    }
  }

  /**
   * Setup build environment
   */
  private async setupBuildEnvironment(options: BuildOptions): Promise<void> {
    // Ensure workspace directory exists
    await fs.mkdir(options.workspaceDir, { recursive: true });
    
    // Setup environment variables
    if (options.environmentVariables) {
      Object.assign(process.env, options.environmentVariables);
    }
  }

  /**
   * Finalize the build
   */
  private async finalizeBuild(workspaceDir: string, sessionId: string): Promise<string> {
    const artifactPath = path.join(workspaceDir, 'build-artifact.tar.gz');
    
    // Create build artifact (simplified - would use proper archiving)
    await execAsync(`tar -czf ${artifactPath} -C ${workspaceDir} .`);
    
    return artifactPath;
  }

  /**
   * Cleanup failed build
   */
  private async cleanupFailedBuild(workspaceDir: string): Promise<void> {
    try {
      // Remove workspace directory on failure
      await fs.rmdir(workspaceDir, { recursive: true });
    } catch (error) {
      this.logger.warn(`Failed to cleanup build directory: ${error.message}`);
    }
  }

  /**
   * Collect build metrics
   */
  private async collectBuildMetrics(workspaceDir: string, metrics: BuildMetrics): Promise<void> {
    try {
      // Calculate disk usage
      const { stdout } = await execAsync(`du -sm ${workspaceDir}`);
      metrics.resourceUsage.diskUsageMB = parseInt(stdout.split('\t')[0]);
    } catch (error) {
      this.logger.warn(`Failed to collect disk usage metrics: ${error.message}`);
    }
  }

  /**
   * Verify build environment
   */
  private async verifyBuildEnvironment(): Promise<void> {
    const requiredTools = ['node', 'npm'];
    
    for (const tool of requiredTools) {
      try {
        await execAsync(`${tool} --version`);
        this.logger.debug(`Verified tool: ${tool}`);
      } catch (error) {
        throw new Error(`Required tool not found: ${tool}`);
      }
    }
  }

  /**
   * Add log entry to build result
   */
  private log(
    buildResult: BuildResult, 
    level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG', 
    message: string, 
    step?: string,
    data?: any
  ): void {
    const logEntry: BuildLog = {
      timestamp: new Date(),
      level,
      step,
      message,
      data
    };
    
    buildResult.logs.push(logEntry);
    this.logger.log(level.toLowerCase() as any, message, data);
  }
}

export default OSBuilderEngine;