import axios, { AxiosInstance } from 'axios';
import {
  AgentRole,
  AgentTask,
  AgentMetrics,
  AgentSwarm,
  SwarmConfig,
  AgentDefinition,
} from './types';

/**
 * AgentOrchestrator — Client for Ruflo MCP server
 * Coordinates trading signal agents, backtesting workers, risk monitors, and performance trackers
 */
class AgentOrchestrator {
  private mcpClient: AxiosInstance;
  private wsUrl: string;
  private taskQueue: Map<string, AgentTask> = new Map();
  private agentMetrics: Map<AgentRole, AgentMetrics> = new Map();

  constructor(mcpServerUrl: string = 'http://localhost:3001') {
    this.mcpClient = axios.create({
      baseURL: mcpServerUrl,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });
    this.wsUrl = mcpServerUrl.replace(/^http/, 'ws');
  }

  /**
   * Load agent definition from .claude/agents/
   */
  async loadAgentDefinition(agentRole: AgentRole): Promise<AgentDefinition> {
    try {
      const response = await this.mcpClient.get(`/agents/${agentRole}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to load agent definition for ${agentRole}:`, error);
      throw new Error(`Cannot load agent: ${agentRole}`);
    }
  }

  /**
   * Spawn a new agent task
   */
  async spawnTask(
    agent: AgentRole,
    taskType: string,
    input: Record<string, unknown>
  ): Promise<AgentTask> {
    const task: AgentTask = {
      id: `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      agent,
      type: taskType,
      input,
      status: 'idle',
      startTime: new Date(),
    };

    try {
      await this.mcpClient.post('/agents/spawn', {
        agent,
        taskType,
        input,
        taskId: task.id,
      });

      task.status = 'running';
      this.taskQueue.set(task.id, task);

      // Start polling for task completion
      this.pollTaskStatus(task.id);

      return task;
    } catch (error) {
      task.status = 'error';
      task.error = `Failed to spawn task: ${error}`;
      throw error;
    }
  }

  /**
   * Poll task status until completion
   */
  private async pollTaskStatus(taskId: string, pollInterval = 2000): Promise<void> {
    const startTime = Date.now();
    const maxDuration = 5 * 60 * 1000; // 5 minutes max

    const poll = async () => {
      if (Date.now() - startTime > maxDuration) {
        const task = this.taskQueue.get(taskId);
        if (task) {
          task.status = 'error';
          task.error = 'Task execution timeout';
        }
        return;
      }

      try {
        const response = await this.mcpClient.get(`/agents/tasks/${taskId}`);
        const task = this.taskQueue.get(taskId);

        if (task) {
          task.status = response.data.status;
          task.result = response.data.result;
          task.tokensUsed = response.data.tokensUsed;
          task.costUSD = response.data.costUSD;

          if (
            response.data.status === 'completed' ||
            response.data.status === 'error'
          ) {
            task.endTime = new Date();
            this.updateMetrics(task);
            return;
          }
        }

        // Continue polling
        setTimeout(poll, pollInterval);
      } catch (error) {
        console.error(`Error polling task ${taskId}:`, error);
        setTimeout(poll, pollInterval * 2); // Back off on error
      }
    };

    poll();
  }

  /**
   * Create a swarm of coordinated agents
   */
  async createSwarm(
    agents: AgentRole[],
    config: SwarmConfig
  ): Promise<AgentSwarm> {
    try {
      const response = await this.mcpClient.post('/swarms/create', {
        agents,
        config,
      });

      return response.data;
    } catch (error) {
      console.error('Failed to create swarm:', error);
      throw error;
    }
  }

  /**
   * Execute a coordinated task across multiple agents
   */
  async executeSwarmTask(
    swarmId: string,
    taskType: string,
    input: Record<string, unknown>
  ): Promise<Record<string, AgentTask>> {
    try {
      const _response = await this.mcpClient.post(`/swarms/${swarmId}/execute`, {
        taskType,
        input,
      });

      return _response.data;
    } catch (error) {
      console.error('Failed to execute swarm task:', error);
      throw error;
    }
  }

  /**
   * Store memory across agent namespace
   */
  async storeMemory(
    namespace: string,
    key: string,
    value: unknown
  ): Promise<void> {
    try {
      await this.mcpClient.post('/memory/store', {
        namespace,
        key,
        value,
      });
    } catch (error) {
      console.error(`Failed to store memory in ${namespace}:`, error);
      throw error;
    }
  }

  /**
   * Search memory vector store
   */
  async searchMemory(namespace: string, query: string, limit = 10) {
    try {
      const response = await this.mcpClient.post('/memory/search', {
        namespace,
        query,
        limit,
      });

      return response.data;
    } catch (error) {
      console.error(`Failed to search memory in ${namespace}:`, error);
      throw error;
    }
  }

  /**
   * Get agent metrics
   */
  async getMetrics(agent: AgentRole): Promise<AgentMetrics | null> {
    return this.agentMetrics.get(agent) || null;
  }

  /**
   * Update agent metrics from completed task
   */
  private updateMetrics(task: AgentTask): void {
    let metrics = this.agentMetrics.get(task.agent);

    if (!metrics) {
      metrics = {
        agentId: task.agent,
        tasksCompleted: 0,
        tasksRunning: 0,
        tasksFailed: 0,
        averageExecutionTime: 0,
        totalTokensUsed: 0,
        totalCostUSD: 0,
        reliability: 1.0,
        lastActivityAt: new Date(),
      };
    }

    const executionTime = task.endTime
      ? task.endTime.getTime() - task.startTime.getTime()
      : 0;

    if (task.status === 'completed') {
      metrics.tasksCompleted++;
      metrics.averageExecutionTime =
        (metrics.averageExecutionTime * (metrics.tasksCompleted - 1) +
          executionTime) /
        metrics.tasksCompleted;
    } else if (task.status === 'error') {
      metrics.tasksFailed++;
      metrics.reliability = metrics.tasksCompleted /
        (metrics.tasksCompleted + metrics.tasksFailed);
    }

    metrics.totalTokensUsed += task.tokensUsed || 0;
    metrics.totalCostUSD += task.costUSD || 0;
    metrics.lastActivityAt = new Date();

    this.agentMetrics.set(task.agent, metrics);
  }

  /**
   * Cancel a running task
   */
  async cancelTask(taskId: string): Promise<void> {
    try {
      await this.mcpClient.post(`/agents/tasks/${taskId}/cancel`);
      const task = this.taskQueue.get(taskId);
      if (task) {
        task.status = 'cancelled';
        task.endTime = new Date();
      }
    } catch (error) {
      console.error(`Failed to cancel task ${taskId}:`, error);
      throw error;
    }
  }

  /**
   * Get all active tasks
   */
  getActiveTasks(): AgentTask[] {
    return Array.from(this.taskQueue.values()).filter(
      (t) => t.status === 'running' || t.status === 'idle'
    );
  }

  /**
   * Get task by ID
   */
  getTask(taskId: string): AgentTask | undefined {
    return this.taskQueue.get(taskId);
  }

  /**
   * Reset orchestrator state
   */
  reset(): void {
    this.taskQueue.clear();
    this.agentMetrics.clear();
  }
}

// Export singleton
export const agentOrchestrator = new AgentOrchestrator();
