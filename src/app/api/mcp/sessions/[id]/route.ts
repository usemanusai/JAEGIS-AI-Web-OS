/**
 * Individual MCP Session API Routes
 * Handles operations for specific sessions
 */

import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import { z } from 'zod';
import MCPServerOrchestrator from '../../../../../services/mcp-server/MCPServerOrchestrator';

const prisma = new PrismaClient();

// Get orchestrator instance (should be singleton)
const mcpOrchestrator = new MCPServerOrchestrator({
  workspaceDir: process.env.MCP_WORKSPACE_DIR || './workspace',
  maxConcurrentSessions: parseInt(process.env.MCP_MAX_CONCURRENT_SESSIONS || '5'),
  sessionTimeoutMs: parseInt(process.env.MCP_SESSION_TIMEOUT_MS || '1800000'),
  enableDocker: process.env.MCP_ENABLE_DOCKER === 'true',
  zaiApiKey: process.env.ZAI_API_KEY || '',
  redisUrl: process.env.REDIS_URL
});

// Validation schemas
const UpdateSessionSchema = z.object({
  action: z.enum(['cancel', 'retry', 'pause', 'resume']),
  metadata: z.record(z.any()).optional()
});

interface RouteParams {
  params: {
    id: string;
  };
}

/**
 * GET /api/mcp/sessions/[id]
 * Get session details with real-time status
 */
export async function GET(request: NextRequest, { params }: RouteParams) {
  try {
    const sessionId = params.id;

    // Get session from database
    const dbSession = await prisma.generativeSession.findUnique({
      where: { id: sessionId },
      include: {
        user: {
          select: { id: true, name: true, email: true }
        },
        parentSession: {
          select: { id: true, name: true, status: true }
        },
        childSessions: {
          select: { id: true, name: true, status: true, createdAt: true }
        },
        buildSteps: {
          orderBy: { executionOrder: 'asc' },
          select: {
            id: true,
            stepId: true,
            type: true,
            description: true,
            status: true,
            executionOrder: true,
            startTime: true,
            endTime: true,
            executionTime: true,
            errorMessage: true,
            retryCount: true,
            critical: true
          }
        }
      }
    });

    if (!dbSession) {
      return NextResponse.json({
        success: false,
        error: 'Session not found'
      }, { status: 404 });
    }

    // Get real-time status from orchestrator
    let orchestratorStatus = null;
    try {
      orchestratorStatus = mcpOrchestrator.getSessionStatus(sessionId);
    } catch (error) {
      // Session might not be in orchestrator memory (completed/old session)
      console.warn(`Session ${sessionId} not found in orchestrator:`, error.message);
    }

    // Merge database and orchestrator data
    const sessionData = {
      ...dbSession,
      logs: dbSession.logs ? JSON.parse(dbSession.logs) : [],
      metadata: dbSession.metadata ? JSON.parse(dbSession.metadata) : {},
      systemAnalysis: dbSession.systemAnalysis ? JSON.parse(dbSession.systemAnalysis) : null,
      // Use orchestrator data if available, otherwise use database data
      status: orchestratorStatus?.status || dbSession.status,
      progress: orchestratorStatus?.progress ?? dbSession.progress,
      realtimeLogs: orchestratorStatus?.logs || [],
      lastUpdated: orchestratorStatus?.lastUpdated || dbSession.updatedAt
    };

    // Get build metrics if available
    const buildMetrics = await prisma.buildMetrics.findUnique({
      where: { sessionId }
    });

    return NextResponse.json({
      success: true,
      data: {
        session: sessionData,
        buildMetrics,
        isRealtime: !!orchestratorStatus
      }
    });

  } catch (error) {
    console.error('Error fetching session:', error);
    
    return NextResponse.json({
      success: false,
      error: 'Failed to fetch session details'
    }, { status: 500 });
  }
}

/**
 * PUT /api/mcp/sessions/[id]
 * Update session (cancel, retry, pause, resume)
 */
export async function PUT(request: NextRequest, { params }: RouteParams) {
  try {
    const sessionId = params.id;
    const body = await request.json();
    const validatedData = UpdateSessionSchema.parse(body);

    // Check if session exists
    const dbSession = await prisma.generativeSession.findUnique({
      where: { id: sessionId }
    });

    if (!dbSession) {
      return NextResponse.json({
        success: false,
        error: 'Session not found'
      }, { status: 404 });
    }

    let result: any = {};

    switch (validatedData.action) {
      case 'cancel':
        try {
          await mcpOrchestrator.cancelSession(sessionId);
          
          // Update database
          await prisma.generativeSession.update({
            where: { id: sessionId },
            data: {
              status: 'CANCELLED',
              updatedAt: new Date()
            }
          });

          result = { message: 'Session cancelled successfully' };
        } catch (error) {
          // Session might already be completed or not in memory
          await prisma.generativeSession.update({
            where: { id: sessionId },
            data: {
              status: 'CANCELLED',
              updatedAt: new Date()
            }
          });
          result = { message: 'Session marked as cancelled' };
        }
        break;

      case 'retry':
        if (dbSession.status !== 'FAILED' && dbSession.status !== 'CANCELLED') {
          return NextResponse.json({
            success: false,
            error: 'Can only retry failed or cancelled sessions'
          }, { status: 400 });
        }

        // Create new session for retry
        const retrySession = await mcpOrchestrator.createSession(
          `${dbSession.name} (Retry)`,
          dbSession.type as any,
          {
            masterPrompt: dbSession.masterPrompt || undefined,
            baseDocument: dbSession.baseDocument || undefined,
            parentSessionId: sessionId,
            metadata: dbSession.metadata ? JSON.parse(dbSession.metadata) : {}
          }
        );

        // Save retry session to database
        const dbRetrySession = await prisma.generativeSession.create({
          data: {
            id: retrySession.id,
            name: retrySession.name,
            type: retrySession.type as any,
            masterPrompt: retrySession.masterPrompt,
            baseDocument: retrySession.baseDocument,
            status: retrySession.status as any,
            progress: retrySession.progress,
            logs: JSON.stringify(retrySession.logs),
            parentSessionId: sessionId,
            metadata: JSON.stringify(retrySession.metadata)
          }
        });

        // Start generation process
        if (dbSession.type === 'SPEC_TO_SYSTEM') {
          mcpOrchestrator.executeSpecToSystem(retrySession.id).catch(error => {
            console.error(`Retry generation failed for session ${retrySession.id}:`, error);
          });
        } else {
          // For system-to-spec, we need the original system target
          // This should be stored in metadata
          const metadata = dbSession.metadata ? JSON.parse(dbSession.metadata) : {};
          const systemTarget = metadata.systemTarget;
          
          if (systemTarget) {
            mcpOrchestrator.executeSystemToSpec(retrySession.id, systemTarget).catch(error => {
              console.error(`Retry analysis failed for session ${retrySession.id}:`, error);
            });
          }
        }

        result = { 
          message: 'Retry session created and started',
          retrySessionId: retrySession.id
        };
        break;

      case 'pause':
        // Note: Pausing is not implemented in the orchestrator yet
        // This would require more complex state management
        return NextResponse.json({
          success: false,
          error: 'Pause functionality not yet implemented'
        }, { status: 501 });

      case 'resume':
        // Note: Resuming is not implemented in the orchestrator yet
        return NextResponse.json({
          success: false,
          error: 'Resume functionality not yet implemented'
        }, { status: 501 });

      default:
        return NextResponse.json({
          success: false,
          error: 'Invalid action'
        }, { status: 400 });
    }

    // Update metadata if provided
    if (validatedData.metadata) {
      const currentMetadata = dbSession.metadata ? JSON.parse(dbSession.metadata) : {};
      const updatedMetadata = { ...currentMetadata, ...validatedData.metadata };
      
      await prisma.generativeSession.update({
        where: { id: sessionId },
        data: {
          metadata: JSON.stringify(updatedMetadata),
          updatedAt: new Date()
        }
      });
    }

    return NextResponse.json({
      success: true,
      data: result
    });

  } catch (error) {
    console.error('Error updating session:', error);
    
    if (error instanceof z.ZodError) {
      return NextResponse.json({
        success: false,
        error: 'Invalid request data',
        details: error.errors
      }, { status: 400 });
    }

    return NextResponse.json({
      success: false,
      error: 'Failed to update session'
    }, { status: 500 });
  }
}

/**
 * DELETE /api/mcp/sessions/[id]
 * Delete session and cleanup artifacts
 */
export async function DELETE(request: NextRequest, { params }: RouteParams) {
  try {
    const sessionId = params.id;

    // Check if session exists
    const dbSession = await prisma.generativeSession.findUnique({
      where: { id: sessionId },
      include: {
        childSessions: {
          select: { id: true }
        }
      }
    });

    if (!dbSession) {
      return NextResponse.json({
        success: false,
        error: 'Session not found'
      }, { status: 404 });
    }

    // Check if session has child sessions
    if (dbSession.childSessions.length > 0) {
      return NextResponse.json({
        success: false,
        error: 'Cannot delete session with child sessions. Delete child sessions first.',
        childSessions: dbSession.childSessions.map(child => child.id)
      }, { status: 400 });
    }

    // Delete from orchestrator (cleanup artifacts)
    try {
      await mcpOrchestrator.deleteSession(sessionId);
    } catch (error) {
      // Session might not be in orchestrator memory
      console.warn(`Session ${sessionId} not found in orchestrator for cleanup:`, error.message);
    }

    // Delete from database (cascade will handle related records)
    await prisma.generativeSession.delete({
      where: { id: sessionId }
    });

    return NextResponse.json({
      success: true,
      data: {
        message: 'Session deleted successfully'
      }
    });

  } catch (error) {
    console.error('Error deleting session:', error);
    
    return NextResponse.json({
      success: false,
      error: 'Failed to delete session'
    }, { status: 500 });
  }
}

/**
 * PATCH /api/mcp/sessions/[id]
 * Partial update of session metadata
 */
export async function PATCH(request: NextRequest, { params }: RouteParams) {
  try {
    const sessionId = params.id;
    const body = await request.json();

    // Validate that only allowed fields are being updated
    const allowedFields = ['name', 'metadata'];
    const updateData: any = {};

    for (const [key, value] of Object.entries(body)) {
      if (allowedFields.includes(key)) {
        if (key === 'metadata') {
          updateData[key] = JSON.stringify(value);
        } else {
          updateData[key] = value;
        }
      }
    }

    if (Object.keys(updateData).length === 0) {
      return NextResponse.json({
        success: false,
        error: 'No valid fields to update'
      }, { status: 400 });
    }

    updateData.updatedAt = new Date();

    const updatedSession = await prisma.generativeSession.update({
      where: { id: sessionId },
      data: updateData,
      include: {
        user: {
          select: { id: true, name: true, email: true }
        },
        parentSession: {
          select: { id: true, name: true, status: true }
        }
      }
    });

    return NextResponse.json({
      success: true,
      data: {
        session: {
          ...updatedSession,
          metadata: updatedSession.metadata ? JSON.parse(updatedSession.metadata) : {}
        }
      }
    });

  } catch (error) {
    console.error('Error updating session:', error);
    
    if (error.code === 'P2025') {
      return NextResponse.json({
        success: false,
        error: 'Session not found'
      }, { status: 404 });
    }

    return NextResponse.json({
      success: false,
      error: 'Failed to update session'
    }, { status: 500 });
  }
}