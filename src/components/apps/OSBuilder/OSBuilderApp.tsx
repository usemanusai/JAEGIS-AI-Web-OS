/**
 * OS Builder App - Main application for MCP Server AI-Powered OS Generation
 */

'use client'

import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Cpu, 
  FileText, 
  Settings, 
  Activity, 
  Zap, 
  Brain,
  Database,
  Search,
  GitBranch,
  Clock,
  Users,
  BarChart3
} from 'lucide-react';

import SessionDashboard from './SessionDashboard';
import NewSessionForm from './NewSessionForm';
import SessionDetail from './SessionDetail';
import SpecificationViewer from './SpecificationViewer';

export interface OSBuilderAppProps {
  onClose?: () => void;
}

export interface GenerativeSession {
  id: string;
  name: string;
  type: 'SPEC_TO_SYSTEM' | 'SYSTEM_TO_SPEC';
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  progress: number;
  masterPrompt?: string;
  baseDocument?: string;
  generatedArtifactPath?: string;
  createdAt: string;
  updatedAt: string;
  buildTime?: number;
  metadata: Record<string, any>;
  parentSession?: {
    id: string;
    name: string;
    status: string;
  };
  childSessions?: Array<{
    id: string;
    name: string;
    status: string;
    createdAt: string;
  }>;
  buildSteps?: Array<{
    id: string;
    stepId: string;
    type: string;
    description: string;
    status: string;
    executionOrder: number;
    executionTime?: number;
  }>;
}

export default function OSBuilderApp({ onClose }: OSBuilderAppProps) {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedSession, setSelectedSession] = useState<GenerativeSession | null>(null);
  const [sessions, setSessions] = useState<GenerativeSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    totalSessions: 0,
    activeSessions: 0,
    completedSessions: 0,
    failedSessions: 0,
    avgBuildTime: 0,
    successRate: 0
  });

  // Load sessions and stats on component mount
  useEffect(() => {
    loadSessions();
    loadStats();
    
    // Set up polling for real-time updates
    const interval = setInterval(() => {
      if (activeTab === 'dashboard') {
        loadSessions();
        loadStats();
      }
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, [activeTab]);

  const loadSessions = async () => {
    try {
      const response = await fetch('/api/mcp/sessions');
      const data = await response.json();
      
      if (data.success) {
        setSessions(data.data.sessions);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch('/api/mcp/sessions/stats');
      const data = await response.json();
      
      if (data.success) {
        setStats(data.data);
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleSessionCreated = (session: GenerativeSession) => {
    setSessions(prev => [session, ...prev]);
    setSelectedSession(session);
    setActiveTab('session-detail');
    loadStats(); // Refresh stats
  };

  const handleSessionSelected = (session: GenerativeSession) => {
    setSelectedSession(session);
    setActiveTab('session-detail');
  };

  const handleSessionUpdated = (updatedSession: GenerativeSession) => {
    setSessions(prev => 
      prev.map(session => 
        session.id === updatedSession.id ? updatedSession : session
      )
    );
    
    if (selectedSession?.id === updatedSession.id) {
      setSelectedSession(updatedSession);
    }
    
    loadStats(); // Refresh stats
  };

  const handleSessionDeleted = (sessionId: string) => {
    setSessions(prev => prev.filter(session => session.id !== sessionId));
    
    if (selectedSession?.id === sessionId) {
      setSelectedSession(null);
      setActiveTab('dashboard');
    }
    
    loadStats(); // Refresh stats
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'bg-green-500';
      case 'IN_PROGRESS': return 'bg-blue-500';
      case 'FAILED': return 'bg-red-500';
      case 'CANCELLED': return 'bg-gray-500';
      default: return 'bg-yellow-500';
    }
  };

  const getTypeIcon = (type: string) => {
    return type === 'SPEC_TO_SYSTEM' ? <Cpu className="h-4 w-4" /> : <FileText className="h-4 w-4" />;
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                OS Builder
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                AI-Powered OS Generation System
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Quick Stats */}
            <div className="hidden md:flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-1">
                <Activity className="h-4 w-4 text-blue-500" />
                <span className="text-gray-600 dark:text-gray-300">
                  {stats.activeSessions} Active
                </span>
              </div>
              <div className="flex items-center space-x-1">
                <BarChart3 className="h-4 w-4 text-green-500" />
                <span className="text-gray-600 dark:text-gray-300">
                  {stats.successRate}% Success
                </span>
              </div>
              <div className="flex items-center space-x-1">
                <Clock className="h-4 w-4 text-purple-500" />
                <span className="text-gray-600 dark:text-gray-300">
                  {Math.round(stats.avgBuildTime / 1000)}s Avg
                </span>
              </div>
            </div>
            
            {onClose && (
              <Button variant="outline" onClick={onClose}>
                Close
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
          <TabsList className="grid w-full grid-cols-4 mb-6">
            <TabsTrigger value="dashboard" className="flex items-center space-x-2">
              <Activity className="h-4 w-4" />
              <span>Dashboard</span>
            </TabsTrigger>
            <TabsTrigger value="new-session" className="flex items-center space-x-2">
              <Zap className="h-4 w-4" />
              <span>New Session</span>
            </TabsTrigger>
            <TabsTrigger 
              value="session-detail" 
              className="flex items-center space-x-2"
              disabled={!selectedSession}
            >
              <Settings className="h-4 w-4" />
              <span>Session Detail</span>
            </TabsTrigger>
            <TabsTrigger 
              value="specification" 
              className="flex items-center space-x-2"
              disabled={!selectedSession || selectedSession.status !== 'COMPLETED'}
            >
              <FileText className="h-4 w-4" />
              <span>Specification</span>
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="h-full">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
              {/* Stats Cards */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Sessions</CardTitle>
                  <Database className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.totalSessions}</div>
                  <p className="text-xs text-muted-foreground">
                    All time sessions
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Sessions</CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-blue-600">{stats.activeSessions}</div>
                  <p className="text-xs text-muted-foreground">
                    Currently running
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
                  <BarChart3 className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">{stats.successRate}%</div>
                  <p className="text-xs text-muted-foreground">
                    Completed successfully
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Avg Build Time</CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-purple-600">
                    {Math.round(stats.avgBuildTime / 1000)}s
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Average completion time
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Session Dashboard */}
            <SessionDashboard
              sessions={sessions}
              isLoading={isLoading}
              onSessionSelected={handleSessionSelected}
              onSessionUpdated={handleSessionUpdated}
              onSessionDeleted={handleSessionDeleted}
              onRefresh={loadSessions}
            />
          </TabsContent>

          {/* New Session Tab */}
          <TabsContent value="new-session" className="h-full">
            <Card className="max-w-4xl mx-auto">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Zap className="h-5 w-5" />
                  <span>Create New Generation Session</span>
                </CardTitle>
                <CardDescription>
                  Start a new AI-powered OS generation or analysis session
                </CardDescription>
              </CardHeader>
              <CardContent>
                <NewSessionForm onSessionCreated={handleSessionCreated} />
              </CardContent>
            </Card>
          </TabsContent>

          {/* Session Detail Tab */}
          <TabsContent value="session-detail" className="h-full">
            {selectedSession ? (
              <SessionDetail
                session={selectedSession}
                onSessionUpdated={handleSessionUpdated}
                onSessionDeleted={handleSessionDeleted}
                onBack={() => setActiveTab('dashboard')}
              />
            ) : (
              <Card>
                <CardContent className="flex items-center justify-center h-64">
                  <div className="text-center">
                    <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">Select a session to view details</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Specification Tab */}
          <TabsContent value="specification" className="h-full">
            {selectedSession && selectedSession.status === 'COMPLETED' ? (
              <SpecificationViewer
                session={selectedSession}
                onBack={() => setActiveTab('session-detail')}
              />
            ) : (
              <Card>
                <CardContent className="flex items-center justify-center h-64">
                  <div className="text-center">
                    <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">
                      Specification available only for completed sessions
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Footer */}
      <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-3">
        <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
          <div className="flex items-center space-x-4">
            <span>JAEGIS MCP Server v1.0.0</span>
            <Badge variant="outline" className="text-xs">
              AI-Powered
            </Badge>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${stats.activeSessions > 0 ? 'bg-green-500' : 'bg-gray-400'}`} />
            <span>
              {stats.activeSessions > 0 ? 'Active' : 'Idle'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}