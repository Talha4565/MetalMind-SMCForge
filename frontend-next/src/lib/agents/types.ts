export type AgentRole = 
  | 'signal-analyzer' 
  | 'backtest-executor' 
  | 'risk-monitor' 
  | 'performance-tracker' 
  | 'data-curator';

export type AgentTier = 'primary' | 'secondary' | 'utility';

export type AgentStatus = 
  | 'idle' 
  | 'running' 
  | 'paused' 
  | 'error' 
  | 'completed' 
  | 'cancelled';

export interface AgentCapability {
  name: string;
  description: string;
  tools?: string[];
}

export interface AgentMemoryConfig {
  namespace: string;
  retention: string;
  shared_with?: AgentRole[];
}

export interface AgentConfig {
  max_concurrent_tasks: number;
  timeout_ms: number;
  retry_policy: 'exponential' | 'linear' | 'none';
  priority: 'critical' | 'high' | 'normal' | 'low';
  budget: {
    tokens: number;
    cost_limit_usd: number;
  };
}

export interface AgentDefinition {
  name: AgentRole;
  role: string;
  description: string;
  tier: AgentTier;
  model: string;
  capabilities: string[];
  tools: string[];
  memory: AgentMemoryConfig;
  config: AgentConfig;
}

export interface AgentTask {
  id: string;
  agent: AgentRole;
  type: string;
  input: Record<string, unknown>;
  status: AgentStatus;
  result?: Record<string, unknown>;
  error?: string;
  startTime: Date;
  endTime?: Date;
  tokensUsed?: number;
  costUSD?: number;
}

export interface AgentMemory {
  namespace: string;
  entries: Array<{
    key: string;
    value: unknown;
    timestamp: Date;
    relevance?: number;
  }>;
}

export interface SwarmConfig {
  topology: 'hierarchical' | 'mesh' | 'adaptive';
  consensus: 'voting' | 'leader' | 'federated';
  replication: number;
  heartbeat_ms: number;
}

export interface AgentSwarm {
  id: string;
  agents: AgentRole[];
  config: SwarmConfig;
  status: 'active' | 'paused' | 'error';
  createdAt: Date;
  updatedAt: Date;
}

export interface AgentMetrics {
  agentId: AgentRole;
  tasksCompleted: number;
  tasksRunning: number;
  tasksFailed: number;
  averageExecutionTime: number;
  totalTokensUsed: number;
  totalCostUSD: number;
  reliability: number; // 0-1
  lastActivityAt: Date;
}
