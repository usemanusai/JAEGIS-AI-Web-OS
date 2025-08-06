#!/usr/bin/env node

/**
 * Basic CLI Test for MCP Server
 * 
 * Tests the Node.js CLI wrapper functionality without requiring
 * full Python environment setup.
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

class MCPServerTest {
    constructor() {
        this.cliPath = path.join(__dirname, '..', 'cli.js');
        this.testsPassed = 0;
        this.testsTotal = 0;
    }

    async runTests() {
        console.log('🧪 Running MCP Server CLI Tests\n');

        await this.testHelpCommand();
        await this.testVersionCommand();
        await this.testInvalidCommand();
        await this.testFileStructure();

        console.log(`\n📊 Test Results: ${this.testsPassed}/${this.testsTotal} passed`);
        
        if (this.testsPassed === this.testsTotal) {
            console.log('✅ All tests passed!');
            process.exit(0);
        } else {
            console.log('❌ Some tests failed!');
            process.exit(1);
        }
    }

    async testHelpCommand() {
        this.testsTotal++;
        console.log('🔍 Testing help command...');

        try {
            const output = await this.runCLI(['--help']);
            
            if (output.includes('MCP Server') && output.includes('USAGE:')) {
                console.log('✅ Help command works');
                this.testsPassed++;
            } else {
                console.log('❌ Help command output invalid');
            }
        } catch (error) {
            console.log(`❌ Help command failed: ${error.message}`);
        }
    }

    async testVersionCommand() {
        this.testsTotal++;
        console.log('🔍 Testing version command...');

        try {
            const output = await this.runCLI(['--version']);
            
            if (output.includes('MCP Server v')) {
                console.log('✅ Version command works');
                this.testsPassed++;
            } else {
                console.log('❌ Version command output invalid');
            }
        } catch (error) {
            console.log(`❌ Version command failed: ${error.message}`);
        }
    }

    async testInvalidCommand() {
        this.testsTotal++;
        console.log('🔍 Testing invalid command handling...');

        try {
            // This should fail gracefully
            await this.runCLI(['invalid-command'], { expectFailure: true });
            console.log('✅ Invalid command handled gracefully');
            this.testsPassed++;
        } catch (error) {
            // Expected to fail, but should be graceful
            if (error.message.includes('Command failed')) {
                console.log('✅ Invalid command handled gracefully');
                this.testsPassed++;
            } else {
                console.log(`❌ Invalid command not handled properly: ${error.message}`);
            }
        }
    }

    async testFileStructure() {
        this.testsTotal++;
        console.log('🔍 Testing file structure...');

        const requiredFiles = [
            'cli.js',
            'package.json',
            'requirements.txt',
            'README.md',
            'mcp_server/__init__.py',
            'mcp_server/__main__.py',
            'mcp_server/ingestion.py',
            'mcp_server/asm.py',
            'mcp_server/builder.py'
        ];

        let allFilesExist = true;
        const missingFiles = [];

        for (const file of requiredFiles) {
            const filePath = path.join(__dirname, '..', file);
            if (!fs.existsSync(filePath)) {
                allFilesExist = false;
                missingFiles.push(file);
            }
        }

        if (allFilesExist) {
            console.log('✅ All required files exist');
            this.testsPassed++;
        } else {
            console.log(`❌ Missing files: ${missingFiles.join(', ')}`);
        }
    }

    async runCLI(args, options = {}) {
        const { expectFailure = false } = options;

        return new Promise((resolve, reject) => {
            const child = spawn('node', [this.cliPath, ...args], {
                stdio: 'pipe'
            });

            let output = '';
            let errorOutput = '';

            child.stdout.on('data', (data) => {
                output += data.toString();
            });

            child.stderr.on('data', (data) => {
                errorOutput += data.toString();
            });

            child.on('close', (code) => {
                if (expectFailure || code === 0) {
                    resolve(output + errorOutput);
                } else {
                    reject(new Error(`Command failed with exit code ${code}: ${errorOutput}`));
                }
            });

            child.on('error', (error) => {
                reject(new Error(`Failed to start command: ${error.message}`));
            });
        });
    }
}

// Run tests if this file is executed directly
if (require.main === module) {
    const tester = new MCPServerTest();
    tester.runTests().catch((error) => {
        console.error('❌ Test runner failed:', error.message);
        process.exit(1);
    });
}

module.exports = MCPServerTest;
