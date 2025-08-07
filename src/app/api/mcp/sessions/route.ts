/**
 * MCP Sessions API Routes
 * Handles CRUD operations for generative sessions
 */

import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import { z } from 'zod';
import MCPServerOrchestrator from '../../../../services/mcp-server/MCPServerOrchestrator';

const prisma = new PrismaClient();

// Initialize MCP Server Orchestrator
const mcpOrchestrator = new MCPServerOrchestrator({
  workspaceDir: process.env.MCP_WORKSPACE_DIR || './workspace',
  maxConcurrentSessions: parseInt(process.env.MCP_MAX_CONCURRENT_SESSIONS || '5'),
  sessionTimeoutMs: parseInt(process.env.MCP_SESSION_TIMEOUT_MS || '1800000'), // 30 minutes
  enableDocker: process.env.MCP_ENABLE_DOCKER === 'true',
  zaiApiKey: process.env.ZAI_API_KEY || '',
  redisUrl: process.env.REDIS_URL
});

// Initialize orchestrator on first use
let orchestratorInitialized = false;
async function ensureOrchestratorInitialized() {
  if (!orchestratorInitialized) {
    await mcpOrchestrator.initialize();
    orchestratorInitialized = true;
  }
}

// Validation schemas
const CreateSessionSchema = z.object({
  name: z.string().min(1).max(255),
  type: z.enum(['SPEC_TO_SYSTEM', 'SYSTEM_TO_SPEC']),
  masterPrompt: z.string().optional(),
  baseDocument: z.string().optional(),
  systemTarget: z.string().optional(),
  parentSessionId: z.string().optional(),
  metadata: z.record(z.any()).optional()
});

const ListSessionsSchema = z.object({
  page: z.string().optional().transform(val => val ? parseInt(val) : 1),
  limit: z.string().optional().transform(val => val ? parseInt(val) : 20),
  status: z.enum(['PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELLED']).optional(),
  type: z.enum(['SPEC_TO_SYSTEM', 'SYSTEM_TO_SPEC']).optional(),
  parentSessionId: z.string().optional(),
  search: z.string().optional()
});

/**
 * GET /api/mcp/sessions
 * List all sessions with pagination and filtering
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const params = Object.fromEntries(searchParams.entries());
    
    const validatedParams = ListSessionsSchema.parse(params);
    const { page, limit, status, type, parentSessionId, search } = validatedParams;

    // Build where clause
    const where: any = {};
    
    if (status) where.status = status;
    if (type) where.type = type;
    if (parentSessionId) where.parentSessionId = parentSessionId;
    if (search) {
      where.OR = [
        { name: { contains: search, mode: 'insensitive' } },
        { masterPrompt: { contains: search, mode: 'insensitive' } }
      ];
    }

    // Calculate pagination
    const skip = (page - 1) * limit;

    // Fetch sessions with counts
    const [sessions, totalCount] = await Promise.all([
      prisma.generativeSession.findMany({
        where,
        skip,
        take: limit,
        orderBy: { createdAt: 'desc' },
        include: {
          user: {
            select: { id: true, name: true, email: true }
          },
          parentSession: {
            select: { id: true, name: true, status: true }
          },
          childSessions: {
            select: { id: true, name: true, status: true }
          },
          _count: {
            select: { buildSteps: true }
          }
        }
      }),
      prisma.generativeSession.count({ where })
    ]);

    // Calculate pagination metadata
    const totalPages = Math.ceil(totalCount / limit);
    const hasNextPage = page < totalPages;
    const hasPreviousPage = page > 1;

    return NextResponse.json({
      success: true,
      data: {
        sessions,
        pagination: {
          page,
          limit,
          totalCount,
          totalPages,
          hasNextPage,
          hasPreviousPage
        }
      }
    });

  } catch (error) {
    console.error('Error fetching sessions:', error);
    
    if (error instanceof z.ZodError) {
      return NextResponse.json({
        success: false,
        error: 'Invalid query parameters',
        details: error.errors
      }, { status: 400 });
    }

    return NextResponse.json({
      success: false,
      error: 'Failed to fetch sessions'
    }, { status: 500 });
  }
}

/**
 * POST /api/mcp/sessions
 * Create new session and trigger generation
 */
export async function POST(request: NextRequest) {
  try {
    await ensureOrchestratorInitialized();
    
    const body = await request.json();
    const validatedData = CreateSessionSchema.parse(body);

    // Validate required fields based on session type
    if (validatedData.type === 'SPEC_TO_SYSTEM') {
      if (!validatedData.masterPrompt || !validatedData.baseDocument) {
        return NextResponse.json({
          success: false,
          error: 'Master prompt and base document are required for Spec-to-System generation'
        }, { status: 400 });
      }
    } else if (validatedData.type === 'SYSTEM_TO_SPEC') {
      if (!validatedData.systemTarget) {
        return NextResponse.json({
          success: false,
          error: 'System target is required for System-to-Spec analysis'
        }, { status: 400 });
      }
    }

    // Create session in orchestrator
    const session = await mcpOrchestrator.createSession(
      validatedData.name,
      validatedData.type,
      {
        masterPrompt: validatedData.masterPrompt,
        baseDocument: validatedData.baseDocument,
        systemTarget: validatedData.systemTarget,
        parentSessionId: validatedData.parentSessionId,
        metadata: validatedData.metadata
      }
    );

    // Save session to database
    const dbSession = await prisma.generativeSession.create({
      data: {
        id: session.id,
        name: session.name,
        type: session.type as any,
        masterPrompt: session.masterPrompt,
        baseDocument: session.baseDocument,
        status: session.status as any,
        progress: session.progress,
        logs: JSON.stringify(session.logs),
        parentSessionId: session.parentSessionId,
        metadata: JSON.stringify(session.metadata)
      },
      include: {
        parentSession: {
          select: { id: true, name: true, status: true }
        }
      }
    });

    // Start generation process asynchronously
    if (validatedData.type === 'SPEC_TO_SYSTEM') {
      mcpOrchestrator.executeSpecToSystem(session.id).catch(error => {
        console.error(`Spec-to-System generation failed for session ${session.id}:`, error);
      });
    } else {
      mcpOrchestrator.executeSystemToSpec(session.id, validatedData.systemTarget!).catch(error => {
        console.error(`System-to-Spec analysis failed for session ${session.id}:`, error);
      });
    }

    return NextResponse.json({
      success: true,
      data: {
        session: dbSession,
        message: 'Session created and generation started'
      }
    }, { status: 201 });

  } catch (error) {
    console.error('Error creating session:', error);
    
    if (error instanceof z.ZodError) {
      return NextResponse.json({
        success: false,
        error: 'Invalid request data',
        details: error.errors
      }, { status: 400 });
    }

    return NextResponse.json({
      success: false,
      error: 'Failed to create session'
    }, { status: 500 });
  }
}

/**
 * DELETE /api/mcp/sessions
 * Bulk delete sessions
 */
export async function DELETE(request: NextRequest) {
  try {
    await ensureOrchestratorInitialized();
    
    const { searchParams } = new URL(request.url);
    const sessionIds = searchParams.get('ids')?.split(',') || [];

    if (sessionIds.length === 0) {
      return NextResponse.json({
        success: false,
        error: 'No session IDs provided'
      }, { status: 400 });
    }

    // Delete sessions from orchestrator
    const deletePromises = sessionIds.map(async (sessionId) => {
      try {
        await mcpOrchestrator.deleteSession(sessionId);
        return { sessionId, success: true };
      } catch (error) {
        return { sessionId, success: false, error: error.message };
      }
    });

    const results = await Promise.all(deletePromises);

    // Delete from database
    await prisma.generativeSession.deleteMany({
      where: {
        id: { in: sessionIds }
      }
    });

    const successCount = results.filter(r => r.success).length;
    const failureCount = results.length - successCount;

    return NextResponse.json({
      success: true,
      data: {
        deleted: successCount,
        failed: failureCount,
        results
      }
    });

  } catch (error) {
    console.error('Error deleting sessions:', error);
    
    return NextResponse.json({
      success: false,
      error: 'Failed to delete sessions'
    }, { status: 500 });
  }
}

// Utility function to sync session status from orchestrator to database
export async function syncSessionStatus(sessionId: string) {
  try {
    const orchestratorSession = mcpOrchestrator.getSession(sessionId);
    
    if (orchestratorSession) {
      await prisma.generativeSession.update({
        where: { id: sessionId },
        data: {
          status: orchestratorSession.status as any,
          progress: orchestratorSession.progress,
          logs: JSON.stringify(orchestratorSession.logs),
          generatedArtifactPath: orchestratorSession.generatedArtifactPath,
          updatedAt: new Date()
        }
      });
    }
  } catch (error) {
    console.error(`Failed to sync session status for ${sessionId}:`, error);
  }
}

// Setup real-time session updates
mcpOrchestrator.on('sessionStatusChanged', async ({ sessionId, status }) => {
  await syncSessionStatus(sessionId);
});

mcpOrchestrator.on('sessionProgressChanged', async ({ sessionId, progress }) => {
  await syncSessionStatus(sessionId);
});

mcpOrchestrator.on('sessionCompleted', async (session) => {
  await syncSessionStatus(session.id);
});

mcpOrchestrator.on('sessionLogAdded', async ({ sessionId }) => {
  await syncSessionStatus(sessionId);
});