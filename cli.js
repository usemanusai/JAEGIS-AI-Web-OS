#!/usr/bin/env node

/**
 * MCP Server CLI Wrapper
 * 
 * Node.js wrapper that manages Python environment setup and provides
 * seamless command execution for the MCP Server application foundry.
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

class MCPServerCLI {
    constructor() {
        this.projectRoot = __dirname;
        this.mcpEnvPath = path.join(this.projectRoot, '.mcp-env');
        this.requirementsPath = path.join(this.projectRoot, 'requirements.txt');
        this.isWindows = os.platform() === 'win32';
        
        // Python executable paths
        this.pythonCmd = this.isWindows ? 'python' : 'python3';
        this.pipCmd = this.isWindows ? 'pip' : 'pip3';
        
        // Virtual environment paths
        this.venvPython = this.isWindows 
            ? path.join(this.mcpEnvPath, 'Scripts', 'python.exe')
            : path.join(this.mcpEnvPath, 'bin', 'python');
            
        this.venvPip = this.isWindows
            ? path.join(this.mcpEnvPath, 'Scripts', 'pip.exe')
            : path.join(this.mcpEnvPath, 'bin', 'pip');
    }

    /**
     * Main entry point for CLI execution
     */
    async run() {
        try {
            // Parse command line arguments
            const args = process.argv.slice(2);
            
            if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
                this.showHelp();
                return;
            }

            if (args[0] === '--version' || args[0] === '-v') {
                this.showVersion();
                return;
            }

            // Ensure Python environment is set up
            await this.ensurePythonEnvironment();

            // Execute the Python CLI with provided arguments
            await this.executePythonCLI(args);

        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    }

    /**
     * Ensure Python environment is properly set up
     */
    async ensurePythonEnvironment() {
        console.log('🔧 Checking Python environment...');

        // Check if virtual environment exists
        if (!fs.existsSync(this.mcpEnvPath)) {
            console.log('📦 Setting up Python environment for first time...');
            await this.setupPythonEnvironment();
        } else {
            console.log('✅ Python environment found');
            
            // Verify dependencies are installed
            if (!await this.verifyDependencies()) {
                console.log('📦 Installing missing dependencies...');
                await this.installDependencies();
            }
        }
    }

    /**
     * Set up Python virtual environment and install dependencies
     */
    async setupPythonEnvironment() {
        // Verify Python is available
        await this.verifyPython();

        // Create virtual environment
        console.log('🐍 Creating Python virtual environment...');
        await this.runCommand(this.pythonCmd, ['-m', 'venv', this.mcpEnvPath]);

        // Install dependencies
        await this.installDependencies();
    }

    /**
     * Verify Python is available and meets minimum version requirements
     */
    async verifyPython() {
        try {
            const version = await this.runCommand(this.pythonCmd, ['--version'], { capture: true });
            console.log(`✅ Found Python: ${version.trim()}`);
            
            // Check version (should be 3.8+)
            const versionMatch = version.match(/Python (\d+)\.(\d+)/);
            if (versionMatch) {
                const major = parseInt(versionMatch[1]);
                const minor = parseInt(versionMatch[2]);
                
                if (major < 3 || (major === 3 && minor < 8)) {
                    throw new Error(`Python 3.8+ required, found ${major}.${minor}`);
                }
            }
        } catch (error) {
            throw new Error(`Python not found or invalid. Please install Python 3.8+ and ensure it's in your PATH.\nError: ${error.message}`);
        }
    }

    /**
     * Install Python dependencies in virtual environment
     */
    async installDependencies() {
        if (!fs.existsSync(this.requirementsPath)) {
            throw new Error(`Requirements file not found: ${this.requirementsPath}`);
        }

        console.log('📦 Installing Python dependencies...');

        try {
            // Upgrade pip first (with retry logic)
            console.log('🔄 Upgrading pip...');
            await this.runCommand(this.venvPython, ['-m', 'pip', 'install', '--upgrade', 'pip'], {
                timeout: 120000 // 2 minutes for pip upgrade
            });
        } catch (error) {
            console.log('⚠️ Pip upgrade failed, continuing with existing version...');
            // Don't fail the entire process if pip upgrade fails
        }

        try {
            // Install requirements with retry
            console.log('📦 Installing requirements...');
            await this.runCommand(this.venvPython, ['-m', 'pip', 'install', '-r', this.requirementsPath], {
                timeout: 300000 // 5 minutes for requirements installation
            });
            console.log('✅ Dependencies installed successfully');
        } catch (error) {
            throw new Error(`Failed to install Python dependencies: ${error.message}`);
        }
    }

    /**
     * Verify that required dependencies are installed
     */
    async verifyDependencies() {
        try {
            // Check if key packages are installed
            const result = await this.runCommand(this.venvPython, ['-c', 'import click, docx, PyPDF2, openai'], { capture: true, silent: true });
            return true;
        } catch (error) {
            return false;
        }
    }

    /**
     * Execute the Python CLI with provided arguments
     */
    async executePythonCLI(args) {
        console.log('🚀 Launching MCP Server...\n');
        
        // Execute Python module with arguments
        const pythonArgs = ['-m', 'mcp_server', ...args];
        
        await this.runCommand(this.venvPython, pythonArgs, { 
            stdio: 'inherit',
            cwd: this.projectRoot 
        });
    }

    /**
     * Run a command and return output or handle stdio
     */
    async runCommand(command, args = [], options = {}) {
        return new Promise((resolve, reject) => {
            const {
                capture = false,
                silent = false,
                stdio = capture ? 'pipe' : 'inherit',
                cwd = this.projectRoot,
                timeout = 300000 // 5 minute default timeout
            } = options;

            if (!silent) {
                console.log(`🔧 Running: ${command} ${args.join(' ')}`);
            }

            // Properly handle paths with spaces on Windows
            let execCommand = command;
            let execArgs = args;

            if (this.isWindows) {
                // On Windows, use cmd.exe to properly handle paths with spaces
                execCommand = 'cmd.exe';
                execArgs = ['/c', `"${command}"`, ...args];
            }

            const child = spawn(execCommand, execArgs, {
                stdio,
                cwd,
                shell: false, // We handle shell explicitly above
                windowsHide: true
            });

            let output = '';
            let errorOutput = '';
            let timeoutId;

            if (capture) {
                child.stdout?.on('data', (data) => {
                    output += data.toString();
                });

                child.stderr?.on('data', (data) => {
                    errorOutput += data.toString();
                });
            }

            // Set up timeout
            if (timeout > 0) {
                timeoutId = setTimeout(() => {
                    child.kill('SIGTERM');
                    reject(new Error(`Command timed out after ${timeout}ms`));
                }, timeout);
            }

            child.on('close', (code) => {
                if (timeoutId) clearTimeout(timeoutId);

                if (code === 0) {
                    resolve(capture ? output : code);
                } else {
                    const error = new Error(`Command failed with exit code ${code}`);
                    if (capture && errorOutput) {
                        error.message += `\nError output: ${errorOutput}`;
                    }
                    reject(error);
                }
            });

            child.on('error', (error) => {
                if (timeoutId) clearTimeout(timeoutId);
                reject(new Error(`Failed to start command: ${error.message}`));
            });
        });
    }

    /**
     * Show help information
     */
    showHelp() {
        console.log(`
🚀 MCP Server - Universal AI-Powered Application Foundry

USAGE:
    mcp-server <command> [options]

COMMANDS:
    build       Build an application from architectural documentation
    execute     Execute an existing build plan
    analyze     Analyze a document and show processing results

OPTIONS:
    --help, -h      Show this help message
    --version, -v   Show version information

EXAMPLES:
    # Build from a document
    mcp-server build --base ./architecture.docx --output ./my-project

    # Build with overlay document
    mcp-server build --base ./base.docx --overlay ./overlay.md --output ./project

    # Generate build plan only
    mcp-server build --base ./docs.pdf --plan-only

    # Execute existing build plan
    mcp-server execute ./UnifiedBuildPlan.json --output ./project

    # Analyze document structure
    mcp-server analyze ./document.docx

For detailed help on specific commands, use:
    mcp-server <command> --help

ENVIRONMENT VARIABLES:
    OPENAI_API_KEY    OpenAI API key for AI-enhanced synthesis

REQUIREMENTS:
    - Python 3.8+
    - Node.js 14+
    - Internet connection for AI features (optional)
        `);
    }

    /**
     * Show version information
     */
    showVersion() {
        const packageJson = JSON.parse(fs.readFileSync(path.join(this.projectRoot, 'package.json'), 'utf8'));
        console.log(`MCP Server v${packageJson.version}`);
    }
}

// Main execution
if (require.main === module) {
    const cli = new MCPServerCLI();
    cli.run().catch((error) => {
        console.error('❌ Fatal error:', error.message);
        process.exit(1);
    });
}

module.exports = MCPServerCLI;
